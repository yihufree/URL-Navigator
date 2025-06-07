#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理工具类
提供高级配置管理功能，包括配置文件的导入导出、验证、备份等
"""

import os
import json
import shutil
import logging
import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理工具类"""
    
    def __init__(self, config: Config):
        """
        初始化配置管理器
        
        Args:
            config: Config实例
        """
        self.config = config
        self.backup_history = []
    
    def export_config_to_file(self, file_path: str, include_paths: bool = True, 
                             include_ui: bool = True, include_advanced: bool = True) -> bool:
        """
        导出配置到文件
        
        Args:
            file_path: 导出文件路径
            include_paths: 是否包含路径配置
            include_ui: 是否包含界面配置
            include_advanced: 是否包含高级配置
            
        Returns:
            bool: 是否成功
        """
        try:
            export_data = {
                "export_info": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "version": "1.0",
                    "app_name": self.config.app_name
                },
                "config": {}
            }
            
            # 选择性导出配置
            if include_paths:
                export_data["config"]["paths"] = self.config.config.get("paths", {})
            
            if include_ui:
                export_data["config"]["window"] = self.config.config.get("window", {})
                export_data["config"]["view"] = self.config.config.get("view", {})
            
            if include_advanced:
                export_data["config"]["favicon"] = self.config.config.get("favicon", {})
                export_data["config"]["advanced"] = self.config.config.get("advanced", {})
                export_data["config"]["language"] = self.config.config.get("language", {})
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"配置已导出到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config_from_file(self, file_path: str, backup_current: bool = True) -> bool:
        """
        从文件导入配置
        
        Args:
            file_path: 导入文件路径
            backup_current: 是否备份当前配置
            
        Returns:
            bool: 是否成功
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"配置文件不存在: {file_path}")
                return False
            
            # 备份当前配置
            if backup_current:
                self.backup_current_config()
            
            # 读取导入文件
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 验证文件格式
            if not self._validate_import_data(import_data):
                logger.error("导入文件格式无效")
                return False
            
            # 导入配置
            imported_config = import_data.get("config", {})
            
            for section, options in imported_config.items():
                if section in self.config.config:
                    for key, value in options.items():
                        self.config.set(section, key, value)
            
            # 保存配置
            self.config.save()
            
            logger.info(f"配置已从 {file_path} 导入")
            return True
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def backup_current_config(self, backup_name: Optional[str] = None) -> str:
        """
        备份当前配置
        
        Args:
            backup_name: 备份名称，如果为None则自动生成
            
        Returns:
            str: 备份文件路径
        """
        try:
            if backup_name is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"config_backup_{timestamp}"
            
            # 获取备份目录
            backup_dir = self.config.get_path("backup_dir")
            config_backup_dir = os.path.join(backup_dir, "config_backups")
            os.makedirs(config_backup_dir, exist_ok=True)
            
            backup_file = os.path.join(config_backup_dir, f"{backup_name}.json")
            
            # 导出当前配置
            if self.export_config_to_file(backup_file):
                self.backup_history.append({
                    "name": backup_name,
                    "file": backup_file,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                logger.info(f"配置已备份到: {backup_file}")
                return backup_file
            else:
                logger.error("配置备份失败")
                return ""
                
        except Exception as e:
            logger.error(f"备份配置失败: {e}")
            return ""
    
    def restore_config_from_backup(self, backup_file: str) -> bool:
        """
        从备份恢复配置
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            bool: 是否成功
        """
        return self.import_config_from_file(backup_file, backup_current=True)
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """
        获取备份列表
        
        Returns:
            List[Dict]: 备份信息列表
        """
        try:
            backup_dir = self.config.get_path("backup_dir")
            config_backup_dir = os.path.join(backup_dir, "config_backups")
            
            if not os.path.exists(config_backup_dir):
                return []
            
            backups = []
            for file in os.listdir(config_backup_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(config_backup_dir, file)
                    stat = os.stat(file_path)
                    backups.append({
                        "name": file[:-5],  # 去掉.json后缀
                        "file": file_path,
                        "size": stat.st_size,
                        "timestamp": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # 按时间排序
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
            return []
    
    def clean_old_backups(self, keep_count: int = 10) -> int:
        """
        清理旧的备份文件
        
        Args:
            keep_count: 保留的备份数量
            
        Returns:
            int: 删除的备份数量
        """
        try:
            backups = self.get_backup_list()
            
            if len(backups) <= keep_count:
                return 0
            
            # 删除多余的备份
            deleted_count = 0
            for backup in backups[keep_count:]:
                try:
                    os.remove(backup["file"])
                    deleted_count += 1
                    logger.debug(f"已删除旧备份: {backup['name']}")
                except Exception as e:
                    logger.warning(f"删除备份失败 {backup['name']}: {e}")
            
            logger.info(f"已清理 {deleted_count} 个旧备份文件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理备份失败: {e}")
            return 0
    
    def validate_current_config(self) -> Dict[str, List[str]]:
        """
        验证当前配置
        
        Returns:
            Dict[str, List[str]]: 验证结果，包含错误和警告
        """
        result = {
            "errors": [],
            "warnings": []
        }
        
        try:
            # 验证路径配置
            path_issues = self.config.validate_paths()
            if path_issues:
                result["warnings"].extend(path_issues)
            
            # 验证窗口配置
            window_config = self.config.config.get("window", {})
            if window_config.get("width", 0) < 400:
                result["warnings"].append("窗口宽度过小，可能影响使用体验")
            if window_config.get("height", 0) < 300:
                result["warnings"].append("窗口高度过小，可能影响使用体验")
            
            # 验证视图配置
            view_config = self.config.config.get("view", {})
            if view_config.get("grid_columns", 0) < 1:
                result["errors"].append("网格列数必须大于0")
            if view_config.get("tree_width", 0) < 100:
                result["warnings"].append("文件夹树宽度过小，可能影响使用")
            
            # 验证高级配置
            advanced_config = self.config.config.get("advanced", {})
            timeout = advanced_config.get("connection_timeout", 10)
            if timeout < 1 or timeout > 60:
                result["warnings"].append("连接超时时间建议设置在1-60秒之间")
            
            logger.info(f"配置验证完成: {len(result['errors'])} 个错误, {len(result['warnings'])} 个警告")
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            result["errors"].append(f"验证过程出错: {str(e)}")
        
        return result
    
    def reset_section_to_defaults(self, section: str) -> bool:
        """
        重置指定配置节到默认值
        
        Args:
            section: 配置节名称
            
        Returns:
            bool: 是否成功
        """
        try:
            if section not in self.config.defaults:
                logger.error(f"未知的配置节: {section}")
                return False
            
            # 备份当前配置
            self.backup_current_config(f"before_reset_{section}")
            
            # 重置配置节
            self.config.config[section] = self.config.defaults[section].copy()
            self.config.save()
            
            logger.info(f"配置节 '{section}' 已重置为默认值")
            return True
            
        except Exception as e:
            logger.error(f"重置配置节失败: {e}")
            return False
    
    def _validate_import_data(self, data: Dict) -> bool:
        """
        验证导入数据格式
        
        Args:
            data: 导入的数据
            
        Returns:
            bool: 是否有效
        """
        try:
            # 检查基本结构
            if not isinstance(data, dict):
                return False
            
            if "config" not in data:
                return False
            
            config_data = data["config"]
            if not isinstance(config_data, dict):
                return False
            
            # 检查配置节是否有效
            valid_sections = set(self.config.defaults.keys())
            for section in config_data.keys():
                if section not in valid_sections:
                    logger.warning(f"未知的配置节将被忽略: {section}")
            
            return True
            
        except Exception as e:
            logger.error(f"验证导入数据失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要信息
        
        Returns:
            Dict: 配置摘要
        """
        try:
            paths = self.config.get_all_paths()
            
            summary = {
                "app_name": self.config.app_name,
                "config_sections": list(self.config.config.keys()),
                "paths": {
                    "data_file": paths.get("data_file", ""),
                    "icons_dir": paths.get("icons_dir", ""),
                    "backup_dir": paths.get("backup_dir", "")
                },
                "window": {
                    "size": f"{self.config.get('window', 'width', 1000)}x{self.config.get('window', 'height', 600)}",
                    "maximized": self.config.get('window', 'maximized', False)
                },
                "language": self.config.get('language', 'current', 'zh'),
                "backup_count": len(self.get_backup_list())
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取配置摘要失败: {e}")
            return {}