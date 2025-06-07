# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QAbstractItemView, QPushButton, QWidget, QSizePolicy,
    QMessageBox, QMenu, QAction, QCheckBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from ui.icons import icon_provider
from utils.language_manager import language_manager

logger = logging.getLogger(__name__)

class HistoryDialog(QDialog):
    """历史记录对话框"""
    
    def __init__(self, parent, history_data, data_manager, history_manager):
        super().__init__(parent)
        self.history_data = history_data
        self.data_manager = data_manager
        self.history_manager = history_manager
        self.selected_items = []  # 存储多选的项目
        self.deletion_performed = False  # 标记是否执行了删除操作
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("历史记录")
        self.setMinimumWidth(1100)  # 增加宽度以容纳位置信息列
        self.setMinimumHeight(550)
        self.resize(1200, 650)  # 设置默认大小
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 使用传入的历史记录数据
        history_records = self.history_data
        
        # 创建结果标签
        self.result_label = QLabel(f"共有 {len(history_records)} 条历史记录")
        self.result_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.result_label)
        
        # 创建列标题头部
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(45, 5, 25, 5)  # 左边距45px为图标留空间
        header_layout.setSpacing(12)
        
        # 创建列标题
        name_header = QLabel("网址名称")
        name_header.setStyleSheet("font-weight: bold; color: #333; font-size: 10pt; border-bottom: 2px solid #ddd; padding-bottom: 3px;")
        name_header.setMinimumWidth(300)
        name_header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        location_header = QLabel("位置信息")
        location_header.setStyleSheet("font-weight: bold; color: #333; font-size: 10pt; border-bottom: 2px solid #ddd; padding-bottom: 3px;")
        location_header.setMinimumWidth(200)
        location_header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        time_header = QLabel("访问时间")
        time_header.setStyleSheet("font-weight: bold; color: #333; font-size: 10pt; border-bottom: 2px solid #ddd; padding-bottom: 3px;")
        time_header.setMinimumWidth(150)
        time_header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 添加标题到布局，按4:3:3比例
        header_layout.addWidget(name_header, 4)
        header_layout.addWidget(location_header, 3)
        header_layout.addWidget(time_header, 3)
        
        layout.addWidget(header_widget)
        
        # 创建历史记录列表
        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # 允许多选
        self.history_list.setIconSize(QSize(32, 32))  # 设置图标大小
        
        # 调整列表项高度，使其更宽松
        self.history_list.setStyleSheet("""
            QListWidget::item { 
                padding: 8px 4px; 
                min-height: 52px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #e6f0fa;
                border: 1px solid #99c2ff;
            }
            QListWidget {
                font-size: 10pt;
            }
        """)
        # 设置垂直滚动条始终显示，避免选择时宽度变化
        self.history_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self.history_list)
        
        # 添加历史记录项
        self._populate_list()
        
        # 创建底部按钮区域
        button_layout = QHBoxLayout()
        
        # 创建全选/清除选择按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._toggle_select_all)
        button_layout.addWidget(self.select_all_btn)
        
        # 创建打开按钮
        open_btn = QPushButton("打开选中网址")
        open_btn.clicked.connect(self._open_selected_urls)
        button_layout.addWidget(open_btn)
        
        # 创建定位按钮
        locate_btn = QPushButton("定位到所选网址的标签")
        locate_btn.clicked.connect(self._locate_selected_items)
        button_layout.addWidget(locate_btn)
        
        # 创建删除按钮
        delete_btn = QPushButton("删除选中项")
        delete_btn.clicked.connect(self._delete_selected_items)
        button_layout.addWidget(delete_btn)
        
        # 创建清空按钮
        clear_all_btn = QPushButton("清空所有历史")
        clear_all_btn.clicked.connect(self._clear_all_history)
        button_layout.addWidget(clear_all_btn)
        
        # 检查锁定状态
        main_win = self.parent()
        if main_win and hasattr(main_win, 'is_locked') and main_win.is_locked:
            delete_btn.setEnabled(False)
            delete_btn.setToolTip("当前处于锁定状态，无法删除历史记录")
            clear_all_btn.setEnabled(False)
            clear_all_btn.setToolTip("当前处于锁定状态，无法清空历史记录")
        
        # 创建关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        # 添加按钮布局到主布局
        layout.addLayout(button_layout)
        
        # 设置对话框布局
        self.setLayout(layout)
        
        # 连接信号
        self.history_list.itemSelectionChanged.connect(self._update_selection_status)
        self.history_list.itemDoubleClicked.connect(self._open_selected_item)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # 设置快捷键
        self._setup_shortcuts()
        
        # 更新选择状态
        self._update_selection_status()
    
    def _populate_list(self):
        """填充历史记录列表"""
        # 清空列表
        self.history_list.clear()
        
        # 添加历史记录项
        for record in self.history_data:
            # 创建列表项
            item = QListWidgetItem()
            
            # 设置图标
            if "icon" in record and record.get("icon"):
                item.setIcon(icon_provider.get_icon(record["icon"]))
            else:
                item.setIcon(icon_provider.get_icon("globe"))
            
            # 存储完整数据到UserRole
            item.setData(Qt.UserRole, record)
            
            # 使用自定义布局显示
            widget = QWidget()
            item_layout = QHBoxLayout(widget)
            # 增加内边距
            item_layout.setContentsMargins(8, 10, 8, 10)
            item_layout.setSpacing(12)  # 控件之间的间距
            
            # 格式化时间
            timestamp = record.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError) as e:
                    logger.warning(f"时间格式解析失败: {e}")
                    time_str = timestamp
            else:
                time_str = '未知时间'
            
            # 格式化位置信息
            path = record.get('path', [])
            # 兼容性处理：确保路径为列表格式
            if isinstance(path, str):
                if path:
                    path = path.split('/')
                else:
                    path = []
            
            # 生成位置信息字符串
            if path and len(path) > 0:
                # 显示完整的路径层次结构
                # 不移除最后一个元素，因为在历史记录中，路径的最后一个元素通常是目录名而不是文件名
                location_str = '/'.join(path) if path else '根目录'
            else:
                location_str = '根目录'
            
            # 完整的提示文本
            tooltip_text = f"名称: {record['name']}\n网址: {record['url']}\n位置: {location_str}\n时间: {time_str}"
            
            # 创建名称标签（40%宽度）
            name_label = QLabel(record['name'])
            name_label.setStyleSheet("font-weight: bold; color: #000; font-size: 10pt;")
            name_label.setMinimumWidth(300)
            name_label.setMaximumWidth(450)
            name_label.setTextFormat(Qt.PlainText)
            name_label.setWordWrap(False)
            name_label.setText(record['name'])
            name_label.setToolTip(record['name'])
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            # 创建位置信息标签（30%宽度）
            location_label = QLabel(location_str)
            location_label.setStyleSheet("color: #0066cc; font-size: 9pt;")
            location_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            location_label.setMinimumWidth(200)
            location_label.setMaximumWidth(350)
            location_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            location_label.setTextFormat(Qt.PlainText)
            location_label.setWordWrap(False)
            location_label.setText(location_str)
            location_label.setToolTip(f"位置: {location_str}")
            
            # 创建时间标签（30%宽度）
            time_label = QLabel(time_str)
            time_label.setStyleSheet("color: #666; font-size: 9pt;")
            time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            time_label.setMinimumWidth(150)
            time_label.setMaximumWidth(200)
            time_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            time_label.setTextFormat(Qt.PlainText)
            time_label.setWordWrap(False)
            time_label.setText(time_str)
            time_label.setToolTip(f"访问时间: {time_str}")
            
            # 为整个item设置工具提示
            widget.setToolTip(tooltip_text)
            
            # 添加布局，按4:3:3比例分配
            item_layout.addWidget(name_label, 4)  # 40%
            item_layout.addWidget(location_label, 3)  # 30%
            item_layout.addWidget(time_label, 3)  # 30%
            
            # 设置列表项高度
            item.setSizeHint(QSize(widget.sizeHint().width(), 52))
            
            # 添加项目到列表
            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, widget)
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        # 可以在这里添加快捷键设置
        pass
    
    def _update_selection_status(self):
        """更新选择状态"""
        # 获取选中的项目
        selected_items = self.history_list.selectedItems()
        self.selected_items = selected_items
        
        # 更新全选按钮文本
        if len(selected_items) == self.history_list.count() and self.history_list.count() > 0:
            self.select_all_btn.setText("清除选择")
        else:
            self.select_all_btn.setText("全选")
    
    def _toggle_select_all(self):
        """切换全选/清除选择"""
        if len(self.selected_items) == self.history_list.count() and self.history_list.count() > 0:
            # 清除选择
            self.history_list.clearSelection()
        else:
            # 全选
            self.history_list.selectAll()
    
    def _show_context_menu(self, pos):
        """显示右键上下文菜单"""
        # 创建上下文菜单
        context_menu = self._create_context_menu()
        
        # 显示菜单
        context_menu.exec_(self.history_list.mapToGlobal(pos))
    
    def _create_context_menu(self):
        """创建右键上下文菜单"""
        menu = QMenu(self)
        selected_items = self.history_list.selectedItems()
        
        # 打开网址
        open_action = menu.addAction("打开网址")
        open_action.triggered.connect(self._open_selected_urls)
        
        # 定位到所选网址的标签 - 仅在选中单个项目时显示
        if len(selected_items) == 1:
            locate_action = menu.addAction("定位到所选网址的标签")
            locate_action.triggered.connect(self._locate_selected_items)
        
        menu.addSeparator()
        
        # 删除选中项
        delete_action = menu.addAction("删除选中项")
        delete_action.triggered.connect(self._delete_selected_items)
        
        # 检查锁定状态
        main_win = self.parent()
        if not main_win:
            delete_action.setEnabled(False)
            delete_action.setToolTip("无法获取主窗口实例")
            return menu
            
        if hasattr(main_win, 'is_locked') and main_win.is_locked:
            delete_action.setEnabled(False)
            delete_action.setToolTip("当前处于锁定状态，无法删除历史记录")
        
        return menu
    
    def _open_selected_urls(self):
        """打开选中的URL"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            return
        
        import webbrowser
        import time
        history_urls = []  # 用于收集需要添加到历史记录的URL
        
        for item in selected_items:
            history_data = item.data(Qt.UserRole)
            if history_data and history_data.get('url'):
                try:
                    webbrowser.open(history_data['url'])
                    time.sleep(0.3)  # 避免浏览器进程冲突
                    
                    # 收集历史记录信息
                    url = history_data['url']
                    name = history_data.get('name', '未知网站')
                    path = history_data.get('path', [])
                    history_urls.append((url, name, path))
                except Exception as e:
                    logger.error(f"打开URL失败: {history_data['url']}, 错误: {e}")
        
        # 添加到历史记录
        if history_urls:
            try:
                # 获取主窗口实例
                main_window = None
                current_parent = self.parent()
                while current_parent:
                    if hasattr(current_parent, 'blind_box_manager'):
                        main_window = current_parent
                        break
                    current_parent = current_parent.parent()
                
                if main_window and hasattr(main_window, 'blind_box_manager'):
                    main_window.blind_box_manager._add_to_history(history_urls)
                    logger.info(f"已添加 {len(history_urls)} 个网址到历史记录")
            except Exception as e:
                logger.error(f"添加历史记录失败: {e}")
    
    def _locate_selected_items(self):
        """定位选中项到文件夹"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            return
        
        # 获取第一个选中项的数据
        first_item = selected_items[0]
        history_data = first_item.data(Qt.UserRole)
        if not history_data or not history_data.get('path'):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "定位失败", "无效的历史记录数据")
            return
            
        # 获取主窗口
        main_win = self.parent()
        if not main_win:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "定位失败", "无法获取主窗口实例")
            return
            
        if not hasattr(main_win, 'folder_tree') or not hasattr(main_win, 'bookmark_grid'):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "定位失败", "无法访问主界面，定位失败")
            return
            
        # 处理路径（兼容旧格式和新格式）
        path = history_data['path']
        
        # 兼容性处理：如果路径是字符串格式，转换为列表格式
        if isinstance(path, str):
            if path == '/' or path == '':
                path = []
            else:
                # 移除开头的斜杠并按斜杠分割
                path = path.lstrip('/').split('/') if path.strip() else []
        
        # 确保路径是列表格式
        if not isinstance(path, list):
            path = []
            
        # 如果路径是列表且最后一个元素是项目名称，则去掉最后一个元素
        if isinstance(path, list) and len(path) > 0:
            if history_data.get('type') == 'url':
                path = path[:-1] if len(path) > 1 else []
        
        name = history_data.get('name', '')
        
        try:
            # 切换目录树和卡片区
            main_win.folder_tree.select_path(path)
            main_win.bookmark_grid.set_current_path(path)
            
            # 如果是网址，高亮并选中卡片
            if history_data.get('type') == 'url' and name:
                # 先清除之前的选择和高亮
                main_win.bookmark_grid.clear_selection()
                main_win.bookmark_grid.highlighted_item = None
                
                # 设置新的高亮和选中
                main_win.bookmark_grid.highlight_item(name)
                main_win.bookmark_grid.selected_items = [(name, history_data.get('type', 'url'))]
                
                # 刷新显示
                main_win.bookmark_grid.refresh()
                
                # 滚动到目标项目
                for w, n, t in getattr(main_win.bookmark_grid, '_item_widgets', []):
                    if n == name:
                        # 确保滚动到可见区域
                        if hasattr(main_win.bookmark_grid, 'ensureWidgetVisible'):
                            main_win.bookmark_grid.ensureWidgetVisible(w)
                        else:
                            # 尝试用scrollArea滚动
                            try:
                                grid = main_win.bookmark_grid
                                area = grid.viewport().parent()
                                rect = w.geometry()
                                area.ensureVisible(rect.x(), rect.y(), rect.width(), rect.height())
                            except Exception:
                                pass
                        break
            
            # 使主界面获得焦点
            main_win.activateWindow()
            main_win.raise_()
            
            # 提示成功
            from PyQt5.QtWidgets import QMessageBox
            if name:
                QMessageBox.information(self, "定位成功", f"已定位到：{name}")
            else:
                QMessageBox.information(self, "定位成功", f"已定位到所选网址的标签")
                
        except Exception as e:
            logger.error(f"定位失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "定位失败", f"无法定位到主界面，错误: {e}")
    
    def _delete_selected_items(self):
        """删除选中的历史记录项"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            return
            
        # 检查锁定状态
        main_win = self.parent()
        if not main_win:
            QMessageBox.warning(self, "删除失败", "无法获取主窗口实例")
            return
            
        if hasattr(main_win, 'is_locked') and main_win.is_locked:
            QMessageBox.warning(self, "删除失败", "当前处于锁定状态，无法删除历史记录")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_items)} 条历史记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除选中的历史记录
            for item in selected_items:
                history_data = item.data(Qt.UserRole)
                if history_data:
                    self.history_manager.remove_history_item(history_data)
            
            # 刷新列表
            self._refresh_list()
    
    def _open_selected_item(self, item):
        """打开选中的单个项目"""
        history_data = item.data(Qt.UserRole)
        if history_data and history_data.get('url'):
            try:
                import webbrowser
                webbrowser.open(history_data['url'])
                
                # 添加到历史记录
                url = history_data['url']
                name = history_data.get('name', '未知网站')
                path = history_data.get('path', [])
                history_urls = [(url, name, path)]
                
                # 获取主窗口实例
                main_window = None
                current_parent = self.parent()
                while current_parent:
                    if hasattr(current_parent, 'blind_box_manager'):
                        main_window = current_parent
                        break
                    current_parent = current_parent.parent()
                
                if main_window and hasattr(main_window, 'blind_box_manager'):
                    main_window.blind_box_manager._add_to_history(history_urls)
                    logger.info(f"已添加网址到历史记录: {name} ({url})")
            except Exception as e:
                logger.error(f"打开URL失败: {history_data['url']}, 错误: {e}")
    
    def _clear_all_history(self):
        """清空所有历史记录"""
        # 检查锁定状态
        main_win = self.parent()
        if not main_win:
            QMessageBox.warning(self, "清空失败", "无法获取主窗口实例")
            return
            
        if hasattr(main_win, 'is_locked') and main_win.is_locked:
            QMessageBox.warning(self, "清空失败", "当前处于锁定状态，无法清空历史记录")
            return
            
        # 确认清空
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有历史记录吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清空历史记录
            self.history_manager.clear_history()
            
            # 刷新列表
            self._refresh_list()
    
    def _refresh_list(self):
        """刷新历史记录列表"""
        # 获取最新的历史记录
        self.history_data = self.history_manager.get_history()
        
        # 重新填充列表
        self._populate_list()
        
        # 更新结果标签
        self.result_label.setText(f"共有 {len(self.history_data)} 条历史记录")
        
        # 更新按钮状态
        self._update_selection_status()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 如果执行了删除操作，可以在这里处理
        event.accept()