#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class Folder(QObject):
    """文件夹模型类"""
    
    # 定义信号
    changed = pyqtSignal()
    
    def __init__(self, name="", description="", created=None, modified=None):
        """
        初始化文件夹
        
        Args:
            name: 文件夹名称
            description: 描述
            created: 创建时间
            modified: 修改时间
        """
        super().__init__()
        
        from datetime import datetime
        
        self.name = name
        self.description = description
        self.created = created or datetime.now()
        self.modified = modified or datetime.now()
        self.children = {}  # 子项目（书签和文件夹）
    
    def to_dict(self):
        """
        转换为字典
        
        Returns:
            字典表示
        """
        children_dict = {}
        for name, child in self.children.items():
            children_dict[name] = child.to_dict()
        
        return {
            "type": "folder",
            "name": self.name,
            "description": self.description,
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
            "children": children_dict
        }
    
    @classmethod
    def from_dict(cls, data, load_children=True):
        """
        从字典创建文件夹
        
        Args:
            data: 字典数据
            load_children: 是否加载子项目
            
        Returns:
            文件夹对象
        """
        from datetime import datetime
        
        folder = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            created=datetime.fromisoformat(data["created"]) if data.get("created") else None,
            modified=datetime.fromisoformat(data["modified"]) if data.get("modified") else None
        )
        
        # 加载子项目
        if load_children and "children" in data:
            from models.bookmark import Bookmark
            
            for name, child_data in data["children"].items():
                if child_data["type"] == "folder":
                    folder.children[name] = cls.from_dict(child_data)
                else:  # url
                    folder.children[name] = Bookmark.from_dict(child_data)
        
        return folder
    
    def update(self, name=None, description=None):
        """
        更新文件夹
        
        Args:
            name: 新名称
            description: 新描述
        """
        from datetime import datetime
        
        if name is not None:
            self.name = name
        
        if description is not None:
            self.description = description
        
        self.modified = datetime.now()
        self.changed.emit()
    
    def add_child(self, name, child):
        """
        添加子项目
        
        Args:
            name: 子项目名称
            child: 子项目对象
            
        Returns:
            是否成功
        """
        if name in self.children:
            return False
        
        self.children[name] = child
        self.changed.emit()
        return True
    
    def remove_child(self, name):
        """
        移除子项目
        
        Args:
            name: 子项目名称
            
        Returns:
            是否成功
        """
        if name not in self.children:
            return False
        
        del self.children[name]
        self.changed.emit()
        return True
    
    def rename_child(self, old_name, new_name):
        """
        重命名子项目
        
        Args:
            old_name: 旧名称
            new_name: 新名称
            
        Returns:
            是否成功
        """
        if old_name not in self.children or new_name in self.children:
            return False
        
        self.children[new_name] = self.children.pop(old_name)
        self.changed.emit()
        return True
    
    def get_child(self, name):
        """
        获取子项目
        
        Args:
            name: 子项目名称
            
        Returns:
            子项目对象
        """
        return self.children.get(name)
    
    def get_child_at_path(self, path):
        """
        获取指定路径的子项目
        
        Args:
            path: 路径列表
            
        Returns:
            子项目对象
        """
        if not path:
            return self
        
        first = path[0]
        if first not in self.children:
            return None
        
        child = self.children[first]
        if len(path) == 1:
            return child
        
        if hasattr(child, "get_child_at_path"):
            return child.get_child_at_path(path[1:])
        
        return None
    
    def search(self, query):
        """
        搜索子项目
        
        Args:
            query: 搜索查询
            
        Returns:
            匹配的项目列表，每个项目是 (路径, 项目) 元组
        """
        results = []
        query = query.lower()
        
        # 检查当前文件夹是否匹配
        if query in self.name.lower() or query in self.description.lower():
            results.append(([], self))
        
        # 搜索子项目
        for name, child in self.children.items():
            if hasattr(child, "search"):
                # 文件夹
                child_results = child.search(query)
                for path, item in child_results:
                    results.append(([name] + path, item))
            else:
                # 书签
                if child.matches_search(query):
                    results.append(([name], child))
        
        return results