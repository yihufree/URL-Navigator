#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
布局优化测试脚本
用于验证网址卡片布局和快捷命令按钮间距的优化效果
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

def test_card_layout_spacing():
    """测试网址卡片间距设置"""
    print("=== 测试网址卡片布局优化 ===")
    
    # 检查bookmark_grid.py文件中的间距设置
    bookmark_grid_file = "ui/bookmark_grid.py"
    
    with open(bookmark_grid_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查主布局间距
    if "main_layout.setSpacing(6)" in content:
        print("✓ 主布局间距已优化 (12px -> 6px)")
    else:
        print("✗ 主布局间距未正确设置")
    
    # 检查右侧布局间距  
    if "right_layout.setSpacing(1)" in content:
        print("✓ 右侧布局间距已优化 (2px -> 1px)")
    else:
        print("✗ 右侧布局间距未正确设置")

def test_toolbar_button_spacing():
    """测试工具栏按钮间距设置"""
    print("\n=== 测试快捷命令按钮间距优化 ===")
    
    # 检查main_window.py文件中的间距设置
    main_window_file = "ui/main_window.py"
    
    with open(main_window_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查工具栏间距
    if "spacing: 1px" in content:
        print("✓ 工具栏间距已优化 (2px -> 1px)")
    else:
        print("✗ 工具栏间距未正确设置")
    
    # 检查样式文件
    style_file = "resources/styles/style.qss"
    
    with open(style_file, 'r', encoding='utf-8') as f:
        style_content = f.read()
    
    # 检查按钮样式
    if "padding: 2px;" in style_content and "margin: 0px;" in style_content:
        print("✓ 按钮样式已优化 (padding: 3px->2px, margin: 1px->0px)")
    else:
        print("✗ 按钮样式未正确设置")

def test_backup_message():
    """测试备份提示语修改"""
    print("\n=== 测试备份提示语修改 ===")
    
    dialogs_file = "ui/dialogs.py"
    
    with open(dialogs_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查新的备份提示语
    expected_message = "软件每次启动时，会自动将书签数据以JSON和HTML格式备份到设置的备份文件夹，同时备份日志文件。当备份数量较多占用空间较大时，您可进入自动备份目录下手工进行清理。"
    
    if expected_message in content:
        print("✓ 备份提示语已更新")
    else:
        print("✗ 备份提示语未正确修改")

def show_optimization_summary():
    """显示优化汇总信息"""
    print("\n=== 布局优化汇总 ===")
    print("1. 网址卡片布局优化:")
    print("   - 图标与内容间距: 12px -> 6px")
    print("   - 名称与网址间距: 2px -> 1px")
    print("\n2. 快捷命令按钮优化:")
    print("   - 工具栏间距: 2px -> 1px")
    print("   - 按钮内边距: 3px -> 2px")  
    print("   - 按钮外边距: 1px -> 0px")
    print("\n3. 备份提示语优化:")
    print("   - 增加了清理提醒信息")

if __name__ == "__main__":
    print("网址导航软件布局优化测试")
    print("=" * 40)
    
    try:
        test_card_layout_spacing()
        test_toolbar_button_spacing()
        test_backup_message()
        show_optimization_summary()
        
        print("\n✓ 所有优化项目测试完成!")
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        sys.exit(1)