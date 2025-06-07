#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多语言功能测试脚本
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QComboBox
from PyQt5.QtCore import Qt

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.language_manager import language_manager

class MultiLanguageTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多语言测试")
        self.setGeometry(300, 300, 500, 400)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 语言选择下拉框
        self.language_combo = QComboBox()
        available_languages = language_manager.get_available_languages()
        current_language = language_manager.get_current_language()
        
        for code, name in available_languages.items():
            self.language_combo.addItem(name, code)
            if code == current_language:
                self.language_combo.setCurrentText(name)
        
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        layout.addWidget(QLabel("语言选择 / Language Selection:"))
        layout.addWidget(self.language_combo)
        
        # 测试文本标签
        self.test_labels = []
        
        # 测试不同类型的文本
        test_keys = [
            ("app_title", "应用标题"),
            ("main_window.add_url", "添加网址按钮"),
            ("main_window.settings", "设置按钮"),
            ("dialogs.add_url_title", "添加网址对话框标题"),
            ("settings.language_label", "语言标签"),
            ("messages.confirm_title", "确认对话框标题"),
            ("tooltips.add_url_tooltip", "添加网址工具提示")
        ]
        
        for key, description in test_keys:
            desc_label = QLabel(f"{description} ({key}):")
            desc_label.setStyleSheet("font-weight: bold; color: #666;")
            layout.addWidget(desc_label)
            
            text_label = QLabel(language_manager.tr(key))
            text_label.setStyleSheet("margin-left: 20px; padding: 5px; background-color: #f0f0f0; border: 1px solid #ddd;")
            text_label.setWordWrap(True)
            layout.addWidget(text_label)
            
            self.test_labels.append((key, text_label))
        
        # 连接语言切换信号
        language_manager.language_changed.connect(self.update_texts)
        
    def on_language_changed(self, language_name):
        """语言切换处理"""
        available_languages = language_manager.get_available_languages()
        for code, name in available_languages.items():
            if name == language_name:
                language_manager.set_language(code)
                break
    
    def update_texts(self):
        """更新界面文本"""
        print(f"语言切换到: {language_manager.get_current_language()}")
        
        # 更新所有测试标签
        for key, label in self.test_labels:
            translated_text = language_manager.tr(key)
            label.setText(translated_text)
            print(f"  {key}: {translated_text}")

def test_language_files():
    """测试所有语言文件"""
    print("=== 测试语言文件 ===")
    
    available_languages = language_manager.get_available_languages()
    test_key = "main_window.add_url"
    
    for code, name in available_languages.items():
        language_manager.set_language(code)
        text = language_manager.tr(test_key)
        print(f"{name} ({code}): {text}")
    
    # 恢复中文
    language_manager.set_language("zh")
    print("=== 测试完成 ===\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 先测试语言文件
    test_language_files()
    
    # 显示测试窗口
    window = MultiLanguageTestWindow()
    window.show()
    
    print("请在窗口中测试语言切换功能...")
    sys.exit(app.exec_())