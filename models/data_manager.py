#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from utils.file_utils import safe_read_file, safe_write_file
from utils.json_utils import safe_json_load, safe_json_dump, validate_json_schema
from ui.icons import resource_path

logger = logging.getLogger(__name__)

class DataManager(QObject):
    """数据管理器，负责书签数据的加载、保存和管理"""
    
    # 定义信号
    data_changed = pyqtSignal()
    
    def __init__(self, data_file):
        super().__init__()
        self.data_file = data_file
        self.data = {}
    
    def load(self):
        """加载书签数据"""
        # 获取数据文件所在目录作为基础目录
        base_dir = os.path.dirname(self.data_file)
        
        if os.path.exists(self.data_file):
            # 使用安全文件读取
            success, content = safe_read_file(base_dir, self.data_file, encoding='utf-8')
            
            if success:
                # 使用安全 JSON 解析
                json_success, json_data, json_error = safe_json_load(content, {})
                
                if json_success:
                    # 验证 JSON 结构
                    valid, validation_error = validate_json_schema(json_data)
                    
                    if valid:
                        self.data = json_data
                        logger.info(f"从 {self.data_file} 加载了数据")
                    else:
                        logger.error(f"JSON 格式验证失败: {validation_error}")
                        self.load_default_data()
                        QMessageBox.warning(
                            None, 
                            "数据加载失败", 
                            f"书签数据结构无效，将使用默认数据。\n错误: {validation_error}"
                        )
                else:
                    logger.error(f"JSON 解析失败: {json_error}")
                    self.load_default_data()
                    QMessageBox.warning(
                        None, 
                        "数据加载失败", 
                        f"无法解析书签数据，将使用默认数据。\n错误: {json_error}"
                    )
            else:
                logger.error(f"读取文件失败: {content}")
                self.load_default_data()
                QMessageBox.warning(
                    None, 
                    "数据加载失败", 
                    f"无法读取数据文件，将使用默认数据。\n错误: {content}"
                )
        else:
            logger.info(f"数据文件 {self.data_file} 不存在，将使用默认数据")
            self.load_default_data()
    
    def save(self):
        """保存书签数据"""
        # 获取数据文件所在目录作为基础目录
        base_dir = os.path.dirname(self.data_file)
        
        # 验证数据结构
        valid, validation_error = validate_json_schema(self.data)
        if not valid:
            logger.error(f"数据结构验证失败，无法保存: {validation_error}")
            QMessageBox.warning(
                None, 
                "保存失败", 
                f"书签数据结构无效，无法保存。\n错误: {validation_error}"
            )
            return
        
        # 使用安全 JSON 序列化
        json_success, json_data, json_error = safe_json_dump(self.data)
        
        if not json_success:
            logger.error(f"序列化数据失败: {json_error}")
            QMessageBox.warning(
                None, 
                "保存失败", 
                f"无法序列化书签数据。\n错误: {json_error}"
            )
            return
            
        # 使用安全文件写入
        success, message = safe_write_file(base_dir, self.data_file, json_data, encoding='utf-8')
        
        if success:
            logger.info(f"数据已保存到 {self.data_file}")
        else:
            logger.error(f"保存数据失败: {message}")
            QMessageBox.warning(
                None, 
                "保存失败", 
                f"无法保存书签数据。\n错误: {message}"
            )
    
    def load_default_data(self):
        """加载默认数据"""
        self.data = {
            "技术资源": {
                "type": "folder",
                "children": {
                    "编程语言": {
                        "type": "folder",
                        "children": {
                            "Python": {
                                "type": "url",
                                "url": "https://www.python.org",
                                "name": "Python官网",
                                "icon": ""
                            },
                            "JavaScript": {
                                "type": "url",
                                "url": "https://developer.mozilla.org/zh-CN/docs/Web/JavaScript",
                                "name": "MDN JavaScript",
                                "icon": ""
                            }
                        }
                    },
                    "GitHub": {
                        "type": "url",
                        "url": "https://github.com",
                        "name": "GitHub",
                        "icon": ""
                    }
                }
            },
            "工具箱": {
                "type": "folder",
                "children": {
                    "搜索引擎": {
                        "type": "folder",
                        "children": {
                            "Google": {
                                "type": "url",
                                "url": "https://www.google.com",
                                "name": "Google搜索",
                                "icon": ""
                            },
                            "百度": {
                                "type": "url",
                                "url": "https://www.baidu.com",
                                "name": "百度搜索",
                                "icon": ""
                            }
                        }
                    }
                }
            }
        }
        logger.info("已加载默认数据")
        self.data_changed.emit()
    
    def get_item_at_path(self, path):
        """获取指定路径的项目"""
        current = self.data
        
        for segment in path:
            if segment in current and current[segment]["type"] == "folder":
                current = current[segment]["children"]
            else:
                return None
        
        return current
    
    def get_folder_data(self, path):
        """
        获取指定路径的文件夹数据
        
        Args:
            path: 文件夹路径列表
            
        Returns:
            文件夹数据字典，如果找不到则返回None
        """
        if not path:
            return None
            
        # 处理路径到倒数第二层
        parent = self.data
        for i, segment in enumerate(path[:-1]):
            if segment in parent:
                if parent[segment]["type"] == "folder":
                    parent = parent[segment]["children"]
                else:
                    return None
            else:
                return None
                
        # 获取最后一个节点
        last_segment = path[-1]
        if last_segment in parent and parent[last_segment]["type"] == "folder":
            return parent[last_segment]
        
        return None
    
    def add_folder(self, path, name):
        """添加文件夹"""
        parent = self.get_item_at_path(path)
        if parent is None:
            logger.error(f"路径不存在: {'/'.join(path)}")
            return False
        
        if name in parent:
            logger.error(f"名称已存在: {name}")
            return False
        
        parent[name] = {
            "type": "folder",
            "children": {}
        }
        
        logger.info(f"已添加文件夹: {name} 到 {'/'.join(path)}")
        self.data_changed.emit()
        return True
    
    def add_url(self, path, name, url, icon=""):
        """添加URL"""
        parent = self.get_item_at_path(path)
        if parent is None:
            logger.error(f"路径不存在: {'/'.join(path)}")
            return False
        
        if name in parent:
            logger.error(f"名称已存在: {name}")
            return False
        
        # 标准化图标路径
        standardized_icon = self._standardize_icon_path(icon)
        
        parent[name] = {
            "type": "url",
            "url": url,
            "name": name,
            "icon": standardized_icon
        }
        
        logger.info(f"已添加URL: {name} ({url}) 到 {'/'.join(path)}")
        self.data_changed.emit()
        return True
    
    def update_item(self, path, old_name, new_name, item_data):
        """更新项目"""
        parent = self.get_item_at_path(path)
        if parent is None:
            logger.error(f"路径不存在: {'/'.join(path)}")
            return False
        
        if old_name not in parent:
            logger.error(f"项目不存在: {old_name}")
            return False
        
        if old_name != new_name and new_name in parent:
            logger.error(f"名称已存在: {new_name}")
            return False
        
        # 删除旧项目
        item = parent.pop(old_name)
        
        # 更新项目数据
        if item["type"] == "url":
            # 标准化图标路径
            new_icon = item_data.get("icon", item["icon"])
            standardized_icon = self._standardize_icon_path(new_icon)
            
            item.update({
                "url": item_data.get("url", item["url"]),
                "name": new_name,
                "icon": standardized_icon
            })
        else:  # folder
            item["name"] = new_name
        
        # 添加更新后的项目
        parent[new_name] = item
        
        logger.info(f"已更新项目: {old_name} -> {new_name}")
        self.data_changed.emit()
        return True
    
    def delete_item(self, path, name):
        """删除项目"""
        parent = self.get_item_at_path(path)
        if parent is None:
            logger.error(f"路径不存在: {'/'.join(path)}")
            return False
        
        if name not in parent:
            logger.error(f"项目不存在: {name}")
            return False
        
        del parent[name]
        
        logger.info(f"已删除项目: {name} 从 {'/'.join(path)}")
        self.data_changed.emit()
        return True
    
    def move_item(self, source_path, source_name, target_path):
        """移动项目"""
        # 获取源和目标文件夹
        source_parent = self.get_item_at_path(source_path)
        target_parent = self.get_item_at_path(target_path)
        
        if source_parent is None:
            logger.error(f"源路径不存在: {'/'.join(source_path)}")
            return False
        
        if target_parent is None:
            logger.error(f"目标路径不存在: {'/'.join(target_path)}")
            return False
        
        if source_name not in source_parent:
            logger.error(f"源项目不存在: {source_name}")
            return False
        
        if source_name in target_parent:
            logger.error(f"目标文件夹中已存在同名项目: {source_name}")
            return False
        
        # 检查是否将文件夹移动到其子文件夹中
        if source_parent[source_name]["type"] == "folder":
            # 构建完整的源路径
            full_source_path = source_path + [source_name]
            
            # 检查目标路径是否是源路径的子路径
            if len(target_path) >= len(full_source_path):
                is_subpath = True
                for i in range(len(full_source_path)):
                    if full_source_path[i] != target_path[i]:
                        is_subpath = False
                        break
                
                if is_subpath:
                    logger.error("不能将文件夹移动到其子文件夹中")
                    return False
        
        # 移动项目
        item = source_parent.pop(source_name)
        target_parent[source_name] = item
        
        logger.info(f"已移动项目: {source_name} 从 {'/'.join(source_path)} 到 {'/'.join(target_path)}")
        self.data_changed.emit()
        return True
    
    def search(self, query):
        """搜索项目"""
        results = []
        
        def search_in(items, path):
            for name, item in items.items():
                current_path = path + [name]
                item_type = item.get("type", "unknown")
                
                # 检查名称是否匹配
                if query.lower() in name.lower():
                    results.append({
                        "path": current_path,
                        "item": item,
                        "name": name
                    })
                
                # 如果是URL，检查URL是否匹配
                if item_type == "url" and "url" in item and query.lower() in item["url"].lower():
                    if not any(r["path"] == current_path for r in results):
                        results.append({
                            "path": current_path,
                            "item": item,
                            "name": name
                        })
                
                # 如果是文件夹，递归搜索
                if item_type == "folder" and "children" in item:
                    search_in(item["children"], current_path)
        
        try:
            search_in(self.data, [])
        except Exception as e:
            logger.error(f"搜索过程中发生错误: {e}")
        
        return results
    
    def _standardize_icon_path(self, icon_path):
        """标准化图标路径，避免硬编码路径问题"""
        if not icon_path:
            return "resources/icons/globe.png"  # 默认图标

        # 1. 如果是程序内部资源路径，直接返回
        if icon_path.startswith("resources/"):
            return icon_path

        # 2. 如果是绝对路径且文件存在 (通常是用户缓存的图标)，直接返回
        if os.path.isabs(icon_path) and os.path.exists(icon_path):
            # 确保路径分隔符统一，这有助于跨平台和比较
            return os.path.normpath(icon_path)

        # 3. 处理其他情况：可能是相对路径（非resources/开头）或无效路径
        # 尝试将其视为一个文件名，并在 PyslInstaller 临时目录或用户缓存目录中查找
        # (这部分逻辑基于之前的硬编码判断，现在简化处理)
        
        # 提取文件名
        filename = os.path.basename(icon_path)
        if not filename: # 如果icon_path是目录或者解析不出文件名
            logger.warning(f"无法从路径 '{icon_path}' 提取有效的文件名，使用默认图标")
            return "resources/icons/globe.png"
            
        if '.' not in filename:
            # 如果文件名没有扩展名，尝试添加常见的图标扩展名
            # 这里可以根据实际情况调整，或者依赖 FaviconService 返回带扩展名的路径
            # 为简化，如果之前能获取到图标，它应该已经有扩展名了
            # 如果没有，则可能本身就是个问题路径
            pass # filename += '.png' # 暂时不自动加扩展名，依赖输入

        # 尝试在应用的 resources/icons 目录中查找 (作为一种后备)
        standard_icon_path_in_resources = f"resources/icons/{filename}"
        full_standard_path_in_resources = resource_path(standard_icon_path_in_resources)

        if os.path.exists(full_standard_path_in_resources):
            logger.debug(f"在 resources/icons 中找到图标: {standard_icon_path_in_resources}")
            return standard_icon_path_in_resources
        
        # 检查是否在用户特定的图标缓存目录 ( ~/.url_navigator/icons/ )
        # 这个路径应该由 FaviconService 维护，这里只是一个额外的检查点
        # DataManager 本身不应该硬编码这个路径，但为了修复当前问题，可以做一个判断
        user_icon_cache_dir = os.path.join(os.path.expanduser("~"), ".url_navigator", "icons")
        path_in_user_cache = os.path.join(user_icon_cache_dir, filename)
        if os.path.exists(path_in_user_cache):
            logger.debug(f"在用户缓存目录中找到图标: {path_in_user_cache}")
            return os.path.normpath(path_in_user_cache) # 返回绝对路径

        # 如果上述都找不到，记录警告并返回默认图标
        logger.warning(f"图标路径 '{icon_path}' (文件名: '{filename}') 无法解析或文件不存在，使用默认图标")
        return "resources/icons/globe.png"