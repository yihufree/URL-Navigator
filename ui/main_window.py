#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import copy
import datetime
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter, 
    QToolBar, QAction, QFileDialog, QInputDialog, 
    QMessageBox, QProgressDialog, QLineEdit, QToolButton, QMenu, QStatusBar, QPushButton, QDialog, QRadioButton, QDialogButtonBox, QLabel, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore

from ui.folder_tree import FolderTreeWidget
from ui.bookmark_grid import BookmarkGridWidget
from ui.dialogs import AddUrlDialog, AddFolderDialog, SearchDialog, SettingsDialog, ExportDialog
from ui.history_dialog import HistoryDialog
from ui.blind_box_dialog import WebsiteBlindBoxDialog
from ui.icons import icon_provider
from ui.icons import resource_path
from utils.language_manager import language_manager
from utils.blind_box_manager import BlindBoxManager

logger = logging.getLogger(__name__)

class MainWindow(QWidget):
    """主窗口"""
    
    # 定义信号
    closing = pyqtSignal()
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.undo_stack = []  # 撤销栈
        self.sort_mode = 'name'  # 默认按名字排序
        self.is_locked = False  # 添加锁定状态变量
        self.blind_box_manager = BlindBoxManager(app.data_manager, app.config)  # 网站盲盒管理器
        
        # 连接语言切换信号
        language_manager.language_changed.connect(self.update_ui_texts)
        
        self.init_ui()
        self._update_actions_state()  # Ensure initial action states are set
        
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏
        toolbar = QToolBar()
        toolbar.setIconSize(QtCore.QSize(32, 32))
        toolbar.setStyleSheet("QToolBar { spacing: 1px; }")  # 进一步减小工具栏按钮间距
        
        # 先创建所有QAction
        self.add_url_action = QAction(icon_provider.get_icon("globe"), language_manager.tr("main_window.add_url"), self)
        self.edit_url_action = QAction(QIcon(resource_path("resources/icons/editurl.png")), language_manager.tr("main_window.edit_url"), self)
        self.add_folder_action = QAction(icon_provider.get_icon("folder"), language_manager.tr("main_window.add_folder"), self)
        self.rename_action = QAction(icon_provider.get_icon("edit"), language_manager.tr("main_window.rename"), self)
        self.cut_action = QAction(QIcon(resource_path("resources/icons/cut.ico")), language_manager.tr("main_window.cut"), self)
        self.copy_action = QAction(icon_provider.get_icon("copy"), language_manager.tr("main_window.copy"), self)
        self.paste_action = QAction(icon_provider.get_icon("paste"), language_manager.tr("main_window.paste"), self)
        self.delete_action = QAction(icon_provider.get_icon("delete"), language_manager.tr("main_window.delete"), self)
        self.import_action = QAction(icon_provider.get_icon("import"), language_manager.tr("main_window.import"), self)
        self.export_action = QAction(icon_provider.get_icon("export"), language_manager.tr("main_window.export"), self)
        self.refresh_icons_action = QAction(icon_provider.get_icon("refresh"), language_manager.tr("main_window.refresh"), self)
        self.search_action = QAction(icon_provider.get_icon("search"), language_manager.tr("main_window.search"), self)
        self.settings_action = QAction(QIcon(resource_path("resources/icons/setup.ico")), language_manager.tr("main_window.settings"), self)
        self.lock_action = QAction(QIcon(resource_path("resources/icons/lock.ico")), language_manager.tr("main_window.lock"), self)
        self.about_action = QAction(QIcon(resource_path("resources/icons/info.ico")), language_manager.tr("main_window.about"), self)
        self.undo_action = QAction(QIcon(resource_path("resources/icons/undo.ico")), language_manager.tr("main_window.undo"), self)
        self.sort_action = QAction(QIcon(resource_path("resources/icons/sort.ico")), language_manager.tr("main_window.sort"), self)
        self.open_url_action = QAction(QIcon(resource_path("resources/icons/open.ico")), language_manager.tr("main_window.open_website"), self)

        # 连接QAction的triggered信号到对应槽函数
        self.add_url_action.triggered.connect(self._add_url)
        self.edit_url_action.triggered.connect(self._edit_selected_url)
        self.add_folder_action.triggered.connect(self._add_folder)
        self.rename_action.triggered.connect(self._rename_selected)
        self.cut_action.triggered.connect(self._cut_selected)
        self.copy_action.triggered.connect(self._copy_selected)
        self.paste_action.triggered.connect(self._paste_selected)
        self.delete_action.triggered.connect(self._delete_selected)
        self.import_action.triggered.connect(self._import_bookmarks)
        self.export_action.triggered.connect(self._export_bookmarks)
        self.refresh_icons_action.triggered.connect(self._refresh_all_icons)
        self.search_action.triggered.connect(self._search)
        self.settings_action.triggered.connect(self._show_settings_dialog)
        self.lock_action.triggered.connect(self._toggle_lock)  # 添加锁定按钮点击事件
        self.about_action.triggered.connect(self._show_about_dialog)
        self.undo_action.triggered.connect(self._undo_last_action)
        self.sort_action.triggered.connect(self._toggle_sort_mode)
        self.open_url_action.triggered.connect(self._open_selected_url)  # 连接打开网站按钮点击事件
        
        # 工具栏按钮配置（顺序、变量、图标、文字、tooltip、槽函数）
        button_configs = [
            (self.add_url_action, language_manager.tr("main_window.add_url"), self._add_url),
            (self.edit_url_action, language_manager.tr("main_window.edit_url"), self._edit_selected_url),
            (self.add_folder_action, language_manager.tr("main_window.add_folder"), self._add_folder),
            (self.rename_action, language_manager.tr("main_window.edit_folder"), self._rename_selected),
            (self.cut_action, language_manager.tr("main_window.cut"), self._cut_selected),
            (self.copy_action, language_manager.tr("main_window.copy"), self._copy_selected),
            (self.paste_action, language_manager.tr("main_window.paste"), self._paste_selected),
            (self.delete_action, language_manager.tr("main_window.delete"), self._delete_selected),
            (self.undo_action, language_manager.tr("main_window.undo"), self._undo_last_action),
            (self.import_action, language_manager.tr("main_window.import"), self._import_bookmarks),
            (self.export_action, language_manager.tr("main_window.export"), self._export_bookmarks),
            (self.refresh_icons_action, language_manager.tr("main_window.refresh"), self._refresh_all_icons),
            (self.sort_action, language_manager.tr("main_window.sort"), self._toggle_sort_mode),
            (self.open_url_action, language_manager.tr("main_window.open_website"), self._open_selected_url),
            (self.settings_action, language_manager.tr("main_window.settings"), self._show_settings_dialog),
            (self.lock_action, language_manager.tr("main_window.lock"), self._toggle_lock),
            (self.about_action, language_manager.tr("main_window.about"), self._show_about_dialog),
        ]
        # 清空toolbar原有action
        toolbar.clear()
        # 依次添加自定义按钮
        for action, text, slot in button_configs:
            btn = QToolButton()
            btn.setDefaultAction(action)
            if action == self.paste_action: # 新增判断
                btn.setObjectName("pasteButton") # 为粘贴按钮设置 objectName
                btn.setAutoRaise(False)  # <--- 新增这一行
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setText(text)
            btn.setMinimumWidth(50)  # 减小按钮最小宽度
            if text in ["添加网址", "添加目录"]:
                btn.setMinimumWidth(60)  # 减小特定按钮宽度
            elif text == "打开网站":
                btn.setMinimumWidth(70)  # 减小打开网站按钮宽度
            btn.setSizePolicy(btn.sizePolicy().horizontalPolicy(), btn.sizePolicy().verticalPolicy())
            toolbar.addWidget(btn)
        
        # 添加垂直分隔线
        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setStyleSheet("background-color: #CCCCCC;")  # 设置分隔线颜色
        separator.setFixedHeight(40)  # 设置分隔线高度
        toolbar.addWidget(separator)
        
        # 创建搜索框和搜索按钮
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(2)  # 紧凑布局
        
        # 添加搜索输入框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(language_manager.tr("main_window.search_placeholder"))
        self.search_edit.returnPressed.connect(self._search)
        self.search_edit.setMinimumWidth(50)  # 设置搜索框宽度在100-200之间
        self.search_edit.setMaximumWidth(750)  # 最大宽度限制
        search_layout.addWidget(self.search_edit)
        
        # 创建搜索按钮
        search_btn = QToolButton()
        search_btn.setDefaultAction(self.search_action)
        search_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        search_btn.setText("搜索")
        search_btn.setMinimumWidth(50)
        search_btn.setIconSize(QtCore.QSize(32, 32))  # 设置搜索按钮图标大小与工具栏其他按钮一致
        search_layout.addWidget(search_btn)

        # === 添加语言选择下拉框 ===
        from PyQt5.QtWidgets import QComboBox
        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(90)
        self.language_combo.setMaximumWidth(150)
        available_languages = language_manager.get_available_languages()
        current_language = language_manager.get_current_language()
        for code, name in available_languages.items():
            self.language_combo.addItem(name, code)
            if code == current_language:
                self.language_combo.setCurrentText(name)
        self.language_combo.setToolTip(language_manager.tr("settings.language_label", "语言"))
        # 切换语言时立即生效
        def on_language_changed(name):
            for i in range(self.language_combo.count()):
                if self.language_combo.itemText(i) == name:
                    code = self.language_combo.itemData(i)
                    if code != language_manager.get_current_language():
                        language_manager.set_language(code)
                        # 保存到设置（与设置界面一致）
                        if hasattr(self.app, 'settings'):
                            self.app.settings.setValue("language", code)
                    break
        self.language_combo.currentTextChanged.connect(on_language_changed)
        # 设置右侧外边距为10
        search_layout.addWidget(self.language_combo)
        search_layout.setSpacing(5)
        search_layout.setContentsMargins(0, 0, 5, 0)  # 仅右侧外边距为5
        # === 语言选择下拉框结束 ===

        # 创建一个容器小部件以保存搜索布局
        search_widget = QWidget()
        search_widget.setLayout(search_layout)
        
        # 添加自动伸展来推动搜索框到右侧
        toolbar.addWidget(QWidget())
        toolbar.addWidget(search_widget)
        
        # 添加工具栏到布局
        layout.addWidget(toolbar)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧根目录栏
        self.root_bar = QHBoxLayout()
        self.root_bar.setContentsMargins(8, 4, 8, 4)
        self.root_bar.setSpacing(4)
        self.root_bar_widget = QWidget()
        self.root_bar_widget.setLayout(self.root_bar)
        
        # 创建文件夹树
        self.folder_tree = FolderTreeWidget(self.app.data_manager)
        self.folder_tree.set_root_bar(self.root_bar)
        self.folder_tree.set_main_window(self)  # 设置主窗口引用
        
        # 左侧布局（目录区域）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.root_bar_widget)
        left_layout.addWidget(self.folder_tree)
        
        # 添加历史记录按钮
        self._create_history_button(left_layout)
        
        splitter.addWidget(left_widget)
        
        # 创建中间区域容器（网址卡片区域）
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        
        # 创建面包屑导航栏
        self.breadcrumb_bar = QHBoxLayout()
        self.breadcrumb_bar.setContentsMargins(8, 4, 8, 4)
        self.breadcrumb_bar.setSpacing(4)
        self.breadcrumb_widget = QWidget()
        self.breadcrumb_widget.setLayout(self.breadcrumb_bar)
        middle_layout.addWidget(self.breadcrumb_widget)
        
        # 创建书签网格
        self.bookmark_grid = BookmarkGridWidget(self.app.data_manager, self.app.favicon_service)
        self.bookmark_grid.set_breadcrumb_bar(self.breadcrumb_bar)
        middle_layout.addWidget(self.bookmark_grid)
        # --- 新增：连接选中项变化信号 ---
        self.bookmark_grid.selection_changed.connect(self._update_actions_state)
        
        splitter.addWidget(middle_widget)
        
        # 创建右侧区域容器（网站盲盒按钮区域）
        self.right_widget = QWidget()
        self.right_widget.setFixedWidth(100)  # 恢复原始宽度
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        # 创建"Magic Box 开魔盒"文本标签
        self.magic_box_label = QLabel("MagicBox\n开魔盒")
        self.magic_box_label.setAlignment(Qt.AlignCenter)
        self.magic_box_label.setStyleSheet("""
            QLabel {
                color: #8B0040;
                font-size: 18px;
                font-weight: bold;
                font-family: "方正古隶简体", "华文隶书", "华文琥珀", "SimSun", serif;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                background: transparent;
                margin: 5px;
                line-height: 1.2;
            }
        """)
        # 初始状态隐藏标签
        self.magic_box_label.hide()
        
        # 创建网站盲盒按钮
        self.blind_box_button = QPushButton()
        self.blind_box_button.setFixedSize(90, 90)  # 设置为90x90像素的正方形
        self.blind_box_button.setToolTip(language_manager.tr("tooltips.blind_box_tooltip", "网站盲盒 - 随机打开网站"))
        self.blind_box_button.clicked.connect(self._show_blind_box_dialog)
        
        # 设置圆形按钮样式
        manghe_icon_path = resource_path("resources/icons/manghe.png").replace("\\", "/")
        self.blind_box_button.setStyleSheet(f"""
            QPushButton {{
                border-radius: 45px;
                background-color: #f0ad4e;
                background-image: url({manghe_icon_path});
                background-position: center;
                background-repeat: no-repeat;
                background-size: 60px 60px;
                border: 2px solid #ec971f;
            }}
            QPushButton:hover {{
                background-color: #ec971f;
                border: 2px solid #d58512;
            }}
            QPushButton:pressed {{
                background-color: #d58512;
                border: 2px solid #b8741f;
            }}
        """)
        
        # 创建随机网址图标显示区域
        self.random_urls_scroll = QScrollArea()
        self.random_urls_scroll.setWidgetResizable(True)
        self.random_urls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.random_urls_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.random_urls_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        
        # 创建图标容器
        self.random_urls_container = QWidget()
        self.random_urls_layout = QVBoxLayout(self.random_urls_container)
        self.random_urls_layout.setAlignment(Qt.AlignTop)
        self.random_urls_layout.setContentsMargins(3, 3, 3, 3)
        self.random_urls_layout.setSpacing(5)
        self.random_urls_scroll.setWidget(self.random_urls_container)
        
        # 添加标签、按钮和图标显示区域到右侧布局
        # 使"Magic Box 开魔盒"标签上方与左侧网址标签区域边框在同一水平线上
        right_layout.addWidget(self.magic_box_label, 0, Qt.AlignCenter)
        # 为两行文字标签和按钮之间增加间距
        right_layout.addSpacing(10)
        right_layout.addWidget(self.blind_box_button, 0, Qt.AlignCenter)
        # 为"网站盲盒"按钮的动画运动预留空间
        right_layout.addSpacing(20)  # 增加按钮与图标显示框之间的间距
        right_layout.addWidget(self.random_urls_scroll, 3)  # 增加权重，使其占据更多空间
        
        splitter.addWidget(self.right_widget)
        
        # 设置分割器初始大小（左侧200，中间700，右侧100）
        splitter.setSizes([200, 700, 100])
        
        # 保存分割器为类成员变量以便后续访问
        self.splitter = splitter
        
        # 连接splitter的splitterMoved信号，用于监听分割器移动
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        
        # 添加分割器到布局
        layout.addWidget(splitter)
        
        # 添加状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(25)
        layout.addWidget(self.status_bar)
        self.update_status_bar()
        
        # 设置布局
        self.setLayout(layout)
        # 美化主窗口边框
        self.setStyleSheet("""
            QWidget#MainWindow {
                border: 10px solid #7a8ba7;
                border-radius: 12px;
                background: #f8f9fa;
                box-shadow: 0 0 0 4px #c7d0e0 inset;
            }
        """)
        self.setObjectName("MainWindow")
        
        # 连接信号
        self.folder_tree.path_changed.connect(self.bookmark_grid.set_current_path)
        self.folder_tree.path_changed.connect(self._update_blind_box_button_visibility)  # 路径变化时更新按钮显示
        self.bookmark_grid.navigate_to.connect(self._navigate_to)
        # 连接选择清除信号
        self.folder_tree.selection_cleared.connect(self._handle_selection_cleared)
        self.folder_tree.selection_cleared.connect(self._update_blind_box_button_visibility)  # 选择清除时更新按钮显示
        
        # 初始化按钮显示状态
        self._update_blind_box_button_visibility()
        
        logger.info("主窗口初始化完成")
    
    def _navigate_to(self, path):
        """导航到指定路径"""
        self.folder_tree.select_path(path)
        self.bookmark_grid.set_current_path(path)
    
    def _handle_selection_cleared(self):
        """处理文件夹树选择清除事件"""
        # 显示根目录内容
        self.bookmark_grid.set_current_path([])
    
    def _on_splitter_moved(self, pos, index):
        """处理分割器移动事件，确保两侧面板都有最小宽度"""
        MIN_WIDTH = 50  # 最小宽度限制（像素）
        
        # 获取当前窗口总宽度
        total_width = self.width()
        
        # 获取当前分割位置
        sizes = self.splitter.sizes()
        
        # 检查左侧面板宽度是否满足最小要求
        if sizes[0] < MIN_WIDTH:
            # 调整分割位置，确保左侧面板有最小宽度
            sizes[0] = MIN_WIDTH
            sizes[1] = total_width - MIN_WIDTH - self.splitter.handleWidth()
            self.splitter.setSizes(sizes)
        
        # 检查右侧面板宽度是否满足最小要求
        elif sizes[1] < MIN_WIDTH:
            # 调整分割位置，确保右侧面板有最小宽度
            sizes[1] = MIN_WIDTH
            sizes[0] = total_width - MIN_WIDTH - self.splitter.handleWidth()
            self.splitter.setSizes(sizes)
    
    def _rename_selected(self):
        """重命名选中的文件夹"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        self._save_undo_snapshot()
        # 获取当前选中的路径
        selected_path = self.folder_tree.get_selected_path()
        if not selected_path:
            QMessageBox.information(self, "提示", "请先选择要重命名的文件夹")
            return
        
        # 获取文件夹名称和路径
        folder_name = selected_path[-1]
        parent_path = selected_path[:-1]
        
        # 显示重命名对话框
        new_name, ok = QInputDialog.getText(
            self, 
            "编辑目录", 
            "请输入新的目录名称:",
            text=folder_name
        )
        
        if ok and new_name and new_name != folder_name:
            # 重命名文件夹
            success = self.app.data_manager.update_item(
                parent_path,
                folder_name,
                new_name,
                {}
            )
            
            if success:
                self.app.data_manager.save()
                QMessageBox.information(self, "编辑目录成功", f"目录已重命名为: {new_name}")
                
                # 如果是当前显示的文件夹，更新路径
                if self.bookmark_grid.current_path == selected_path:
                    new_path = parent_path + [new_name]
                    self.folder_tree.select_path(new_path)
                    self.bookmark_grid.set_current_path(new_path)
            else:
                QMessageBox.warning(self, "编辑目录失败", "无法重命名目录，可能是名称已存在")
    
    def _delete_selected(self):
        """删除选中的项目（优先删除卡片区选中项，弹出自定义确认消息框）"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        self._save_undo_snapshot()
        # 优先删除右侧卡片区选中项
        if hasattr(self, 'bookmark_grid') and self.bookmark_grid.selected_items:
            items = self.bookmark_grid.selected_items
            url_count = sum(1 for n, t in items if t == 'url')
            folder_count = sum(1 for n, t in items if t == 'folder')
            if len(items) == 1:
                n, t = items[0]
                if t == 'url':
                    msg = f'你确定要删除"{n}"网址吗？'
                else:
                    msg = f'你确定要删除"{n}"文件夹吗？'
            else:
                msg_parts = []
                if url_count:
                    msg_parts.append(f"{url_count}个网址")
                if folder_count:
                    msg_parts.append(f"{folder_count}个文件夹")
                msg = "你确定要删除" + "、".join(msg_parts) + "吗？"
            reply = QMessageBox.question(self, "确认删除", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.bookmark_grid._batch_delete(confirm_from_main=True)
            return
        # 否则删除左侧文件夹树选中的文件夹
        selected_path = self.folder_tree.get_selected_path()
        if not selected_path:
            QMessageBox.information(self, "提示", "请先选择要删除的文件夹或卡片")
            return
        folder_name = selected_path[-1]
        msg = f'你确定要删除"{folder_name}"文件夹吗？'
        reply = QMessageBox.question(self, "确认删除", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 删除文件夹
            success = self.app.data_manager.delete_item(selected_path[:-1], folder_name)
            
            if success:
                self.app.data_manager.save()
                QMessageBox.information(self, "删除成功", f"文件夹 {folder_name} 已删除")
                
                # 如果是当前显示的文件夹，返回上一级
                if self.bookmark_grid.current_path == selected_path:
                    self.folder_tree.select_path(selected_path[:-1])
                    self.bookmark_grid.set_current_path(selected_path[:-1])
            else:
                QMessageBox.warning(self, "删除失败", "无法删除文件夹")
    
    def _add_url(self):
        """添加URL"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        self._save_undo_snapshot()
        # 获取当前路径，优先使用树形视图的选择
        selected_path = self.folder_tree.get_selected_path()
        if selected_path:
            current_path = selected_path
        else:
            # 如果没有选择，则使用书签网格当前显示的路径
            current_path = self.bookmark_grid.current_path
            
        dialog = AddUrlDialog(self.app.favicon_service, current_path, self)
        
        if dialog.exec_():
            url_data = dialog.get_data()
            
            # 添加URL
            success = self.app.data_manager.add_url(
                current_path,
                url_data["name"],
                url_data["url"],
                url_data["icon"]
            )
            
            if success:
                self.app.data_manager.save()
                QMessageBox.information(self, "添加成功", f"已添加网址: {url_data['name']}")
            else:
                QMessageBox.warning(self, "添加失败", "无法添加网址，可能是名称已存在")
    
    def _add_folder(self):
        """添加文件夹"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        self._save_undo_snapshot()
        # 获取当前路径，优先使用树形视图的选择
        selected_path = self.folder_tree.get_selected_path()
        if selected_path:
            current_path = selected_path
        else:
            # 如果没有选择，则使用书签网格当前显示的路径
            current_path = self.bookmark_grid.current_path
            
        dialog = AddFolderDialog(current_path, self)
        
        if dialog.exec_():
            folder_name = dialog.get_folder_name()
            
            # 添加文件夹
            success = self.app.data_manager.add_folder(current_path, folder_name)
            
            if success:
                self.app.data_manager.save()
                QMessageBox.information(self, "添加成功", f"已添加文件夹: {folder_name}")
                
                # 如果是在根目录添加，刷新文件夹树，并选择新文件夹
                if not current_path:
                    self.folder_tree.refresh()
                    self.folder_tree.select_path([folder_name])
                    self.bookmark_grid.set_current_path([folder_name])
            else:
                QMessageBox.warning(self, "添加失败", "无法添加文件夹，可能是名称已存在")
    
    def _import_bookmarks(self):
        """导入书签"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
        
        # 选择文件对话框 - 同时支持HTML和JSON格式文件
        file_path, filter_type = QFileDialog.getOpenFileName(
            self,
            "导入书签",
            "",
            "书签文件 (*.html *.htm *.json);;HTML文件 (*.html *.htm);;JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
            
        # 文件安全验证和用户通知
        try:
            # 验证文件是否存在
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "导入书签", "选择的文件不存在")
                return
                
            # 验证文件大小
            file_size_mb = os.path.getsize(file_path) / (1024*1024)
            MAX_SIZE_MB = 3
            if file_size_mb > MAX_SIZE_MB:
                QMessageBox.warning(
                    self, 
                    "文件太大", 
                    f"所选文件大小为 {file_size_mb:.1f} MB，超过了 {MAX_SIZE_MB} MB 的限制。\n请选择更小的文件。"
                )
                return
                
            # 用户安全提醒
            reply = QMessageBox.question(
                self,
                "导入书签",
                f"您正在导入外部文件: \n{file_path}\n\n导入外部文件可能存在安全风险。确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        except Exception as e:
            QMessageBox.warning(self, "导入书签", f"文件验证错误: {str(e)}")
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在导入书签...", "取消", 0, 100, self)
        progress.setWindowTitle("导入书签")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        # 连接信号
        self.app.import_export_service.import_progress.connect(
            lambda value, text: progress.setValue(value) or progress.setLabelText(text)
        )
        
        # 根据文件类型选择导入方法
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.json']:
            # JSON导入
            count = self.app.import_export_service.import_json(file_path)
            import_type = "JSON"
        else:
            # HTML导入（默认）
            count = self.app.import_export_service.import_html(file_path)
            import_type = "HTML"
        
        # 断开信号
        self.app.import_export_service.import_progress.disconnect()
        
        if count > 0:
            QMessageBox.information(self, "导入成功", f"已成功从{import_type}文件导入 {count} 个书签")
        else:
            QMessageBox.warning(self, "导入失败", f"导入书签失败，请检查{import_type}文件格式")
            
    def _export_bookmarks(self):
        """导出书签"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
        
        # 获取当前路径
        current_path = self.folder_tree.get_selected_path()
        
        # 使用ExportDialog代替简单的文件选择对话框
        dialog = ExportDialog(self, default_dir=None, current_path=current_path)
        if not dialog.exec_():
            return
        
        # 获取导出类型和路径
        export_type = dialog.get_export_type()  # 0:HTML, 1:JSON, 2:日志
        export_path = dialog.get_export_path()
        export_scope = dialog.get_export_scope()  # 0:全部导出, 1:导出部分数据
        export_directory = dialog.get_export_directory()  # 要导出的目录路径
        
        if not export_path:
            return
            
        # 调用执行导出方法
        self._execute_export(export_type, export_path, export_scope, export_directory, dialog.selected_type)
    
    def _execute_export(self, export_type, export_path, export_scope, export_directory, selected_all=None):
        """执行导出操作"""
        # 安全验证和用户通知
        try:
            # 验证文件路径是否安全
            from utils.file_utils import is_safe_path
            
            # 获取用户主目录和系统临时目录
            home_dir = os.path.expanduser("~")
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(export_path)), "temp")
            
            # 检查路径是否在用户目录或临时目录中
            if not (is_safe_path(home_dir, export_path) or is_safe_path(temp_dir, export_path)):
                reply = QMessageBox.question(
                    self,
                    "路径安全警告",
                    f"您选择的路径可能不在安全的位置：\n{export_path}\n\n确定要继续吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                    
            # 用户权限通知 - 根据导出类型显示不同信息
            operation_name = ""
            if selected_all == 'all':
                operation_name = "所有类型的文件（HTML书签、JSON数据、日志文件）"
            elif export_type == 0:
                operation_name = "HTML书签"
            elif export_type == 1:
                operation_name = "JSON数据"
            elif export_type == 2:
                operation_name = "日志文件"
            
            # 添加导出范围提示
            if export_scope == 1 and export_directory:
                folder_name = export_directory[-1] if export_directory else ""
                operation_name += f"（仅包含「{folder_name}」文件夹）"
                
            reply = QMessageBox.question(
                self,
                "导出确认",
                f"您即将导出{operation_name}到：\n{os.path.dirname(export_path)}\n\n确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Yes:
                return
                
        except Exception as e:
            QMessageBox.warning(self, "导出书签", f"文件路径验证错误: {str(e)}")
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在导出...", "取消", 0, 100, self)
        progress.setWindowTitle("导出中")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        # 设置进度条更新函数
        def update_progress(value, text):
            progress.setValue(value)
            progress.setLabelText(text)
            
        # 连接信号
        self.app.import_export_service.export_progress.connect(update_progress)
        
        success = False
        export_type_name = "未知类型"  # 初始化导出类型名称变量
        
        try:
            # 处理导出全部文件的情况
            if selected_all == 'all':
                # 准备三种不同类型的文件路径
                base_dir = os.path.dirname(export_path)
                # 获取当前日期时间
                date_str = datetime.datetime.now().strftime('%Y%m%d')
                time_str = datetime.datetime.now().strftime('%H%M%S')
                
                html_path = os.path.join(base_dir, f"{date_str}_{time_str}_bookmarks.html")
                json_path = os.path.join(base_dir, f"{date_str}_{time_str}_bookmarks.json")
                log_path = os.path.join(base_dir, f"{date_str}_{time_str}_bookmarks.log")
                
                # 导出HTML书签
                update_progress(0, "正在导出HTML书签...")
                html_success = self.app.import_export_service.export_html(html_path)
                
                # 导出JSON数据
                update_progress(33, "正在导出JSON数据...")
                json_success = self.app.import_export_service.export_json(json_path)
                
                # 导出日志文件
                update_progress(66, "正在导出日志文件...")
                log_success = False
                try:
                    if os.path.exists(self.app.log_file):
                        shutil.copy2(self.app.log_file, log_path)
                        log_success = True
                        logger.info(f"日志文件已导出到: {log_path}")
                except Exception as e:
                    logger.error(f"导出日志文件失败: {str(e)}")
                
                update_progress(100, "导出完成")
                
                # 显示结果
                success_count = sum([html_success, json_success, log_success])
                if success_count == 3:
                    QMessageBox.information(self, "导出成功", f"已成功导出所有3个文件到:\n{os.path.dirname(html_path)}")
                    success = True
                else:
                    QMessageBox.warning(self, "导出部分成功", 
                        f"成功导出 {success_count}/3 个文件:\n" +
                        f"HTML书签: {'成功' if html_success else '失败'}\n" +
                        f"JSON数据: {'成功' if json_success else '失败'}\n" +
                        f"日志文件: {'成功' if log_success else '失败'}")
                    success = success_count > 0
                
            # 处理单一类型导出
            else:
                # 根据范围选择不同的导出方法
                if export_scope == 0:  # 全部导出
                    if export_type == 0:  # HTML
                        success = self.app.import_export_service.export_html(export_path)
                        export_type_name = "HTML书签"
                    elif export_type == 1:  # JSON
                        success = self.app.import_export_service.export_json(export_path)
                        export_type_name = "JSON数据"
                    elif export_type == 2:  # 日志文件
                        try:
                            if os.path.exists(self.app.log_file):
                                shutil.copy2(self.app.log_file, export_path)
                                success = True
                                logger.info(f"日志文件已导出到: {export_path}")
                            else:
                                QMessageBox.warning(self, "导出失败", f"日志文件不存在: {self.app.log_file}")
                                success = False
                        except Exception as e:
                            logger.error(f"导出日志文件失败: {str(e)}")
                            QMessageBox.warning(self, "导出失败", f"导出日志文件失败: {str(e)}")
                            success = False
                        export_type_name = "日志文件"
                else:  # 导出部分数据
                    if not export_directory:
                        QMessageBox.warning(self, "导出失败", "未选择要导出的文件夹")
                        success = False
                    else:
                        folder_name = export_directory[-1]
                        if export_type == 0:  # HTML
                            success = self.app.import_export_service.export_specific_folder_html(export_path, export_directory)
                            export_type_name = f"HTML书签（{folder_name}文件夹）"
                        elif export_type == 1:  # JSON
                            success = self.app.import_export_service.export_specific_folder_json(export_path, export_directory)
                            export_type_name = f"JSON数据（{folder_name}文件夹）"
                        elif export_type == 2:  # 日志文件
                            try:
                                if os.path.exists(self.app.log_file):
                                    shutil.copy2(self.app.log_file, export_path)
                                    success = True
                                    logger.info(f"日志文件已导出到: {export_path}")
                                else:
                                    QMessageBox.warning(self, "导出失败", f"日志文件不存在: {self.app.log_file}")
                                    success = False
                            except Exception as e:
                                logger.error(f"导出日志文件失败: {str(e)}")
                                QMessageBox.warning(self, "导出失败", f"导出日志文件失败: {str(e)}")
                                success = False
                            export_type_name = "日志文件"
                
                if success:
                    QMessageBox.information(self, "导出成功", f"已成功导出{export_type_name}到:\n{export_path}")
                else:
                    QMessageBox.warning(self, "导出失败", f"导出{export_type_name}失败")
                
        except Exception as e:
            logger.error(f"导出失败: {str(e)}")
            QMessageBox.warning(self, "导出失败", f"导出失败: {str(e)}")
            success = False
        finally:
            # 断开信号
            self.app.import_export_service.export_progress.disconnect(update_progress)
            progress.close()
    
    def _search(self):
        """搜索书签"""
        query = self.search_edit.text().strip()
        if not query:
            QMessageBox.information(self, "搜索", "请输入搜索关键词")
            return
        
        try:
            results = self.app.data_manager.search(query)
            
            if not results:
                QMessageBox.information(self, "搜索结果", "没有找到匹配的书签")
                return
            
            dialog = SearchDialog(results, self)
            dialog.setWindowTitle(f"搜索 \"{query}\" 的结果")
            if dialog.exec_():
                selected_path = dialog.get_selected_path()
                if selected_path:
                    # 导航到选中的路径
                    parent_path = selected_path[:-1]
                    item_name = selected_path[-1]
                    
                    # 选择文件夹路径
                    self.folder_tree.select_path(parent_path)
                    self.bookmark_grid.set_current_path(parent_path)
                    
                    # 高亮显示选定的项目
                    self.bookmark_grid.highlight_item(item_name)
                    
                    # 记录状态信息
                    message = f"已导航到 {'/'.join(parent_path) or '根目录'}/{item_name}"
                    if self.status_bar:
                        self.status_bar.showMessage(message, 3000)
                    
                    # 查找并选中该项目
                    for w, name, typ in getattr(self.bookmark_grid, '_item_widgets', []):
                        if name == item_name:
                            # 设置选中状态
                            self.bookmark_grid.selected_items = [(name, typ)]
                            self.bookmark_grid.refresh()
                            
                            # 如果是URL类型，可以选择自动打开
                            if typ == "url":
                                # 询问用户是否要打开此URL
                                reply = QMessageBox.question(
                                    self,
                                    "打开网址",
                                    f"是否要打开选中的网址 '{name}'?",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes
                                )
                                
                                if reply == QMessageBox.Yes:
                                    # 调用打开URL方法
                                    w._open_url()
                            break
            
            # 如果进行了删除操作，刷新UI
            if hasattr(dialog, 'deletion_performed') and dialog.deletion_performed:
                self.app.data_manager.data_changed.emit()
                
        except Exception as e:
            logging.error(f"搜索出错: {str(e)}")
            QMessageBox.warning(self, "搜索失败", f"搜索过程中发生错误：{str(e)}")
    
    def _refresh_all_icons(self):
        """批量更新网址的图标"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        # 获取当前选中的路径
        selected_path = self.folder_tree.get_selected_path()
        
        # 如果没有选择更新范围（即默认更新全部书签库），给出提示
        if not selected_path:
            message = """你准备进行的操作将更新全部网址的图标，耗费时间较长，可以在非工作时间进行。

建议返回重新选择更新范围。

如返回重新选择请点击"取消（Cancel）"，如确定更新全部图标请点击"确定（OK）"。"""
            
            reply = QMessageBox.question(
                self,
                "更新范围提示",
                message,
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            # 用户选择返回，则中断操作
            if reply == QMessageBox.Cancel:
                return
        
        if selected_path:
            # 如果有选中的文件夹，只刷新该文件夹下的图标
            folder_display = selected_path[-1]
            title_prefix = f"刷新 '{folder_display}' 的图标"
        else:
            # 如果没有选中的文件夹，刷新所有图标
            title_prefix = "刷新所有图标"
        
        # 创建选择更新模式的对话框
        mode_dialog = QDialog(self)
        mode_dialog.setWindowTitle(f"{title_prefix}选项")
        mode_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(mode_dialog)
        # This software was developed by Fan Huiyong, and all rights belong to Fan Huiyong himself. This software is only allowed for personal non-commercial use; it is prohibited for any organization or individual to use it for profit-making purposes without authorization.
        info_label = QLabel("请选择图标更新方式：")
        layout.addWidget(info_label)
        
        # 只更新不存在图标的网址
        option1 = QRadioButton("仅更新缺失图标的网址（速度较快）")
        option1.setChecked(True)  # 默认选中
        layout.addWidget(option1)
        
        # 强制更新全部网址图标
        option2 = QRadioButton("强制更新全部网址图标（速度较慢）")
        layout.addWidget(option2)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(mode_dialog.accept)
        button_box.rejected.connect(mode_dialog.reject)
        layout.addWidget(button_box)
        
        # 显示对话框
        if not mode_dialog.exec_():
            return  # 用户取消
        
        # 确定更新模式
        force_refresh_all = option2.isChecked()
        
        # 构建确认消息
        if force_refresh_all:
            confirm_text = "强制更新全部"
        else:
            confirm_text = "仅更新缺失"
            
        if selected_path:
            confirm_message = f"这将{confirm_text}文件夹 '{folder_display}' 下网址的图标，是否继续？"
        else:
            confirm_message = f"这将{confirm_text}网址的图标，可能需要较长时间。是否继续？"
            
        # 确认操作
        reply = QMessageBox.question(
            self,
            f"{title_prefix}确认",
            confirm_message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在刷新图标...", "取消", 0, 100, self)
        progress.setWindowTitle(title_prefix)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        try:
            # 获取需要刷新的书签
            all_bookmarks = []
            
            if selected_path:
                # 获取选中文件夹内的内容
                folder_items = self.app.data_manager.get_item_at_path(selected_path)
                if folder_items and isinstance(folder_items, dict):
                    self._collect_all_bookmarks(folder_items, selected_path, all_bookmarks)
            else:
                # 获取所有书签
                self._collect_all_bookmarks(self.app.data_manager.data, [], all_bookmarks)
            
            total_bookmarks = len(all_bookmarks)
            if total_bookmarks == 0:
                QMessageBox.information(self, title_prefix, "没有找到需要更新图标的书签")
                progress.close()
                return
            
            # 更新进度对话框
            progress.setMaximum(total_bookmarks)
            
            # 更新每个书签的图标
            updated_count = 0
            skipped_count = 0
            for i, (path, name, item) in enumerate(all_bookmarks):
                if progress.wasCanceled():
                    break
                
                # 更新进度
                progress.setValue(i + 1)
                progress.setLabelText(f"正在刷新 ({i + 1}/{total_bookmarks}): {name}")
                
                try:
                    # 检查是否需要更新该图标
                    url = item["url"]
                    current_icon = item.get("icon", "")
                    
                    # 判断当前图标是否存在
                    icon_exists = current_icon and os.path.exists(current_icon) and not current_icon.endswith("globe.png")
                    
                    # 如果选择仅更新缺失图标且当前图标存在，则跳过
                    if not force_refresh_all and icon_exists:
                        skipped_count += 1
                        logger.info(f"跳过已有图标: {name}")
                        continue
                    
                    # 获取新图标
                    new_icon = self.app.favicon_service.get_favicon(url, force_refresh=True)
                    
                    # 更新书签
                    if new_icon:
                        item["icon"] = new_icon
                        updated_count += 1
                except Exception as e:
                    logger.error(f"更新图标失败 ({name}): {e}")
            
            # 保存更改
            self.app.data_manager.save()
            
            # 刷新UI
            self.app.data_manager.data_changed.emit()
            
            # 显示完成消息
            result_message = f"已成功更新 {updated_count} 个书签的图标"
            if not force_refresh_all and skipped_count > 0:
                result_message += f"，跳过 {skipped_count} 个已有图标的书签"
                
            QMessageBox.information(
                self, 
                f"{title_prefix}完成", 
                result_message
            )
        
        except Exception as e:
            logger.error(f"刷新图标过程中出错: {e}")
            QMessageBox.warning(self, f"{title_prefix}失败", f"刷新图标过程中出错: {str(e)}")
        
        finally:
            progress.close()
    
    def _collect_all_bookmarks(self, items, current_path, result):
        """递归收集所有书签"""
        for name, item in items.items():
            path = current_path.copy()
            
            if item["type"] == "folder":
                # 递归收集子文件夹中的书签
                self._collect_all_bookmarks(item["children"], path + [name], result)
            else:
                # 添加书签到结果列表
                result.append((path, name, item))
        
        return result
    
    def _show_about_dialog(self):
        """显示关于对话框"""
        # message = """<div style="font-size: 10pt;"><b>URL Navigator</b><br>作者：Yifree(开发者昵称)<br>版本：V0.5<br>时间：20250603<br><br>
        message = """<div style="font-size: 10pt;"><b>名称：URL Navigator（中文名称：飞歌网址导航）</b><h3><pre>作者：Yifree(开发者昵称)               版本：V0.5             时间：20250607</pre></h3>
    （一）URL Navigator（飞歌网址导航） 是一款功能丰富的网址导航与书签管理工具，支持书签的添加、编辑、剪切、复制、粘贴、删除、回退、移动、导入、导出、排序、锁定、图标更新、分组管理、智能搜索、语种切换、开魔盒、历史查询、自动备份等功能，帮助用户高效管理和访问保存的网址。<br>
    （二）💖特色功能："开魔盒"功能可随机浏览收藏的书签中的网站。用户先选择目录范围（不选择时为全部），再输入想打开的网址数量，软件会在选定的范围内随机打开指定数量的网址供浏览，每次浏览的网址图标会显示在“开魔盒”按钮下方，再次开魔盒时刷新。此功能方便保存大量书签的朋友查看自己保存的网站历史。<br>    
    （三）用户可自行设置网址的书签数据、图标文件、历史记录数据、日志文件的文件夹或名称，也可以设置数据自动备份文件夹（书签数据一般在C:\\Users\\用户名\\.url_navigator\\目录下，名称为bookmarks.json，用户可使用设置功能进行更改）。系统有每日自动备份功能，位置可在设置中更改。<br>
    （四）可导入chrome等浏览器导出的规范HTML格式书签文件（尽量只有一个层级，在一个目录下，否则速度慢且容易出错），也可以使用本软件导出或备份的json格式书签文件（将书签备份文件名称改为bookmarks.json）直接覆盖掉原来的json文件，速度更快）；用户的书签数据可全部或部分导出为json格式和HTML格式。可搜索网址和查看历史记录，在结果中再打开或定位网址位置。<br>
    （五）可批量全部或部分更新图标（速度较慢），可将网址卡片按照名称和添加时间排序。为防止误操作，可使用'锁定'功能暂时禁用部分功能，再次点击时解锁。<br>
    （六）软件有语种选择功能，提供部分语言主要操作界面翻译，满足不同语种使用人员的基本使用。<br>
    （七）本软件为个人开发，产权属于开发者本人（本页所示作者名称为昵称，权利人为昵称对应的实际开发者）。作者许可您一项个人的、可撤销的、不可转让的、非独占地和非商业的合法使用本产品的权利，您不享有本产品的所有权。作者基于本协议对您的授权仅为授权您个人以非商业的目的对于本产品进行使用，任何超出个人使用目的的使用行为都必须另行获得作者本人具体的、单独的、书面的授权，协议未明示授权的其他一切权利仍由我方保留，您在行使该等权利前须另行获得我方的书面许可，同时我方如未行使前述任何权利，并不构成对该权利的放弃。严禁任何单位和个人未经授权将软件（或将项目改头换面）用于营利或非法用途，否则将追究法律责任。<br>
    （八）本软件为个人开发，开发者不承担任何责任，请用户自行承担使用风险。<br>
      💖🌹感谢您的使用！欢迎提出宝贵意见！😊 <br> </div>"""
        
        # 创建自定义对话框以更可靠地控制宽度
        dialog = QDialog(self)
        dialog.setWindowTitle("关于 飞歌网址导航")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QMessageBox.standardIcon(QMessageBox.Information))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # 使用QTextBrowser显示HTML内容
        from PyQt5.QtWidgets import QTextBrowser
        text_browser = QTextBrowser()
        text_browser.setHtml(message)
        text_browser.setOpenExternalLinks(True)
        text_browser.setReadOnly(True)
        
        # 设置宽度为原来的130%
        base_width = 650
        text_browser.setMinimumWidth(int(base_width * 1.4))
        
        # 设置高度为当前高度的2倍
        base_height = 400  # 假设当前基础高度
        text_browser.setMinimumHeight(int(base_height * 1.3))
        
        layout.addWidget(text_browser)
        
        # 添加确定按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.exec_()
    
    def _copy_selected(self):
        """批量复制右侧网格多选的项目"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        if hasattr(self, 'bookmark_grid'):
            self.bookmark_grid._batch_copy()
    
    def _paste_selected(self):
        """批量粘贴到右侧网格当前目录"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        if hasattr(self, 'bookmark_grid'):
            self._save_undo_snapshot()  # 先保存快照
            self.bookmark_grid._paste_item()
    
    def _show_settings_dialog(self):
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        dialog = SettingsDialog(self.app, self)
        dialog.exec_()
    
    def _cut_selected(self):
        """调用右侧网格的剪切方法"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        self.bookmark_grid._cut_selected()
    
    def _save_undo_snapshot(self):
        # 保存当前数据快照到撤销栈
        self.undo_stack.append(copy.deepcopy(self.app.data_manager.data))
        # 限制撤销栈长度，防止内存溢出
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def _undo_last_action(self):
        """撤销上一步操作"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            self._show_locked_message()
            return
            
        if not self.undo_stack:
            QMessageBox.information(self, "回退", "没有可回退的操作。")
            return
        reply = QMessageBox.question(self, "回退确认", "确定要撤销上一步操作吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            last_data = self.undo_stack.pop()
            self.app.data_manager.data = copy.deepcopy(last_data)
            self.app.data_manager.data_changed.emit()
            QMessageBox.information(self, "回退", "已撤销上一步操作。")
    
    def _toggle_sort_mode(self):
        """切换排序方式"""
        if self.sort_mode == 'name':
            self.sort_mode = 'time'
        else:
            self.sort_mode = 'name'
        if hasattr(self, 'bookmark_grid'):
            self.bookmark_grid.set_sort_mode(self.sort_mode)
    
    def _toggle_lock(self):
        """切换锁定状态"""
        self.is_locked = not self.is_locked
        
        # 更新锁定按钮图标和文字
        if self.is_locked:
            self.lock_action.setIcon(QIcon(resource_path("resources/icons/lock.ico")))
            self.lock_action.setText("已锁定")
            QMessageBox.information(self, "锁定状态", "已启用锁定状态，部分编辑功能已禁用。")
        else:
            self.lock_action.setIcon(QIcon(resource_path("resources/icons/lock.ico")))
            self.lock_action.setText("锁定")
            QMessageBox.information(self, "锁定状态", "已解除锁定状态，所有功能可正常使用。")
        
        # 更新按钮启用状态
        self._update_actions_state()
        
        # 更新书签网格和文件夹树的锁定状态
        if hasattr(self, 'bookmark_grid'):
            self.bookmark_grid.set_locked_state(self.is_locked)
        
        if hasattr(self, 'folder_tree'):
            self.folder_tree.set_locked_state(self.is_locked)
            
        # 解锁后强制刷新选中项和UI，确保按钮状态恢复
        if not self.is_locked and hasattr(self, 'bookmark_grid'):
            self.bookmark_grid.refresh()
    
    def _update_actions_state(self):
        """根据锁定状态和选择状态更新按钮的启用状态"""
        # 检查是否有网格选中项
        has_grid_selection = bool(hasattr(self, 'bookmark_grid') and self.bookmark_grid.selected_items)
        # 检查是否有文件夹树选中项
        has_folder_selection = bool(hasattr(self, 'folder_tree') and self.folder_tree.get_selected_path())
        # 综合判断是否有任何选中项
        has_selection = has_grid_selection or has_folder_selection
        
        # 不依赖选择状态的按钮
        self.add_url_action.setEnabled(not self.is_locked)
        self.add_folder_action.setEnabled(not self.is_locked)
        self.import_action.setEnabled(not self.is_locked)
        self.refresh_icons_action.setEnabled(not self.is_locked)
        self.undo_action.setEnabled(not self.is_locked)
        self.export_action.setEnabled(not self.is_locked)
        self.settings_action.setEnabled(not self.is_locked)
        
        # 依赖选择状态的按钮
        self.rename_action.setEnabled(has_selection and not self.is_locked)
        self.delete_action.setEnabled(has_selection and not self.is_locked)
        self.cut_action.setEnabled(has_selection and not self.is_locked)
        self.copy_action.setEnabled(has_selection and not self.is_locked)
        
        # 编辑网址按钮只对单个URL启用
        is_single_url = (has_grid_selection and len(self.bookmark_grid.selected_items) == 1 
                         and self.bookmark_grid.selected_items[0][1] == "url")
        self.edit_url_action.setEnabled(is_single_url and not self.is_locked)
        
        # 打开网站按钮始终可用（锁定和解锁状态下均可用）
        self.open_url_action.setEnabled(True)
        
        # 粘贴按钮需要检查剪贴板内容
        has_clipboard_data = False
        if hasattr(self, 'bookmark_grid'):
            has_clipboard_data = (hasattr(self.bookmark_grid, 'clipboard_data') and self.bookmark_grid.clipboard_data is not None and bool(self.bookmark_grid.clipboard_data)) or \
                                (hasattr(self.bookmark_grid, 'cut_data') and self.bookmark_grid.cut_data is not None and bool(self.bookmark_grid.cut_data))
        self.paste_action.setEnabled(bool(has_clipboard_data) and not self.is_locked)
        
        # 这些功能在锁定状态下仍可用
        self.search_action.setEnabled(True)
        self.sort_action.setEnabled(True)
        self.about_action.setEnabled(True)
        self.lock_action.setEnabled(True)
    
    def _show_locked_message(self):
        """显示锁定状态提示消息"""
        QMessageBox.warning(self, "锁定状态", "目前处于编辑锁定状态，如需使用相关功能，请点击锁定按钮进行解锁。")
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        self.closing.emit()
        event.accept()

    def update_status_bar(self):
        """更新状态栏信息"""
        # 统计各级目录数量
        data = self.app.data_manager.data
        level_counts = []
        def count_levels(d, level=1):
            if len(level_counts) < level:
                level_counts.append(0)
            for v in d.values():
                if v["type"] == "folder":
                    level_counts[level-1] += 1
                    count_levels(v["children"], level+1)
        count_levels(data)
        level_info = '，'.join([f'{i+1}级目录{n}个' for i, n in enumerate(level_counts)])
        # 统计全部网址卡片总数
        def count_urls(d):
            cnt = 0
            for v in d.values():
                if v["type"] == "url":
                    cnt += 1
                elif v["type"] == "folder":
                    cnt += count_urls(v["children"])
            return cnt
        total_urls = count_urls(data)
        # 当前文件夹下一级目录和网址卡片数量
        current_path = self.bookmark_grid.current_path if hasattr(self, 'bookmark_grid') else []
        current_items = self.app.data_manager.get_item_at_path(current_path)
        subdir_count = 0
        url_count = 0
        if current_items:
            for v in current_items.values():
                if v["type"] == "folder":
                    subdir_count += 1
                elif v["type"] == "url":
                    url_count += 1
        # 当前文件夹下所有网址卡片数量（递归）
        def count_urls_in_folder(d):
            cnt = 0
            for v in d.values():
                if v["type"] == "url":
                    cnt += 1
                elif v["type"] == "folder":
                    cnt += count_urls_in_folder(v["children"])
            return cnt
        total_urls_in_current = count_urls_in_folder(current_items) if current_items else 0
        # 状态栏文本
        current_path_str = '/'.join(current_path) if current_path else '根目录'
        text = f'    【 统计信息： 1. {level_info}，全部网址{total_urls}个。    ||  2.当前目录：{current_path_str}，下一级目录{subdir_count}个，网址{url_count}个，包含所有子目录网址{total_urls_in_current}个。】'
        self.status_bar.showMessage(text)

    def _open_selected_url(self):
        """打开选中的URL"""
        if not hasattr(self, 'bookmark_grid'):
            return
            
        # 获取所有选中的项目
        selected_items = self.bookmark_grid.selected_items
        
        if not selected_items:
            QMessageBox.information(self, "打开网站", "请先选择要打开的网址")
            return
            
        # 遍历所有选中项目
        opened_count = 0
        for name, item_type in selected_items:
            # 只打开URL类型的项目
            if item_type == "url":
                # 获取项目数据
                for w, n, t in self.bookmark_grid._item_widgets:
                    if n == name and t == item_type:
                        # 调用项目的_open_url方法
                        w._open_url()
                        opened_count += 1
        
        # 显示提示消息
        if opened_count > 0:
            msg = f"已打开 {opened_count} 个网址"
            self.status_bar.showMessage(msg, 3000)
        else:
            QMessageBox.information(self, "打开网站", "没有选中有效的网址项目")

    def _edit_selected_url(self):
        """编辑选中的网址卡片（仅支持单选且为网址类型）"""
        if self.is_locked:
            self._show_locked_message()
            return
        if not hasattr(self, 'bookmark_grid') or not self.bookmark_grid.selected_items:
            QMessageBox.information(self, "编辑网址", "请先选择一个网址卡片")
            return
        items = self.bookmark_grid.selected_items
        if len(items) != 1 or items[0][1] != 'url':
            QMessageBox.information(self, "编辑网址", "只能编辑单个网址卡片")
            return
        name, typ = items[0]
        # 获取当前路径下的项目
        current_items = self.app.data_manager.get_item_at_path(self.bookmark_grid.current_path)
        if not current_items or name not in current_items:
            QMessageBox.warning(self, "编辑网址", "未找到选中的网址")
            return
        item = current_items[name]
        # 复用BookmarkGridWidget._edit_item逻辑
        self.bookmark_grid._edit_item(self.bookmark_grid.current_path, name, item)

    def update_ui_texts(self):
        """更新界面文本（语言切换时调用）"""
        try:
            # 更新窗口标题
            if hasattr(self, 'app') and hasattr(self.app, 'setWindowTitle'):
                self.app.setWindowTitle(language_manager.tr("app_title"))
            # 更新动作文本
            if hasattr(self, 'add_url_action'):
                self.add_url_action.setText(language_manager.tr("main_window.add_url"))
            if hasattr(self, 'edit_url_action'):
                self.edit_url_action.setText(language_manager.tr("main_window.edit_url"))
            if hasattr(self, 'add_folder_action'):
                self.add_folder_action.setText(language_manager.tr("main_window.add_folder"))
            if hasattr(self, 'rename_action'):
                self.rename_action.setText(language_manager.tr("main_window.rename"))
            if hasattr(self, 'cut_action'):
                self.cut_action.setText(language_manager.tr("main_window.cut"))
            if hasattr(self, 'copy_action'):
                self.copy_action.setText(language_manager.tr("main_window.copy"))
            if hasattr(self, 'paste_action'):
                self.paste_action.setText(language_manager.tr("main_window.paste"))
            if hasattr(self, 'delete_action'):
                self.delete_action.setText(language_manager.tr("main_window.delete"))
            if hasattr(self, 'import_action'):
                self.import_action.setText(language_manager.tr("main_window.import"))
            if hasattr(self, 'export_action'):
                self.export_action.setText(language_manager.tr("main_window.export"))
            if hasattr(self, 'refresh_icons_action'):
                self.refresh_icons_action.setText(language_manager.tr("main_window.refresh"))
            if hasattr(self, 'search_action'):
                self.search_action.setText(language_manager.tr("main_window.search"))
            if hasattr(self, 'settings_action'):
                self.settings_action.setText(language_manager.tr("main_window.settings"))
            if hasattr(self, 'lock_action'):
                self.lock_action.setText(language_manager.tr("main_window.lock"))
            if hasattr(self, 'about_action'):
                self.about_action.setText(language_manager.tr("main_window.about"))
            if hasattr(self, 'undo_action'):
                self.undo_action.setText(language_manager.tr("main_window.undo"))
            if hasattr(self, 'sort_action'):
                self.sort_action.setText(language_manager.tr("main_window.sort"))
            if hasattr(self, 'open_url_action'):
                self.open_url_action.setText(language_manager.tr("main_window.open_website"))
            # 更新工具提示
            if hasattr(self, 'add_url_action'):
                self.add_url_action.setToolTip(language_manager.tr("tooltips.add_url_tooltip"))
            if hasattr(self, 'add_folder_action'):
                self.add_folder_action.setToolTip(language_manager.tr("tooltips.add_folder_tooltip"))
            if hasattr(self, 'delete_action'):
                self.delete_action.setToolTip(language_manager.tr("tooltips.delete_tooltip"))
            if hasattr(self, 'cut_action'):
                self.cut_action.setToolTip(language_manager.tr("tooltips.cut_tooltip"))
            if hasattr(self, 'copy_action'):
                self.copy_action.setToolTip(language_manager.tr("tooltips.copy_tooltip"))
            if hasattr(self, 'paste_action'):
                self.paste_action.setToolTip(language_manager.tr("tooltips.paste_tooltip"))
            if hasattr(self, 'search_action'):
                self.search_action.setToolTip(language_manager.tr("tooltips.search_tooltip"))
            if hasattr(self, 'lock_action'):
                self.lock_action.setToolTip(language_manager.tr("tooltips.lock_tooltip"))
            if hasattr(self, 'undo_action'):
                self.undo_action.setToolTip(language_manager.tr("tooltips.undo_tooltip"))
            # 更新搜索框占位符
            if hasattr(self, 'search_edit') and self.search_edit:
                self.search_edit.setPlaceholderText(language_manager.tr("main_window.search_placeholder"))
            # 更新工具栏按钮文本（如果工具栏存在）
            if hasattr(self, '_update_toolbar_texts'):
                self._update_toolbar_texts()
            # 同步主界面语言下拉框选中项
            if hasattr(self, 'language_combo') and self.language_combo:
                current_language = language_manager.get_current_language()
                for i in range(self.language_combo.count()):
                    code = self.language_combo.itemData(i)
                    if code == current_language:
                        self.language_combo.setCurrentIndex(i)
                        break
            logger.info(f"主窗口界面文本已更新为: {language_manager.get_current_language()}")
        except Exception as e:
            logger.error(f"更新主窗口界面文本时发生错误: {e}")

    def _update_toolbar_texts(self):
        """更新工具栏按钮文本"""
        try:
            from PyQt5.QtWidgets import QToolButton
            for child in self.findChildren(QToolButton):
                action = child.defaultAction()
                if action:
                    if action == self.add_url_action:
                        child.setText(language_manager.tr("main_window.add_url"))
                    elif action == self.edit_url_action:
                        child.setText(language_manager.tr("main_window.edit_url"))
                    elif action == self.add_folder_action:
                        child.setText(language_manager.tr("main_window.add_folder"))
                    elif action == self.rename_action:
                        child.setText(language_manager.tr("main_window.edit_folder"))
                    elif action == self.cut_action:
                        child.setText(language_manager.tr("main_window.cut"))
                    elif action == self.copy_action:
                        child.setText(language_manager.tr("main_window.copy"))
                    elif action == self.paste_action:
                        child.setText(language_manager.tr("main_window.paste"))
                    elif action == self.delete_action:
                        child.setText(language_manager.tr("main_window.delete"))
                    elif action == self.undo_action:
                        child.setText(language_manager.tr("main_window.undo"))
                    elif action == self.import_action:
                        child.setText(language_manager.tr("main_window.import"))
                    elif action == self.export_action:
                        child.setText(language_manager.tr("main_window.export"))
                    elif action == self.refresh_icons_action:
                        child.setText(language_manager.tr("main_window.refresh"))
                    elif action == self.search_action:
                        child.setText(language_manager.tr("main_window.search"))
                    elif action == self.settings_action:
                        child.setText(language_manager.tr("main_window.settings"))
                    elif action == self.lock_action:
                        child.setText(language_manager.tr("main_window.lock"))
                    elif action == self.about_action:
                        child.setText(language_manager.tr("main_window.about"))
        except Exception as e:
            logger.error(f"更新工具栏文本时发生错误: {e}")
    
    def _show_blind_box_dialog(self):
        """显示网站盲盒对话框"""
        # 盲盒功能在锁定状态下仍可使用，因为它是只读操作
        
        # 创建并显示网站盲盒对话框
        dialog = WebsiteBlindBoxDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # 获取用户选择的网站数量
            count = dialog.get_website_count()
            
            # 使用盲盒管理器打开随机网站
            current_path = self.bookmark_grid.current_path if hasattr(self, 'bookmark_grid') else []
            opened_count, random_urls = self.blind_box_manager.open_random_urls(self, current_path, count)
            
            # 显示随机选择的网址图标
            self._display_random_url_icons(random_urls)
    
    def _update_blind_box_button_visibility(self):
        """更新网站盲盒按钮和标签的显示状态"""
        if hasattr(self, 'blind_box_button'):
            # 始终显示按钮和标签（修改为程序首次打开时即显示）
            self.blind_box_button.show()
            if hasattr(self, 'magic_box_label'):
                self.magic_box_label.show()
    
    def _display_random_url_icons(self, random_urls):
        """显示随机选择的网址图标
        
        Args:
            random_urls: 随机选择的URL列表，每个元素为 (url, name, path) 元组
        """
        # 清空之前的图标
        while self.random_urls_layout.count():
            item = self.random_urls_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 如果没有随机URL，则显示提示信息
        if not random_urls:
            label = QLabel("没有可用的网址")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 12px; color: #666; padding: 20px;")
            self.random_urls_layout.addWidget(label, 0, 0)
            return
        
        # 设置垂直布局间距
        self.random_urls_layout.setSpacing(10)
        
        logger.debug(f"显示随机URL图标数量: {len(random_urls)}")
        
        for index, (url, name, path) in enumerate(random_urls):
            if not url:
                continue
            
            # 创建图标按钮 - 调整为60x60
            icon_button = QPushButton()
            icon_button.setFixedSize(60, 60)
            
            # 设置图标大小
            icon_button.setIconSize(QtCore.QSize(50, 50))
            
            # 先设置加载中的占位符图标
            loading_icon = QIcon(resource_path("resources/icons/globe.png"))
            icon_button.setIcon(loading_icon)
            
            # 获取网址图标
            icon_path = self.app.favicon_service.get_favicon(url)
            if icon_path:
                try:
                    # 尝试加载图标
                    favicon_icon = QIcon(resource_path(icon_path))
                    # 检查图标是否有效
                    if not favicon_icon.isNull():
                        icon_button.setIcon(favicon_icon)
                    else:
                        # 图标无效，使用默认图标
                        icon_button.setIcon(QIcon(resource_path("resources/icons/globe.png")))
                except Exception as e:
                    # 图标加载失败，使用默认图标
                    logger.warning(f"图标加载失败: {icon_path}, 错误: {e}")
                    icon_button.setIcon(QIcon(resource_path("resources/icons/globe.png")))
            else:
                # 没有找到图标，使用默认图标
                icon_button.setIcon(QIcon(resource_path("resources/icons/globe.png")))
            
            # 设置按钮样式（适应60x60大小）
            icon_button.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    border: 1px solid #ddd;
                    border-radius: 30px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border: 2px solid #007bff;
                    border-radius: 32px;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                    border: 1px solid #adb5bd;
                }
            """)
            
            # 设置工具提示（鼠标悬停时显示名称和网址）
            tooltip_text = f"<b>{name}</b><br/><span style='color: #666;'>{url}</span>"
            if len(tooltip_text) > 100:
                tooltip_text = tooltip_text[:97] + "..."
            icon_button.setToolTip(tooltip_text)
            
            # 将URL信息保存到按钮的属性中
            icon_button.setProperty("url", url)
            icon_button.setProperty("name", name)
            
            # 添加左键点击事件
            icon_button.clicked.connect(self._create_url_opener(url))
            
            # 添加右键菜单
            icon_button.setContextMenuPolicy(Qt.CustomContextMenu)
            icon_button.customContextMenuRequested.connect(
                lambda pos, u=url, n=name, btn=icon_button: self._show_icon_context_menu(pos, u, n, btn)
            )
            
            # 直接添加到垂直布局
            self.random_urls_layout.addWidget(icon_button)
    
    def _create_url_opener(self, url):
        """创建URL打开器，避免lambda闭包问题
        
        Args:
            url: 要打开的URL
            
        Returns:
            callable: 用于连接到按钮点击事件的函数
        """
        def opener():
            self._open_url(url)
        return opener
    
    def _show_icon_context_menu(self, pos, url, name, button):
        """显示图标右键菜单
        
        Args:
            pos: 鼠标位置
            url: 网址URL
            name: 网址名称
            button: 触发菜单的按钮
        """
        menu = QMenu(self)
        
        # 在浏览器中打开
        open_action = QAction(QIcon(resource_path("resources/icons/open.png")), 
                             language_manager.tr("context_menu.open_in_browser", "在浏览器中打开"), self)
        open_action.triggered.connect(lambda: self._open_url(url))
        menu.addAction(open_action)
        
        # 在默认浏览器中打开
        open_default_action = QAction(QIcon(resource_path("resources/icons/globe.png")), 
                                     language_manager.tr("context_menu.open_in_default_browser", "在默认浏览器中打开"), self)
        open_default_action.triggered.connect(lambda: self._open_url_in_default_browser(url))
        menu.addAction(open_default_action)
        
        # 添加分隔符
        menu.addSeparator()
        
        # 定位到网址标签
        locate_action = QAction(QIcon(resource_path("resources/icons/search.png")), 
                               "定位到网址标签", self)
        locate_action.triggered.connect(lambda: self._locate_url_in_grid(url, name))
        menu.addAction(locate_action)
        
        # 显示菜单（确保位置跟随图标）
        global_pos = button.mapToGlobal(pos)
        menu.exec_(global_pos)
    
    def _open_url(self, url):
        """打开URL
        
        Args:
            url: 要打开的URL
        """
        try:
            import webbrowser
            import time
            
            # 打开URL
            webbrowser.open(url)
            logger.info(f"打开URL: {url}")
            
            # 添加到历史记录
            self._add_url_to_history(url)
            
            # 添加短暂延迟，避免浏览器进程冲突
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"打开URL失败: {url}, 错误: {e}")
            # 显示错误消息
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.showMessage(f"打开URL失败: {e}", 3000)
    
    def _add_url_to_history(self, url):
        """添加URL到历史记录
        
        Args:
            url: 要添加的URL
        """
        try:
            # 查找当前选中的URL项目信息
            current_path = self.folder_tree.get_current_path()
            url_name = "未知网站"
            
            # 尝试从当前显示的书签中找到对应的URL信息
            if hasattr(self, 'bookmark_grid') and self.bookmark_grid:
                for item in self.bookmark_grid.get_all_items():
                    if item.get('type') == 'url' and item.get('url') == url:
                        url_name = item.get('name', '未知网站')
                        break
            
            # 构造历史记录项
            history_urls = [(url, url_name, current_path if current_path else [])]
            
            # 添加到历史记录
            if hasattr(self, 'blind_box_manager') and self.blind_box_manager:
                self.blind_box_manager._add_to_history(history_urls)
                logger.info(f"已添加到历史记录: {url_name} ({url})")
        except Exception as e:
            logger.error(f"添加历史记录失败: {e}")
    
    def _open_url_in_default_browser(self, url):
        """在默认浏览器中打开URL
        
        Args:
            url: 要打开的URL
        """
        try:
            import webbrowser
            import time
            
            # 使用默认浏览器打开URL
            webbrowser.get().open(url)
            logger.info(f"在默认浏览器中打开URL: {url}")
            
            # 添加到历史记录
            self._add_url_to_history(url)
            
            # 添加短暂延迟，避免浏览器进程冲突
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"在默认浏览器中打开URL失败: {url}, 错误: {e}")
            # 显示错误消息
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.showMessage(f"在默认浏览器中打开URL失败: {e}", 3000)
    
    def _locate_url_in_grid(self, url, name):
        """定位到主界面对应网址卡片并高亮显示
        
        Args:
            url: 要定位的网址URL
            name: 网址名称
        """
        try:
            # 在数据中查找匹配的URL项目
            found_item = None
            found_path = None
            
            def search_in_data(data, current_path=[]):
                nonlocal found_item, found_path
                if found_item:  # 已找到，停止搜索
                    return
                
                # 处理字典结构的数据
                if isinstance(data, dict):
                    for key, item in data.items():
                        if isinstance(item, dict):
                            if item.get('type') == 'url' and item.get('url') == url:
                                found_item = item
                                found_path = current_path.copy()
                                return
                            elif item.get('type') == 'folder' and 'children' in item:
                                new_path = current_path + [key]
                                search_in_data(item['children'], new_path)
                # 处理列表结构的数据（兼容性）
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            if item.get('type') == 'url' and item.get('url') == url:
                                found_item = item
                                found_path = current_path.copy()
                                return
                            elif item.get('type') == 'folder' and 'children' in item:
                                new_path = current_path + [item.get('name', '')]
                                search_in_data(item['children'], new_path)
            
            # 从数据管理器中搜索
            if hasattr(self.app, 'data_manager') and self.app.data_manager:
                data = self.app.data_manager.data
                search_in_data(data)
            
            if not found_item or found_path is None:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "定位失败", f"未找到网址 '{name}' 在数据中的位置")
                return
            
            # 切换目录树和卡片区
            if hasattr(self, 'folder_tree') and hasattr(self, 'bookmark_grid'):
                self.folder_tree.select_path(found_path)
                self.bookmark_grid.set_current_path(found_path)
                
                # 高亮并选中卡片
                self.bookmark_grid.highlight_item(found_item.get('name', name))
                self.bookmark_grid.selected_items = [(found_item.get('name', name), 'url')]
                self.bookmark_grid.refresh()
                
                # 滚动到目标卡片
                for w, n, t in getattr(self.bookmark_grid, '_item_widgets', []):
                    if n == found_item.get('name', name):
                        w.set_selected(True)
                        if hasattr(self.bookmark_grid, 'ensureWidgetVisible'):
                            self.bookmark_grid.ensureWidgetVisible(w)
                        else:
                            # 尝试用scrollArea滚动
                            try:
                                grid = self.bookmark_grid
                                area = grid.viewport().parent()
                                rect = w.geometry()
                                area.ensureVisible(rect.x(), rect.y(), rect.width(), rect.height())
                            except Exception:
                                pass
                        break
                
                # 使主界面获得焦点
                self.activateWindow()
                self.raise_()
                
                # 提示成功
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "定位成功", f"已定位到：{found_item.get('name', name)}")
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "定位失败", "无法访问主界面组件，定位失败")
                
        except Exception as e:
            logger.error(f"定位网址失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "定位失败", f"定位过程中发生错误: {str(e)}")
    
    def _create_history_button(self, layout):
        """创建历史记录按钮
        
        Args:
            layout: 要添加按钮的布局
        """
        # 创建水平布局容器，用于按钮居中
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 5, 10, 5)
        
        # 创建历史记录按钮
        history_button = QPushButton()
        history_button.setFixedSize(150, 60)  # 设置按钮大小：宽度150，高度60
        history_button.setToolTip("历史记录")
        
        # 设置按钮背景图片样式
        try:
            history_icon_path = resource_path("resources/bgimages/history.jpg")
            # 转换路径分隔符为正斜杠，避免CSS路径问题
            history_icon_path_css = history_icon_path.replace("\\", "/")
            
            if os.path.exists(history_icon_path):
                # 使用背景图片而不是图标，让图片平铺整个按钮
                history_button.setStyleSheet(f"""
                    QPushButton {{
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        background-image: url({history_icon_path_css});
                        background-repeat: no-repeat;
                        background-position: center;
                        background-size: cover;
                        margin: 0px;
                    }}
                    QPushButton:hover {{
                        border-color: #999;
                        opacity: 0.8;
                    }}
                    QPushButton:pressed {{
                        border-color: #666;
                        opacity: 0.6;
                    }}
                """)
            else:
                history_button.setText("历史")
                history_button.setStyleSheet("""
                    QPushButton {
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        background-color: #f0f0f0;
                        margin: 0px;
                        font-size: 12pt;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                        border-color: #999;
                    }
                    QPushButton:pressed {
                        background-color: #d0d0d0;
                    }
                """)
                logger.warning(f"历史记录图标文件不存在: {history_icon_path}")
        except Exception as e:
            history_button.setText("历史")
            history_button.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                    margin: 0px;
                    font-size: 12pt;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border-color: #999;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            logger.error(f"设置历史记录按钮图标失败: {e}")
        
        # 连接点击事件
        history_button.clicked.connect(self._show_history_dialog)
        
        # 将按钮添加到水平布局中，实现居中
        button_layout.addStretch()  # 左侧弹性空间
        button_layout.addWidget(history_button)
        button_layout.addStretch()  # 右侧弹性空间
        
        # 将容器添加到主布局
        layout.addWidget(button_container)
    
    def _show_history_dialog(self):
        """显示历史记录对话框"""
        try:
            # 获取历史记录
            history_data = self.blind_box_manager.get_history()
            
            # 创建并显示历史记录对话框
            dialog = HistoryDialog(self, history_data, self.app.data_manager, self.blind_box_manager)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"显示历史记录对话框失败: {e}")
            QMessageBox.warning(
                self,
                "错误",
                f"显示历史记录失败: {e}"
            )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.closing.emit()
        event.accept()