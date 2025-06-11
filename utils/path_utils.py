#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
路径工具模块
提供开发环境和打包环境的路径兼容性
"""

import os
import sys

def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径，兼容开发环境和打包后环境
    
    Args:
        relative_path (str): 相对路径
        
    Returns:
        str: 绝对路径
    """
    # 如果是PyInstaller打包后的环境
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    
    # 开发环境：从项目根目录开始
    # 获取当前文件所在目录的上级目录（项目根目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # 上级目录
    return os.path.join(project_root, relative_path)

def get_language_file_path(language_code):
    """
    获取语言文件路径
    
    Args:
        language_code (str): 语言代码，如 'zh', 'en'
        
    Returns:
        str: 语言文件的绝对路径
    """
    return get_resource_path(os.path.join("languages", f"{language_code}.json"))