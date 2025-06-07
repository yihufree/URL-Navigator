#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class Bookmark(QObject):
    """书签模型类"""
    
    # 定义信号
    changed = pyqtSignal()
    
    def __init__(self, name="", url="", icon="", tags=None, description="", created=None, modified=None):
        """
        初始化书签
        
        Args:
            name: 书签名称
            url: 书签URL
            icon: 图标路径
            tags: 标签列表
            description: 描述
            created: 创建时间
            modified: 修改时间
        """
        super().__init__()
        
        from datetime import datetime
        
        self.name = name
        self.url = url
        self.icon = icon
        self.tags = tags or []
        self.description = description
        self.created = created or datetime.now()
        self.modified = modified or datetime.now()
        self.visits = 0
        self.last_visit = None
    
    def to_dict(self):
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "type": "url",
            "name": self.name,
            "url": self.url,
            "icon": self.icon,
            "tags": self.tags,
            "description": self.description,
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
            "visits": self.visits,
            "last_visit": self.last_visit.isoformat() if self.last_visit else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建书签
        
        Args:
            data: 字典数据
            
        Returns:
            书签对象
        """
        from datetime import datetime
        
        bookmark = cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            icon=data.get("icon", ""),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            created=datetime.fromisoformat(data["created"]) if data.get("created") else None,
            modified=datetime.fromisoformat(data["modified"]) if data.get("modified") else None
        )
        
        bookmark.visits = data.get("visits", 0)
        if data.get("last_visit"):
            bookmark.last_visit = datetime.fromisoformat(data["last_visit"])
        
        return bookmark
    
    def update(self, name=None, url=None, icon=None, tags=None, description=None):
        """
        更新书签
        
        Args:
            name: 新名称
            url: 新URL
            icon: 新图标
            tags: 新标签
            description: 新描述
        """
        from datetime import datetime
        
        if name is not None:
            self.name = name
        
        if url is not None:
            self.url = url
        
        if icon is not None:
            self.icon = icon
        
        if tags is not None:
            self.tags = tags
        
        if description is not None:
            self.description = description
        
        self.modified = datetime.now()
        self.changed.emit()
    
    def record_visit(self):
        """记录访问"""
        from datetime import datetime
        
        self.visits += 1
        self.last_visit = datetime.now()
        self.changed.emit()
    
    def matches_search(self, query):
        """
        检查是否匹配搜索查询
        
        Args:
            query: 搜索查询
            
        Returns:
            是否匹配
        """
        query = query.lower()
        
        # 检查名称
        if query in self.name.lower():
            return True
        
        # 检查URL
        if query in self.url.lower():
            return True
        
        # 检查描述
        if query in self.description.lower():
            return True
        
        # 检查标签
        for tag in self.tags:
            if query in tag.lower():
                return True
        
        return False