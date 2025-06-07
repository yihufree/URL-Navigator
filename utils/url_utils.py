#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode

logger = logging.getLogger(__name__)

def normalize_url(url):
    """
    规范化URL
    
    Args:
        url: 输入URL
        
    Returns:
        规范化后的URL
    """
    # 添加协议前缀
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # 解析URL
    parsed = urlparse(url)
    
    # 移除www前缀
    netloc = parsed.netloc
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    
    # 移除默认端口
    if ':' in netloc:
        host, port = netloc.split(':', 1)
        if (parsed.scheme == 'http' and port == '80') or (parsed.scheme == 'https' and port == '443'):
            netloc = host
    
    # 移除尾部斜杠
    path = parsed.path
    if path == '/':
        path = ''
    
    # 重建URL
    normalized = urlunparse((
        parsed.scheme,
        netloc,
        path,
        parsed.params,
        parsed.query,
        ''  # 移除片段
    ))
    
    return normalized

def get_domain(url):
    """
    获取URL的域名
    
    Args:
        url: 输入URL
        
    Returns:
        域名
    """
    # 添加协议前缀
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # 解析URL
    parsed = urlparse(url)
    
    # 获取域名
    domain = parsed.netloc
    
    # 移除端口
    if ':' in domain:
        domain = domain.split(':', 1)[0]
    
    return domain

def get_base_url(url):
    """
    获取URL的基础URL
    
    Args:
        url: 输入URL
        
    Returns:
        基础URL
    """
    # 添加协议前缀
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # 解析URL
    parsed = urlparse(url)
    
    # 构建基础URL
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    return base_url

def is_valid_url(url):
    """
    检查URL是否有效
    
    Args:
        url: 输入URL
        
    Returns:
        是否有效
    """
    # 简单的URL验证正则表达式
    pattern = re.compile(
        r'^(https?://)?' # 协议
        r'((([a-z\d]([a-z\d-]*[a-z\d])*)\.)+[a-z]{2,}|' # 域名
        r'((\d{1,3}\.){3}\d{1,3}))' # IP地址
        r'(:\d+)?' # 端口
        r'(/[-a-z\d%_.~+]*)*' # 路径
        r'(\?[;&a-z\d%_.~+=-]*)?' # 查询字符串
        r'(#[-a-z\d_]*)?$', # 片段
        re.IGNORECASE
    )
    
    return bool(pattern.match(url))

def clean_url_for_display(url, max_length=50):
    """
    清理URL用于显示
    
    Args:
        url: 输入URL
        max_length: 最大长度
        
    Returns:
        清理后的URL
    """
    # 移除协议
    if url.startswith(('http://', 'https://')):
        url = url.split('://', 1)[1]
    
    # 移除尾部斜杠
    if url.endswith('/'):
        url = url[:-1]
    
    # 截断长URL
    if len(url) > max_length:
        url = url[:max_length-3] + '...'
    
    return url

def extract_query_params(url):
    """
    提取URL查询参数
    
    Args:
        url: 输入URL
        
    Returns:
        查询参数字典
    """
    # 解析URL
    parsed = urlparse(url)
    
    # 提取查询参数
    params = parse_qs(parsed.query)
    
    # 转换为单值字典
    result = {}
    for key, values in params.items():
        result[key] = values[0] if values else ''
    
    return result

def build_url(base_url, path=None, params=None):
    """
    构建URL
    
    Args:
        base_url: 基础URL
        path: 路径
        params: 查询参数字典
        
    Returns:
        构建的URL
    """
    # 规范化基础URL
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'https://{base_url}'
    
    # 添加路径
    if path:
        if not path.startswith('/'):
            path = f'/{path}'
        url = urljoin(base_url, path)
    else:
        url = base_url
    
    # 添加查询参数
    if params:
        parsed = urlparse(url)
        query = urlencode(params)
        url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query,
            parsed.fragment
        ))
    
    return url

def validate_url(url):
    """
    验证 URL 是否合法安全
    
    Args:
        url: 要验证的 URL
        
    Returns:
        (is_valid, sanitized_url, message) 元组:
        - is_valid: 布尔值，表示 URL 是否有效
        - sanitized_url: 清理后的 URL
        - message: 如果无效，包含错误消息；如果有警告，包含警告消息；否则为空字符串
    """
    if not url or not isinstance(url, str):
        return False, "", "URL 不能为空"
        
    # 移除前后空白
    url = url.strip()
    
    if not url:
        return False, "", "URL 不能为空"
        
    # 提取协议
    protocol = ""
    if "://" in url:
        protocol = url.split("://")[0].lower()
    
    # 检查危险协议
    dangerous_protocols = [
        "javascript", "data", "vbscript", "file"
    ]
    
    if protocol in dangerous_protocols:
        return False, "", f"不安全的协议: {protocol}"
    
    # 对于没有协议的 URL，添加 https://
    if not protocol:
        url = "https://" + url
        protocol = "https"
    
    # 对于非 http/https 的协议，标记为警告但仍然有效
    if protocol not in ["http", "https"]:
        return True, url, f"警告: 非标准协议 {protocol}"
    
    # 基本格式检查
    if "." not in url.split("://")[1].split("/")[0]:
        return False, "", "无效的 URL 格式"
    
    return True, url, ""