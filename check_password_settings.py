#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查密码设置状态
"""

from PyQt5.QtCore import QSettings

def main():
    settings = QSettings("URL Navigator", "URL Navigator")
    
    # 检查各项设置
    password_enabled = settings.value("security/password_enabled", False)
    password_hash = settings.value("security/password_hash", "")
    password_salt = settings.value("security/password_salt", "")
    security_question = settings.value("security/security_question", "")
    
    print(f"密码保护启用: {password_enabled}")
    print(f"密码哈希: {'存在' if password_hash else '不存在'}")
    print(f"密码盐值: {'存在' if password_salt else '不存在'}")
    print(f"密保问题: {security_question if security_question else '未设置'}")
    
    # 如果启用了密码保护但没有密码数据，说明有问题
    if password_enabled and (not password_hash or not password_salt):
        print("\n问题: 密码保护已启用但密码数据缺失！")
        print("建议: 运行 reset_password_protection.py 重置设置")
    elif password_enabled:
        print("\n状态: 密码保护正常")
    else:
        print("\n状态: 密码保护未启用")

if __name__ == "__main__":
    main()