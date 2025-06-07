#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多语言管理器
支持界面的多语种动态切换
"""

import json
import os
import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class LanguageManager(QObject):
    """轻量级多语言管理器"""
    
    # 语言切换信号
    language_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_language = "zh"  # 默认中文
        self.translations = {}
        self.available_languages = {
            "zh": "中文",
            "en": "English", 
            "ja": "日本語",
            "de": "Deutsch",
            "fr": "Français",
            "ko": "한국어",
            "es": "Español"
        }
        self.load_language(self.current_language)
    
    def get_available_languages(self):
        """获取可用语言列表"""
        return self.available_languages
    
    def get_current_language(self):
        """获取当前语言"""
        return self.current_language
    
    def load_language(self, language_code):
        """加载指定语言文件"""
        try:
            # 使用 resource_path 获取正确的语言文件路径
            from build import resource_path
            language_file = resource_path(os.path.join("languages", f"{language_code}.json"))
            if os.path.exists(language_file):
                with open(language_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                logger.info(f"已加载语言文件: {language_file}")
            else:
                logger.warning(f"语言文件不存在: {language_file}")
                # 如果文件不存在，使用中文作为默认值
                if language_code != "zh":
                    self.load_language("zh")
                    return
        except Exception as e:
            logger.error(f"加载语言文件失败: {e}")
            # 加载失败时使用空字典，tr方法会返回原始key
            self.translations = {}
    
    def set_language(self, language_code):
        """设置当前语言"""
        if language_code in self.available_languages:
            old_language = self.current_language
            self.current_language = language_code
            self.load_language(language_code)
            if old_language != language_code:
                self.language_changed.emit(language_code)
                logger.info(f"语言已切换: {old_language} -> {language_code}")
    
    def tr(self, key, default_text=None):
        """翻译文本"""
        # 处理嵌套键（如 "main_window.add_url"）
        if "." in key:
            keys = key.split(".")
            current = self.translations
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    current = None
                    break
            if current is not None:
                return current
        elif key in self.translations:
            return self.translations[key]
        
        if default_text is not None:
            return default_text
        else:
            # 如果没有找到翻译，返回key本身
            return key
    
    def get_language_name(self, language_code):
        """获取语言显示名称"""
        return self.available_languages.get(language_code, language_code)

# 全局实例
language_manager = LanguageManager()