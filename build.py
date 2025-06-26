#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
import platform
import datetime

def build_exe():
    """构建EXE文件"""
    print("开始构建EXE文件...")
    
    # 清理旧的构建文件
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        
    # 确保资源文件夹存在
    if not os.path.exists("resources"):
        print("错误: 资源文件夹不存在!")
        return
        
    # 获取版本日期
    version_date = datetime.datetime.now().strftime("%Y%m%d")
    output_filename = f"URLNav_{version_date}"
    
    # 构建命令
    cmd = [
        "pyinstaller",
        f"--name={output_filename}",
        "--windowed",  # 无控制台窗口
        "--onefile",   # 单个EXE文件
        "--clean",     # 清理临时文件
        "--icon=resources/icons/app_icon.ico",  # 应用图标
        "--add-data=resources;resources",  # 添加整个资源目录
        "--add-data=languages;languages",  # 添加语言文件目录
        "--noconfirm",  # 不显示确认对话框
        "main.py"  # 主程序入口
    ]
    
    # 根据操作系统调整路径分隔符
    if platform.system() != "Windows":
        # 对于Unix系统使用冒号分隔符
        for i in range(len(cmd)):
            if "--add-data=" in cmd[i]:
                cmd[i] = cmd[i].replace(";", ":")
    
    print(f"运行命令: {' '.join(cmd)}")
    
    # 执行构建
    try:
        subprocess.call(cmd, shell=False)  # 明确禁用shell以防止命令注入
        
        # 检查是否成功创建EXE文件
        exe_path = os.path.join("dist", f"{output_filename}.exe")
        if os.path.exists(exe_path):
            print(f"构建成功！EXE文件大小: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
            print(f"EXE文件位置: {os.path.abspath(exe_path)}")
        else:
            print("构建似乎完成，但找不到EXE文件")
            
    except Exception as e:
        print(f"构建过程中出错: {e}")
        return

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和打包后环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

if __name__ == "__main__":
    build_exe()