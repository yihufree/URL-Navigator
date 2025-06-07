#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import logging
import json
import tempfile
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

def ensure_dir(directory):
    """
    确保目录存在
    
    Args:
        directory: 目录路径
        
    Returns:
        目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def get_file_hash(file_path):
    """
    获取文件哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件的MD5哈希值
    """
    if not os.path.isfile(file_path):
        return None
    
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read(65536)  # 读取64KB块
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    
    return hasher.hexdigest()

def safe_filename(filename):
    """
    生成安全的文件名
    
    Args:
        filename: 原始文件名
        
    Returns:
        安全的文件名
    """
    # 移除非法字符
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    
    # 如果文件名为空，使用时间戳
    if not safe_name:
        safe_name = f"file_{int(datetime.now().timestamp())}"
    
    return safe_name

def get_file_extension(file_path):
    """
    获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件扩展名（小写）
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower()

def get_temp_file(prefix="", suffix=""):
    """
    获取临时文件路径
    
    Args:
        prefix: 文件名前缀
        suffix: 文件名后缀
        
    Returns:
        临时文件路径
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path

def copy_file(src, dst, overwrite=False):
    """
    复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        是否成功
    """
    if not os.path.isfile(src):
        logger.error(f"源文件不存在: {src}")
        return False
    
    if os.path.exists(dst) and not overwrite:
        logger.error(f"目标文件已存在: {dst}")
        return False
    
    try:
        shutil.copy2(src, dst)
        logger.info(f"文件已复制: {src} -> {dst}")
        return True
    except Exception as e:
        logger.error(f"复制文件失败: {e}")
        return False

def move_file(src, dst, overwrite=False):
    """
    移动文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        是否成功
    """
    if not os.path.isfile(src):
        logger.error(f"源文件不存在: {src}")
        return False
    
    if os.path.exists(dst) and not overwrite:
        logger.error(f"目标文件已存在: {dst}")
        return False
    
    try:
        shutil.move(src, dst)
        logger.info(f"文件已移动: {src} -> {dst}")
        return True
    except Exception as e:
        logger.error(f"移动文件失败: {e}")
        return False

def delete_file(file_path):
    """
    删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否成功
    """
    if not os.path.isfile(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False
    
    try:
        os.remove(file_path)
        logger.info(f"文件已删除: {file_path}")
        return True
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return False

def read_json_file(file_path, default=None):
    """
    读取JSON文件
    
    Args:
        file_path: 文件路径
        default: 默认值
        
    Returns:
        JSON数据
    """
    if not os.path.isfile(file_path):
        logger.warning(f"JSON文件不存在: {file_path}")
        return default
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取JSON文件失败: {e}")
        return default

def write_json_file(file_path, data, indent=2):
    """
    写入JSON文件
    
    Args:
        file_path: 文件路径
        data: JSON数据
        indent: 缩进
        
    Returns:
        是否成功
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory:
            ensure_dir(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        
        logger.info(f"JSON数据已写入: {file_path}")
        return True
    except Exception as e:
        logger.error(f"写入JSON文件失败: {e}")
        return False

def clean_old_files(directory, days=30, extensions=None):
    """
    清理旧文件
    
    Args:
        directory: 目录路径
        days: 天数
        extensions: 文件扩展名列表
        
    Returns:
        删除的文件数量
    """
    if not os.path.isdir(directory):
        logger.error(f"目录不存在: {directory}")
        return 0
    
    now = datetime.now()
    count = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # 检查是否是文件
        if not os.path.isfile(file_path):
            continue
        
        # 检查扩展名
        if extensions:
            ext = get_file_extension(file_path)
            if ext not in extensions:
                continue
        
        # 检查文件修改时间
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        age_days = (now - mtime).days
        
        if age_days > days:
            if delete_file(file_path):
                count += 1
    
    logger.info(f"已清理 {count} 个旧文件")
    return count

def is_safe_path(base_dir, path):
    """
    验证给定的路径是否安全（防止路径遍历攻击）
    
    Args:
        base_dir: 基础目录，所有路径必须在此目录内
        path: 需要验证的路径
        
    Returns:
        布尔值，表示路径是否安全
    """
    # 将路径转换为绝对路径
    abs_base_dir = os.path.abspath(base_dir)
    abs_path = os.path.abspath(path)
    
    # 验证路径是否在基础目录内
    is_safe = abs_path.startswith(abs_base_dir)
    
    if not is_safe:
        logger.warning(f"检测到不安全的路径访问尝试: {path} 不在 {base_dir} 内")
    
    return is_safe

def safe_file_operation(base_dir, path, operation_func, *args, **kwargs):
    """
    安全执行文件操作，带路径验证和错误处理
    
    Args:
        base_dir: 基础目录
        path: 目标文件路径
        operation_func: 文件操作函数
        *args, **kwargs: 传递给操作函数的参数
        
    Returns:
        (success, result) 元组:
        - success: 布尔值，表示操作是否成功
        - result: 如果成功，包含操作结果；如果失败，包含错误消息
    """
    try:
        # 验证路径安全性
        if not is_safe_path(base_dir, path):
            return False, "不安全的文件路径"
            
        # 执行文件操作
        result = operation_func(path, *args, **kwargs)
        return True, result
    except PermissionError:
        logger.error(f"权限错误: 无法访问 {path}")
        return False, "权限错误: 无法访问文件"
    except FileNotFoundError:
        logger.error(f"文件未找到: {path}")
        return False, "文件未找到"
    except IsADirectoryError:
        logger.error(f"目标是目录，非文件: {path}")
        return False, "目标是目录，非文件"
    except Exception as e:
        logger.error(f"文件操作错误: {e}")
        return False, f"文件操作错误: {str(e)}"
        
def safe_read_file(base_dir, file_path, encoding='utf-8'):
    """
    安全地读取文件内容
    
    Args:
        base_dir: 基础目录
        file_path: 文件路径
        encoding: 文件编码
        
    Returns:
        (success, content) 元组:
        - success: 布尔值，表示读取是否成功
        - content: 如果成功，包含文件内容；如果失败，包含错误消息
    """
    def read_func(path, enc):
        with open(path, 'r', encoding=enc) as f:
            return f.read()
            
    return safe_file_operation(base_dir, file_path, read_func, encoding)
    
def safe_write_file(base_dir, file_path, content, encoding='utf-8'):
    """
    安全地写入文件内容
    
    Args:
        base_dir: 基础目录
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码
        
    Returns:
        (success, message) 元组:
        - success: 布尔值，表示写入是否成功
        - message: 如果失败，包含错误消息；如果成功，为空字符串
    """
    def write_func(path, cont, enc):
        with open(path, 'w', encoding=enc) as f:
            f.write(cont)
        return ""
            
    return safe_file_operation(base_dir, file_path, write_func, content, encoding)