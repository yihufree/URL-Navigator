#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class SearchService(QObject):
    """搜索服务"""
    
    # 定义信号
    search_started = pyqtSignal(str)
    search_progress = pyqtSignal(int, int)  # 当前进度，总数
    search_completed = pyqtSignal(list)  # 结果列表
    search_error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, data_manager):
        """
        初始化搜索服务
        
        Args:
            data_manager: 数据管理器
        """
        super().__init__()
        self.data_manager = data_manager
    
    def search(self, query, search_options=None):
        """
        执行搜索
        
        Args:
            query: 搜索查询
            search_options: 搜索选项
                - case_sensitive: 区分大小写
                - search_urls: 搜索URL
                - search_names: 搜索名称
                - search_descriptions: 搜索描述
                - search_tags: 搜索标签
                - max_results: 最大结果数
                
        Returns:
            搜索结果列表
        """
        if not query:
            self.search_error.emit("搜索查询不能为空")
            return []
        
        # 默认搜索选项
        default_options = {
            "case_sensitive": False,
            "search_urls": True,
            "search_names": True,
            "search_descriptions": True,
            "search_tags": True,
            "max_results": 100
        }
        
        # 合并搜索选项
        options = default_options.copy()
        if search_options:
            options.update(search_options)
        
        try:
            self.search_started.emit(query)
            
            # 执行搜索
            results = self._perform_search(query, options)
            
            self.search_completed.emit(results)
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            self.search_error.emit(f"搜索失败: {str(e)}")
            return []
    
    def _perform_search(self, query, options):
        """
        执行搜索
        
        Args:
            query: 搜索查询
            options: 搜索选项
            
        Returns:
            搜索结果列表
        """
        results = []
        
        # 如果不区分大小写，转换为小写
        if not options["case_sensitive"]:
            query = query.lower()
        
        # 获取所有书签
        all_bookmarks = self._get_all_bookmarks(options)
        
        # 搜索书签
        for path, bookmark in all_bookmarks:
            if self._bookmark_matches(bookmark, query, options):
                results.append({
                    "path": path,
                    "item": bookmark.to_dict(),
                    "name": bookmark.name
                })
                
                # 检查是否达到最大结果数
                if options["max_results"] > 0 and len(results) >= options["max_results"]:
                    break
        
        return results
    
    def _get_all_bookmarks(self, options):
        """
        获取所有书签
        
        Args:
            options: 搜索选项
            
        Returns:
            书签列表，每个元素是 (路径, 书签) 元组
        """
        bookmarks = []
        
        def traverse_folder(folder, path):
            for name, item in folder.items():
                current_path = path + [name]
                
                if item["type"] == "url":
                    from models.bookmark import Bookmark
                    bookmark = Bookmark.from_dict(item)
                    bookmarks.append((current_path, bookmark))
                else:  # folder
                    traverse_folder(item["children"], current_path)
        
        traverse_folder(self.data_manager.data, [])
        return bookmarks
    
    def _bookmark_matches(self, bookmark, query, options):
        """
        检查书签是否匹配搜索查询
        
        Args:
            bookmark: 书签对象
            query: 搜索查询
            options: 搜索选项
            
        Returns:
            是否匹配
        """
        # 搜索名称
        if options["search_names"]:
            name = bookmark.name if options["case_sensitive"] else bookmark.name.lower()
            if query in name:
                return True
        
        # 搜索URL
        if options["search_urls"]:
            url = bookmark.url if options["case_sensitive"] else bookmark.url.lower()
            if query in url:
                return True
        
        # 搜索描述
        if options["search_descriptions"] and bookmark.description:
            description = bookmark.description if options["case_sensitive"] else bookmark.description.lower()
            if query in description:
                return True
        
        # 搜索标签
        if options["search_tags"] and bookmark.tags:
            for tag in bookmark.tags:
                tag_text = tag if options["case_sensitive"] else tag.lower()
                if query in tag_text:
                    return True
        
        return False