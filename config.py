#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
from PyQt5.QtCore import QSettings

logger = logging.getLogger(__name__)

class Config:
    """配置管理类"""
    
    def __init__(self, app_name="URL Navigator"):
        """
        初始化配置管理器
        
        Args:
            app_name: 应用程序名称
        """
        self.app_name = app_name
        
        # 使用QSettings存储应用程序设置
        self.settings = QSettings(app_name, app_name)
        
        # 设置默认配置
        self.defaults = {
            "window": {
                "width": 1000,
                "height": 600,
                "maximized": False
            },
            "view": {
                "tree_width": 200,
                "grid_columns": 4,
                "show_url_in_grid": True
            },
            "favicon": {
                "min_size": 16,
                "prefer_size": 32,
                "cache_days": 30
            },
            "advanced": {
                "connection_timeout": 10,
                "debug_mode": False
            },
            "paths": {
                "data_file": "",
                "icons_dir": "",
                "log_file": "",
                "history_file": "",
                "backup_dir": "",
                "export_dir": "",
                "import_dir": "",
                "temp_dir": ""
            },
            "language": {
                "current": "zh",
                "auto_detect": True
            }
        }
        
        # 加载配置
        self.load()
    
    def load(self):
        """加载配置"""
        # 从QSettings加载配置
        self.config = {}
        
        # 遍历默认配置，从QSettings加载值或使用默认值
        for section, options in self.defaults.items():
            self.config[section] = {}
            for key, default_value in options.items():
                value = self.settings.value(f"{section}/{key}", default_value)
                
                # 确保布尔值正确转换
                if isinstance(default_value, bool):
                    if isinstance(value, str):
                        value = value.lower() == "true"
                    else:
                        value = bool(value)
                
                # 确保数值正确转换
                elif isinstance(default_value, int):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = default_value
                
                # 确保浮点数正确转换
                elif isinstance(default_value, float):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = default_value
                
                self.config[section][key] = value
        
        logger.info("配置已加载")
    
    def save(self):
        """保存配置"""
        # 将配置保存到QSettings
        for section, options in self.config.items():
            for key, value in options.items():
                self.settings.setValue(f"{section}/{key}", value)
        
        self.settings.sync()
        logger.info("配置已保存")
    
    def get(self, section, key, default=None):
        """
        获取配置值
        
        Args:
            section: 配置节
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default
    
    def set(self, section, key, value):
        """
        设置配置值
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        self.settings.setValue(f"{section}/{key}", value)
    
    def export_to_json(self, file_path):
        """
        导出配置到JSON文件
        
        Args:
            file_path: JSON文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info(f"配置已导出到 {file_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_from_json(self, file_path):
        """
        从JSON文件导入配置
        
        Args:
            file_path: JSON文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 更新配置
            for section, options in imported_config.items():
                if section not in self.config:
                    self.config[section] = {}
                
                for key, value in options.items():
                    self.config[section][key] = value
                    self.settings.setValue(f"{section}/{key}", value)
            
            logger.info(f"配置已从 {file_path} 导入")
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self.config = self.defaults.copy()
        self.save()
        logger.info("配置已重置为默认值")
    
    def get_default_paths(self):
        """获取默认路径配置"""
        import platform
        
        # 用户主目录下的应用数据目录
        user_data_dir = os.path.join(os.path.expanduser("~"), ".url_navigator")
        
        # 检查D盘是否存在（Windows系统）
        backup_dir = "D:\\urlnav" if (platform.system() == "Windows" and os.path.exists("D:\\")) else "C:\\urlnav"
        
        return {
            "data_file": os.path.join(user_data_dir, "bookmarks.json"),
            "icons_dir": os.path.join(user_data_dir, "icons"),
            "log_file": os.path.join(user_data_dir, "logs", "url_navigator.log"),
            "history_file": os.path.join(user_data_dir, "blind_box_history.json"),
            "backup_dir": backup_dir,
            "export_dir": os.path.join(os.path.expanduser("~"), "Documents"),
            "import_dir": os.path.join(os.path.expanduser("~"), "Documents"),
            "temp_dir": os.path.join(user_data_dir, "temp")
        }
    
    def get_path(self, path_type):
        """获取指定类型的路径"""
        path = self.get("paths", path_type)
        if not path:  # 如果路径为空，返回默认路径
            default_paths = self.get_default_paths()
            return default_paths.get(path_type, "")
        return path
    
    def set_path(self, path_type, path):
        """设置指定类型的路径"""
        self.set("paths", path_type, path)
        logger.info(f"路径已设置: {path_type} = {path}")
    
    def get_all_paths(self):
        """获取所有路径配置"""
        default_paths = self.get_default_paths()
        current_paths = self.config.get("paths", {})
        
        # 合并默认路径和当前配置
        all_paths = {}
        for key in default_paths:
            all_paths[key] = current_paths.get(key) or default_paths[key]
        
        return all_paths
    
    def set_all_paths(self, paths_dict):
        """批量设置路径"""
        for path_type, path in paths_dict.items():
            if path_type in self.get_default_paths():
                self.set_path(path_type, path)
        self.save()
        logger.info("所有路径配置已更新")
    
    def create_directories(self):
        """创建所有必要的目录"""
        paths = self.get_all_paths()
        
        # 为文件路径创建父目录
        file_paths = ["data_file", "log_file", "history_file"]
        for path_type in file_paths:
            path = paths.get(path_type)
            if path:
                parent_dir = os.path.dirname(path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                    logger.debug(f"创建目录: {parent_dir}")
        
        # 为目录路径直接创建目录
        dir_paths = ["icons_dir", "backup_dir", "export_dir", "import_dir", "temp_dir"]
        for path_type in dir_paths:
            path = paths.get(path_type)
            if path:
                os.makedirs(path, exist_ok=True)
                logger.debug(f"创建目录: {path}")
        
        logger.info("所有必要目录已创建")
    
    def validate_paths(self):
        """验证路径配置的有效性"""
        paths = self.get_all_paths()
        issues = []
        
        for path_type, path in paths.items():
            if not path:
                continue
                
            # 检查父目录是否可写
            if path_type in ["data_file", "log_file", "history_file"]:
                parent_dir = os.path.dirname(path)
                if parent_dir and not os.access(parent_dir, os.W_OK):
                    if not os.path.exists(parent_dir):
                        try:
                            os.makedirs(parent_dir, exist_ok=True)
                        except Exception as e:
                            issues.append(f"{path_type}: 无法创建目录 {parent_dir} - {e}")
                    else:
                        issues.append(f"{path_type}: 目录 {parent_dir} 不可写")
            else:
                # 目录路径检查
                if not os.access(path, os.W_OK):
                    if not os.path.exists(path):
                        try:
                            os.makedirs(path, exist_ok=True)
                        except Exception as e:
                            issues.append(f"{path_type}: 无法创建目录 {path} - {e}")
                    else:
                        issues.append(f"{path_type}: 目录 {path} 不可写")
        
        if issues:
            logger.warning(f"路径配置验证发现问题: {'; '.join(issues)}")
        else:
            logger.info("路径配置验证通过")
        
        return issues