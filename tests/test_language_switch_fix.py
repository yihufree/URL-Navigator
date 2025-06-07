#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语言切换修复验证脚本
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QComboBox, QMessageBox
from PyQt5.QtCore import Qt

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.language_manager import language_manager

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LanguageSwitchTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语言切换修复测试")
        self.setGeometry(300, 300, 600, 500)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 当前语言显示
        self.current_lang_label = QLabel(f"当前语言: {language_manager.get_current_language()}")
        self.current_lang_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(self.current_lang_label)
        
        # 语言选择下拉框
        self.language_combo = QComboBox()
        available_languages = language_manager.get_available_languages()
        current_language = language_manager.get_current_language()
        
        for code, name in available_languages.items():
            self.language_combo.addItem(name, code)
            if code == current_language:
                self.language_combo.setCurrentText(name)
        
        self.language_combo.currentTextChanged.connect(self.on_language_selected)
        layout.addWidget(QLabel("选择语言（不会立即切换）:"))
        layout.addWidget(self.language_combo)
        
        # 保存按钮
        self.save_button = QPushButton("保存并应用语言设置")
        self.save_button.clicked.connect(self.apply_language_change)
        layout.addWidget(self.save_button)
        
        # 重置按钮
        self.reset_button = QPushButton("重置为当前语言")
        self.reset_button.clicked.connect(self.reset_language_selection)
        layout.addWidget(self.reset_button)
        
        # 测试文本显示区域
        layout.addWidget(QLabel("测试文本:"))
        self.test_texts = {}
        
        test_keys = [
            ("app_title", "应用标题"),
            ("main_window.add_url", "添加网址按钮"),
            ("main_window.settings", "设置按钮"),
            ("dialogs.add_url_title", "添加网址对话框标题"),
            ("settings.language_label", "语言标签"),
        ]
        
        for key, description in test_keys:
            label = QLabel(f"{description}: {language_manager.tr(key)}")
            label.setStyleSheet("margin: 2px; padding: 3px; background-color: #f5f5f5; border: 1px solid #ddd;")
            layout.addWidget(label)
            self.test_texts[key] = label
        
        # 选择的语言（未保存）
        self.selected_language_code = language_manager.get_current_language()
        
        # 连接语言切换信号
        language_manager.language_changed.connect(self.on_language_changed)
        
    def on_language_selected(self, language_name):
        """语言选择（模拟设置对话框的行为）"""
        try:
            # 记录选择的语言，但不立即切换
            available_languages = language_manager.get_available_languages()
            for code, name in available_languages.items():
                if name == language_name:
                    self.selected_language_code = code
                    print(f"用户选择了语言: {name} ({code})，但尚未保存")
                    self.save_button.setText(f"保存并应用语言设置 ({name})")
                    break
        except Exception as e:
            print(f"语言选择处理失败: {e}")
            QMessageBox.warning(self, "错误", f"语言选择失败: {str(e)}")
    
    def apply_language_change(self):
        """应用语言变更（模拟保存按钮）"""
        try:
            current_language = language_manager.get_current_language()
            if self.selected_language_code != current_language:
                print(f"正在切换语言: {current_language} -> {self.selected_language_code}")
                language_manager.set_language(self.selected_language_code)
                print(f"语言切换成功: {self.selected_language_code}")
                QMessageBox.information(self, "成功", f"语言已切换到: {language_manager.get_language_name(self.selected_language_code)}")
            else:
                print("语言未发生变化，无需切换")
                QMessageBox.information(self, "提示", "语言未发生变化")
                
            self.save_button.setText("保存并应用语言设置")
            
        except Exception as e:
            print(f"语言切换失败: {e}")
            QMessageBox.critical(self, "错误", f"语言切换失败: {str(e)}")
    
    def reset_language_selection(self):
        """重置语言选择"""
        current_language = language_manager.get_current_language()
        self.selected_language_code = current_language
        
        # 更新下拉框显示
        current_name = language_manager.get_language_name(current_language)
        self.language_combo.setCurrentText(current_name)
        self.save_button.setText("保存并应用语言设置")
        print(f"已重置为当前语言: {current_name}")
    
    def on_language_changed(self):
        """语言切换后更新界面"""
        try:
            current_lang = language_manager.get_current_language()
            current_name = language_manager.get_language_name(current_lang)
            
            print(f"语言切换信号触发: {current_lang}")
            
            # 更新当前语言显示
            self.current_lang_label.setText(f"当前语言: {current_lang} ({current_name})")
            
            # 更新所有测试文本
            for key, label in self.test_texts.items():
                translated_text = language_manager.tr(key)
                description = label.text().split(":")[0]  # 获取描述部分
                label.setText(f"{description}: {translated_text}")
            
            print("界面文本更新完成")
            
        except Exception as e:
            print(f"更新界面文本时发生错误: {e}")

def test_language_manager():
    """测试语言管理器基本功能"""
    print("=== 测试语言管理器基本功能 ===")
    
    # 测试当前语言
    current = language_manager.get_current_language()
    print(f"当前语言: {current}")
    
    # 测试翻译
    test_text = language_manager.tr("main_window.add_url")
    print(f"翻译测试 (main_window.add_url): {test_text}")
    
    # 测试语言切换
    print("测试语言切换...")
    language_manager.set_language("en")
    en_text = language_manager.tr("main_window.add_url")
    print(f"英语: {en_text}")
    
    language_manager.set_language("zh")
    zh_text = language_manager.tr("main_window.add_url")
    print(f"中文: {zh_text}")
    
    print("=== 基本功能测试完成 ===\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 先测试基本功能
    test_language_manager()
    
    # 显示测试窗口
    window = LanguageSwitchTestWindow()
    window.show()
    
    print("请在窗口中测试修复后的语言切换功能:")
    print("1. 选择不同语言（不会立即切换）")
    print("2. 点击'保存并应用语言设置'按钮")
    print("3. 观察界面是否正确切换语言")
    print("4. 程序应该不会崩溃")
    
    sys.exit(app.exec_())