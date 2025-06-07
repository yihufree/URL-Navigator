#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标路径标准化脚本
用于修复default_data.json中的硬编码路径问题
"""

import json
import os
import sys
import shutil
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.icons import resource_path

def backup_file(file_path):
    """备份文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"已备份原文件: {backup_path}")
    return backup_path

def extract_icon_filename(icon_path):
    """从路径中提取图标文件名"""
    if not icon_path:
        return "globe.png"
    
    # 提取文件名
    filename = os.path.basename(icon_path)
    
    # 如果没有扩展名，默认为png
    if '.' not in filename:
        filename += '.png'
    
    return filename

def is_hardcoded_path(icon_path):
    """判断是否为硬编码路径（需要修复的路径）"""
    if not icon_path:
        return False
    
    # 需要修复的硬编码路径模式
    hardcoded_patterns = [
        "C:\\Users\\",  # 用户目录
        "E:\\YifreePreject\\",  # 开发环境路径
        "AppData\\Local\\Temp\\",  # 临时目录
        "\\_MEI",  # PyInstaller临时目录
    ]
    
    for pattern in hardcoded_patterns:
        if pattern in icon_path:
            return True
    
    return False

def standardize_icon_path(icon_path):
    """标准化图标路径"""
    if not icon_path:
        return resource_path("resources/icons/globe.png")
    
    # 如果已经是标准路径，直接返回
    if icon_path.startswith("resources/"):
        return icon_path
    
    # 如果不是硬编码路径，保持原样（可能是用户设置的路径）
    if not is_hardcoded_path(icon_path):
        return icon_path
    
    # 提取图标文件名
    filename = extract_icon_filename(icon_path)
    
    # 检查标准图标目录中是否存在该文件
    standard_icon_path = f"resources/icons/{filename}"
    full_standard_path = resource_path(standard_icon_path)
    
    if os.path.exists(full_standard_path):
        return standard_icon_path
    else:
        # 如果文件不存在，使用默认图标
        print(f"警告: 图标文件不存在 {filename}，使用默认图标")
        return "resources/icons/globe.png"

def process_item(item, stats):
    """处理单个项目"""
    if not isinstance(item, dict):
        return
    
    if item.get("type") == "url" and "icon" in item:
        original_icon = item["icon"]
        if is_hardcoded_path(original_icon):
            new_icon = standardize_icon_path(original_icon)
            item["icon"] = new_icon
            stats["fixed_count"] += 1
            print(f"修复路径: {os.path.basename(original_icon)} -> {new_icon}")
        else:
            stats["kept_count"] += 1
    
    elif item.get("type") == "folder" and "children" in item:
        for child in item["children"].values():
            process_item(child, stats)

def fix_default_data_paths(data_file):
    """修复default_data.json中的图标路径"""
    print(f"开始处理文件: {data_file}")
    
    # 检查文件是否存在
    if not os.path.exists(data_file):
        print(f"错误: 文件不存在 {data_file}")
        return False
    
    # 备份原文件
    backup_path = backup_file(data_file)
    
    try:
        # 读取JSON数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 统计信息
        stats = {
            "fixed_count": 0,  # 修复的路径数量
            "kept_count": 0,   # 保留的路径数量
        }
        
        # 处理所有项目
        for item in data.values():
            process_item(item, stats)
        
        # 保存修复后的文件
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n修复完成!")
        print(f"修复的硬编码路径: {stats['fixed_count']} 个")
        print(f"保留的用户路径: {stats['kept_count']} 个")
        print(f"备份文件: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"错误: 处理文件时出现异常: {e}")
        # 恢复备份文件
        shutil.copy2(backup_path, data_file)
        print(f"已恢复原文件")
        return False

def main():
    """主函数"""
    # 获取default_data.json文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_file = os.path.join(project_root, "resources", "default_data.json")
    
    print("=" * 60)
    print("图标路径标准化脚本")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print(f"数据文件: {data_file}")
    print()
    print("开始执行路径修复...")
    
    # 执行修复
    success = fix_default_data_paths(data_file)
    
    if success:
        print("\n路径标准化完成! 请测试应用程序功能是否正常。")
    else:
        print("\n路径标准化失败! 请检查错误信息。")

if __name__ == "__main__":
    main()