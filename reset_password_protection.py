#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码保护重置工具
用于解决密码保护设置问题
"""

import sys
import os
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication, QMessageBox

def check_password_status():
    """检查当前密码保护状态"""
    settings = QSettings("URL Navigator", "URL Navigator")
    
    print("=== 密码保护状态检查 ===")
    
    # 检查各项设置
    password_enabled = settings.value("security/password_enabled", False)
    password_hash = settings.value("security/password_hash", "")
    password_salt = settings.value("security/password_salt", "")
    security_question = settings.value("security/security_question", "")
    
    print(f"密码保护启用状态: {password_enabled}")
    print(f"密码哈希存在: {'是' if password_hash else '否'}")
    print(f"密码盐值存在: {'是' if password_salt else '否'}")
    print(f"密保问题: {security_question if security_question else '未设置'}")
    
    # 判断问题
    if password_enabled and (not password_hash or not password_salt):
        print("\n⚠️  发现问题: 密码保护已启用但密码数据不完整！")
        return True
    elif password_enabled:
        print("\n✅ 密码保护正常启用")
        return False
    else:
        print("\n✅ 密码保护未启用")
        return False

def reset_password_protection():
    """重置密码保护设置"""
    settings = QSettings("URL Navigator", "URL Navigator")
    
    print("\n=== 重置密码保护设置 ===")
    
    # 清除所有密码相关设置
    settings.remove("security/password_enabled")
    settings.remove("security/password_hash")
    settings.remove("security/password_salt")
    settings.remove("security/security_question")
    settings.remove("security/security_answer_hash")
    settings.remove("security/security_answer_salt")
    settings.sync()
    
    print("✅ 密码保护设置已重置")
    print("现在可以正常启动应用程序了")

def main():
    """主函数"""
    print("URLNav 密码保护重置工具")
    print("=" * 40)
    
    # 检查状态
    has_problem = check_password_status()
    
    if has_problem:
        print("\n检测到密码保护配置问题")
        choice = input("是否要重置密码保护设置？(y/n): ").lower().strip()
        
        if choice in ['y', 'yes', '是']:
            reset_password_protection()
        else:
            print("操作已取消")
    else:
        print("\n如果您仍然遇到密码问题，可以选择重置")
        choice = input("是否要强制重置密码保护设置？(y/n): ").lower().strip()
        
        if choice in ['y', 'yes', '是']:
            reset_password_protection()
        else:
            print("操作已取消")
    
    print("\n程序结束")
    input("按回车键退出...")

if __name__ == "__main__":
    main()