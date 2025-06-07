#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import shutil
import datetime
import platform
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDesktopWidget
from PyQt5.QtCore import QSettings, Qt

from ui.main_window import MainWindow
from models.data_manager import DataManager
from services.favicon_service import FaviconService
from services.import_export import ImportExportService
from config import Config
from utils.language_manager import language_manager

logger = logging.getLogger(__name__)

class UrlNavigatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化设置
        self.settings = QSettings("URL Navigator", "URL Navigator")
        # 新增：初始化配置对象
        self.config = Config()
        
        # 加载语言设置
        saved_language = self.settings.value("language", "zh")
        language_manager.set_language(saved_language)
        
        # 从配置系统获取路径
        self._init_paths_from_config()
        
        # 创建必要的目录
        self.config.create_directories()
        
        # 验证路径配置
        path_issues = self.config.validate_paths()
        if path_issues:
            logger.warning(f"路径配置存在问题: {path_issues}")
        
        # 初始化服务
        self.data_manager = DataManager(self.data_file)
        self.favicon_service = FaviconService(self.icons_dir)
        self.import_export_service = ImportExportService(self.data_manager)
        
        # 加载数据
        self.load_data()
        
        # 自动备份
        self.perform_auto_backup()
        
        # 初始化UI
        self.init_ui()
        
        logger.info("应用程序初始化完成")
    
    def _init_paths_from_config(self):
        """从配置系统初始化路径"""
        # 获取所有路径配置
        paths = self.config.get_all_paths()
        
        # 设置应用程序路径属性
        self.data_file = paths.get("data_file")
        self.icons_dir = paths.get("icons_dir")
        self.log_file = paths.get("log_file")
        self.backup_dir = paths.get("backup_dir")
        self.export_dir = paths.get("export_dir")
        self.import_dir = paths.get("import_dir")
        self.temp_dir = paths.get("temp_dir")
        
        # 保存默认路径引用（用于UI显示）
        default_paths = self.config.get_default_paths()
        self.default_data_file = default_paths.get("data_file")
        self.default_icons_dir = default_paths.get("icons_dir")
        self.default_log_file = default_paths.get("log_file")
        self.default_backup_dir = default_paths.get("backup_dir")
        
        logger.info("已从配置系统初始化路径")
        
        return paths
    
    def perform_auto_backup(self):
        """执行自动备份"""
        try:
            # 确保备份目录存在
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # 获取当前日期和时间
            now = datetime.datetime.now()
            today = now.strftime("%Y%m%d")
            time_str = now.strftime("%H%M%S")
            date_time_str = f"{today}_{time_str}"
            
            # 检查备份目录是否为空
            is_backup_dir_empty = True
            if os.path.exists(self.backup_dir):
                backup_files = [f for f in os.listdir(self.backup_dir) if os.path.isfile(os.path.join(self.backup_dir, f))]
                is_backup_dir_empty = len(backup_files) == 0
            
            # 检查今天是否已经备份过
            last_backup_date = self.settings.value("backup/last_backup_date", "")
            
            # 如果今天已经备份过且备份目录不为空，跳过备份
            if last_backup_date == today and not is_backup_dir_empty:
                logger.info(f"今天 ({today}) 已经执行过备份，跳过")
                return
            
            # 如果备份目录为空，强制执行备份
            if is_backup_dir_empty:
                logger.info("备份目录为空，执行自动备份...")
            
            # JSON 格式备份
            json_backup_path = os.path.join(self.backup_dir, f"{date_time_str}_bookmarks.json")
            if not os.path.exists(json_backup_path):
                shutil.copy2(self.data_file, json_backup_path)
                logger.info(f"数据文件已备份到: {json_backup_path}")
            
            # HTML 格式备份
            html_backup_path = os.path.join(self.backup_dir, f"{date_time_str}_bookmarks.html")
            if not os.path.exists(html_backup_path):
                self.import_export_service.export_html(html_backup_path)
                logger.info(f"书签已备份为HTML到: {html_backup_path}")
            
            # 日志文件备份
            if os.path.exists(self.log_file):
                log_backup_path = os.path.join(self.backup_dir, f"{date_time_str}_bookmarks.log")
                if not os.path.exists(log_backup_path):
                    shutil.copy2(self.log_file, log_backup_path)
                    logger.info(f"日志文件已备份到: {log_backup_path}")
            
            # 更新最后备份日期
            self.settings.setValue("backup/last_backup_date", today)
            logger.info(f"自动备份已完成，日期: {today}")
            
        except Exception as e:
            logger.error(f"自动备份失败: {e}")
    
    def init_ui(self):
        """初始化用户界面"""
        self.main_window = MainWindow(self)
        self.setCentralWidget(self.main_window)
        
        # 设置窗口属性
        self.setWindowTitle(language_manager.tr("app_title"))
        self.resize(1200, 600)
        
        # 连接语言切换信号以更新窗口标题
        language_manager.language_changed.connect(self.update_window_title)
        
        # 将窗口居中显示在屏幕靠上方位置
        desktop = QDesktopWidget()
        screen_geometry = desktop.availableGeometry()
        
        # 计算窗口位置，使其居中且靠上
        window_width = 1200
        window_height = 600
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 3  # 设置为屏幕高度的1/3位置，使其靠上
        
        self.setGeometry(x, y, window_width, window_height)
        
        # 连接信号
        self.main_window.closing.connect(self.save_settings)
    
    def load_data(self):
        """加载数据"""
        try:
            self.data_manager.load()
            logger.info("数据加载成功")
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            QMessageBox.warning(
                self, 
                "数据加载失败", 
                f"无法加载书签数据: {str(e)}\n将使用默认数据。"
            )
            self.data_manager.load_default_data()
    
    def save_settings(self):
        """保存应用设置"""
        # 不再保存窗口位置
        self.data_manager.save()
        logger.info("数据已保存")
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        self.save_settings()
        event.accept()

    def set_paths(self, data_file, icons_dir, log_file, history_file=None, backup_dir=None, export_dir=None, import_dir=None, temp_dir=None):
        """设置自定义路径并保存到配置系统，并自动迁移原有数据/图标/日志文件"""
        # 保存当前路径以便迁移
        old_data_file = self.data_file
        old_icons_dir = self.icons_dir
        old_log_file = self.log_file
        old_history_file = getattr(self, 'history_file', self.config.get_path('history_file'))
        
        # 准备新的路径配置
        paths_dict = {
            "data_file": data_file,
            "icons_dir": icons_dir,
            "log_file": log_file,
            "history_file": history_file
        }
        
        # 添加可选路径
        if backup_dir:
            paths_dict["backup_dir"] = backup_dir
        if export_dir:
            paths_dict["export_dir"] = export_dir
        if import_dir:
            paths_dict["import_dir"] = import_dir
        if temp_dir:
            paths_dict["temp_dir"] = temp_dir
            
        # 更新配置系统中的路径
        self.config.set_all_paths(paths_dict)
        
        # 重新从配置加载路径
        self._init_paths_from_config()
        
        # 创建必要的目录
        self.config.create_directories()
        
        # 自动迁移数据文件
        if os.path.abspath(data_file) != os.path.abspath(old_data_file):
            if os.path.exists(old_data_file) and not os.path.exists(data_file):
                try:
                    shutil.copy2(old_data_file, data_file)
                    logger.info(f"已迁移数据文件: {old_data_file} -> {data_file}")
                except Exception as e:
                    logger.error(f"迁移数据文件失败: {e}")
        
        # 自动迁移图标文件夹
        if os.path.abspath(icons_dir) != os.path.abspath(old_icons_dir):
            if os.path.exists(old_icons_dir) and not os.path.exists(icons_dir):
                try:
                    shutil.copytree(old_icons_dir, icons_dir)
                    logger.info(f"已迁移图标文件夹: {old_icons_dir} -> {icons_dir}")
                except Exception as e:
                    logger.error(f"迁移图标文件夹失败: {e}")
        
        # 自动迁移日志文件
        if os.path.abspath(log_file) != os.path.abspath(old_log_file):
            if os.path.exists(old_log_file) and not os.path.exists(log_file):
                try:
                    shutil.copy2(old_log_file, log_file)
                    logger.info(f"已迁移日志文件: {old_log_file} -> {log_file}")
                except Exception as e:
                    logger.error(f"迁移日志文件失败: {e}")
        
        # 自动迁移历史记录文件
        if history_file and old_history_file:
            if os.path.abspath(history_file) != os.path.abspath(old_history_file):
                if os.path.exists(old_history_file) and not os.path.exists(history_file):
                    try:
                        shutil.copy2(old_history_file, history_file)
                        logger.info(f"已迁移历史记录文件: {old_history_file} -> {history_file}")
                    except Exception as e:
                        logger.error(f"迁移历史记录文件失败: {e}")
        
        # 重新初始化服务
        self.data_manager = DataManager(self.data_file)
        self.favicon_service = FaviconService(self.icons_dir)
        self.import_export_service = ImportExportService(self.data_manager)
        
        # 重新加载数据
        self.load_data()
        
        # 更新UI组件的引用
        if hasattr(self, 'main_window'):
            self.main_window.folder_tree.data_manager = self.data_manager
            self.main_window.bookmark_grid.data_manager = self.data_manager
            self.main_window.bookmark_grid.favicon_service = self.favicon_service
            # 更新盲盒管理器的历史记录文件路径
            if hasattr(self.main_window, 'blind_box_manager'):
                self.main_window.blind_box_manager.history_file = self.config.get_path('history_file')
            self.main_window.folder_tree.refresh()
            self.main_window.bookmark_grid.set_current_path([])
        
        logger.info(f"已切换路径配置并应用更改")
        return True

    def get_log_file(self):
        return self.log_file
        
    def get_backup_dir(self):
        """获取备份目录"""
        return self.backup_dir
    
    def update_window_title(self):
        """更新窗口标题（语言切换时调用）"""
        self.setWindowTitle(language_manager.tr("app_title"))