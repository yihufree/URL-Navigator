#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码保护诊断和修复工具
"""

import sys
import os
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

def check_all_settings():
    """检查所有相关设置"""
    print("=== 完整诊断报告 ===")
    
    # 检查不同的设置存储位置
    settings_configs = [
        ("URL Navigator", "URL Navigator"),
        ("URLNav", "URLNav"),
        ("URLNavigator", "URLNavigator"),
    ]
    
    found_settings = False
    
    for org, app in settings_configs:
        settings = QSettings(org, app)
        
        # 获取所有键
        all_keys = settings.allKeys()
        security_keys = [key for key in all_keys if key.startswith('security/')]
        
        if security_keys:
            found_settings = True
            print(f"\n在 {org}/{app} 中找到安全设置:")
            
            for key in security_keys:
                value = settings.value(key)
                print(f"  {key}: {value}")
            
            # 检查密码保护状态
            password_enabled = settings.value("security/password_enabled", False)
            if isinstance(password_enabled, str):
                password_enabled = password_enabled.lower() == "true"
            
            if password_enabled:
                print(f"  ⚠️  在 {org}/{app} 中发现启用的密码保护！")
                return settings, org, app
    
    if not found_settings:
        print("\n✅ 未找到任何密码保护设置")
        return None, None, None
    
    return None, None, None

def clear_all_password_settings():
    """清除所有可能的密码设置"""
    print("\n=== 清除所有密码设置 ===")
    
    settings_configs = [
        ("URL Navigator", "URL Navigator"),
        ("URLNav", "URLNav"),
        ("URLNavigator", "URLNavigator"),
    ]
    
    for org, app in settings_configs:
        settings = QSettings(org, app)
        
        # 清除所有安全相关设置
        security_keys = [
            "security/password_enabled",
            "security/password_hash",
            "security/password_salt",
            "security/security_question",
            "security/security_answer_hash",
            "security/security_answer_salt"
        ]
        
        cleared_any = False
        for key in security_keys:
            if settings.contains(key):
                settings.remove(key)
                cleared_any = True
        
        if cleared_any:
            settings.sync()
            print(f"✅ 已清除 {org}/{app} 中的密码设置")
    
    print("\n所有密码设置已清除")

def test_password_manager():
    """测试密码管理器"""
    print("\n=== 测试密码管理器 ===")
    
    try:
        # 添加项目路径
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from utils.password_manager import PasswordManager
        
        pm = PasswordManager()
        enabled = pm.is_password_enabled()
        
        print(f"密码管理器报告状态: {enabled}")
        
        if enabled:
            print("⚠️  密码管理器认为密码保护已启用")
            return True
        else:
            print("✅ 密码管理器认为密码保护未启用")
            return False
            
    except Exception as e:
        print(f"❌ 测试密码管理器时出错: {e}")
        return False

def main():
    """主函数"""
    print("URLNav 密码保护诊断工具")
    print("=" * 50)
    
    # 1. 检查所有设置
    problem_settings, org, app = check_all_settings()
    
    # 2. 测试密码管理器
    pm_problem = test_password_manager()
    
    # 3. 提供解决方案
    if problem_settings or pm_problem:
        print("\n🔧 发现问题，提供解决方案:")
        print("1. 清除所有密码设置")
        print("2. 退出")
        
        choice = input("\n请选择 (1/2): ").strip()
        
        if choice == '1':
            clear_all_password_settings()
            print("\n✅ 修复完成！现在应该可以正常启动应用程序了")
        else:
            print("操作已取消")
    else:
        print("\n✅ 未发现密码保护问题")
        print("如果仍然遇到密码提示，可能是其他原因")
    
    print("\n程序结束")

if __name__ == "__main__":
    # 创建临时应用程序实例
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    
    try:
        main()
    finally:
        if app:
            app.quit()