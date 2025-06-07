#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import re
from urllib.parse import urlparse
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFormLayout, QDialogButtonBox,
    QListWidget, QListWidgetItem, QAbstractItemView, QComboBox, QFileDialog, QTreeWidget, QTreeWidgetItem, QMenu, QAction, QWidget, QSizePolicy,
    QMessageBox, QTabWidget, QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from ui.icons import icon_provider
from datetime import datetime
from utils.language_manager import language_manager

logger = logging.getLogger(__name__)

class AddUrlDialog(QDialog):
    """添加URL对话框"""
    
    def __init__(self, favicon_service, path, parent=None):
        super().__init__(parent)
        self.favicon_service = favicon_service
        self.path = path
        self.icon_path = ""
        self.data_manager = None
        self.auto_get_favicon_done = False  # 标记是否已自动获取图标和标题
        
        # 尝试获取data_manager
        if parent and hasattr(parent, 'data_manager'):
            self.data_manager = parent.data_manager
        elif parent and hasattr(parent, 'app') and hasattr(parent.app, 'data_manager'):
            self.data_manager = parent.app.data_manager
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(language_manager.tr("dialogs.add_url_title"))
        self.setFixedSize(450, 250)
        
        layout = QVBoxLayout()
        
        # 表单布局
        form_layout = QFormLayout()
        
        # URL - 移到第一行
        self.url_edit = QLineEdit()
        self.url_edit.textChanged.connect(self._on_url_changed)
        form_layout.addRow(language_manager.tr("dialogs.url_label"), self.url_edit)
        
        # 名称 - 移到第二行
        self.name_edit = QLineEdit()
        form_layout.addRow(language_manager.tr("dialogs.name_label"), self.name_edit)
        
        # 图标预览和选择按钮
        icon_layout = QHBoxLayout()
        
        # 图标预览
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(32, 32)
        self.icon_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        self.update_icon_preview("")  # 使用默认图标
        icon_layout.addWidget(self.icon_preview)
        
        # 获取图标按钮
        self.get_icon_btn = QPushButton(language_manager.tr("dialogs.get_info_button"))
        self.get_icon_btn.clicked.connect(self._get_favicon)
        icon_layout.addWidget(self.get_icon_btn)
        
        # 浏览本地图标按钮
        self.browse_icon_btn = QPushButton(language_manager.tr("dialogs.browse_button"))
        self.browse_icon_btn.clicked.connect(self._browse_icon)
        icon_layout.addWidget(self.browse_icon_btn)
        
        form_layout.addRow("图标:", icon_layout)
        
        layout.addLayout(form_layout)
        
        # 按钮
        self.btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btn_box.accepted.connect(self.validate_and_accept)  # 修改为自定义验证函数
        self.btn_box.rejected.connect(self.reject)
        
        layout.addWidget(self.btn_box)
        
        self.setLayout(layout)
    
    def update_icon_preview(self, icon_path):
        """更新图标预览"""
        self.icon_path = icon_path
        
        if icon_path:
            # 使用icon_provider加载图标，它能处理相对路径和绝对路径
            icon = icon_provider.get_icon(icon_path)
            pixmap = icon.pixmap(32, 32)
            self.icon_preview.setPixmap(pixmap)
        else:
            # 使用默认图标
            icon = icon_provider.get_icon("globe")
            pixmap = icon.pixmap(32, 32)
            self.icon_preview.setPixmap(pixmap)
    
    def _on_url_changed(self, text):
        """URL改变时的处理"""
        # 清除之前的图标
        self.update_icon_preview("")
        # 重置自动获取标识
        self.auto_get_favicon_done = False
    
    def _get_favicon(self):
        """获取网站图标"""
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "获取图标", "请先输入网址")
            return
        
        # 获取网站图标
        try:
            icon_path = self.favicon_service.get_favicon(url)
            if icon_path:
                self.update_icon_preview(icon_path)
                
                # 如果网站标题是空的，尝试获取网站标题
                if not self.name_edit.text():
                    title = self.favicon_service.get_website_title(url)
                    if title:
                        self.name_edit.setText(title)
            
            # 如果未获取到名称，则尝试使用域名作为名称
            if not self.name_edit.text():
                domain = self._extract_domain_from_url(url)
                if domain:
                    self.name_edit.setText(domain)
            
            # 标记已进行获取操作
            self.auto_get_favicon_done = True
                
        except Exception as e:
            QMessageBox.warning(self, "获取图标失败", f"无法获取网站图标: {str(e)}")
    
    def _extract_domain_from_url(self, url):
        """从URL中提取域名作为名称"""
        try:
            # 确保URL有协议前缀
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
                
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # 移除www.前缀和端口号
            domain = re.sub(r'^www\.', '', domain)
            domain = re.sub(r':\d+$', '', domain)
            
            return domain
        except Exception:
            return None
    
    def _browse_icon(self):
        """浏览本地图标"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择图标", 
            "", 
            "图片文件 (*.png *.jpg *.jpeg *.gif *.ico);;所有文件 (*)"
        )
        
        if file_path:
            self.update_icon_preview(file_path)
    
    def get_data(self):
        """获取对话框数据"""
        return {
            "url": self.url_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "icon": self.icon_path
        }
    
    def validate_and_accept(self):
        """验证表单并接受"""
        url = self.url_edit.text().strip()
        name = self.name_edit.text().strip()
        
        # 1. 检查网址是否为空
        if not url:
            if not name:
                QMessageBox.warning(self, "信息不完整", "请输入网址和名称")
                return
            else:
                QMessageBox.warning(self, "信息不完整", "请输入网址信息")
                return
        
        # 2. 检查名称是否为空，如果为空，尝试自动获取
        if not name:
            # 如果未尝试自动获取，先尝试获取网站标题和图标
            if not self.auto_get_favicon_done:
                try:
                    # 自动尝试获取
                    icon_path = self.favicon_service.get_favicon(url)
                    if icon_path:
                        self.update_icon_preview(icon_path)
                    
                    title = self.favicon_service.get_website_title(url)
                    if title:
                        self.name_edit.setText(title)
                        name = title
                except Exception:
                    pass
                    
                # 标记已自动获取
                self.auto_get_favicon_done = True
            
            # 如果仍然没有名称，使用域名
            if not name:
                domain = self._extract_domain_from_url(url)
                if domain:
                    self.name_edit.setText(domain)
                    name = domain
                else:
                    QMessageBox.warning(self, "信息不完整", "请输入名称信息")
                    return
        
        # 3. 检查当前目录中是否存在相同URL和名称的项目
        if self.data_manager:
            current_items = self.data_manager.get_item_at_path(self.path)
            if current_items:
                # 检查是否存在名称和URL都相同的项目
                for item_name, item_data in current_items.items():
                    if item_data.get("type") == "url":
                        if item_name == name and item_data.get("url") == url:
                            QMessageBox.warning(
                                self, 
                                "重复项目", 
                                f"当前目录中已存在相同名称和网址的书签"
                            )
                            return
                
                # 检查是否存在相同URL但名称不同的项目
                url_exists = False
                for item_name, item_data in current_items.items():
                    if (item_data.get("type") == "url" and 
                        item_data.get("url") == url and 
                        item_name != name):
                        url_exists = True
                        break
                
                if url_exists:
                    reply = QMessageBox.question(
                        self,
                        "网址已存在",
                        f"当前目录中已存在相同网址但名称不同的书签，是否继续保存？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
        
        # 4. 如果图标为空，确保使用默认图标
        if not self.icon_path:
            # 使用默认图标
            self.icon_path = ""  # 数据管理器会处理为默认图标
        
        # 通过验证，接受对话框
        super().accept()


class EditUrlDialog(AddUrlDialog):
    """编辑URL对话框"""
    
    def __init__(self, favicon_service, path, name, item, parent=None):
        self.edit_name = name
        self.edit_item = item
        self.original_name = name
        self.original_url = item.get("url", "")
        super().__init__(favicon_service, path, parent)
    
    def init_ui(self):
        """初始化UI"""
        super().init_ui()
        
        self.setWindowTitle("编辑网址")
        
        # 设置初始值
        self.url_edit.setText(self.edit_item.get("url", ""))
        self.name_edit.setText(self.edit_name)
        
        if self.edit_item.get("icon"):
            # 使用update_icon_preview方法设置图标，确保正确处理相对路径
            self.update_icon_preview(self.edit_item["icon"])

    def validate_and_accept(self):
        """验证表单并接受（编辑模式下的增强验证）"""
        url = self.url_edit.text().strip()
        name = self.name_edit.text().strip()
        
        # 1. 检查网址是否为空
        if not url:
            if not name:
                QMessageBox.warning(self, "信息不完整", "请输入网址和名称")
                return
            else:
                QMessageBox.warning(self, "信息不完整", "请输入网址信息")
                return
        
        # 2. 检查名称是否为空，如果为空，尝试自动获取
        if not name:
            # 如果未尝试自动获取，先尝试获取网站标题和图标
            if not self.auto_get_favicon_done:
                try:
                    # 自动尝试获取
                    icon_path = self.favicon_service.get_favicon(url)
                    if icon_path:
                        self.update_icon_preview(icon_path)
                    
                    title = self.favicon_service.get_website_title(url)
                    if title:
                        self.name_edit.setText(title)
                        name = title
                except Exception:
                    pass
                    
                # 标记已自动获取
                self.auto_get_favicon_done = True
            
            # 如果仍然没有名称，使用域名
            if not name:
                domain = self._extract_domain_from_url(url)
                if domain:
                    self.name_edit.setText(domain)
                    name = domain
                else:
                    QMessageBox.warning(self, "信息不完整", "请输入名称信息")
                    return
        
        # 3. 编辑模式特殊处理：检查是否与自身相同（无变化）
        if name == self.original_name and url == self.original_url:
            # 无变化，直接接受
            super().accept()
            return
        
        # 4. 检查当前目录中是否存在相同URL和名称的项目（排除自身）
        if self.data_manager:
            current_items = self.data_manager.get_item_at_path(self.path)
            if current_items:
                # 检查是否存在名称和URL都相同的项目(排除自身)
                for item_name, item_data in current_items.items():
                    if (item_data.get("type") == "url" and 
                        item_name == name and 
                        item_data.get("url") == url and 
                        item_name != self.original_name):  # 排除自身
                        
                        QMessageBox.warning(
                            self, 
                            "重复项目", 
                            f"当前目录中已存在相同名称和网址的书签，请修改名称或网址"
                        )
                        return
                
                # 检查是否存在相同URL但名称不同的项目(排除自身)
                url_exists = False
                for item_name, item_data in current_items.items():
                    if (item_data.get("type") == "url" and 
                        item_data.get("url") == url and 
                        item_name != name and
                        item_name != self.original_name):  # 排除自身
                        
                        url_exists = True
                        break
                
                if url_exists:
                    reply = QMessageBox.question(
                        self,
                        "网址已存在",
                        f"当前目录中已存在相同网址但名称不同的书签，是否继续保存？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
        
        # 5. 如果图标为空，确保使用默认图标
        if not self.icon_path:
            # 使用默认图标
            self.icon_path = ""  # 数据管理器会处理为默认图标
        
        # 通过验证，接受对话框
        super().accept()


class AddFolderDialog(QDialog):
    """添加文件夹对话框"""
    
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("添加文件夹")
        self.setMinimumWidth(300)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建表单
        form_layout = QFormLayout()
        
        # 名称输入框
        self.name_edit = QLineEdit()
        form_layout.addRow("文件夹名称:", self.name_edit)
        
        layout.addLayout(form_layout)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 设置布局
        self.setLayout(layout)
    
    def get_folder_name(self):
        """获取文件夹名称"""
        return self.name_edit.text()


class EditFolderDialog(AddFolderDialog):
    """编辑文件夹对话框"""
    
    def __init__(self, path, name, parent=None):
        self.edit_name = name
        super().__init__(path, parent)
    
    def init_ui(self):
        """初始化UI"""
        super().init_ui()
        
        self.setWindowTitle("编辑文件夹")
        
        # 设置初始值
        self.name_edit.setText(self.edit_name)


class SearchDialog(QDialog):
    """搜索对话框"""
    
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.selected_path = None
        self.selected_items = []  # 新增：存储多选的项目
        self.data_manager = None
        self.deletion_performed = False  # 新增：标记是否执行了删除操作
        
        # 尝试获取data_manager的引用
        if parent and hasattr(parent, 'app') and hasattr(parent.app, 'data_manager'):
            self.data_manager = parent.app.data_manager
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy
        from PyQt5.QtCore import QSize
        
        self.setWindowTitle("搜索结果")
        self.setMinimumWidth(850)
        self.setMinimumHeight(550)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建结果标签
        result_label = QLabel(f"找到 {len(self.results)} 个匹配项")
        result_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(result_label)
        
        # 创建结果列表
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # 修改为多选模式
        # 调整列表项高度，使其更宽松 - 增加行间距
        self.results_list.setStyleSheet("""
            QListWidget::item { 
                padding: 8px 4px; 
                min-height: 48px;
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
        self.results_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self.results_list)
        
        # 添加结果项，使用自定义格式显示
        for result in self.results:
            # 创建自定义项目，分开显示名称和路径
            path_display = '/'.join(result['path'][:-1]) if len(result['path']) > 0 else '根目录'
            
            # 创建列表项
            item = QListWidgetItem()
            
            # 设置图标
            if "type" in result["item"] and result["item"]["type"] == "folder":
                item.setIcon(icon_provider.get_icon("folder"))
            elif "item" in result and "icon" in result["item"] and result["item"].get("icon"):
                # 使用icon_provider加载图标，它能处理相对路径和绝对路径
                item.setIcon(icon_provider.get_icon(result["item"]["icon"]))
            else:
                item.setIcon(icon_provider.get_icon("globe"))
            
            # 存储完整数据到UserRole
            item.setData(Qt.UserRole, result)
            
            # 使用自定义布局显示
            widget = QWidget()
            item_layout = QHBoxLayout(widget)
            # 增加内边距
            item_layout.setContentsMargins(5, 8, 5, 8)
            item_layout.setSpacing(15)  # 增加控件之间的间距
            
            # 完整的提示文本（用于工具提示）
            tooltip_text = f"名称: {result['name']}\n位置: {path_display}"
            
            # 创建名称标签 - 靠左显示
            name_label = QLabel(result['name'])
            name_label.setStyleSheet("font-weight: bold; color: #000;")
            name_label.setMinimumWidth(150)  # 设置最小宽度
            # 移除最大宽度限制，允许名称完整显示
            name_label.setMaximumWidth(450)  # 设置最大宽度
            # 使用纯文本格式
            name_label.setTextFormat(Qt.PlainText)  # 使用纯文本格式
            name_label.setWordWrap(False)  # 禁用自动换行
            # 直接显示完整文本
            name_label.setText(result['name'])
            # 设置工具提示，显示完整内容
            name_label.setToolTip(result['name'])
            # 设置合适的大小策略，让名称可以占用更多空间
            name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            
            # 创建路径标签 - 靠左显示，使用暗灰色
            path_label = QLabel(f"  ▶ 网址位置: {path_display}")
            path_label.setStyleSheet("color: #666;")
            path_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 右对齐和垂直居中
            path_label.setMinimumWidth(150)  # 设置最小宽度
            path_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)  # 路径标签固定大小
            path_label.setTextFormat(Qt.PlainText)  # 使用纯文本格式
            path_label.setWordWrap(False)  # 禁用自动换行
            # 直接显示完整文本
            path_label.setText(f"  ▶ 网址位置: {path_display}")
            # 设置工具提示，显示完整路径
            path_label.setToolTip(f"  ▶ 网址位置: {path_display}")
            
            # 为整个item设置工具提示
            widget.setToolTip(tooltip_text)
            
            # 添加布局，使名称占据更多空间，路径相对固定
            item_layout.addWidget(name_label, 6)  # 分配比例为7
            item_layout.addWidget(path_label, 4)  # 分配比例为3
            
            # 设置列表项高度 - 增加高度确保内容完全显示
            item.setSizeHint(QSize(widget.sizeHint().width(), 48))
            
            # 添加项目到列表
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)
        
        # 添加操作按钮布局
        button_layout = QHBoxLayout()
        
        # 添加全选按钮
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)
        
        # 添加清除选择按钮
        clear_selection_btn = QPushButton("清除选择")
        clear_selection_btn.clicked.connect(self._clear_selection)
        button_layout.addWidget(clear_selection_btn)
        
        # 添加批量删除按钮
        delete_btn = QPushButton("删除选中的全部网址")
        delete_btn.setIcon(icon_provider.get_icon("delete"))
        delete_btn.clicked.connect(self._delete_selected)
        
        # 检查锁定状态
        main_win = self.parent()
        if main_win and hasattr(main_win, 'is_locked') and main_win.is_locked:
            delete_btn.setEnabled(False)
            delete_btn.setToolTip("当前处于锁定状态，无法删除项目")
            
        button_layout.addWidget(delete_btn)
        
        # 添加上下文菜单支持
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # 添加按钮布局
        layout.addLayout(button_layout)
        
        # 添加对话框按钮
        dialog_btn_layout = QHBoxLayout()
        
        # 状态标签，显示当前选中的项目数
        self.status_label = QLabel("未选择项目")
        dialog_btn_layout.addWidget(self.status_label)
        
        dialog_btn_layout.addStretch()
        
        # 添加导航按钮
        navigate_btn = QPushButton("打开所选网址的网页")
        navigate_btn.setDefault(True)
        navigate_btn.clicked.connect(self.accept)
        dialog_btn_layout.addWidget(navigate_btn)

        # 添加定位按钮
        locate_btn = QPushButton("定位到所选网址的标签")
        locate_btn.clicked.connect(lambda: self._locate_selected())
        dialog_btn_layout.insertWidget(dialog_btn_layout.count()-2, locate_btn)  # 插在导航按钮左侧

        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.reject)
        dialog_btn_layout.addWidget(close_btn)
        
        layout.addLayout(dialog_btn_layout)
        
        # 设置布局
        self.setLayout(layout)
        
        # 选择第一项
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
            self.results_list.setFocus()
        
        # 设置双击行为
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 连接选择变化信号
        self.results_list.itemSelectionChanged.connect(self._update_selection_status)
        
        # 设置快捷键
        self._setup_shortcuts()
        
        # 初始更新选择状态样式
        self._update_items_selection_style()
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        from PyQt5.QtGui import QKeySequence
        from PyQt5.QtWidgets import QShortcut
        
        # 全选快捷键 (Ctrl+A)
        select_all_shortcut = QShortcut(QKeySequence.SelectAll, self)
        select_all_shortcut.activated.connect(self._select_all)
        
        # 删除快捷键 (Delete)
        delete_shortcut = QShortcut(QKeySequence.Delete, self)
        
        # 检查锁定状态
        parent = self.parent()
        if parent and hasattr(parent, 'is_locked') and parent.is_locked:
            # 在锁定状态下禁用删除快捷键
            delete_shortcut.setEnabled(False)
        else:
            delete_shortcut.activated.connect(self._delete_selected)
    
    def _select_all(self):
        """全选"""
        self.results_list.selectAll()
        # 直接更新样式，不依赖于信号响应
        self._update_items_selection_style()
    
    def _clear_selection(self):
        """清除选择"""
        self.results_list.clearSelection()
        # 直接更新样式，不依赖于信号响应
        self._update_items_selection_style()
    
    def _update_selection_status(self):
        """更新选择状态"""
        count = len(self.results_list.selectedItems())
        if count == 0:
            self.status_label.setText("未选择项目")
        elif count == 1:
            self.status_label.setText("已选择 1 个项目")
        else:
            self.status_label.setText(f"已选择 {count} 个项目")
        
        # 更新所有项目的选择状态样式
        self._update_items_selection_style()
    
    def _update_items_selection_style(self):
        """更新所有项目的选择状态样式"""
        # 获取所有选中项的索引
        selected_indexes = [self.results_list.row(item) for item in self.results_list.selectedItems()]
        
        # 遍历所有项目，更新样式
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            widget = self.results_list.itemWidget(item)
            
            if widget:
                # 查找名称和路径标签
                name_label = None
                path_label = None
                
                for j in range(widget.layout().count()):
                    w = widget.layout().itemAt(j).widget()
                    if isinstance(w, QLabel):
                        # 通过标签文本内容判断而不是对齐方式
                        if w.text().startswith("  ▶ 网址位置:"):
                            path_label = w
                        else:
                            name_label = w
                
                # 根据选择状态设置样式
                if i in selected_indexes:
                    # 选中状态样式
                    widget.setStyleSheet("background-color: #e6f0fa;")
                    if name_label:
                        name_label.setStyleSheet("font-weight: bold; color: #000066;")
                    if path_label:
                        path_label.setStyleSheet("color: #333366;")
                else:
                    # 未选中状态样式
                    widget.setStyleSheet("")
                    if name_label:
                        name_label.setStyleSheet("font-weight: bold; color: #000;")
                    if path_label:
                        path_label.setStyleSheet("color: #666;")
    
    def _on_item_double_clicked(self, item):
        """处理项目双击事件"""
        self.selected_path = item.data(Qt.UserRole)["path"]
        self.accept()
    
    def _show_context_menu(self, pos):
        """显示上下文菜单"""
        selected = self.results_list.selectedItems()
        if not selected:
            return
        
        menu = QMenu(self)
        
        # 定位到此项
        if len(selected) == 1:
            locate_action = QAction("定位到此网址的标签", self)
            locate_action.triggered.connect(lambda: self._locate_selected(selected[0]))
            menu.addAction(locate_action)
        
        # 导航到选中项 - 单选时显示单个打开，多选时显示批量打开
        if len(selected) == 1:
            navigate_action = QAction("打开此项网址的网页", self)
            navigate_action.triggered.connect(lambda: self._navigate_to_selected(selected[0]))
            menu.addAction(navigate_action)
        else:
            # 多选时添加批量打开选项
            batch_navigate_action = QAction("打开所选网址的网页", self)
            batch_navigate_action.triggered.connect(self._batch_open_selected)
            menu.addAction(batch_navigate_action)
            
        menu.addSeparator()
        
        # 删除操作
        delete_action = QAction(icon_provider.get_icon("delete"), "删除选中的全部网址", self)
        delete_action.triggered.connect(self._delete_selected)
        
        # 检查锁定状态
        main_win = self.parent()
        if main_win and hasattr(main_win, 'is_locked') and main_win.is_locked:
            delete_action.setEnabled(False)
            delete_action.setToolTip("当前处于锁定状态，无法删除项目")
            
        menu.addAction(delete_action)
        
        menu.exec_(self.results_list.mapToGlobal(pos))
    
    def _navigate_to_selected(self, item):
        """导航到选中项"""
        self.selected_path = item.data(Qt.UserRole)["path"]
        self.accept()
    
    def _batch_open_selected(self):
        """批量打开选中的网址"""
        selected = self.results_list.selectedItems()
        if not selected:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "打开网址", "请选择要打开的网址")
            return
        
        # 统计URL类型的项目
        url_items = []
        for item in selected:
            result = item.data(Qt.UserRole)
            if result["item"]["type"] == "url":
                url_items.append(result)
        
        if not url_items:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "打开网址", "选中项中没有可打开的网址")
            return
        
        # 打开所有URL
        opened_count = 0
        import webbrowser
        from utils.url_utils import validate_url
        history_urls = []  # 用于收集需要添加到历史记录的URL
        
        for result in url_items:
            url = result["item"]["url"]
            # 验证URL
            is_valid, sanitized_url, message = validate_url(url)
            
            if is_valid:
                # 更新为清理后的URL
                if sanitized_url != url:
                    result["item"]["url"] = sanitized_url
                    url = sanitized_url
                
                # 打开URL
                webbrowser.open(url)
                opened_count += 1
                
                # 收集历史记录信息
                name = result["item"].get("name", "未知网站")
                path = result["path"][:-1] if result["path"] else []  # 去掉最后一个元素（项目名称）
                history_urls.append((url, name, path))
        
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
        
        # 显示提示消息
        from PyQt5.QtWidgets import QMessageBox
        if opened_count > 0:
            QMessageBox.information(self, "打开网址", f"已打开 {opened_count} 个网址")
        else:
            QMessageBox.warning(self, "打开网址", "没有成功打开任何网址")
    
    def _delete_selected(self):
        """删除选中项"""
        selected = self.results_list.selectedItems()
        if not selected:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "删除", "请选择要删除的项目")
            return
        
        if not self.data_manager:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "删除失败", "无法访问数据管理器")
            return
            
        # 检查锁定状态
        main_win = self.parent()
        if not main_win:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "删除失败", "无法获取主窗口实例")
            return
            
        if hasattr(main_win, 'is_locked') and main_win.is_locked:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "删除失败", "当前处于锁定状态，无法删除项目")
            return
        
        # 统计选中的项目类型
        folders = []
        urls = []
        
        for item in selected:
            result = item.data(Qt.UserRole)
            item_type = result["item"]["type"]
            path = result["path"]
            name = result["name"]
            
            if item_type == "folder":
                folders.append((path[:-1], name))
            else:
                urls.append((path[:-1], name))
        
        # 创建确认消息
        if len(selected) == 1:
            result = selected[0].data(Qt.UserRole)
            name = result["name"]
            if result["item"]["type"] == "folder":
                confirm_msg = f'您确定要删除文件夹"{name}"吗？这将删除其中的所有内容。'
            else:
                confirm_msg = f'您确定要删除网址"{name}"吗？'
        else:
            parts = []
            if urls:
                parts.append(f"{len(urls)}个网址")
            if folders:
                parts.append(f"{len(folders)}个文件夹")
            confirm_msg = f"您确定要删除{' 和 '.join(parts)}吗？"
        
        # 确认操作
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "删除确认",
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 执行删除
        try:
            # 保存备份（如果主窗口支持）
            parent = self.parent()
            if parent and hasattr(parent, '_save_undo_snapshot'):
                parent._save_undo_snapshot()
            
            # 删除操作
            deleted_count = 0
            
            # 先删除URLs
            for path, name in urls:
                if self.data_manager.delete_item(path, name):
                    deleted_count += 1
            
            # 再删除文件夹
            for path, name in folders:
                if self.data_manager.delete_item(path, name):
                    deleted_count += 1
            
            # 保存更改
            if deleted_count > 0:
                self.data_manager.save()
                self.data_manager.data_changed.emit()
                
                # 标记已执行删除操作
                self.deletion_performed = True
                
                # 更新结果列表
                for item in selected[:]:
                    row = self.results_list.row(item)
                    self.results_list.takeItem(row)
                
                # 更新结果标签
                remaining = self.results_list.count()
                result_text = f"找到 {remaining} 个匹配项"
                if deleted_count > 0:
                    result_text += f" (已删除 {deleted_count} 项)"
                
                # 找到并更新结果标签
                for i in range(self.layout().count()):
                    item = self.layout().itemAt(i)
                    if item.widget() and isinstance(item.widget(), QLabel):
                        item.widget().setText(result_text)
                        break
                
                QMessageBox.information(self, "删除成功", f"已成功删除 {deleted_count} 个项目")
            else:
                QMessageBox.warning(self, "删除失败", "没有删除任何项目")
            
        except Exception as e:
            logger.error(f"删除失败: {e}")
            QMessageBox.warning(self, "删除失败", f"删除过程中出错: {str(e)}")
    
    def accept(self):
        """接受对话框"""
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "导航提示", "请选择要操作的项目")
            return
        # This software was developed by Fan Huiyong, and all rights belong to Fan Huiyong himself. This software is only allowed for personal non-commercial use; it is prohibited for any organization or individual to use it for profit-making purposes without authorization.    
        # 如果只选择了一个项目，执行原有的导航逻辑
        if len(selected_items) == 1:
            # 获取完整的路径信息
            self.selected_path = selected_items[0].data(Qt.UserRole)["path"]
            # 确保selected_path不为空，否则可能导致导航失败
            if not self.selected_path:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "导航失败", "无法获取有效的路径信息")
                return
            super().accept()
            return
        
        # 如果选择了多个项目，执行批量打开逻辑
        self._batch_open_selected()
        # 不关闭对话框，让用户可以继续操作
    
    def get_selected_path(self):
        """获取选中的路径"""
        return self.selected_path

    def _locate_selected(self, item=None):
        """定位到主界面对应网址卡片并高亮显示"""
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
        # 获取选中项
        if item is None or isinstance(item, bool):
            selected = self.results_list.selectedItems()
            if not selected or len(selected) != 1:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "定位提示", "请仅选择一个网址进行定位")
                return
            item = selected[0]
        result = item.data(Qt.UserRole)
        path = result["path"][:-1]
        name = result["name"]
        # 切换目录树和卡片区
        main_win.folder_tree.select_path(path)
        main_win.bookmark_grid.set_current_path(path)
        # 高亮并选中卡片
        main_win.bookmark_grid.highlight_item(name)
        main_win.bookmark_grid.selected_items = [(name, result["item"]["type"])]
        main_win.bookmark_grid.refresh()
        # 滚动到中间
        for w, n, t in getattr(main_win.bookmark_grid, '_item_widgets', []):
            if n == name:
                w.set_selected(True)
                w.scrollToWidget = getattr(w, 'scrollToWidget', None)
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
        self.raise_()
        # 提示
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "定位成功", f"已定位到：{name}")

