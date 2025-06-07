#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from utils.language_manager import language_manager

logger = logging.getLogger(__name__)

class BlindBoxManager:
    """网站盲盒管理器，用于随机选择和打开网站"""
    
    def __init__(self, data_manager, config=None):
        """
        初始化盲盒管理器
        
        Args:
            data_manager: 数据管理器实例
            config: 配置管理器实例
        """
        self.data_manager = data_manager
        self.config = config
        
        # 获取历史记录文件路径
        if config:
            self.history_file = config.get_path("history_file")
        else:
            self.history_file = "blind_box_history.json"  # 兼容旧版本
            
        self.max_history_count = 100  # 历史记录数量上限
        self._load_history()
    
    def collect_all_urls(self, path=None):
        """收集指定路径及其子目录下的所有URL
        
        Args:
            path: 起始路径，默认为根目录
            
        Returns:
            URL列表，每个元素为 (url, name, path) 元组
        """
        if path is None:
            path = []
        
        result = []
        
        # 获取当前路径下的所有项目
        items = self.data_manager.get_item_at_path(path)
        if not items:
            return result
        
        # 遍历当前路径下的所有项目
        for name, item in items.items():
            if item["type"] == "url":
                # 如果是URL，添加到结果列表
                result.append((item.get("url", ""), name, path))
            elif item["type"] == "folder":
                # 如果是文件夹，递归收集子目录中的URL
                sub_path = path + [name]
                result.extend(self.collect_all_urls(sub_path))
        
        return result
    
    def get_random_urls(self, path=None, count=1):
        """获取随机URL
        
        Args:
            path: 起始路径，默认为根目录
            count: 要获取的URL数量
            
        Returns:
            随机选择的URL列表，每个元素为 (url, name, path) 元组
        """
        # 收集所有URL
        all_urls = self.collect_all_urls(path)
        
        if not all_urls:
            return []
        
        # 如果请求的数量大于可用的URL数量，则返回所有URL（随机排序）
        if count >= len(all_urls):
            random.shuffle(all_urls)
            return all_urls
        
        # 随机选择指定数量的URL
        return random.sample(all_urls, count)
    
    def open_random_urls(self, parent_widget, path=None, count=1):
        """打开随机URL
        
        Args:
            parent_widget: 父窗口部件，用于显示消息框
            path: 起始路径，默认为根目录
            count: 要打开的URL数量
            
        Returns:
            tuple: (成功打开的URL数量, 随机选择的URL列表)
        """
        # 获取随机URL
        random_urls = self.get_random_urls(path, count)
        
        if not random_urls:
            # 显示没有可用URL的消息
            QMessageBox.information(
                parent_widget,
                language_manager.tr("blind_box.title", "网站盲盒"),
                language_manager.tr("blind_box.no_urls", "当前目录及子目录下没有可用的网址")
            )
            return 0, []
        
        # 显示正在打开URL的消息
        message = language_manager.tr(
            "blind_box.opening_urls", 
            "正在打开 {count} 个随机网站..."
        ).format(count=len(random_urls))
        
        # 安全地显示状态栏消息
        if hasattr(parent_widget, 'status_bar') and parent_widget.status_bar:
            parent_widget.status_bar.showMessage(message, 3000)
        
        # 打开URL
        opened_count = 0
        import webbrowser
        import time
        
        for url, name, path in random_urls:
            if url:
                try:
                    webbrowser.open(url)
                    logger.info(f"盲盒打开URL: {url}")
                    opened_count += 1
                    # 添加延迟，避免浏览器进程冲突
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"盲盒打开URL失败: {url}, 错误: {e}")
                    # 安全地显示状态栏消息
                    if hasattr(parent_widget, 'status_bar') and parent_widget.status_bar:
                        parent_widget.status_bar.showMessage(f"打开URL失败: {e}", 3000)
                    # 继续处理下一个URL
                    continue
        
        # 记录历史
        self._add_to_history(random_urls)
        
        return opened_count, random_urls
    
    def _load_history(self):
        """加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            self.history = []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def _add_to_history(self, urls):
        """添加URL到历史记录
        
        Args:
            urls: URL列表，每个元素为 (url, name, path) 元组
        """
        timestamp = datetime.now().isoformat()
        
        for url, name, path in urls:
            if url:  # 只记录有效的URL
                # 查找对应的图标
                icon = self._get_url_icon(path, name)
                
                history_item = {
                    'url': url,
                    'name': name,
                    'path': path,
                    'icon': icon,
                    'timestamp': timestamp
                }
                
                # 添加到历史记录开头
                self.history.insert(0, history_item)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history_count:
            self.history = self.history[:self.max_history_count]
        
        # 保存历史记录
        self._save_history()
    
    def _get_url_icon(self, path, name):
        """获取URL的图标路径
        
        Args:
            path: URL所在路径
            name: URL名称
            
        Returns:
            图标路径字符串
        """
        try:
            # 获取URL项目
            items = self.data_manager.get_item_at_path(path)
            if items and name in items:
                item = items[name]
                if item.get('type') == 'url':
                    return item.get('icon', '')
        except Exception as e:
            logger.error(f"获取URL图标失败: {e}")
        
        return ''
    
    def get_history(self):
        """获取历史记录
        
        Returns:
            历史记录列表
        """
        return self.history.copy()
    
    def remove_history_item(self, item):
        """删除单个历史记录项
        
        Args:
            item: 要删除的历史记录项
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if item in self.history:
                self.history.remove(item)
                self._save_history()
                return True
            else:
                # 尝试根据关键字段匹配删除
                for i, record in enumerate(self.history):
                    if (record.get('url') == item.get('url') and 
                        record.get('name') == item.get('name') and 
                        record.get('timestamp') == item.get('timestamp')):
                        del self.history[i]
                        self._save_history()
                        return True
        except Exception as e:
            logger.error(f"删除历史记录项失败: {e}")
        
        return False
    
    def clear_history(self):
        """清空所有历史记录"""
        try:
            self.history = []
            self._save_history()
            return True
        except Exception as e:
            logger.error(f"清空历史记录失败: {e}")
            return False
    
    def get_history_count(self):
        """获取历史记录数量
        
        Returns:
            int: 历史记录数量
        """
        return len(self.history)
    
    def is_history_full(self):
        """检查历史记录是否已满
        
        Returns:
            bool: 历史记录是否已满
        """
        return len(self.history) >= self.max_history_count