#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URLNav 密码问题快速修复工具

这个工具用于解决首次启动时要求输入密码但不知道密码的问题。
"""

import sys
import os
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication, QMessageBox

def clear_all_password_settings():
    """清除所有密码相关设置"""
    try:
        # 尝试不同的组织名和应用名组合
        settings_combinations = [
            ("URL Navigator", "URL Navigator"),
            ("URLNav", "URLNav"),
            ("", "URLNav"),
            ("", "URL Navigator")
        ]
        
        cleared_any = False
        
        for org, app in settings_combinations:
            settings = QSettings(org, app)
            
            # 检查是否有密码相关设置
            keys_to_check = [
                "security/password_enabled",
                "security/password_hash",
                "security/password_salt",
                "security/security_question",
                "security/security_answer_hash",
                "security/security_answer_salt"
            ]
            
            has_settings = any(settings.contains(key) for key in keys_to_check)
            
            if has_settings:
                print(f"发现密码设置在: 组织='{org}', 应用='{app}'")
                
                # 清除所有密码相关设置
                for key in keys_to_check:
                    if settings.contains(key):
                        settings.remove(key)
                        print(f"  已清除: {key}")
                
                settings.sync()
                cleared_any = True
        
        return cleared_any
        
    except Exception as e:
        print(f"清除设置时出错: {e}")
        return False

def main():
    print("URLNav 密码问题快速修复工具")
    print("=" * 40)
    
    # 创建临时应用（不显示界面）
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    
    print("正在检查和清除密码设置...")
    
    if clear_all_password_settings():
        print("\n✅ 已成功清除所有密码设置")
        print("\n现在您可以正常启动 URLNav 应用程序了。")
        print("如果需要重新设置密码保护，请在应用程序的设置中进行配置。")
    else:
        print("\n❓ 未找到任何密码设置")
        print("\n如果仍然遇到密码提示问题，可能的原因：")
        print("1. 配置文件位置不同")
        print("2. 应用程序代码中有其他问题")
        print("\n建议联系开发者获取进一步帮助。")
    
    print("\n修复工具执行完成。")
    
    # 不需要显示GUI，直接退出
    sys.exit(0)

if __name__ == "__main__":
    main()