class SettingsDialog(QDialog):
    """设置对话框，显示和设置数据、图标、日志文件路径"""
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.selected_language_code = language_manager.get_current_language()  # 初始化为当前语言
        self.setWindowTitle(language_manager.tr("dialogs.settings_title"))
        self.setMinimumWidth(600)
        
        # 初始化配置管理器
        try:
            from utils.config_manager import ConfigManager
            self.config_manager = ConfigManager(self.app.config)
        except ImportError:
            logger.warning("配置管理器不可用")
            self.config_manager = None
        
        self.init_ui()

    def init_ui(self):
        from PyQt5.QtWidgets import QFormLayout, QLineEdit, QPushButton, QFileDialog, QHBoxLayout, QVBoxLayout, QLabel, QDialogButtonBox, QComboBox, QTabWidget, QWidget, QScrollArea
        
        # 创建主布局
        layout = QVBoxLayout()
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 创建基本路径选项卡
        basic_paths_tab = QWidget()
        basic_paths_layout = QVBoxLayout(basic_paths_tab)
        basic_form = QFormLayout()
        
        # 获取当前路径配置
        paths = self.app.config.get_all_paths()
        default_paths = self.app.config.get_default_paths()
        
        # 基本路径设置
        self.data_file_edit = QLineEdit(paths.get("data_file", ""))
        self.icon_dir_edit = QLineEdit(paths.get("icons_dir", ""))
        self.log_file_edit = QLineEdit(paths.get("log_file", ""))
        self.history_file_edit = QLineEdit(paths.get("history_file", ""))
        self.backup_dir_edit = QLineEdit(paths.get("backup_dir", ""))
        
        # 选择按钮
        data_btn = QPushButton(language_manager.tr("dialogs.choose_button"))
        icon_btn = QPushButton(language_manager.tr("dialogs.choose_button"))
        log_btn = QPushButton(language_manager.tr("dialogs.choose_button"))
        history_btn = QPushButton(language_manager.tr("dialogs.choose_button"))
        backup_btn = QPushButton(language_manager.tr("dialogs.choose_button"))
        
        # 连接按钮信号
        data_btn.clicked.connect(lambda: self._choose_file(self.data_file_edit, True))
        icon_btn.clicked.connect(lambda: self._choose_dir(self.icon_dir_edit))
        log_btn.clicked.connect(lambda: self._choose_file(self.log_file_edit, False))
        history_btn.clicked.connect(lambda: self._choose_file(self.history_file_edit, True))
        backup_btn.clicked.connect(lambda: self._choose_dir(self.backup_dir_edit))
        
        # 行布局
        data_layout = QHBoxLayout(); data_layout.addWidget(self.data_file_edit); data_layout.addWidget(data_btn)
        icon_layout = QHBoxLayout(); icon_layout.addWidget(self.icon_dir_edit); icon_layout.addWidget(icon_btn)
        log_layout = QHBoxLayout(); log_layout.addWidget(self.log_file_edit); log_layout.addWidget(log_btn)
        history_layout = QHBoxLayout(); history_layout.addWidget(self.history_file_edit); history_layout.addWidget(history_btn)
        backup_layout = QHBoxLayout(); backup_layout.addWidget(self.backup_dir_edit); backup_layout.addWidget(backup_btn)
        
        # 添加到表单
        basic_form.addRow(language_manager.tr("settings.data_file_label"), data_layout)
        basic_form.addRow(language_manager.tr("settings.icon_folder_label"), icon_layout)
        basic_form.addRow(language_manager.tr("settings.log_file_label"), log_layout)
        basic_form.addRow("历史记录文件：", history_layout)
        basic_form.addRow(language_manager.tr("settings.backup_folder_label"), backup_layout)
        
        # 添加备份说明
        backup_info = QLabel(language_manager.tr("settings.backup_info"))
        backup_info.setWordWrap(True)
        basic_form.addRow("", backup_info)
        
        # 默认路径信息
        default_paths_info = QLabel("默认路径设置：\n" +
            f"数据文件: {default_paths.get('data_file', '')}\n" +
            f"图标文件夹: {default_paths.get('icons_dir', '')}\n" +
            f"日志文件: {default_paths.get('log_file', '')}\n" +
            f"历史记录文件: {default_paths.get('history_file', '')}\n" +
            f"备份文件夹: {default_paths.get('backup_dir', '')}")
        default_paths_info.setWordWrap(True)
        
        # 添加表单和默认路径信息到基本路径选项卡
        basic_paths_layout.addLayout(basic_form)
        basic_paths_layout.addWidget(default_paths_info)
        
        # 创建高级路径选项卡
        advanced_paths_tab = QWidget()
        advanced_paths_layout = QVBoxLayout(advanced_paths_tab)
        advanced_form = QFormLayout()
        
        # 高级路径设置
        self.export_dir_edit = QLineEdit(paths.get("export_dir", ""))
        self.import_dir_edit = QLineEdit(paths.get("import_dir", ""))
        self.temp_dir_edit = QLineEdit(paths.get("temp_dir", ""))
        
        # 选择按钮
        export_btn = QPushButton(language_manager.tr("dialogs.choose_button"))
        import_btn = QPushButton(language_manager.tr("dialogs.choose_button"))
        temp_btn = QPushButton(language_manager.tr("dialogs.choose_button"))
        
        # 连接按钮信号
        export_btn.clicked.connect(lambda: self._choose_dir(self.export_dir_edit))
        import_btn.clicked.connect(lambda: self._choose_dir(self.import_dir_edit))
        temp_btn.clicked.connect(lambda: self._choose_dir(self.temp_dir_edit))
        
        # 行布局
        export_layout = QHBoxLayout(); export_layout.addWidget(self.export_dir_edit); export_layout.addWidget(export_btn)
        import_layout = QHBoxLayout(); import_layout.addWidget(self.import_dir_edit); import_layout.addWidget(import_btn)
        temp_layout = QHBoxLayout(); temp_layout.addWidget(self.temp_dir_edit); temp_layout.addWidget(temp_btn)
        
        # 添加到表单
        advanced_form.addRow("导出目录：", export_layout)
        advanced_form.addRow("导入目录：", import_layout)
        advanced_form.addRow("临时文件目录：", temp_layout)
        
        # 高级路径说明
        advanced_paths_info = QLabel("高级路径设置说明：\n" +
            "导出目录：用于保存导出的书签文件\n" +
            "导入目录：导入书签时的默认目录\n" +
            "临时文件目录：用于存储临时文件")
        advanced_paths_info.setWordWrap(True)
        
        # 添加表单和说明到高级路径选项卡
        advanced_paths_layout.addLayout(advanced_form)
        advanced_paths_layout.addWidget(advanced_paths_info)
        advanced_paths_layout.addStretch(1)
        
        # 创建语言设置选项卡
        language_tab = QWidget()
        language_layout = QVBoxLayout(language_tab)
        language_form = QFormLayout()
        
        # 语言选择下拉框
        self.language_combo = QComboBox()
        available_languages = language_manager.get_available_languages()
        current_language = language_manager.get_current_language()
        
        for code, name in available_languages.items():
            self.language_combo.addItem(name, code)
            if code == current_language:
                self.language_combo.setCurrentText(name)
        
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        
        # 添加到表单
        language_form.addRow(language_manager.tr("settings.language_label"), self.language_combo)
        
        # 语言设置说明
        language_info = QLabel("语言设置说明：\n" +
            "选择界面显示语言，更改后立即生效。")
        language_info.setWordWrap(True)
        
        # 添加表单和说明到语言设置选项卡
        language_layout.addLayout(language_form)
        language_layout.addWidget(language_info)
        language_layout.addStretch(1)
        
        # 添加选项卡到选项卡控件
        tab_widget.addTab(basic_paths_tab, "基本路径")
        tab_widget.addTab(advanced_paths_tab, "高级路径")
        tab_widget.addTab(language_tab, "语言设置")
        
        # 如果配置管理器可用，添加配置管理选项卡
        if self.config_manager:
            config_management_tab = self._create_config_management_tab()
            tab_widget.addTab(config_management_tab, "配置管理")
        
        # 添加选项卡控件到主布局
        layout.addWidget(tab_widget)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel | QDialogButtonBox.Reset)
        button_box.accepted.connect(self._save)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Reset).clicked.connect(self._reset_to_defaults)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

    def _choose_file(self, line_edit, is_json):
        from PyQt5.QtWidgets import QFileDialog
        if is_json:
            path, _ = QFileDialog.getSaveFileName(self, "选择数据文件", line_edit.text(), "JSON文件 (*.json);;所有文件 (*.*)")
        else:
            path, _ = QFileDialog.getSaveFileName(self, "选择日志文件", line_edit.text(), "日志文件 (*.log);;所有文件 (*.*)")
        if path:
            line_edit.setText(path)

    def _choose_dir(self, line_edit):
        from PyQt5.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "选择文件夹", line_edit.text())
        if path:
            line_edit.setText(path)

    def _on_language_changed(self, language_name):
        """语言切换处理"""
        try:
            # 记录选择的语言，但不立即切换
            # 等到用户点击保存时再真正切换语言
            available_languages = language_manager.get_available_languages()
            for code, name in available_languages.items():
                if name == language_name:
                    self.selected_language_code = code
                    logger.info(f"用户选择了语言: {name} ({code})")
                    break
        except Exception as e:
            logger.error(f"语言选择处理失败: {e}")

    def _save(self):
        try:
            # 收集所有路径设置
            paths_dict = {
                "data_file": self.data_file_edit.text().strip(),
                "icons_dir": self.icon_dir_edit.text().strip(),
                "log_file": self.log_file_edit.text().strip(),
                "history_file": self.history_file_edit.text().strip(),
                "backup_dir": self.backup_dir_edit.text().strip(),
                "export_dir": self.export_dir_edit.text().strip(),
                "import_dir": self.import_dir_edit.text().strip(),
                "temp_dir": self.temp_dir_edit.text().strip()
            }
            
            # 过滤空值，使用默认路径
            filtered_paths = {}
            for key, value in paths_dict.items():
                if value:  # 只保存非空路径
                    filtered_paths[key] = value
            
            # 使用新的set_paths方法
            self.app.set_paths(
                data_file=paths_dict["data_file"] or self.app.config.get_path("data_file"),
                icons_dir=paths_dict["icons_dir"] or self.app.config.get_path("icons_dir"),
                log_file=paths_dict["log_file"] or self.app.config.get_path("log_file"),
                history_file=paths_dict["history_file"] or self.app.config.get_path("history_file"),
                backup_dir=paths_dict["backup_dir"] or self.app.config.get_path("backup_dir"),
                export_dir=paths_dict["export_dir"] or self.app.config.get_path("export_dir"),
                import_dir=paths_dict["import_dir"] or self.app.config.get_path("import_dir"),
                temp_dir=paths_dict["temp_dir"] or self.app.config.get_path("temp_dir")
            )
            
            # 保存并切换语言设置
            if hasattr(self, 'selected_language_code') and self.selected_language_code:
                current_language = language_manager.get_current_language()
                if self.selected_language_code != current_language:
                    # 保存到配置系统
                    self.app.config.set("language", "current", self.selected_language_code)
                    self.app.config.save()
                    
                    # 同时保存到QSettings（向后兼容）
                    if hasattr(self.app, 'settings'):
                        self.app.settings.setValue("language", self.selected_language_code)
                    
                    # 切换语言
                    language_manager.set_language(self.selected_language_code)
                    logger.info(f"语言已切换到: {self.selected_language_code}")
            
            # 验证路径配置
            path_issues = self.app.config.validate_paths()
            if path_issues:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "路径配置警告", 
                                  f"以下路径配置可能存在问题：\n{chr(10).join(path_issues)}\n\n设置已保存，但请检查这些路径。")
            
            self.accept()
            
        except Exception as e:
            logger.error(f"保存设置时发生错误: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, language_manager.tr("messages.error_title"), 
                              f"{language_manager.tr('messages.operation_failed')}: {str(e)}")
    
    def _reset_to_defaults(self):
        """重置所有路径到默认值"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            
            # 确认对话框
            reply = QMessageBox.question(self, "确认重置", 
                                       "确定要将所有路径设置重置为默认值吗？\n这将清除所有自定义路径配置。",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 获取默认路径
                default_paths = self.app.config.get_default_paths()
                
                # 更新界面
                self.data_file_edit.setText(default_paths.get("data_file", ""))
                self.icon_dir_edit.setText(default_paths.get("icons_dir", ""))
                self.log_file_edit.setText(default_paths.get("log_file", ""))
                self.history_file_edit.setText(default_paths.get("history_file", ""))
                self.backup_dir_edit.setText(default_paths.get("backup_dir", ""))
                self.export_dir_edit.setText(default_paths.get("export_dir", ""))
                self.import_dir_edit.setText(default_paths.get("import_dir", ""))
                self.temp_dir_edit.setText(default_paths.get("temp_dir", ""))
                
                logger.info("路径设置已重置为默认值")
                
        except Exception as e:
            logger.error(f"重置路径设置时发生错误: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"重置失败: {str(e)}")
    
    def _create_config_management_tab(self):
        """创建配置管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 导入导出组
        import_export_group = QGroupBox("配置导入导出")
        import_export_layout = QGridLayout(import_export_group)
        
        # 导出配置
        export_btn = QPushButton("导出配置")
        export_btn.clicked.connect(self._export_config)
        import_export_layout.addWidget(QLabel("导出当前配置到文件:"), 0, 0)
        import_export_layout.addWidget(export_btn, 0, 1)
        
        # 导入配置
        import_btn = QPushButton("导入配置")
        import_btn.clicked.connect(self._import_config)
        import_export_layout.addWidget(QLabel("从文件导入配置:"), 1, 0)
        import_export_layout.addWidget(import_btn, 1, 1)
        
        layout.addWidget(import_export_group)
        
        # 备份管理组
        backup_group = QGroupBox("配置备份管理")
        backup_layout = QVBoxLayout(backup_group)
        
        # 备份按钮
        backup_btn_layout = QHBoxLayout()
        create_backup_btn = QPushButton("创建备份")
        create_backup_btn.clicked.connect(self._create_backup)
        backup_btn_layout.addWidget(create_backup_btn)
        
        clean_backup_btn = QPushButton("清理旧备份")
        clean_backup_btn.clicked.connect(self._clean_backups)
        backup_btn_layout.addWidget(clean_backup_btn)
        backup_btn_layout.addStretch()
        
        backup_layout.addLayout(backup_btn_layout)
        
        # 备份列表
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["备份名称", "创建时间", "操作"])
        self.backup_table.horizontalHeader().setStretchLastSection(True)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        backup_layout.addWidget(self.backup_table)
        
        layout.addWidget(backup_group)
        
        # 配置验证组
        validation_group = QGroupBox("配置验证")
        validation_layout = QVBoxLayout(validation_group)
        
        validate_btn = QPushButton("验证当前配置")
        validate_btn.clicked.connect(self._validate_config)
        validation_layout.addWidget(validate_btn)
        
        self.validation_text = QTextEdit()
        self.validation_text.setMaximumHeight(100)
        self.validation_text.setReadOnly(True)
        validation_layout.addWidget(self.validation_text)
        
        layout.addWidget(validation_group)
        
        # 刷新备份列表
        self._refresh_backup_list()
        
        return tab
    
    def _export_config(self):
        """导出配置"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出配置", "config_export.json", "JSON文件 (*.json)"
            )
            
            if file_path:
                if self.config_manager.export_config_to_file(file_path):
                    QMessageBox.information(self, "成功", f"配置已导出到: {file_path}")
                else:
                    QMessageBox.warning(self, "错误", "导出配置失败")
                    
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            QMessageBox.warning(self, "错误", f"导出配置失败: {str(e)}")
    
    def _import_config(self):
        """导入配置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入配置", "", "JSON文件 (*.json)"
            )
            
            if file_path:
                reply = QMessageBox.question(
                    self, "确认导入", 
                    "导入配置将覆盖当前设置，是否继续？\n\n当前配置将自动备份。",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    if self.config_manager.import_config_from_file(file_path):
                        QMessageBox.information(self, "成功", "配置导入成功，请重启应用程序以应用新配置")
                        self._refresh_ui_from_config()
                        self._refresh_backup_list()
                    else:
                        QMessageBox.warning(self, "错误", "导入配置失败")
                        
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            QMessageBox.warning(self, "错误", f"导入配置失败: {str(e)}")
    
    def _create_backup(self):
        """创建配置备份"""
        try:
            backup_file = self.config_manager.backup_current_config()
            if backup_file:
                QMessageBox.information(self, "成功", f"配置备份已创建: {backup_file}")
                self._refresh_backup_list()
            else:
                QMessageBox.warning(self, "错误", "创建备份失败")
                
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            QMessageBox.warning(self, "错误", f"创建备份失败: {str(e)}")
    
    def _clean_backups(self):
        """清理旧备份"""
        try:
            reply = QMessageBox.question(
                self, "确认清理", 
                "将保留最新的10个备份，删除其余备份文件，是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                deleted_count = self.config_manager.clean_old_backups(10)
                QMessageBox.information(self, "完成", f"已清理 {deleted_count} 个旧备份文件")
                self._refresh_backup_list()
                
        except Exception as e:
            logger.error(f"清理备份失败: {e}")
            QMessageBox.warning(self, "错误", f"清理备份失败: {str(e)}")
    
    def _refresh_backup_list(self):
        """刷新备份列表"""
        try:
            backups = self.config_manager.get_backup_list()
            self.backup_table.setRowCount(len(backups))
            
            for i, backup in enumerate(backups):
                # 备份名称
                name_item = QTableWidgetItem(backup["name"])
                self.backup_table.setItem(i, 0, name_item)
                
                # 创建时间
                time_str = backup["timestamp"][:19].replace('T', ' ')
                time_item = QTableWidgetItem(time_str)
                self.backup_table.setItem(i, 1, time_item)
                
                # 操作按钮
                restore_btn = QPushButton("恢复")
                restore_btn.clicked.connect(lambda checked, f=backup["file"]: self._restore_backup(f))
                self.backup_table.setCellWidget(i, 2, restore_btn)
                
        except Exception as e:
            logger.error(f"刷新备份列表失败: {e}")
    
    def _restore_backup(self, backup_file):
        """恢复备份"""
        try:
            reply = QMessageBox.question(
                self, "确认恢复", 
                "恢复备份将覆盖当前配置，是否继续？\n\n当前配置将自动备份。",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.config_manager.restore_config_from_backup(backup_file):
                    QMessageBox.information(self, "成功", "配置恢复成功，请重启应用程序以应用配置")
                    self._refresh_ui_from_config()
                    self._refresh_backup_list()
                else:
                    QMessageBox.warning(self, "错误", "恢复配置失败")
                    
        except Exception as e:
            logger.error(f"恢复配置失败: {e}")
            QMessageBox.warning(self, "错误", f"恢复配置失败: {str(e)}")
    
    def _validate_config(self):
        """验证配置"""
        try:
            result = self.config_manager.validate_current_config()
            
            validation_text = ""
            if result["errors"]:
                validation_text += "错误:\n"
                for error in result["errors"]:
                    validation_text += f"• {error}\n"
                validation_text += "\n"
            
            if result["warnings"]:
                validation_text += "警告:\n"
                for warning in result["warnings"]:
                    validation_text += f"• {warning}\n"
                validation_text += "\n"
            
            if not result["errors"] and not result["warnings"]:
                validation_text = "配置验证通过，没有发现问题。"
            
            self.validation_text.setText(validation_text)
            
            # 显示消息框
            if result["errors"]:
                QMessageBox.warning(self, "配置验证", f"发现 {len(result['errors'])} 个错误")
            elif result["warnings"]:
                QMessageBox.information(self, "配置验证", f"发现 {len(result['warnings'])} 个警告")
            else:
                QMessageBox.information(self, "配置验证", "配置验证通过")
                
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            QMessageBox.warning(self, "错误", f"配置验证失败: {str(e)}")
    
    def _refresh_ui_from_config(self):
        """从配置刷新UI"""
        try:
            # 刷新路径输入框
            paths = self.app.config.get_all_paths()
            self.data_file_edit.setText(paths.get("data_file", ""))
            self.icon_dir_edit.setText(paths.get("icons_dir", ""))
            self.log_file_edit.setText(paths.get("log_file", ""))
            self.backup_dir_edit.setText(paths.get("backup_dir", ""))
            self.export_dir_edit.setText(paths.get("export_dir", ""))
            self.import_dir_edit.setText(paths.get("import_dir", ""))
            self.temp_dir_edit.setText(paths.get("temp_dir", ""))
            
            # 刷新语言选择
            current_lang = self.app.config.get('language', 'current', 'zh')
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == current_lang:
                    self.language_combo.setCurrentIndex(i)
                    break
                    
        except Exception as e:
            logger.error(f"刷新UI失败: {e}")
    
    def update_ui_texts(self):
        """更新界面文本（语言切换时调用）"""
        try:
            self.setWindowTitle(language_manager.tr("dialogs.settings_title"))
            # 同步下拉框选中项为当前语言
            if hasattr(self, 'language_combo') and self.language_combo:
                current_language = language_manager.get_current_language()
                for i in range(self.language_combo.count()):
                    code = self.language_combo.itemData(i)
                    if code == current_language:
                        self.language_combo.setCurrentIndex(i)
                        break
            # 注意：由于表单标签是在初始化时设置的，我们不会在这里重新设置
            # 如果需要完全动态更新，需要重构表单布局
        except Exception as e:
            logger.error(f"更新设置对话框界面文本时发生错误: {e}")

class ExportDialog(QDialog):
    def __init__(self, parent=None, default_dir=None, current_path=None):
        super().__init__(parent)
        self.setWindowTitle("导出书签/数据/日志")
        # 增加窗口尺寸
        self.resize(550, 320)
        self.selected_type = None
        self.selected_path = None
        self.export_directory = None
        
        # 获取自动备份文件夹路径
        try:
            # 从父窗口获取app对象
            self.app = parent.app if hasattr(parent, 'app') else None
            
            if self.app and hasattr(self.app, 'backup_dir') and self.app.backup_dir:
                # 优先使用app对象中的备份路径
                self.default_dir = self.app.backup_dir
            else:
                # 回退到QSettings
                from PyQt5.QtCore import QSettings
                settings = QSettings("URL Navigator", "URL Navigator")
                backup_dir = settings.value("backup/directory", None)
                if backup_dir and os.path.exists(backup_dir):
                    self.default_dir = backup_dir
                else:
                    self.default_dir = default_dir or os.path.expanduser("~")
        except Exception:
            self.default_dir = default_dir or os.path.expanduser("~")
        
        self.current_path = current_path
        self.selected_folder = None
        self._init_ui()

    def _init_ui(self):
        from PyQt5.QtGui import QFont
        # 设置更大的字体
        font = QFont()
        font.setPointSize(10)  # 增加默认字体大小
        self.setFont(font)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)  # 增加控件之间的间距
        layout.setContentsMargins(15, 20, 15, 20)  # 增加边距
        
        # 标题标签
        title_label = QLabel("请选择要导出的内容类型和保存位置")
        title_label.setFont(QFont(font.family(), 11, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建表单布局以确保对齐
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 左对齐标签
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form_layout.setHorizontalSpacing(20)  # 增加水平间距
        form_layout.setVerticalSpacing(15)    # 增加垂直间距
        form_layout.setContentsMargins(15, 10, 15, 0)  # 设置内边距，使内容更对齐
        
        # 创建一个水平布局的容器
        field_width = 410  # 设置一个统一的宽度变量
        
        # 数据导出范围
        scope_label = QLabel("数据导出范围：")
        scope_layout = QHBoxLayout()
        scope_layout.setSpacing(10)
        scope_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scope_combo = QComboBox()
        self.scope_combo.setMinimumHeight(28)
        self.scope_combo.setFixedWidth(200)  # 使用固定宽度
        self.scope_combo.addItems(["全部导出", "导出部分数据"])
        button_font = QFont(font.family(), 10)
        self.scope_combo.setFont(button_font)
        
        # 添加选择目录按钮
        self.select_folder_btn = QPushButton("选择需要导出的书签目录")
        self.select_folder_btn.setMinimumHeight(28)
        self.select_folder_btn.setFont(button_font)
        self.select_folder_btn.setFixedWidth(200)  # 使用固定宽度，确保对齐
        self.select_folder_btn.clicked.connect(self._select_export_folder)
        self.select_folder_btn.setEnabled(False)
        
        scope_layout.addWidget(self.scope_combo)
        scope_layout.addWidget(self.select_folder_btn)
        scope_layout.addStretch(1)
        
        form_layout.addRow(scope_label, scope_layout)
        
        # 显示选中的文件夹 - 移动到数据导出范围和导出文件类型之间
        self.selected_folder_label = QLabel("")
        # 创建一个粗体字体用于显示选中的文件夹
        bold_font = QFont(font.family(), 10, QFont.Bold)
        self.selected_folder_label.setFont(bold_font)
        self.selected_folder_label.setStyleSheet("color: #000;")  # 设置为黑色
        # 为选中的文件夹标签创建一个专门的行
        folder_layout = QHBoxLayout()
        folder_layout.setContentsMargins(135, 5, 0, 5)  # 左边距与标签对齐，调整上下边距
        folder_layout.addWidget(self.selected_folder_label)
        folder_layout.addStretch(1)
        # 将此布局添加到表单布局中
        empty_label = QLabel("")  # 空标签占位
        form_layout.addRow(empty_label, folder_layout)
        
        # 导出类型选择
        type_label = QLabel("导出文件类型：")
        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(28)
        self.type_combo.setFixedWidth(field_width)  # 使用固定宽度
        self.type_combo.addItems(["HTML书签文件", "原型数据文件（JSON）", "日志文件"])
        self.type_combo.setFont(button_font)
        form_layout.addRow(type_label, self.type_combo)
        
        # 路径选择
        path_label = QLabel("导出文件位置：")
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        self.path_edit = QLineEdit()
        self.path_edit.setMinimumHeight(28)
        self.path_edit.setFixedWidth(330)  # 使用固定宽度
        self.path_edit.setText(self.default_dir)  # 只显示目录，不含文件名
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setMinimumHeight(28)
        browse_btn.setFixedWidth(70)
        browse_btn.setFont(button_font)
        browse_btn.clicked.connect(self._browse)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        path_layout.addStretch(1)  # 添加弹性空间，确保控件左对齐
        
        form_layout.addRow(path_label, path_layout)
        
        # 文件名选择
        filename_label = QLabel("导出文件名称：")
        self.filename_edit = QLineEdit()
        self.filename_edit.setMinimumHeight(28)
        self.filename_edit.setFixedWidth(field_width)  # 使用固定宽度
        form_layout.addRow(filename_label, self.filename_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)  # 增加按钮之间的间距
        export_all_btn = QPushButton("导出全部书签（HTML\\JSON）和日志3个文件")
        export_all_btn.setMinimumHeight(32)  # 增加按钮高度
        export_all_btn.setFont(QFont(button_font.family(), 10, QFont.Bold))
        export_all_btn.clicked.connect(self.accept_all)
        btn_layout.addWidget(export_all_btn)
        
        btn_layout.addStretch(1)
        
        ok_btn = QPushButton("导出")
        ok_btn.setMinimumHeight(32)  # 增加按钮高度
        ok_btn.setMinimumWidth(80)   # 设置按钮宽度
        ok_btn.setFont(button_font)
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(32)  # 增加按钮高度
        cancel_btn.setMinimumWidth(80)   # 设置按钮宽度
        cancel_btn.setFont(button_font)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # 说明文字
        help_text = QLabel("注：导出的文件将根据导出设置命名保存到指定位置")
        help_text.setAlignment(Qt.AlignCenter)
        help_text.setStyleSheet("color: #666;")
        layout.addWidget(help_text)

        # 连接信号
        self.type_combo.currentIndexChanged.connect(self._update_default_name)
        self.scope_combo.currentIndexChanged.connect(self._update_scope)
        self._update_default_name()

    def _update_scope(self):
        """根据导出范围更新界面"""
        if self.scope_combo.currentIndex() == 1:  # 导出部分数据
            self.select_folder_btn.setEnabled(True)
            # 如果有当前路径，默认显示当前路径
            if self.current_path and not self.selected_folder:
                folder_name = self.current_path[-1] if self.current_path else ""
                self.selected_folder = folder_name
                self.selected_folder_label.setText(f"已选择导出目录: {folder_name}")
        else:
            self.select_folder_btn.setEnabled(False)
            self.selected_folder = None
            self.selected_folder_label.setText("")
        self._update_default_name()

    def _select_export_folder(self):
        """选择需要导出的书签目录"""
        from ui.dialogs import SelectFolderDialog
        parent = self.parent()
        app = parent.app if hasattr(parent, 'app') else None
        
        if app:
            dialog = SelectFolderDialog(app.data_manager, self.current_path, self)
            if dialog.exec_():
                selected_path = dialog.get_selected_path()
                if selected_path:
                    self.selected_folder = selected_path[-1]
                    self.export_directory = selected_path
                    self.selected_folder_label.setText(f"已选择导出目录: {self.selected_folder}")
                    self._update_default_name()

    def _update_default_name(self):
        """更新默认文件名"""
        idx = self.type_combo.currentIndex()
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        time_str = datetime.now().strftime("%H%M%S")
        
        folder_name = ""
        if self.scope_combo.currentIndex() == 1 and self.selected_folder:
            folder_name = f"{self.selected_folder}_"
        
        if idx == 0:
            extension = ".html"
        elif idx == 1:
            extension = ".json"
        else:
            extension = ".log"
            
        filename = f"{date_str}_{time_str}_{folder_name}bookmarks{extension}"
        self.filename_edit.setText(filename)
        # 不更新path_edit，保持目录路径不变

    def _browse(self):
        """选择导出文件夹位置"""
        directory = QFileDialog.getExistingDirectory(self, "选择导出文件夹", self.path_edit.text())
        if directory:
            self.path_edit.setText(directory)
            self._update_default_name()  # 更新文件名

    def get_export_path(self):
        """返回完整的导出路径（文件夹路径+文件名）"""
        directory = self.path_edit.text().strip()
        filename = self.filename_edit.text().strip()
        
        if not directory or not filename:
            return ''
            
        return os.path.join(directory, filename)

    def get_export_type(self):
        return self.type_combo.currentIndex()

    def get_export_scope(self):
        """返回导出范围"""
        return self.scope_combo.currentIndex()  # 0: 全部导出, 1: 导出部分数据
    
    def get_export_directory(self):
        """返回要导出的目录"""
        return self.export_directory

    def accept_all(self):
        self.selected_type = 'all'
        super().accept()

# 添加用于选择导出文件夹的对话框
class SelectFolderDialog(QDialog):
    def __init__(self, data_manager, current_path=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择要导出的书签目录")
        self.resize(350, 500)
        self.data_manager = data_manager
        self.current_path = current_path
        self.selected_path = None
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 文件夹树
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self._populate_tree()
        layout.addWidget(self.tree)
        
        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch(1)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def _populate_tree(self):
        """填充文件夹树"""
        self.tree.clear()
        
        def add_folder_items(parent_item, items, path):
            for name, item in items.items():
                if item["type"] == "folder":
                    tree_item = QTreeWidgetItem(parent_item)
                    tree_item.setText(0, name)
                    tree_item.setIcon(0, icon_provider.get_icon("folder"))
                    tree_item.setData(0, Qt.UserRole, {"path": path, "name": name})
                    add_folder_items(tree_item, item["children"], path + [name])
        
        add_folder_items(self.tree, self.data_manager.data, [])
        
        # 展开当前路径
        if self.current_path:
            self._select_path(self.current_path)
    
    def _select_path(self, path):
        """根据路径选择项目"""
        items = self.tree.findItems(path[0], Qt.MatchExactly, 0)
        if not items:
            return
            
        item = items[0]
        self.tree.setCurrentItem(item)
        
        for i in range(1, len(path)):
            found = False
            for j in range(item.childCount()):
                child = item.child(j)
                if child.text(0) == path[i]:
                    item = child
                    self.tree.setCurrentItem(item)
                    item.setExpanded(True)
                    found = True
                    break
            if not found:
                break
    
    def get_selected_path(self):
        """获取选中的路径"""
        item = self.tree.currentItem()
        if not item:
            return None
            
        path = []
        while item:
            path.insert(0, item.text(0))
            item = item.parent()
            
        return path