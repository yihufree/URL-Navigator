#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
依赖安装脚本
用于安装URL导航软件所需的所有依赖库
"""

import sys
import subprocess
import os

def main():
    print("准备安装URL导航软件所需的依赖...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("错误: 需要Python 3.7或更高版本。")
        print(f"当前Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        sys.exit(1)
    
    # 升级pip
    print("\n正在升级pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print("警告: 无法升级pip，但将继续安装依赖。")
    
    # 安装必需依赖
    print("\n正在安装必需依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError:
        print("错误: 安装必需依赖失败。")
        sys.exit(1)
    
    # 询问是否安装可选依赖
    print("\n是否安装可选但推荐的依赖？这些依赖可以提高安全性和功能性。(y/n)")
    choice = input().strip().lower()
    
    if choice == 'y' or choice == 'yes':
        print("\n正在安装可选依赖...")
        try:
            # 安装jsonschema提供高级JSON验证
            print("正在安装jsonschema...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema>=3.2.0"])
            
            # 安装lxml提供更安全的HTML解析
            print("正在安装lxml...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "lxml>=4.6.0"])
            
            print("可选依赖安装成功！")
        except subprocess.CalledProcessError as e:
            print(f"警告: 安装部分可选依赖失败，但这不会阻止程序运行。错误: {e}")
    
    print("\n所有依赖安装完成！")
    print("现在可以运行 'python main.py' 启动URL导航软件。")
    
    input("按任意键继续...")

if __name__ == "__main__":
    main() 