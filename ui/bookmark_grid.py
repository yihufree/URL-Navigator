#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import functools

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLabel, QMenu, QAction, QMessageBox,
    QScrollArea, QSizePolicy, QSpacerItem, QApplication,
    QTreeWidget, QTreeWidgetItem, QDialog
)

from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint, QByteArray, QTimer, QRect
from PyQt5.QtGui import QIcon, QDrag, QPixmap, QPainter, QColor, QCursor, QPen, QMouseEvent, QImage
from PyQt5 import QtCore, QtGui

from ui.dialogs import EditUrlDialog, EditFolderDialog
from ui.icons import icon_provider
from utils.url_utils import validate_url
from utils.language_manager import language_manager

# 设置日志级别为DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BookmarkGridWidget(QScrollArea):
    """书签网格视图"""
    
    # 定义信号
    navigate_to = pyqtSignal(list)
    selection_changed = pyqtSignal()  # 新增：选中项变化信号
    
    def __init__(self, data_manager, favicon_service):
        super().__init__()
        self.data_manager = data_manager
        self.favicon_service = favicon_service
        self.current_path = []
        self.highlighted_item = None
        self.clipboard_data = None  # 用于保存复制的项目数据
        self.cut_data = None  # 新增：用于保存剪切的项目数据
        self.item_width = 360  # 卡片宽度，需与BookmarkItemWidget一致
        self.item_spacing = 30  # 卡片间距
        self.last_width = 0  # 保存上次width用于检测变化
        self.selected_items = []  # [(name, type)] 当前多选的卡片
        self.last_selected_index = None  # Shift区间多选辅助
        self.drag_selecting = False
        self.drag_start_pos = None
        self.drag_current_pos = None
        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)
        self._drag_start_pos = None  # 新增：用于网格层拖拽
        self.sort_mode = 'name'  # 默认按名字排序
        self.is_locked = False  # 新增：锁定状态标志
        
        # 添加背景图片
        self.bg_image = None
        self.bg_hidden = False  # 背景图片隐藏状态标志
        self.bg_label = None  # 背景图片标签引用
        self.load_background_image()
        
        self.init_ui()
        
        # 连接数据变化信号
        self.data_manager.data_changed.connect(self.refresh)
        
        # 连接窗口大小改变信号
        self.content_widget = None  # 初始化为None，在init_ui中创建
    
    def load_background_image(self):
        """加载背景图片"""
        # 尝试加载PNG和JPG图片
        png_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             'resources', 'bgimages', 'netbg.png')
        jpg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             'resources', 'bgimages', 'netbg.jpg')
        
        if os.path.exists(png_path):
            self.bg_image = QPixmap(png_path)
            logger.debug(f"加载背景图片PNG: {png_path}")
        elif os.path.exists(jpg_path):
            self.bg_image = QPixmap(jpg_path)
            logger.debug(f"加载背景图片JPG: {jpg_path}")
        else:
            logger.warning(f"背景图片不存在: {png_path} 或 {jpg_path}")
    
    def init_ui(self):
        """初始化UI"""
        # 设置滚动区域属性
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用横向滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建内容窗口 - 确保它能够跟随父容器调整大小
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setWidget(self.content_widget)
        
        # 创建主布局 - 确保边距合理
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        
        # 创建面包屑导航
        self.breadcrumb_layout = QHBoxLayout()
        self.main_layout.addLayout(self.breadcrumb_layout)
        
        # 创建网格布局 - 确保它能够跟随容器调整大小
        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(self.item_spacing)
        self.grid_layout.setVerticalSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # 左对齐顶部对齐
        self.main_layout.addLayout(self.grid_layout)
        
        # 添加弹性空间
        self.main_layout.addStretch(1)
        
        # 设置拖放
        self.setAcceptDrops(True)
        
        # 保存初始宽度
        self.last_width = self.viewport().width()
        logger.debug(f"初始视口宽度: {self.last_width}")
        
        # 刷新显示
        self.refresh()
    
    def resizeEvent(self, event):
        """窗口大小变化时触发刷新"""
        super().resizeEvent(event)
        
        # 获取当前宽度
        current_width = self.viewport().width()
        width_change = abs(current_width - self.last_width)
        
        # 检查宽度是否发生足够变化（超过20像素就触发）
        if width_change > 20:
            logger.debug(f"窗口宽度变化: {self.last_width} -> {current_width}, 变化了{width_change}像素, 触发刷新")
            self.last_width = current_width
            # 强制重新计算布局
            QtCore.QTimer.singleShot(50, self.refresh)
        
        # 如果是根目录且有背景图，更新背景图的大小
        if not self.current_path and self.bg_image:
            # 找到背景图标签并更新大小
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if isinstance(widget, QLabel) and not widget.text():
                    widget.setPixmap(self.bg_image.scaled(
                        self.viewport().width(), 
                        self.viewport().height(),
                        Qt.IgnoreAspectRatio, 
                        Qt.SmoothTransformation
                    ))
                    break
            
    def _calculate_max_columns(self):
        """根据窗口宽度计算每行最大卡片数"""
        if not self.viewport():
            return 4  # 默认值
            
        # 获取可用宽度 - 直接使用视口宽度
        viewport_width = self.viewport().width()
        
        # 为边距预留空间
        margin = 20  # 减去边距
        available_width = max(200, viewport_width - margin)
        
        logger.debug(f"计算最大列数: 视口宽度={viewport_width}, 可用宽度={available_width}")
        
        # 计算每行可以放置的卡片数量
        # 总宽度 = 卡片宽度 + 水平间距
        total_item_width = self.item_width + self.item_spacing
        
        # 向下取整计算最大列数
        max_cols = max(1, int(available_width / total_item_width))
        
        logger.debug(f"每个项目宽度: {total_item_width}, 计算出的最大列数: {max_cols}")
        
        # 保证最小显示1个卡片，最大显示不超过20个
        result = max(1, min(20, max_cols))
        logger.debug(f"最终列数: {result}")
        
        return result
    
    def set_current_path(self, path):
        """设置当前路径"""
        self.current_path = path
        self.highlighted_item = None
        self.refresh()
        # 状态栏刷新
        main_win = self.parent()
        while main_win and not hasattr(main_win, 'update_status_bar'):
            main_win = main_win.parent()
        if main_win and hasattr(main_win, 'update_status_bar'):
            main_win.update_status_bar()
    
    def highlight_item(self, name):
        """高亮显示项目"""
        self.highlighted_item = name
        self.refresh()
    
    def set_sort_mode(self, mode):
        """设置排序方式并刷新"""
        self.sort_mode = mode
        self.refresh()
    
    def refresh(self):
        """刷新显示"""
        # 清除网格布局中的所有项目
        self._clear_layout(self.grid_layout)
        
        # 清除面包屑导航
        self._clear_layout(self.breadcrumb_layout)
        
        # 更新面包屑导航
        self._update_breadcrumb()
        
        # 获取当前路径的项目
        current_items = self.data_manager.get_item_at_path(self.current_path)
        
        if current_items is None:
            # 路径无效，显示错误信息
            label = QLabel("无效的路径")
            label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(label, 0, 0)
            return
        
        # 检查是否在根目录，如果是则显示背景图片
        if not self.current_path:
            # 在根目录，显示背景图片（如果未被隐藏）
            if self.bg_image and not self.bg_hidden:
                # 创建可点击的背景图片标签
                self.bg_label = ClickableLabel()
                self.bg_label.setPixmap(self.bg_image.scaled(
                    self.viewport().width(), 
                    self.viewport().height(),
                    Qt.IgnoreAspectRatio, 
                    Qt.SmoothTransformation
                ))
                self.bg_label.setAlignment(Qt.AlignCenter)
                self.bg_label.setStyleSheet("QLabel { background: transparent; }")
                
                # 连接点击事件
                self.bg_label.clicked.connect(self._hide_background)
                
                # 将背景图片添加到网格中
                self.grid_layout.addWidget(self.bg_label, 0, 0, 1, self._calculate_max_columns())
                
                # 设置背景图片在最上层显示
                self.bg_label.raise_()
                return
        
        # 动态计算最大列数
        max_cols = self._calculate_max_columns()
        logger.debug(f"刷新视图 - 使用列数: {max_cols}")
        
        # 重置所有列的拉伸因子
        for c in range(max_cols + 1):
            self.grid_layout.setColumnStretch(c, 0)
        
        # 添加项目到网格
        self._item_widgets = []  # 记录所有item widget及其(name, type)
        row, col = 0, 0
        folders = [(name, item) for name, item in current_items.items() if item["type"] == "folder"]
        if self.sort_mode == 'name':
            folders.sort(key=lambda x: x[0].lower())
        elif self.sort_mode == 'time':
            folders.sort(key=lambda x: x[1].get('created_at', 0))
        for name, item in folders:
            w = self._add_item_to_grid(name, item, row, col, max_cols)
            self._item_widgets.append((w, name, item["type"]))
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        urls = [(name, item) for name, item in current_items.items() if item["type"] == "url"]
        if self.sort_mode == 'name':
            urls.sort(key=lambda x: x[0].lower())
        elif self.sort_mode == 'time':
            urls.sort(key=lambda x: x[1].get('created_at', 0))
        for name, item in urls:
            w = self._add_item_to_grid(name, item, row, col, max_cols)
            self._item_widgets.append((w, name, item["type"]))
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        self._add_new_item_button(row, col, max_cols)
        self.grid_layout.setColumnStretch(max_cols, 1)
        # 刷新高亮多选
        for w, name, typ in self._item_widgets:
            # 先处理高亮显示
            if self.highlighted_item and name == self.highlighted_item:
                # 设置高亮样式（比选中状态更明显）
                w.setStyleSheet("background-color: #ffeb3b; border: 3px solid #ff9800; border-radius: 5px;")
                # 同时设置为选中状态
                if (name, typ) not in self.selected_items:
                    self.selected_items.append((name, typ))
                # 设置选中状态但不覆盖高亮样式
                w.selected = True
            else:
                # 处理普通选中状态
                if (name, typ) in self.selected_items:
                    w.set_selected(True)
                else:
                    w.set_selected(False)
        # 状态栏刷新
        main_win = self.parent()
        while main_win and not hasattr(main_win, 'update_status_bar'):
            main_win = main_win.parent()
        if main_win and hasattr(main_win, 'update_status_bar'):
            main_win.update_status_bar()
    
    def _update_breadcrumb(self):
        """更新面包屑导航"""
        # 清空外部bar
        bar = getattr(self, 'external_breadcrumb_bar', None)
        if bar is not None:
            while bar.count():
                item = bar.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
        else:
            return
        # 添加根目录按钮
        root_btn = QPushButton("根目录")
        root_btn.setFlat(True)
        root_btn.clicked.connect(lambda: (self.show_background(), self.navigate_to.emit([])))
        bar.addWidget(root_btn)
        # 添加路径分隔符和路径段按钮
        for i, segment in enumerate(self.current_path):
            separator = QLabel(" > ")
            bar.addWidget(separator)
            path_btn = QPushButton(segment)
            path_btn.setFlat(True)
            path_segment = self.current_path[:i+1]
            path_btn.clicked.connect(functools.partial(self.navigate_to.emit, path_segment))
            bar.addWidget(path_btn)
        bar.addStretch(1)
    
    def _add_item_to_grid(self, name, item, row, col, max_cols):
        """添加项目到网格"""
        item_widget = BookmarkItemWidget(name, item, self.current_path, self.favicon_service)
        item_widget.setMinimumWidth(360)
        item_widget.setMaximumWidth(480)
        item_widget.navigate_to.connect(self.navigate_to)
        item_widget.edit_item.connect(self._edit_item)
        item_widget.delete_item.connect(self._delete_item)
        item_widget.clicked.connect(self._on_item_clicked)
        self.grid_layout.addWidget(item_widget, row, col)
        return item_widget

    def _on_item_clicked(self, name, typ, event, widget):
        # 支持Ctrl/Shift多选
        idx = None
        for i, (w, n, t) in enumerate(self._item_widgets):
            if n == name and t == typ:
                idx = i
                break
        if idx is None:
            return
        if event.modifiers() & Qt.ControlModifier:
            # Ctrl多选
            if (name, typ) in self.selected_items:
                self.selected_items.remove((name, typ))
            else:
                self.selected_items.append((name, typ))
            self.last_selected_index = idx
        elif event.modifiers() & Qt.ShiftModifier and self.last_selected_index is not None:
            # Shift区间多选
            start = min(self.last_selected_index, idx)
            end = max(self.last_selected_index, idx)
            self.selected_items = list({(n, t) for _, n, t in self._item_widgets[start:end+1]})
        else:
            # 单选
            self.selected_items = [(name, typ)]
            self.last_selected_index = idx
        self.selection_changed.emit()  # 新增：每次选中项变化时发射信号
        self.refresh()

    def _add_new_item_button(self, row, col, max_cols):
        """添加"添加新项目"按钮"""
        # 添加新项目按钮
        if col >= max_cols:
            col = 0
            row += 1
        
        # 创建添加按钮
        add_button = QPushButton("+ 添加")
        add_button.setMinimumSize(100, 100)
        add_button.clicked.connect(self._show_add_menu)
        
        # 添加到网格，如果处于锁定状态则禁用按钮
        self.grid_layout.addWidget(add_button, row, col)
        add_button.setEnabled(not self.is_locked)
    

    
    def _show_add_menu(self):
        """显示添加菜单"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "锁定状态", "目前处于编辑锁定状态，如需使用相关功能，请点击锁定按钮进行解锁。")
            return
            
        menu = QMenu(self)
        
        add_url_action = QAction(icon_provider.get_icon("globe"), "添加网址", self)
        add_url_action.triggered.connect(self._add_url)
        menu.addAction(add_url_action)
        
        add_folder_action = QAction(icon_provider.get_icon("folder"), "添加文件夹", self)
        add_folder_action.triggered.connect(self._add_folder)
        menu.addAction(add_folder_action)
        
        menu.exec_(QCursor.pos())
    
    def _add_url(self):
        """添加URL"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "锁定状态", "目前处于编辑锁定状态，如需使用相关功能，请点击锁定按钮进行解锁。")
            return
            
        from ui.dialogs import AddUrlDialog
        dialog = AddUrlDialog(self.favicon_service, self.current_path, self)
        
        if dialog.exec_():
            url_data = dialog.get_data()
            
            # 添加URL
            success = self.data_manager.add_url(
                self.current_path,
                url_data["name"],
                url_data["url"],
                url_data["icon"]
            )
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加网址，可能是名称已存在")
    
    def _add_folder(self):
        """添加文件夹"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "锁定状态", "目前处于编辑锁定状态，如需使用相关功能，请点击锁定按钮进行解锁。")
            return
            
        from ui.dialogs import AddFolderDialog
        dialog = AddFolderDialog(self.current_path, self)
        
        if dialog.exec_():
            folder_name = dialog.get_folder_name()
            
            # 添加文件夹
            success = self.data_manager.add_folder(self.current_path, folder_name)
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加文件夹，可能是名称已存在")
    
    def _edit_item(self, path, name, item):
        """编辑项目"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "锁定状态", "目前处于编辑锁定状态，如需使用相关功能，请点击锁定按钮进行解锁。")
            return
            
        if item["type"] == "url":
            dialog = EditUrlDialog(self.favicon_service, path, name, item, self)
            
            if dialog.exec_():
                url_data = dialog.get_data()
                
                # 更新URL
                success = self.data_manager.update_item(
                    path,
                    name,
                    url_data["name"],
                    {
                        "url": url_data["url"],
                        "icon": url_data["icon"]
                    }
                )
                
                if success:
                    self.data_manager.save()
                else:
                    QMessageBox.warning(self, "编辑失败", "无法更新网址，可能是名称已存在")
        else:  # folder
            dialog = EditFolderDialog(path, name, self)
            
            if dialog.exec_():
                new_name = dialog.get_folder_name()
                
                # 更新文件夹
                success = self.data_manager.update_item(
                    path,
                    name,
                    new_name,
                    {}
                )
                
                if success:
                    self.data_manager.save()
                else:
                    QMessageBox.warning(self, "编辑失败", "无法更新文件夹，可能是名称已存在")
    
    def _delete_item(self, path, name):
        """删除项目"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            parent = self.parent()
            while parent and not hasattr(parent, '_show_locked_message'):
                parent = parent.parent()
            if parent and hasattr(parent, '_show_locked_message'):
                parent._show_locked_message()
            return
        
        # 获取当前路径下的项目
        current_items = self.data_manager.get_item_at_path(path)
        if not current_items or name not in current_items:
            QMessageBox.warning(self, "删除失败", "项目不存在")
            return
            
        item = current_items[name]
        item_type = item["type"]
        
        # 创建确认消息
        if item_type == "url":
            confirm_msg = f'您确定要删除网址"{name}"吗？'
        else:
            confirm_msg = f'您确定要删除文件夹"{name}"吗？这将删除其中的所有内容。'
            
        reply = QMessageBox.question(
            self,
            "删除确认",
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 保存快照（通过主窗口）
                parent = self.parent()
                while parent and not hasattr(parent, '_save_undo_snapshot'):
                    parent = parent.parent()
                if parent and hasattr(parent, '_save_undo_snapshot'):
                    parent._save_undo_snapshot()
                
                success = self.data_manager.delete_item(path, name)
                
                if success:
                    self.data_manager.save()
                    
                    # 显示成功消息
                    if item_type == "url":
                        success_msg = f'已成功删除网址"{name}"'
                    else:
                        success_msg = f'已成功删除文件夹"{name}"及其内容'
                        
                    # 尝试获取主窗口的状态栏
                    parent = self.parent()
                    while parent and not hasattr(parent, 'status_bar'):
                        parent = parent.parent()
                    if parent and hasattr(parent, 'status_bar'):
                        parent.status_bar.showMessage(success_msg, 3000)
                    else:
                        # 如果没有找到状态栏，则使用弹窗提示
                        QMessageBox.information(self, "删除成功", success_msg)
                else:
                    QMessageBox.warning(self, "删除失败", "无法删除项目")
            except Exception as e:
                logger.error(f"删除项目出错: {e}")
                QMessageBox.warning(self, "删除失败", f"删除过程中出错: {str(e)}")
    
    def _clear_layout(self, layout):
        """清除布局中的所有项目"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())
    
    def _show_grid_context_menu(self, pos):
        menu = QMenu(self)
        
        # 如果处于锁定状态，只显示有限的菜单项
        if not self.is_locked:
            add_url_action = QAction(icon_provider.get_icon("globe"), "添加网址", self)
            add_url_action.triggered.connect(self._add_url)
            menu.addAction(add_url_action)
            
            add_folder_action = QAction(icon_provider.get_icon("folder"), "添加文件夹", self)
            add_folder_action.triggered.connect(self._add_folder)
            menu.addAction(add_folder_action)
            
            # 如果剪贴板有数据，添加粘贴选项
            if (self.clipboard_data and self._can_paste_to_current()) or self.cut_data:
                menu.addSeparator()
                paste_action = QAction(icon_provider.get_icon("paste"), "粘贴", self)
                paste_action.triggered.connect(self._paste_item)
                menu.addAction(paste_action)
            
            # 多选时批量操作
            if len(self.selected_items) > 1:
                menu.addSeparator()
                batch_delete = QAction(icon_provider.get_icon("delete"), "批量删除", self)
                batch_delete.triggered.connect(self._batch_delete)
                menu.addAction(batch_delete)
                
                batch_copy = QAction(icon_provider.get_icon("copy"), "批量复制", self)
                batch_copy.triggered.connect(self._batch_copy)
                menu.addAction(batch_copy)
                
                batch_cut = QAction(QIcon(os.path.join(os.path.dirname(__file__), "../resources/icons/cut.ico")), "批量剪切", self)
                batch_cut.triggered.connect(self._cut_selected)
                menu.addAction(batch_cut)
        
        # 如果没有添加任何菜单项，则不显示菜单
        if not menu.actions():
            return
            
        menu.exec_(self.mapToGlobal(pos))

    def _can_paste_to_current(self):
        # 只允许粘贴到文件夹（当前目录）
        if not self.clipboard_data:
            return False
        if self.clipboard_data.get("type") == "batch_urls":
            return True
        if self.clipboard_data.get("type") == "url":
            return True
        if self.clipboard_data.get("type") == "folder":
            return True
        return False

    def _cut_selected(self):
        """剪切所选项目"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            parent = self.parent()
            while parent and not hasattr(parent, '_show_locked_message'):
                parent = parent.parent()
            if parent and hasattr(parent, '_show_locked_message'):
                parent._show_locked_message()
            return
            
        if not self.selected_items:
            QMessageBox.information(self, "剪切", "请选择要剪切的项目")
            return
        
        # 统计选中的项目类型数量
        url_count = sum(1 for _, typ in self.selected_items if typ == "url")
        folder_count = sum(1 for _, typ in self.selected_items if typ == "folder")
        
        # 创建确认消息
        if len(self.selected_items) == 1:
            name, typ = self.selected_items[0]
            if typ == "url":
                confirm_msg = f'您确定要剪切"{name}"网址吗？'
            else:
                confirm_msg = f'您确定要剪切"{name}"文件夹吗？'
        else:
            parts = []
            if url_count > 0:
                parts.append(f"{url_count}个网址")
            if folder_count > 0:
                parts.append(f"{folder_count}个文件夹")
            confirm_msg = f"您确定要剪切{' 和 '.join(parts)}吗？"
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, 
            "剪切确认", 
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # 保存剪切数据
            self.cut_data = {
                "items": [],
                "path": self.current_path,
            }
            
            # 收集所有选中项
            for name, item_type in self.selected_items:
                # 获取当前路径下的项目
                current_items = self.data_manager.get_item_at_path(self.current_path)
                if not current_items or name not in current_items:
                    continue
                    
                item = current_items[name]
                self.cut_data["items"].append({
                    "name": name,
                    "type": item_type,
                    "data": item
                })
            
            # 清空剪贴板数据，避免混淆
            self.clipboard_data = None
            
            # 显示提示
            if self.cut_data["items"]:
                msg = f"已剪切 {len(self.cut_data['items'])} 个项目，可以粘贴到所需位置"
                # 尝试获取主窗口的状态栏
                parent = self.parent()
                while parent and not hasattr(parent, 'status_bar'):
                    parent = parent.parent()
                if parent and hasattr(parent, 'status_bar'):
                    parent.status_bar.showMessage(msg, 3000)
                else:
                    # 如果没有找到状态栏，则使用弹窗提示
                    QMessageBox.information(self, "剪切成功", msg)
                    
                # 更新主窗口的按钮状态（特别是粘贴按钮）
                main_window = parent
                while main_window and not hasattr(main_window, '_update_actions_state'):
                    main_window = main_window.parent()
                if main_window and hasattr(main_window, '_update_actions_state'):
                    main_window._update_actions_state()
                    
                # 突出显示已剪切的项目
                self.refresh()
            else:
                QMessageBox.warning(self, "剪切失败", "没有选中有效项目")
        except Exception as e:
            logger.error(f"剪切出错: {e}")
            QMessageBox.warning(self, "剪切失败", f"剪切过程中出错: {str(e)}")
        finally:
            # 无论成功还是失败，都尝试更新按钮状态
            try:
                parent = self.parent()
                while parent and not hasattr(parent, '_update_actions_state'):
                    parent = parent.parent()
                if parent and hasattr(parent, '_update_actions_state'):
                    parent._update_actions_state()
            except Exception as update_error:
                logger.error(f"更新按钮状态失败: {update_error}")

    def _batch_copy(self):
        """批量复制所选项目"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            parent = self.parent()
            while parent and not hasattr(parent, '_show_locked_message'):
                parent = parent.parent()
            if parent and hasattr(parent, '_show_locked_message'):
                parent._show_locked_message()
            return
            
        if not self.selected_items:
            QMessageBox.information(self, "复制", "请选择要复制的项目")
            return
        
        # 统计选中的项目类型数量
        url_count = sum(1 for _, typ in self.selected_items if typ == "url")
        folder_count = sum(1 for _, typ in self.selected_items if typ == "folder")
        
        # 创建确认消息
        if len(self.selected_items) == 1:
            name, typ = self.selected_items[0]
            if typ == "url":
                confirm_msg = f'您确定要复制"{name}"网址吗？'
            else:
                confirm_msg = f'您确定要复制"{name}"文件夹吗？'
        else:
            parts = []
            if url_count > 0:
                parts.append(f"{url_count}个网址")
            if folder_count > 0:
                parts.append(f"{folder_count}个文件夹")
            confirm_msg = f"您确定要复制{' 和 '.join(parts)}吗？"
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, 
            "复制确认", 
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return

        try:
            # 复制
            self.clipboard_data = {
                "items": [],
                "path": self.current_path,
            }
            
            # 收集所有选中项
            for name, item_type in self.selected_items:
                # 获取当前路径下的项目
                current_items = self.data_manager.get_item_at_path(self.current_path)
                if not current_items or name not in current_items:
                    continue
                    
                item = current_items[name]
                self.clipboard_data["items"].append({
                    "name": name,
                    "type": item_type,
                    "data": item
                })
            
            # 清空剪切数据，避免覆盖剪切操作
            self.cut_data = None
            
            # 显示提示
            if self.clipboard_data["items"]:
                msg = f"已复制 {len(self.clipboard_data['items'])} 个项目到剪贴板"
                # 尝试获取主窗口的状态栏
                parent = self.parent()
                while parent and not hasattr(parent, 'status_bar'):
                    parent = parent.parent()
                if parent and hasattr(parent, 'status_bar'):
                    parent.status_bar.showMessage(msg, 3000)
                else:
                    # 如果没有找到状态栏，则使用弹窗提示
                    QMessageBox.information(self, "复制成功", msg)
                
                # 更新主窗口的按钮状态（特别是粘贴按钮）
                main_window = parent
                while main_window and not hasattr(main_window, '_update_actions_state'):
                    main_window = main_window.parent()
                if main_window and hasattr(main_window, '_update_actions_state'):
                    main_window._update_actions_state()
            else:
                QMessageBox.warning(self, "复制失败", "没有选中有效项目")
        except Exception as e:
            logger.error(f"批量复制出错: {e}")
            QMessageBox.warning(self, "复制失败", f"批量复制过程中出错: {str(e)}")
        finally:
            # 无论成功还是失败，都尝试更新按钮状态
            try:
                parent = self.parent()
                while parent and not hasattr(parent, '_update_actions_state'):
                    parent = parent.parent()
                if parent and hasattr(parent, '_update_actions_state'):
                    parent._update_actions_state()
            except Exception as update_error:
                logger.error(f"更新按钮状态失败: {update_error}")
    
    def _paste_item(self):
        """粘贴项目到当前路径"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            parent = self.parent()
            while parent and not hasattr(parent, '_show_locked_message'):
                parent = parent.parent()
            if parent and hasattr(parent, '_show_locked_message'):
                parent._show_locked_message()
            return
            
        try:
            current_items = self.data_manager.get_item_at_path(self.current_path)
            
            if not current_items:
                QMessageBox.warning(self, "粘贴失败", "当前路径无效")
                return
            
            # 优先处理剪切操作
            if self.cut_data:
                paste_data = self.cut_data
                is_cut = True
                item_count = len(paste_data["items"])
            elif self.clipboard_data:
                paste_data = self.clipboard_data
                is_cut = False
                item_count = len(paste_data["items"])
            else:
                QMessageBox.information(self, "粘贴", "剪贴板为空")
                return
            
            # 获取当前路径显示名称
            current_path_display = ""
            if self.current_path:
                current_path_display = "/" + "/".join(self.current_path)
            else:
                current_path_display = "根目录"
                
            # 创建确认消息
            # 统计选中的项目类型数量
            url_count = sum(1 for item in paste_data["items"] if item["type"] == "url")
            folder_count = sum(1 for item in paste_data["items"] if item["type"] == "folder")
            
            # 构建消息
            operation_type = "剪切" if is_cut else "复制"
            if item_count == 1:
                single_item = paste_data["items"][0]
                name = single_item["name"]
                if single_item["type"] == "url":
                    confirm_msg = f'您确定要将{operation_type}的网址"{name}"粘贴到{current_path_display}吗？'
                else:
                    confirm_msg = f'您确定要将{operation_type}的文件夹"{name}"粘贴到{current_path_display}吗？'
            else:
                parts = []
                if url_count > 0:
                    parts.append(f"{url_count}个网址")
                if folder_count > 0:
                    parts.append(f"{folder_count}个文件夹")
                confirm_msg = f"您确定要将{operation_type}的{' 和 '.join(parts)}粘贴到{current_path_display}吗？"
            
            # 显示确认对话框
            reply = QMessageBox.question(
                self, 
                "粘贴确认", 
                confirm_msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # 保存快照（通过主窗口）
            parent = self.parent()
            while parent and not hasattr(parent, '_save_undo_snapshot'):
                parent = parent.parent()
            if parent and hasattr(parent, '_save_undo_snapshot'):
                parent._save_undo_snapshot()
            
            # 执行粘贴
            success_count = 0
            for item_data in paste_data["items"]:
                name = item_data["name"]
                base_name = name
                
                # 检查目标位置是否已存在同名项目，如果存在则添加序号
                counter = 1
                while name in current_items:
                    name = f"{base_name} ({counter})"
                    counter += 1
                
                # 复制项目数据
                item = item_data["data"].copy()
                
                # 添加项目
                current_items[name] = item
                success_count += 1
            
            # 如果是剪切操作，则从源位置删除
            if is_cut and success_count > 0:
                # 获取源路径
                source_path = paste_data["path"]
                source_items = self.data_manager.get_item_at_path(source_path)
                
                if source_items:
                    # 删除源项目
                    for item_data in paste_data["items"]:
                        name = item_data["name"]
                        if name in source_items:
                            del source_items[name]
                
                # 清空剪切数据
                self.cut_data = None
            
            # 保存更改
            self.data_manager.save()
            
            # 刷新UI
            self.data_manager.data_changed.emit()
            
            # 显示提示
            if success_count > 0:
                info_text = f"已成功粘贴 {success_count} 个项目"
                if is_cut:
                    info_text += "（剪切操作）"
                # 尝试获取主窗口的状态栏
                parent = self.parent()
                while parent and not hasattr(parent, 'status_bar'):
                    parent = parent.parent()
                if parent and hasattr(parent, 'status_bar'):
                    parent.status_bar.showMessage(info_text, 3000)
                else:
                    # 如果没有找到状态栏，则使用弹窗提示
                    QMessageBox.information(self, "粘贴成功", info_text)
            else:
                QMessageBox.warning(self, "粘贴失败", "没有有效项目可粘贴")
        except Exception as e:
            logger.error(f"粘贴出错: {e}")
            QMessageBox.warning(self, "粘贴失败", f"粘贴过程中出错: {str(e)}")
    # This software was developed by Fan Huiyong, and all rights belong to Fan Huiyong himself. This software is only allowed for personal non-commercial use; it is prohibited for any organization or individual to use it for profit-making purposes without authorization.
    def clear_selection(self):
        self.selected_items = []
        self.last_selected_index = None
        self.refresh()

    def _batch_delete(self, confirm_from_main=False):
        """批量删除所选项目"""
        # 如果处于锁定状态，则阻止操作
        if self.is_locked:
            parent = self.parent()
            while parent and not hasattr(parent, '_show_locked_message'):
                parent = parent.parent()
            if parent and hasattr(parent, '_show_locked_message'):
                parent._show_locked_message()
            return
            
        if not self.selected_items:
            QMessageBox.information(self, "删除", "请选择要删除的项目")
            return
        
        try:
            # 统计选中的项目类型数量
            url_count = sum(1 for _, typ in self.selected_items if typ == "url")
            folder_count = sum(1 for _, typ in self.selected_items if typ == "folder")
            
            # 创建确认消息
            if len(self.selected_items) == 1:
                name, typ = self.selected_items[0]
                if typ == "url":
                    confirm_msg = f'您确定要删除网址"{name}"吗？'
                else:
                    confirm_msg = f'您确定要删除文件夹"{name}"吗？这将删除其中的所有内容。'
            else:
                parts = []
                if url_count > 0:
                    parts.append(f"{url_count}个网址")
                if folder_count > 0:
                    parts.append(f"{folder_count}个文件夹")
                confirm_msg = f"您确定要删除{' 和 '.join(parts)}吗？这个操作不可撤销。"
            
            # 弹出确认对话框
            if not confirm_from_main:
                reply = QMessageBox.question(
                    self, 
                    "删除确认", 
                    confirm_msg,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
            
            # 保存快照（通过主窗口）
            parent = self.parent()
            while parent and not hasattr(parent, '_save_undo_snapshot'):
                parent = parent.parent()
            if parent and hasattr(parent, '_save_undo_snapshot'):
                parent._save_undo_snapshot()
            
            # 获取当前路径的项目
            current_items = self.data_manager.get_item_at_path(self.current_path)
            
            if not current_items:
                QMessageBox.warning(self, "删除失败", "当前路径无效")
                return
            
            # 删除所有选中项
            deleted_count = 0
            deleted_urls = 0
            deleted_folders = 0
            
            for name, item_type in self.selected_items:
                if name in current_items:
                    if item_type == "url":
                        deleted_urls += 1
                    else:
                        deleted_folders += 1
                    del current_items[name]
                    deleted_count += 1
            
            # 保存更改
            self.data_manager.save()
            
            # 刷新UI
            self.data_manager.data_changed.emit()
            
            # 提示结果
            if deleted_count > 0:
                # 创建详细的成功消息
                if deleted_count == 1:
                    if deleted_urls == 1:
                        msg = f"已成功删除 1 个网址"
                    else:
                        msg = f"已成功删除 1 个文件夹"
                else:
                    parts = []
                    if deleted_urls > 0:
                        parts.append(f"{deleted_urls}个网址")
                    if deleted_folders > 0:
                        parts.append(f"{deleted_folders}个文件夹")
                    msg = f"已成功删除 {' 和 '.join(parts)}"
                
                # 尝试获取主窗口的状态栏
                parent = self.parent()
                while parent and not hasattr(parent, 'status_bar'):
                    parent = parent.parent()
                if parent and hasattr(parent, 'status_bar'):
                    parent.status_bar.showMessage(msg, 3000)
                else:
                    # 如果没有找到状态栏，则使用弹窗提示
                    QMessageBox.information(self, "删除成功", msg)
            else:
                QMessageBox.warning(self, "删除失败", "没有删除任何项目")
            
            # 清除选择
            self.clear_selection()
        except Exception as e:
            logger.error(f"批量删除出错: {e}")
            QMessageBox.warning(self, "删除失败", f"批量删除过程中出错: {str(e)}")

    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if (event.mimeData().hasFormat("application/x-bookmark-item") or
            event.mimeData().hasFormat("application/x-bookmark-items") or
            event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist")):
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """处理拖拽移动事件"""
        if (event.mimeData().hasFormat("application/x-bookmark-item") or
            event.mimeData().hasFormat("application/x-bookmark-items") or
            event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist")):
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """处理拖拽放置事件"""
        logger.debug(f"接收到dropEvent: {event.mimeData().formats()}")
        drop_success = False
        if event.mimeData().hasFormat("application/x-bookmark-items"):
            import json
            items = json.loads(bytes(event.mimeData().data("application/x-bookmark-items")).decode("utf-8"))
            all_success = True
            for item in items:
                source_path = item["path"]
                source_name = item["name"]
                # 跳过同目录
                if source_path == self.current_path:
                    continue
                success = self.data_manager.move_item(source_path, source_name, self.current_path)
                if not success:
                    logger.error(f"移动失败: {source_name} 从 {source_path} 到 {self.current_path}")
                    all_success = False
            self.data_manager.save()
            if all_success:
                event.accept()
                drop_success = True
            else:
                QMessageBox.warning(self, "部分移动失败", "部分项目移动失败，可能是名称冲突或路径无效")
                event.accept()
                drop_success = True
            # 拖拽后清除选中
            self.clear_selection()
            return
        elif event.mimeData().hasFormat("application/x-bookmark-item") or event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            data = event.mimeData().data("application/x-bookmark-item").data().decode()
            parts = data.split("|")
            logger.debug(f"接收到拖放数据: {data}")
            if len(parts) >= 3:
                source_path_str = parts[0]
                source_name = parts[1]
                source_type = parts[2]
                source_path = source_path_str.split(",") if source_path_str else []
                logger.debug(f"拖放项目: 路径={source_path}, 名称={source_name}, 类型={source_type}")
                logger.debug(f"当前路径: {self.current_path}")
                if source_path == self.current_path:
                    logger.debug("拖放到相同位置，忽略")
                    event.ignore()
                    return
                if source_type == "folder":
                    source_full_path = source_path + [source_name]
                    if len(self.current_path) >= len(source_full_path):
                        is_subpath = True
                        for i in range(len(source_full_path)):
                            if i >= len(self.current_path) or source_full_path[i] != self.current_path[i]:
                                is_subpath = False
                                break
                        if is_subpath:
                            QMessageBox.warning(self, "移动失败", "不能将文件夹移动到其子文件夹中")
                            event.ignore()
                            return
                success = self.data_manager.move_item(source_path, source_name, self.current_path)
                if success:
                    logger.debug("移动成功")
                    self.data_manager.save()
                    event.accept()
                    drop_success = True
                else:
                    logger.error(f"移动失败: {source_name} 从 {source_path} 到 {self.current_path}")
                    QMessageBox.warning(self, "移动失败", "无法移动项目，可能是名称冲突或路径无效")
                    event.ignore()
            else:
                logger.error(f"拖放数据格式无效: {data}")
                event.ignore()
            # 拖拽后清除选中
            self.clear_selection()
            return
        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            # 处理来自树视图的拖放
            # 获取拖放源
            source_widget = event.source()
            if isinstance(source_widget, QTreeWidget):
                # 获取当前选中的树项目
                selected_items = source_widget.selectedItems()
                if selected_items:
                    item = selected_items[0]
                    data = item.data(0, Qt.UserRole)
                    if data:
                        source_path = data["path"]
                        source_name = data["name"]
                        
                        logger.debug(f"从树视图拖放: 路径={source_path}, 名称={source_name}")
                        
                        # 检查目标路径是否是源路径的子路径
                        if data["item"]["type"] == "folder":
                            source_full_path = source_path + [source_name]
                            if len(self.current_path) >= len(source_full_path):
                                is_subpath = True
                                for i in range(len(source_full_path)):
                                    if i >= len(self.current_path) or source_full_path[i] != self.current_path[i]:
                                        is_subpath = False
                                        break
                                
                                if is_subpath:
                                    QMessageBox.warning(self, "移动失败", "不能将文件夹移动到其子文件夹中")
                                    event.ignore()
                                    return
                        
                        # 移动项目
                        success = self.data_manager.move_item(source_path, source_name, self.current_path)
                        
                        if success:
                            logger.debug("移动成功")
                            self.data_manager.save()
                            event.accept()
                        else:
                            logger.error("移动失败")
                            QMessageBox.warning(self, "移动失败", "无法移动项目，可能是名称冲突或路径无效")
                            event.ignore()
                    else:
                        logger.error("无法获取树项数据")
                        event.ignore()
                else:
                    logger.error("没有选中的树项目")
                    event.ignore()
            else:
                logger.error("拖放源不是树视图")
                event.ignore()
        else:
            logger.error(f"不支持的MIME类型: {event.mimeData().formats()}")
            event.ignore()

    def eventFilter(self, obj, event):
        if obj == self.viewport():
            if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # 判断是否点在卡片上
                in_card = None
                for w, name, typ in getattr(self, '_item_widgets', []):
                    if w.geometry().contains(w.mapFrom(self.viewport(), event.pos())):
                        in_card = w
                        break
                
                if not in_card:
                    # 点击空白区域，开始框选
                    self.drag_selecting = True
                    self.drag_start_pos = event.pos()
                    self.drag_current_pos = event.pos()
                    if not (event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)):
                        # 如果没有按下Ctrl或Shift，则清除现有选择
                        if self.selected_items:
                            self.clear_selection()
                            self.viewport().update()
                
                self._drag_start_pos = event.pos()
                self._event_in_card = in_card
                self._dragged = False
            
            elif event.type() == QtCore.QEvent.MouseMove:
                if self.drag_selecting and self.drag_start_pos:
                    # 更新框选区域
                    self.drag_current_pos = event.pos()
                    self.viewport().update()  # 触发重绘
                    return True
                elif self._drag_start_pos:
                    if (event.pos() - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                        self._start_drag()
                        self._drag_start_pos = None
                        self._dragged = True
                        return True
            
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                if self.drag_selecting and self.drag_start_pos and self.drag_current_pos:
                    # 完成框选，选择框内的项目
                    self._select_items_in_rect(self._get_drag_rect())
                    self.drag_selecting = False
                    self.drag_start_pos = None
                    self.drag_current_pos = None
                    self.viewport().update()  # 触发重绘
                    return True
                # 如果鼠标在卡片上且未发生拖拽，则emit clicked
                elif hasattr(self, '_event_in_card') and self._event_in_card and not getattr(self, '_dragged', False):
                    # 构造一个点击事件并emit
                    w = self._event_in_card
                    fake_event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonRelease, w.mapFrom(self.viewport(), event.pos()), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                    w.clicked.emit(w.name, w.item["type"], fake_event, w)
                self._drag_start_pos = None
                self._event_in_card = None
                self._dragged = False
        return super().eventFilter(obj, event)

    def _get_drag_rect(self):
        """获取拖选矩形区域"""
        if not self.drag_start_pos or not self.drag_current_pos:
            return QRect()
        
        # 创建矩形区域（确保宽高都为正值）
        x1 = min(self.drag_start_pos.x(), self.drag_current_pos.x())
        y1 = min(self.drag_start_pos.y(), self.drag_current_pos.y())
        x2 = max(self.drag_start_pos.x(), self.drag_current_pos.x())
        y2 = max(self.drag_start_pos.y(), self.drag_current_pos.y())
        
        return QRect(x1, y1, x2 - x1, y2 - y1)
    
    def _select_items_in_rect(self, rect):
        """选择矩形区域内的项目"""
        if not rect.isValid() or not hasattr(self, '_item_widgets'):
            return
        
        # 获取当前修饰键状态
        modifiers = QApplication.keyboardModifiers()
        ctrl_pressed = bool(modifiers & Qt.ControlModifier)
        shift_pressed = bool(modifiers & Qt.ShiftModifier)
        
        # 创建临时列表存储框选中的项目
        items_in_rect = []
        
        # 检查每个项目是否在选择区域内
        for widget, name, typ in self._item_widgets:
            # 将项目坐标转换为viewport坐标
            widget_rect = QRect(
                widget.mapTo(self.viewport(), QPoint(0, 0)),
                widget.size()
            )
            
            # 检查项目是否与选择矩形相交
            if rect.intersects(widget_rect):
                items_in_rect.append((name, typ))
        # 根据修饰键更新选择
        if ctrl_pressed or shift_pressed:
            # Ctrl或Shift：在已选择的基础上添加或移除
            for item in items_in_rect:
                if item in self.selected_items:
                    if ctrl_pressed:  # Ctrl按下时可以取消选择
                        self.selected_items.remove(item)
                else:
                    self.selected_items.append(item)
        else:
            # 无修饰键：替换当前选择
            self.selected_items = items_in_rect
        
        # 刷新视图以显示选择结果
        if items_in_rect:
            self.refresh()

    def _start_drag(self):
        if not self.selected_items:
            return
        from PyQt5.QtCore import QMimeData, QByteArray
        import json
        drag = QDrag(self)
        mime_data = QMimeData()
        items_to_drag = []
        for name, typ in self.selected_items:
            for w, n, t in getattr(self, '_item_widgets', []):
                if n == name and t == typ:
                    items_to_drag.append({
                        'path': w.path,
                        'name': w.name,
                        'type': w.item['type']
                    })
                    break
        if len(items_to_drag) > 1:
            mime_data.setData('application/x-bookmark-items', QByteArray(json.dumps(items_to_drag).encode('utf-8')))
        else:
            # 单项拖拽
            item = items_to_drag[0]
            path_str = ",".join(item['path']) if item['path'] else ""
            data = f"{path_str}|{item['name']}|{item['type']}"
            mime_data.setData("application/x-bookmark-item", QByteArray(data.encode()))
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.drag_selecting and self.drag_start_pos and self.drag_current_pos:
            painter = QPainter(self.viewport())
            painter.setPen(QPen(QColor(0, 120, 215, 180), 2, Qt.DashLine))
            painter.setBrush(QColor(0, 120, 215, 60))
            rect = self._get_drag_rect()
            painter.drawRect(rect)
            painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # Esc键清除所有选择
            if self.selected_items:
                self.clear_selection()
                return
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_A:
                self.selected_items = [(name, typ) for _, name, typ in getattr(self, '_item_widgets', [])]
                self.last_selected_index = None
                self.refresh()
                return
            elif event.key() == Qt.Key_C:
                self._batch_copy()
                return
            elif event.key() == Qt.Key_X:
                self._cut_selected()
                return
            elif event.key() == Qt.Key_V:
                self._paste_item()
                return
        if event.key() == Qt.Key_Delete:
            self._batch_delete()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 检查是否在根目录
            if not self.current_path:
                # 获取点击位置
                pos = event.pos()
                # 将点击位置转换为相对于viewport的坐标
                viewport_pos = self.viewport().mapFromParent(pos)
                logger.debug(f"鼠标点击事件: pos={pos}, viewport_pos={viewport_pos}")
                
                # 检查是否点击在背景图片上
                clicked_on_background = False
                if hasattr(self, 'bg_label') and self.bg_label and not self.bg_hidden:
                    # 获取背景图片在viewport中的几何位置
                    bg_geometry = self.bg_label.geometry()
                    if bg_geometry.contains(viewport_pos):
                        clicked_on_background = True
                        logger.debug(f"点击在背景图片上: bg_geometry={bg_geometry}")
                
                # 如果点击在背景图片上，直接调用隐藏背景图方法
                if clicked_on_background:
                    self._hide_background()
                    logger.debug("点击背景图片，隐藏背景图")
                    event.accept()
                    return
                
                # 检查是否点击在任何卡片上
                clicked_on_card = False
                
                # 遍历所有卡片检查点击位置
                for w, name, typ in getattr(self, '_item_widgets', []):
                    # 获取卡片在viewport中的几何位置
                    card_geometry = w.geometry()
                    if card_geometry.contains(viewport_pos):
                        clicked_on_card = True
                        logger.debug(f"点击在卡片上: card_geometry={card_geometry}")
                        break
                
                # 如果没有点击在卡片上且没有点击在背景图上，则认为是空白区域点击
                if not clicked_on_card:
                    # 点击在空白区域，恢复背景图显示（像根目录按钮一样）
                    self.show_background()
                    logger.debug(f"在根目录空白区域点击，恢复背景图显示: viewport_pos={viewport_pos}")
                    event.accept()
                    return
        
        # 调用父类方法处理其他情况
        super().mousePressEvent(event)

    def set_breadcrumb_bar(self, bar):
        self.external_breadcrumb_bar = bar
        self._update_breadcrumb()

    def set_locked_state(self, locked):
        """设置锁定状态"""
        self.is_locked = locked
        logger.debug(f"书签网格锁定状态: {locked}")
        # 更新右键菜单状态
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'setContextMenuPolicy'):
                    if locked:
                        # 锁定状态下仍然允许右键菜单，但菜单中只显示"打开"选项
                        widget.setContextMenuPolicy(Qt.CustomContextMenu)
                    else:
                        # 解锁状态下恢复原有右键菜单
                        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.refresh()  # 刷新视图以更新 "+添加" 按钮状态
    
    def _hide_background(self):
        """隐藏背景图片"""
        self.bg_hidden = True
        self.refresh()
        logger.debug("背景图片已隐藏")

    def show_background(self):
        """显示背景图片"""
        self.bg_hidden = False
        # 只在根目录时刷新视图以显示背景图
        if not self.current_path:
            self.refresh()
        logger.debug("背景图片已恢复显示")


class BookmarkItemWidget(QWidget):
    """书签项目小部件"""
    
    # 定义信号
    navigate_to = pyqtSignal(list)
    edit_item = pyqtSignal(list, str, dict)
    delete_item = pyqtSignal(list, str)
    clicked = pyqtSignal(str, str, object, object)  # name, type, event, self
    
    def __init__(self, name, item, path, favicon_service):
        super().__init__()
        self.setObjectName("BookmarkItemWidget")  # 这就是设置对象名
        self.name = name
        self.item = item
        self.path = path
        self.favicon_service = favicon_service
        self.highlighted = False
        self.selected = False
        self.drag_start_position = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 主横向布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(6)  # 缩小图标与右侧内容的间距
        
        # 图标按钮
        self.icon_button = QPushButton()
        self.icon_button.setFlat(True)
        self.icon_button.setIconSize(QtCore.QSize(48, 48))
        self.icon_button.setFixedSize(52, 52)
        if self.item["type"] == "folder":
            self.icon_button.setIcon(icon_provider.get_icon("folder-large"))
        elif self.item.get("icon"):
            # 使用icon_provider加载图标，它能处理相对路径和绝对路径
            self.icon_button.setIcon(icon_provider.get_icon(self.item["icon"]))
        else:
            # 使用默认图标
            self.icon_button.setIcon(icon_provider.get_icon("globe"))
        self.icon_button.clicked.connect(self._on_icon_clicked)
        
        # 右侧竖直布局
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(1)  # 缩小名称与网址之间的间距

        # 名称标签
        self.name_label = QLabel(self.name)
        name_font = self.name_label.font()
        name_font.setPointSizeF(13.0)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet("color: #222;")
        self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.name_label.setWordWrap(False)

        # 网址标签
        self.url_label = QLabel(self.item.get("url", ""))
        url_font = self.url_label.font()
        url_font.setPointSizeF(10.0)
        self.url_label.setFont(url_font)
        self.url_label.setStyleSheet("color: #888;")
        self.url_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.url_label.setWordWrap(False)
        self.url_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.url_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.url_label.customContextMenuRequested.connect(self._url_context_menu)

        # 添加到右侧布局
        right_layout.addWidget(self.name_label)
        right_layout.addWidget(self.url_label)
        
        # 添加到主布局
        main_layout.addWidget(self.icon_button)
        main_layout.addLayout(right_layout)
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 设置卡片尺寸
        self.setMinimumWidth(360)
        self.setMaximumWidth(480)
        self.setMinimumHeight(68)
        self.setMaximumHeight(90)

        # 保持原有上下文菜单、拖拽等逻辑
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setAcceptDrops(True)
    
    def _on_icon_clicked(self):
        # 模拟卡片单击（用于选中/多选，不直接打开网址）
        modifiers = QApplication.keyboardModifiers()
        event = QMouseEvent(QtCore.QEvent.MouseButtonPress, self.icon_button.pos(), Qt.LeftButton, Qt.LeftButton, modifiers)
        self.clicked.emit(self.name, self.item["type"], event, self)

    def _open_url(self):
        """打开URL"""
        if self.item["type"] == "url":
            from utils.url_utils import validate_url
            from PyQt5.QtWidgets import QMessageBox
            
            # 验证URL
            is_valid, sanitized_url, message = validate_url(self.item["url"])
            
            if not is_valid:
                QMessageBox.warning(self, "无效的URL", message)
                return
                
            # 如果有警告信息，显示确认对话框
            if message:
                reply = QMessageBox.question(
                    self, 
                    "URL警告", 
                    f"{message}\n确定要继续打开吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            # 更新为清理后的URL
            if sanitized_url != self.item["url"]:
                self.item["url"] = sanitized_url

            import webbrowser
            webbrowser.open(self.item["url"])
            
            # 添加到历史记录
            self._add_to_history()
        elif self.item["type"] == "folder":
            self.navigate_to.emit(self.path + [self.name])

    def _show_context_menu(self, pos):
        """显示上下文菜单"""
        menu = QMenu(self)
        grid = self.parent()
        while grid and not isinstance(grid, BookmarkGridWidget):
            grid = grid.parent()

        # 检查是否处于锁定状态
        is_locked = grid.is_locked if grid else False
        if is_locked:
            # 锁定状态下只显示"打开"选项
            if self.item["type"] == "folder":
                open_action = QAction(icon_provider.get_icon("folder-open"), "打开", self)
                open_action.triggered.connect(self._open_url)
                menu.addAction(open_action)
            else:
                open_action = QAction(icon_provider.get_icon("globe"), "打开", self)
                open_action.triggered.connect(self._open_url)
                menu.addAction(open_action)

            # 如果没有菜单项则不显示菜单
            if not menu.actions():
                return
                
            menu.exec_(self.mapToGlobal(pos))
            return
            
        # 如果有多选，弹出批量菜单
        if grid and len(grid.selected_items) > 1:
            # 添加批量打开选项
            batch_open = QAction(icon_provider.get_icon("globe"), "打开", self)
            batch_open.triggered.connect(lambda: self._batch_open_urls(grid))
            menu.addAction(batch_open)
            
            batch_delete = QAction(icon_provider.get_icon("delete"), "批量删除", self)
            batch_delete.triggered.connect(grid._batch_delete)
            menu.addAction(batch_delete)
            batch_copy = QAction(icon_provider.get_icon("copy"), "批量复制", self)
            batch_copy.triggered.connect(grid._batch_copy)
            menu.addAction(batch_copy)
            batch_cut = QAction(QIcon(os.path.join(os.path.dirname(__file__), "../resources/icons/cut.ico")), "剪切", self)
            batch_cut.triggered.connect(lambda: grid._cut_selected() if grid else None)
            menu.addAction(batch_cut)
            menu.exec_(self.mapToGlobal(pos))
            return
        # ...原有单项菜单...
        if self.item["type"] == "folder":
            # 文件夹菜单
            open_action = QAction(icon_provider.get_icon("folder-open"), "打开", self)
            open_action.triggered.connect(self._open_url)
            menu.addAction(open_action)
        else:
            # URL菜单
            open_action = QAction(icon_provider.get_icon("globe"), "打开", self)
            open_action.triggered.connect(self._open_url)
            menu.addAction(open_action)
        # 剪切选项（无论单选还是多选都显示）
        cut_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), "../resources/icons/cut.ico")), "剪切", self)
        cut_action.triggered.connect(lambda: grid._cut_selected() if grid else None)
        menu.addAction(cut_action)
        # 复制选项
        copy_action = QAction(icon_provider.get_icon("copy"), "复制", self)
        copy_action.triggered.connect(self._copy_item)
        menu.addAction(copy_action)
        menu.addSeparator()
        # 编辑和删除选项
        edit_action = QAction(icon_provider.get_icon("edit"), "编辑", self)
        edit_action.triggered.connect(lambda: self.edit_item.emit(self.path, self.name, self.item))
        menu.addAction(edit_action)
        delete_action = QAction(icon_provider.get_icon("delete"), "删除", self)
        delete_action.triggered.connect(lambda: self.delete_item.emit(self.path, self.name))
        menu.addAction(delete_action)
        menu.exec_(self.mapToGlobal(pos))
    
    def _copy_item(self):
        """复制项目"""
        # 将项目数据保存到父组件的剪贴板
        parent = self.parent()
        while parent and not isinstance(parent, BookmarkGridWidget):
            parent = parent.parent()
        
        if parent:
            # 创建确认消息
            if self.item["type"] == "url":
                confirm_msg = f'您确定要复制网址"{self.name}"吗？'
            else:
                confirm_msg = f'您确定要复制文件夹"{self.name}"吗？'
            
            # 显示确认对话框
            reply = QMessageBox.question(
                self, 
                "复制确认", 
                confirm_msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
                
            parent.clipboard_data = {
                "path": self.path,
                "name": self.name,
                "type": self.item["type"]
            }
            
            # 清空剪切数据，避免混淆
            if hasattr(parent, 'cut_data'):
                parent.cut_data = None
            
            # 创建成功消息
            if self.item["type"] == "url":
                success_msg = f'已复制网址"{self.name}"到剪贴板'
            else:
                success_msg = f'已复制文件夹"{self.name}"到剪贴板'
                
            # 尝试获取主窗口的状态栏
            main_win = self
            while main_win and not hasattr(main_win, 'status_bar'):
                main_win = main_win.parent()
            if main_win and hasattr(main_win, 'status_bar'):
                main_win.status_bar.showMessage(success_msg, 3000)
            else:
                # 如果没有找到状态栏，则使用弹窗提示
                QMessageBox.information(self, "复制成功", success_msg)
    
    def highlight(self):
        """高亮显示"""
        self.highlighted = True
        self.setStyleSheet("background-color: #e0f0ff; border: 2px solid #0078d7; border-radius: 5px;")
    
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet("background-color: #cce5ff; border: 2px solid #0078d7; border-radius: 5px;")
        else:
            self.setStyleSheet("")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed_pos = event.pos()
            parent = self.parent()
            while parent and not hasattr(parent, '_drag_start_pos'):
                parent = parent.parent()
            if parent and hasattr(parent, '_drag_start_pos'):
                parent._drag_start_pos = self.mapTo(parent.viewport(), event.pos())
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 判断是否为点击（未发生拖拽）
            if hasattr(self, '_pressed_pos') and (event.pos() - self._pressed_pos).manhattanLength() < QApplication.startDragDistance():
                self.clicked.emit(self.name, self.item["type"], event, self)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._open_url()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def _url_context_menu(self, pos):
        """处理URL标签的右键菜单 - 将请求转发到卡片的上下文菜单处理函数"""
        # 将URL标签坐标转换为整个卡片的坐标
        global_pos = self.url_label.mapToGlobal(pos)
        local_pos = self.mapFromGlobal(global_pos)
        # 调用卡片的上下文菜单处理函数
        self._show_context_menu(local_pos)
        
    def _batch_open_urls(self, grid):
        """批量打开选中的URL"""
        if not grid or not hasattr(grid, 'selected_items'):
            return
            
        # 获取主窗口
        main_win = None
        parent = self.parent()
        while parent:
            if hasattr(parent, '_open_selected_url'):
                main_win = parent
                break
            parent = parent.parent()
            
        if main_win:
            # 调用主窗口的打开URL方法
            main_win._open_selected_url()
        else:
            # 如果找不到主窗口，则直接在这里实现打开URL的逻辑
            opened_count = 0
            for name, item_type in grid.selected_items:
                # 只打开URL类型的项目
                if item_type == "url":
                    # 获取项目数据
                    for w, n, t in grid._item_widgets:
                        if n == name and t == item_type:
                            # 调用项目的_open_url方法
                            w._open_url()
                            opened_count += 1
            
            # 显示提示消息
            if opened_count > 0:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "打开网站", f"已打开 {opened_count} 个网址")
    
    def _add_to_history(self):
        """添加当前URL到历史记录"""
        try:
            if self.item["type"] != "url":
                return
                
            # 获取主窗口实例
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'blind_box_manager'):
                    main_window = parent
                    break
                parent = parent.parent()
            
            if main_window and hasattr(main_window, 'blind_box_manager'):
                # 构造历史记录项
                url = self.item["url"]
                name = self.item.get("name", "未知网站")
                path = self.path if self.path else []
                
                history_urls = [(url, name, path)]
                
                # 添加到历史记录
                main_window.blind_box_manager._add_to_history(history_urls)
                logger.info(f"已添加到历史记录: {name} ({url})")
        except Exception as e:
            logger.error(f"添加历史记录失败: {e}")


# 添加可点击标签类和背景图片隐藏/显示方法
class ClickableLabel(QLabel):
    """可点击的标签类"""
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)