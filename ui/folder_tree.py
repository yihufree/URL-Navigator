#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QAction, 
    QMessageBox, QInputDialog, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QDrag, QPixmap, QPainter, QColor, QCursor
from ui.icons import icon_provider

logger = logging.getLogger(__name__)

class FolderTreeWidget(QTreeWidget):
    """文件夹树视图"""
    
    # 定义信号
    path_changed = pyqtSignal(list)
    # 添加新信号，表示清除选择
    selection_cleared = pyqtSignal()
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.clipboard_data = None  # 用于保存复制的项目数据
        self.main_window = None  # 存储主窗口引用
        
        self.init_ui()
        
        # 连接数据变化信号
        self.data_manager.data_changed.connect(self.refresh)
    
    def init_ui(self):
        """初始化UI"""
        # 设置树控件属性
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.InternalMove)
        
        # 设置上下文菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # 连接项目点击信号
        self.itemClicked.connect(self._on_item_clicked)
        
        # 刷新显示
        self.refresh()
    
    def refresh(self):
        """刷新显示"""
        # 保存当前选中的路径
        selected_path = self.get_selected_path()
        # 清空外部根目录bar
        bar = getattr(self, 'external_root_bar', None)
        if bar is not None:
            while bar.count():
                item = bar.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
        # 清除所有项目
        self.clear()
        # 获取所有根目录名
        root_names = [name for name, item in self.data_manager.data.items() if item["type"] == "folder"]
        # 渲染根目录按钮
        for name in root_names:
            btn = QPushButton(name)
            btn.setFlat(True)
            btn.setStyleSheet("font-weight:bold;")
            btn.clicked.connect(self._create_root_shower(name))
            if bar is not None:
                bar.addWidget(btn)
        if bar is not None:
            bar.addStretch(1)
        
        # 显示所有根目录的内容
        self._show_all_roots(select_path=selected_path)
    
    def _show_all_roots(self, select_path=None):
        """显示所有根目录下内容"""
        self.clear()
        self.setColumnCount(2)
        self.header().setSectionResizeMode(0, self.header().ResizeToContents)
        self.header().setSectionResizeMode(1, self.header().Fixed)
        self.setColumnWidth(1, 70)
        self.header().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 遍历并显示所有根目录
        for root_name, item in sorted(self.data_manager.data.items()):
            if item["type"] != "folder":
                continue
                
            tree_item = QTreeWidgetItem(self)
            # 统计下一级子目录和所有下级网址卡片数量
            children = item["children"]
            subdir_count = sum(1 for v in children.values() if v["type"] == "folder")
            def count_urls(d):
                cnt = 0
                for v in d.values():
                    if v["type"] == "url":
                        cnt += 1
                    elif v["type"] == "folder":
                        cnt += count_urls(v["children"])
                return cnt
            url_count = count_urls(children)
            # 格式化显示
            if subdir_count > 0:
                stat_text = f"{subdir_count}类{url_count}个"
            else:
                stat_text = f"{url_count}个"
            tree_item.setText(0, root_name)
            tree_item.setText(1, stat_text)
            tree_item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
            tree_item.setIcon(0, icon_provider.get_icon("folder"))
            tree_item.setData(0, Qt.UserRole, {"path": [], "name": root_name, "item": item})
            font = tree_item.font(0)
            font.setPointSizeF(font.pointSizeF() * 1.3)
            tree_item.setFont(0, font)
            self._add_folder_items(tree_item, item["children"], [root_name], font)
        
        # 恢复选中状态
        if select_path:
            self.select_path(select_path)
    
    def _add_folder_items(self, parent_item, items, path, font=None):
        """递归添加文件夹项目"""
        for name, item in items.items():
            if item["type"] == "folder":
                tree_item = QTreeWidgetItem(parent_item)
                # 统计下一级子目录和所有下级网址卡片数量
                children = item["children"]
                subdir_count = sum(1 for v in children.values() if v["type"] == "folder")
                def count_urls(d):
                    cnt = 0
                    for v in d.values():
                        if v["type"] == "url":
                            cnt += 1
                        elif v["type"] == "folder":
                            cnt += count_urls(v["children"])
                    return cnt
                url_count = count_urls(children)
                # 格式化显示
                if subdir_count > 0:
                    stat_text = f"{subdir_count}类{url_count}个"
                else:
                    stat_text = f"{url_count}个"
                tree_item.setText(0, name)
                tree_item.setText(1, stat_text)
                tree_item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
                tree_item.setIcon(0, icon_provider.get_icon("folder"))
                tree_item.setData(0, Qt.UserRole, {"path": path, "name": name, "item": item})
                # 设置字体
                if font is not None:
                    tree_item.setFont(0, font)
                # 递归添加子项目
                self._add_folder_items(tree_item, item["children"], path + [name], font)
    
    def _on_item_clicked(self, item, column):
        """处理项目点击事件"""
        data = item.data(0, Qt.UserRole)
        if data:
            path = data["path"] + [data["name"]]
            self.path_changed.emit(path)
    
    def _show_context_menu(self, pos):
        """显示上下文菜单"""
        item = self.itemAt(pos)
        if not item:
            # 如果点击在空白区域，显示根目录的上下文菜单
            menu = QMenu(self)
            add_folder_action = QAction(icon_provider.get_icon("folder-add"), "添加文件夹", self)
            add_folder_action.triggered.connect(lambda: self._add_root_folder())
            menu.addAction(add_folder_action)
            
            if self.clipboard_data:
                paste_action = QAction(icon_provider.get_icon("paste"), "粘贴", self)
                paste_action.triggered.connect(lambda: self._paste_item_to_root())
                menu.addAction(paste_action)
            
            menu.exec_(self.mapToGlobal(pos))
            return
        
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        
        menu = QMenu(self)
        
        # 添加菜单项
        add_folder_action = QAction(icon_provider.get_icon("folder-add"), "添加子文件夹", self)
        add_folder_action.triggered.connect(lambda: self._add_subfolder(data))
        menu.addAction(add_folder_action)
        
        add_url_action = QAction(icon_provider.get_icon("globe"), "添加网址", self)
        add_url_action.triggered.connect(lambda: self._add_url(data))
        menu.addAction(add_url_action)
        
        menu.addSeparator()
        
        # 添加导出选项
        export_action = QAction(icon_provider.get_icon("export"), "导出", self)
        export_action.triggered.connect(lambda: self._export_folder(data))
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # 添加复制、粘贴选项
        copy_action = QAction(icon_provider.get_icon("copy"), "复制", self)
        copy_action.triggered.connect(lambda: self._copy_folder(data))
        menu.addAction(copy_action)
        
        paste_action = QAction(icon_provider.get_icon("paste"), "粘贴", self)
        def do_paste():
            # 优先调用主窗口的粘贴逻辑（如有），否则调用自身
            if hasattr(self, 'main_window') and hasattr(self.main_window, '_paste_selected'):
                # 切换当前目录到目标目录
                if hasattr(self.main_window, 'folder_tree'):
                    path = data["path"] + [data["name"]]
                    self.main_window.folder_tree.select_path(path)
                self.main_window._paste_selected()
            else:
                self._paste_item(data)
        paste_action.triggered.connect(do_paste)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        rename_action = QAction(icon_provider.get_icon("edit"), "重命名", self)
        rename_action.triggered.connect(lambda: self._rename_folder(data))
        menu.addAction(rename_action)
        
        delete_action = QAction(icon_provider.get_icon("delete"), "删除", self)
        delete_action.triggered.connect(lambda: self._delete_folder(data))
        menu.addAction(delete_action)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def _add_subfolder(self, data):
        """添加子文件夹"""
        path = data["path"] + [data["name"]]
        
        name, ok = QInputDialog.getText(self, "添加子文件夹", "请输入文件夹名称:")
        if ok and name:
            success = self.data_manager.add_folder(path, name)
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加文件夹，可能是名称已存在")
    
    def _add_url(self, data):
        """添加网址"""
        path = data["path"] + [data["name"]]
        
        from ui.dialogs import AddUrlDialog
        dialog = AddUrlDialog(self.parent().parent().app.favicon_service, path, self)
        
        if dialog.exec_():
            url_data = dialog.get_data()
            
            success = self.data_manager.add_url(
                path,
                url_data["name"],
                url_data["url"],
                url_data["icon"]
            )
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加网址，可能是名称已存在")
    
    def _rename_folder(self, data):
        """重命名文件夹"""
        path = data["path"]
        old_name = data["name"]
        
        new_name, ok = QInputDialog.getText(
            self, 
            "重命名文件夹", 
            "请输入新的文件夹名称:",
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            success = self.data_manager.update_item(path, old_name, new_name, {})
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "重命名失败", "无法重命名文件夹，可能是名称已存在")
    
    def _delete_folder(self, data):
        """删除文件夹"""
        path = data["path"]
        name = data["name"]
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除文件夹 {name} 及其所有内容吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.data_manager.delete_item(path, name)
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "删除失败", "无法删除文件夹")
    
    def _export_folder(self, data):
        """导出文件夹"""
        path = data["path"] + [data["name"]]
        
        # 使用存储的主窗口引用
        if self.main_window and hasattr(self.main_window, '_export_bookmarks'):
            # 打开导出对话框，预选当前文件夹
            try:
                from ui.dialogs import ExportDialog
                dialog = ExportDialog(self.main_window, default_dir=None, current_path=path)
                dialog.scope_combo.setCurrentIndex(1)  # 设置为"导出部分数据"
                dialog._update_scope()  # 更新界面
                
                if dialog.exec_():
                    # 获取导出类型和路径
                    export_type = dialog.get_export_type()  # 0:HTML, 1:JSON, 2:日志
                    export_path = dialog.get_export_path()
                    export_scope = dialog.get_export_scope()  # 0:全部导出, 1:导出部分数据
                    export_directory = dialog.get_export_directory() or path  # 如果未选择目录，使用当前目录
                    
                    if not export_path:
                        return
                        
                    # 调用主窗口的导出方法
                    self.main_window._execute_export(export_type, export_path, export_scope, export_directory, dialog.selected_type)
            except Exception as e:
                # 导出出错时显示错误信息
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "导出错误", f"导出文件夹时出错：{str(e)}")
        else:
            # 如果找不到主窗口或主窗口没有导出方法，显示错误提示
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "功能不可用", "导出功能目前不可用，请使用顶部工具栏的'导出'按钮。")
    
    def get_selected_path(self):
        """获取当前选中的路径"""
        selected_items = self.selectedItems()
        if not selected_items:
            return None
        
        item = selected_items[0]
        data = item.data(0, Qt.UserRole)
        if not data:
            return None
        
        return data["path"] + [data["name"]]
    
    def select_path(self, path):
        """选择指定路径"""
        if not path:
            # 如果路径为空，清除选择并返回
            self.clearSelection()
            return
        
        # 查找匹配的项目
        item = self._find_item_by_path(path)
        if item:
            # 展开所有父项目
            parent = item
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()
            
            # 选择并滚动到该项目
            self.setCurrentItem(item)
            self.scrollToItem(item)
        else:
            logger.warning(f"路径不存在: {'/'.join(path)}")
    
    def _find_item_by_path(self, path):
        """查找指定路径的项目"""
        if not path:
            return None
        
        # 查找第一级项目
        target_name = path[0]
        target_item = None
        
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.text(0) == target_name:
                target_item = item
                break
        
        if not target_item:
            return None
        
        # 如果路径只有一个级别，直接返回
        if len(path) == 1:
            return target_item
        
        # 递归查找子路径
        for i in range(1, len(path)):
            found = False
            for j in range(target_item.childCount()):
                child = target_item.child(j)
                if child.text(0) == path[i]:
                    target_item = child
                    found = True
                    break
            
            if not found:
                return None
        
        return target_item
    
    def dragEnterEvent(self, event):
        """处理拖放进入事件"""
        if (event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist") or 
            event.mimeData().hasFormat("application/x-bookmark-item") or 
            event.mimeData().hasFormat("application/x-bookmark-items")):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """处理拖放移动事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            # 内部拖放处理
            # 获取目标项目
            target_item = self.itemAt(event.pos())
            
            if target_item:
                # 只有文件夹可以作为拖放目标
                data = target_item.data(0, Qt.UserRole)
                if data and data["item"]["type"] == "folder":
                    # 检查是否将文件夹拖动到自己或其子文件夹
                    source_item = self.currentItem()
                    if source_item:
                        source_data = source_item.data(0, Qt.UserRole)
                        if source_data:
                            # 只有当源是文件夹时才需要检查
                            if source_data["item"]["type"] == "folder":
                                # 检查目标是否是源的子文件夹
                                source_path = source_data["path"] + [source_data["name"]]
                                target_path = data["path"] + [data["name"]]
                                
                                # 检查目标路径是否是源路径的子路径
                                if len(target_path) >= len(source_path):
                                    is_subpath = True
                                    for i in range(len(source_path)):
                                        if i >= len(target_path) or source_path[i] != target_path[i]:
                                            is_subpath = False
                                            break
                                    
                                    if is_subpath:
                                        event.ignore()
                                        return
                    
                    event.acceptProposedAction()
                else:
                    event.ignore()
            else:
                # 允许拖放到空白区域（作为根级文件夹）
                event.acceptProposedAction()
        elif event.mimeData().hasFormat("application/x-bookmark-item") or event.mimeData().hasFormat("application/x-bookmark-items"):
            # 支持单项和批量拖拽
            target_item = self.itemAt(event.pos())
            if target_item:
                data = target_item.data(0, Qt.UserRole)
                if data and data["item"]["type"] == "folder":
                        event.acceptProposedAction()
                else:
                    event.ignore()
            else:
                event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """处理拖放事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            # 内部拖放处理
            # 获取源项目
            source_item = self.currentItem()
            if not source_item:
                event.ignore()
                return
            
            # 获取源数据
            source_data = source_item.data(0, Qt.UserRole)
            if not source_data:
                event.ignore()
                return
            
            # 获取目标项目
            target_item = self.itemAt(event.pos())
            
            # 如果目标是空白区域，移动到根目录
            if target_item is None:
                success = self.data_manager.move_item(
                    source_data["path"],
                    source_data["name"],
                    []  # 移动到根目录
                )
            else:
                # 获取目标数据
                target_data = target_item.data(0, Qt.UserRole)
                if not target_data:
                    event.ignore()
                    return
                
                # 移动项目
                success = self.data_manager.move_item(
                    source_data["path"],
                    source_data["name"],
                    target_data["path"] + [target_data["name"]]
                )
            
            if success:
                self.data_manager.save()
                event.acceptProposedAction()
            else:
                event.ignore()
        elif event.mimeData().hasFormat("application/x-bookmark-items"):
            # 批量拖拽
            import json
            try:
                items = json.loads(bytes(event.mimeData().data("application/x-bookmark-items")).decode("utf-8"))
                target_item = self.itemAt(event.pos())
                if target_item is None:
                    target_path = []
                else:
                    target_data = target_item.data(0, Qt.UserRole)
                    if not target_data:
                        event.ignore()
                        return
                    target_path = target_data["path"] + [target_data["name"]]
                all_success = True
                for item in items:
                    source_path = item["path"]
                    source_name = item["name"]
                    # 跳过同目录
                    if source_path == target_path:
                        continue
                    success = self.data_manager.move_item(source_path, source_name, target_path)
                    if not success:
                        all_success = False
                self.data_manager.save()
                if all_success:
                    event.acceptProposedAction()
                else:
                    QMessageBox.warning(self, "部分移动失败", "部分项目移动失败，可能是名称冲突或路径无效")
                    event.acceptProposedAction()
            except Exception as e:
                logger.error(f"批量拖放事件出错: {e}")
                QMessageBox.warning(self, "拖放错误", f"批量拖放事件出错: {str(e)}")
                event.ignore()
        elif event.mimeData().hasFormat("application/x-bookmark-item"):
            # 从网格拖放到树
            try:
                mime_data = event.mimeData().data("application/x-bookmark-item").data().decode()
                parts = mime_data.split("|")
                
                if len(parts) >= 3:
                    source_path_str = parts[0]
                    source_name = parts[1]
                    source_type = parts[2]
                    
                    source_path = source_path_str.split(",") if source_path_str and source_path_str != "" else []
                    
                    # 获取目标项目
                    target_item = self.itemAt(event.pos())
                    
                    if target_item is None:
                        # 拖放到空白区域，移动到根目录
                        target_path = []
                    else:
                        # 获取目标数据
                        target_data = target_item.data(0, Qt.UserRole)
                        if not target_data:
                            event.ignore()
                            return
                        
                        target_path = target_data["path"] + [target_data["name"]]
                    
                    # 检查源路径和目标路径是否有效
                    if source_path == target_path:
                        # 拖放到同一个文件夹，不做任何操作
                        event.acceptProposedAction()
                        return
                    
                    # 移动项目
                    success = self.data_manager.move_item(source_path, source_name, target_path)
                    
                    if success:
                        self.data_manager.save()
                        event.acceptProposedAction()
                    else:
                        QMessageBox.warning(self, "移动失败", "无法移动项目，可能是名称冲突或路径无效")
                        event.ignore()
                else:
                    event.ignore()
            except Exception as e:
                logger.error(f"处理拖放事件出错: {e}")
                QMessageBox.warning(self, "拖放错误", f"处理拖放事件出错: {str(e)}")
                event.ignore()
        else:
            event.ignore()
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，允许点击空白区域取消选择"""
        # 获取点击位置的项目
        item = self.itemAt(event.pos())
        
        # 如果点击在空白区域，清除选择
        if item is None:
            self.clearSelection()
            # 发送清除选择信号
            self.selection_cleared.emit()
            # 如果当前有选中的项目，发送路径变化信号，传递空路径
            if self.currentItem():
                self.setCurrentItem(None)
                self.path_changed.emit([])  # 返回根目录
        
        # 调用父类的事件处理
        super().mousePressEvent(event)

    def _add_root_folder(self):
        """添加根文件夹"""
        name, ok = QInputDialog.getText(self, "添加文件夹", "请输入文件夹名称:")
        if ok and name:
            success = self.data_manager.add_folder([], name)
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加文件夹，可能是名称已存在")

    def _copy_folder(self, data):
        """复制文件夹"""
        # 保存复制的项目数据
        self.clipboard_data = {
            "path": data["path"],
            "name": data["name"],
            "type": "folder"
        }
        QMessageBox.information(self, "复制成功", f"已复制文件夹 {data['name']} 到剪贴板")
    
    def _paste_item(self, target_data):
        """将剪贴板中的项目粘贴到目标文件夹"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        target_path = target_data["path"] + [target_data["name"]]
        
        # 检查是否为粘贴到自己或子文件夹中
        if self.clipboard_data["type"] == "folder":
            source_full_path = source_path + [source_name]
            is_subpath = False
            
            if len(target_path) >= len(source_full_path):
                is_subpath = True
                for i in range(len(source_full_path)):
                    if source_full_path[i] != target_path[i]:
                        is_subpath = False
                        break
            
            if is_subpath:
                QMessageBox.warning(self, "粘贴失败", "不能将文件夹粘贴到自己或其子文件夹中")
                return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查目标是否已存在同名项目
        target_items = self.data_manager.get_item_at_path(target_path)
        if source_name in target_items:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in target_items:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, target_path, new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                target_path,
                new_name,
                item["url"],
                item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到目标文件夹")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _paste_item_to_root(self):
        """将剪贴板中的项目粘贴到根目录"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        
        # 检查是否已经在根目录
        if not source_path:
            QMessageBox.warning(self, "粘贴失败", "项目已经在根目录")
            return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查根目录是否已存在同名项目
        if source_name in self.data_manager.data:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in self.data_manager.data:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, [], new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                [], new_name, item["url"], item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到根目录")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _copy_folder_recursive(self, source_path, source_name, target_path, new_name):
        """递归复制文件夹及其内容"""
        # 创建目标文件夹
        success = self.data_manager.add_folder(target_path, new_name)
        if not success:
            return False
        
        # 获取源文件夹的子项目
        source_children_path = source_path + [source_name]
        source_children = self.data_manager.get_item_at_path(source_children_path)
        if not source_children:
            return True  # 空文件夹复制成功
        
        # 复制子项目
        target_children_path = target_path + [new_name]
        for child_name, child_item in source_children.items():
            if child_item["type"] == "folder":
                # 递归复制子文件夹
                self._copy_folder_recursive(source_children_path, child_name, target_children_path, child_name)
            else:  # url
                # 复制URL
                self.data_manager.add_url(
                    target_children_path,
                    child_name,
                    child_item["url"],
                    child_item.get("icon", "")
                )
        
        return True

    def set_root_bar(self, bar):
        self.external_root_bar = bar
        self.refresh()

    def _create_root_shower(self, name):
        """创建根目录显示器，避免lambda闭包问题
        
        Args:
            name: 根目录名称
            
        Returns:
            callable: 用于连接到按钮点击事件的函数
        """
        def shower(checked=False):
            self._show_root(name)
        return shower
    
    def _show_root(self, root_name, select_path=None):
        """只显示指定根目录下内容"""
        self.clear()
        item = self.data_manager.data.get(root_name)
        if not item or item["type"] != "folder":
            return
        tree_item = QTreeWidgetItem(self)
        # 统计下一级子目录和所有下级网址卡片数量
        children = item["children"]
        subdir_count = sum(1 for v in children.values() if v["type"] == "folder")
        def count_urls(d):
            cnt = 0
            for v in d.values():
                if v["type"] == "url":
                    cnt += 1
                elif v["type"] == "folder":
                    cnt += count_urls(v["children"])
            return cnt
        url_count = count_urls(children)
        if subdir_count > 0:
            stat_text = f"{subdir_count}类{url_count}个"
        else:
            stat_text = f"{url_count}个"
        tree_item.setText(0, root_name)
        tree_item.setText(1, stat_text)
        tree_item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
        tree_item.setIcon(0, icon_provider.get_icon("folder"))
        tree_item.setData(0, Qt.UserRole, {"path": [], "name": root_name, "item": item})
        font = tree_item.font(0)
        font.setPointSizeF(font.pointSizeF() * 1.3)
        tree_item.setFont(0, font)
        self._add_folder_items(tree_item, item["children"], [root_name], font)
        self.setColumnCount(2)
        self.header().setSectionResizeMode(0, self.header().ResizeToContents)
        self.header().setSectionResizeMode(1, self.header().Fixed)
        self.setColumnWidth(1, 70)
        self.header().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._current_root = root_name
        # 恢复选中状态
        if select_path:
            self.select_path(select_path)

    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
        
    def set_locked_state(self, locked):
        """设置锁定状态
        
        Args:
            locked: 是否锁定
        """
        self.is_locked = locked
        logger.debug(f"文件夹树锁定状态: {locked}")
        
        # 更新右键菜单策略
        if locked:
            # 锁定状态下禁用右键菜单
            self.setContextMenuPolicy(Qt.NoContextMenu)
        else:
            # 解锁状态下恢复原有右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 刷新视图
        self.refresh()

    def mousePressEvent(self, event):
        """处理鼠标按下事件，允许点击空白区域取消选择"""
        # 获取点击位置的项目
        item = self.itemAt(event.pos())
        
        # 如果点击在空白区域，清除选择
        if item is None:
            self.clearSelection()
            # 发送清除选择信号
            self.selection_cleared.emit()
            # 如果当前有选中的项目，发送路径变化信号，传递空路径
            if self.currentItem():
                self.setCurrentItem(None)
                self.path_changed.emit([])  # 返回根目录
        
        # 调用父类的事件处理
        super().mousePressEvent(event)

    def _add_root_folder(self):
        """添加根文件夹"""
        name, ok = QInputDialog.getText(self, "添加文件夹", "请输入文件夹名称:")
        if ok and name:
            success = self.data_manager.add_folder([], name)
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加文件夹，可能是名称已存在")

    def _copy_folder(self, data):
        """复制文件夹"""
        # 保存复制的项目数据
        self.clipboard_data = {
            "path": data["path"],
            "name": data["name"],
            "type": "folder"
        }
        QMessageBox.information(self, "复制成功", f"已复制文件夹 {data['name']} 到剪贴板")
    
    def _paste_item(self, target_data):
        """将剪贴板中的项目粘贴到目标文件夹"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        target_path = target_data["path"] + [target_data["name"]]
        
        # 检查是否为粘贴到自己或子文件夹中
        if self.clipboard_data["type"] == "folder":
            source_full_path = source_path + [source_name]
            is_subpath = False
            
            if len(target_path) >= len(source_full_path):
                is_subpath = True
                for i in range(len(source_full_path)):
                    if source_full_path[i] != target_path[i]:
                        is_subpath = False
                        break
            
            if is_subpath:
                QMessageBox.warning(self, "粘贴失败", "不能将文件夹粘贴到自己或其子文件夹中")
                return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查目标是否已存在同名项目
        target_items = self.data_manager.get_item_at_path(target_path)
        if source_name in target_items:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in target_items:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, target_path, new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                target_path,
                new_name,
                item["url"],
                item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到目标文件夹")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _paste_item_to_root(self):
        """将剪贴板中的项目粘贴到根目录"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        
        # 检查是否已经在根目录
        if not source_path:
            QMessageBox.warning(self, "粘贴失败", "项目已经在根目录")
            return
        # This software was developed by Fan Huiyong, and all rights belong to Fan Huiyong himself. This software is only allowed for personal non-commercial use; it is prohibited for any organization or individual to use it for profit-making purposes without authorization.
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查根目录是否已存在同名项目
        if source_name in self.data_manager.data:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in self.data_manager.data:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, [], new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                [], new_name, item["url"], item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到根目录")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _copy_folder_recursive(self, source_path, source_name, target_path, new_name):
        """递归复制文件夹及其内容"""
        # 创建目标文件夹
        success = self.data_manager.add_folder(target_path, new_name)
        if not success:
            return False
        
        # 获取源文件夹的子项目
        source_children_path = source_path + [source_name]
        source_children = self.data_manager.get_item_at_path(source_children_path)
        if not source_children:
            return True  # 空文件夹复制成功
        
        # 复制子项目
        target_children_path = target_path + [new_name]
        for child_name, child_item in source_children.items():
            if child_item["type"] == "folder":
                # 递归复制子文件夹
                self._copy_folder_recursive(source_children_path, child_name, target_children_path, child_name)
            else:  # url
                # 复制URL
                self.data_manager.add_url(
                    target_children_path,
                    child_name,
                    child_item["url"],
                    child_item.get("icon", "")
                )
        
        return True

    def set_root_bar(self, bar):
        self.external_root_bar = bar
        self.refresh()

    def _create_root_shower(self, name):
        """创建根目录显示器，避免lambda闭包问题
        
        Args:
            name: 根目录名称
            
        Returns:
            callable: 用于连接到按钮点击事件的函数
        """
        def shower(checked=False):
            self._show_root(name)
        return shower
    
    def _show_root(self, root_name, select_path=None):
        """只显示指定根目录下内容"""
        self.clear()
        item = self.data_manager.data.get(root_name)
        if not item or item["type"] != "folder":
            return
        tree_item = QTreeWidgetItem(self)
        # 统计下一级子目录和所有下级网址卡片数量
        children = item["children"]
        subdir_count = sum(1 for v in children.values() if v["type"] == "folder")
        def count_urls(d):
            cnt = 0
            for v in d.values():
                if v["type"] == "url":
                    cnt += 1
                elif v["type"] == "folder":
                    cnt += count_urls(v["children"])
            return cnt
        url_count = count_urls(children)
        if subdir_count > 0:
            stat_text = f"{subdir_count}类{url_count}个"
        else:
            stat_text = f"{url_count}个"
        tree_item.setText(0, root_name)
        tree_item.setText(1, stat_text)
        tree_item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
        tree_item.setIcon(0, icon_provider.get_icon("folder"))
        tree_item.setData(0, Qt.UserRole, {"path": [], "name": root_name, "item": item})
        font = tree_item.font(0)
        font.setPointSizeF(font.pointSizeF() * 1.3)
        tree_item.setFont(0, font)
        self._add_folder_items(tree_item, item["children"], [root_name], font)
        self.setColumnCount(2)
        self.header().setSectionResizeMode(0, self.header().ResizeToContents)
        self.header().setSectionResizeMode(1, self.header().Fixed)
        self.setColumnWidth(1, 70)
        self.header().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._current_root = root_name
        # 恢复选中状态
        if select_path:
            self.select_path(select_path)

    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
        
    def set_locked_state(self, locked):
        """设置锁定状态
        
        Args:
            locked: 是否锁定
        """
        self.is_locked = locked
        logger.debug(f"文件夹树锁定状态: {locked}")
        
        # 更新右键菜单策略
        if locked:
            # 锁定状态下禁用右键菜单
            self.setContextMenuPolicy(Qt.NoContextMenu)
        else:
            # 解锁状态下恢复原有右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 刷新视图
        self.refresh()

    def mousePressEvent(self, event):
        """处理鼠标按下事件，允许点击空白区域取消选择"""
        # 获取点击位置的项目
        item = self.itemAt(event.pos())
        
        # 如果点击在空白区域，清除选择
        if item is None:
            self.clearSelection()
            # 发送清除选择信号
            self.selection_cleared.emit()
            # 如果当前有选中的项目，发送路径变化信号，传递空路径
            if self.currentItem():
                self.setCurrentItem(None)
                self.path_changed.emit([])  # 返回根目录
        
        # 调用父类的事件处理
        super().mousePressEvent(event)

    def _add_root_folder(self):
        """添加根文件夹"""
        name, ok = QInputDialog.getText(self, "添加文件夹", "请输入文件夹名称:")
        if ok and name:
            success = self.data_manager.add_folder([], name)
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加文件夹，可能是名称已存在")

    def _copy_folder(self, data):
        """复制文件夹"""
        # 保存复制的项目数据
        self.clipboard_data = {
            "path": data["path"],
            "name": data["name"],
            "type": "folder"
        }
        QMessageBox.information(self, "复制成功", f"已复制文件夹 {data['name']} 到剪贴板")
    
    def _paste_item(self, target_data):
        """将剪贴板中的项目粘贴到目标文件夹"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        target_path = target_data["path"] + [target_data["name"]]
        
        # 检查是否为粘贴到自己或子文件夹中
        if self.clipboard_data["type"] == "folder":
            source_full_path = source_path + [source_name]
            is_subpath = False
            
            if len(target_path) >= len(source_full_path):
                is_subpath = True
                for i in range(len(source_full_path)):
                    if source_full_path[i] != target_path[i]:
                        is_subpath = False
                        break
            
            if is_subpath:
                QMessageBox.warning(self, "粘贴失败", "不能将文件夹粘贴到自己或其子文件夹中")
                return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查目标是否已存在同名项目
        target_items = self.data_manager.get_item_at_path(target_path)
        if source_name in target_items:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in target_items:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, target_path, new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                target_path,
                new_name,
                item["url"],
                item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到目标文件夹")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _paste_item_to_root(self):
        """将剪贴板中的项目粘贴到根目录"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        
        # 检查是否已经在根目录
        if not source_path:
            QMessageBox.warning(self, "粘贴失败", "项目已经在根目录")
            return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查根目录是否已存在同名项目
        if source_name in self.data_manager.data:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in self.data_manager.data:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, [], new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                [], new_name, item["url"], item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到根目录")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _copy_folder_recursive(self, source_path, source_name, target_path, new_name):
        """递归复制文件夹及其内容"""
        # 创建目标文件夹
        success = self.data_manager.add_folder(target_path, new_name)
        if not success:
            return False
        
        # 获取源文件夹的子项目
        source_children_path = source_path + [source_name]
        source_children = self.data_manager.get_item_at_path(source_children_path)
        if not source_children:
            return True  # 空文件夹复制成功
        
        # 复制子项目
        target_children_path = target_path + [new_name]
        for child_name, child_item in source_children.items():
            if child_item["type"] == "folder":
                # 递归复制子文件夹
                self._copy_folder_recursive(source_children_path, child_name, target_children_path, child_name)
            else:  # url
                # 复制URL
                self.data_manager.add_url(
                    target_children_path,
                    child_name,
                    child_item["url"],
                    child_item.get("icon", "")
                )
        
        return True

    def set_root_bar(self, bar):
        self.external_root_bar = bar
        self.refresh()

    def _create_root_shower(self, name):
        """创建根目录显示器，避免lambda闭包问题
        
        Args:
            name: 根目录名称
            
        Returns:
            callable: 用于连接到按钮点击事件的函数
        """
        def shower(checked=False):
            self._show_root(name)
        return shower
    
    def _show_root(self, root_name, select_path=None):
        """只显示指定根目录下内容"""
        self.clear()
        item = self.data_manager.data.get(root_name)
        if not item or item["type"] != "folder":
            return
        tree_item = QTreeWidgetItem(self)
        # 统计下一级子目录和所有下级网址卡片数量
        children = item["children"]
        subdir_count = sum(1 for v in children.values() if v["type"] == "folder")
        def count_urls(d):
            cnt = 0
            for v in d.values():
                if v["type"] == "url":
                    cnt += 1
                elif v["type"] == "folder":
                    cnt += count_urls(v["children"])
            return cnt
        url_count = count_urls(children)
        if subdir_count > 0:
            stat_text = f"{subdir_count}类{url_count}个"
        else:
            stat_text = f"{url_count}个"
        tree_item.setText(0, root_name)
        tree_item.setText(1, stat_text)
        tree_item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
        tree_item.setIcon(0, icon_provider.get_icon("folder"))
        tree_item.setData(0, Qt.UserRole, {"path": [], "name": root_name, "item": item})
        font = tree_item.font(0)
        font.setPointSizeF(font.pointSizeF() * 1.3)
        tree_item.setFont(0, font)
        self._add_folder_items(tree_item, item["children"], [root_name], font)
        self.setColumnCount(2)
        self.header().setSectionResizeMode(0, self.header().ResizeToContents)
        self.header().setSectionResizeMode(1, self.header().Fixed)
        self.setColumnWidth(1, 70)
        self.header().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._current_root = root_name
        # 恢复选中状态
        if select_path:
            self.select_path(select_path)

    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
        
    def set_locked_state(self, locked):
        """设置锁定状态
        
        Args:
            locked: 是否锁定
        """
        self.is_locked = locked
        logger.debug(f"文件夹树锁定状态: {locked}")
        
        # 更新右键菜单策略
        if locked:
            # 锁定状态下禁用右键菜单
            self.setContextMenuPolicy(Qt.NoContextMenu)
        else:
            # 解锁状态下恢复原有右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 刷新视图
        self.refresh()

    def mousePressEvent(self, event):
        """处理鼠标按下事件，允许点击空白区域取消选择"""
        # 获取点击位置的项目
        item = self.itemAt(event.pos())
        
        # 如果点击在空白区域，清除选择
        if item is None:
            self.clearSelection()
            # 发送清除选择信号
            self.selection_cleared.emit()
            # 如果当前有选中的项目，发送路径变化信号，传递空路径
            if self.currentItem():
                self.setCurrentItem(None)
                self.path_changed.emit([])  # 返回根目录
        
        # 调用父类的事件处理
        super().mousePressEvent(event)

    def _add_root_folder(self):
        """添加根文件夹"""
        name, ok = QInputDialog.getText(self, "添加文件夹", "请输入文件夹名称:")
        if ok and name:
            success = self.data_manager.add_folder([], name)
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加文件夹，可能是名称已存在")

    def _copy_folder(self, data):
        """复制文件夹"""
        # 保存复制的项目数据
        self.clipboard_data = {
            "path": data["path"],
            "name": data["name"],
            "type": "folder"
        }
        QMessageBox.information(self, "复制成功", f"已复制文件夹 {data['name']} 到剪贴板")
    
    def _paste_item(self, target_data):
        """将剪贴板中的项目粘贴到目标文件夹"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        target_path = target_data["path"] + [target_data["name"]]
        
        # 检查是否为粘贴到自己或子文件夹中
        if self.clipboard_data["type"] == "folder":
            source_full_path = source_path + [source_name]
            is_subpath = False
            
            if len(target_path) >= len(source_full_path):
                is_subpath = True
                for i in range(len(source_full_path)):
                    if source_full_path[i] != target_path[i]:
                        is_subpath = False
                        break
            
            if is_subpath:
                QMessageBox.warning(self, "粘贴失败", "不能将文件夹粘贴到自己或其子文件夹中")
                return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查目标是否已存在同名项目
        target_items = self.data_manager.get_item_at_path(target_path)
        if source_name in target_items:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in target_items:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, target_path, new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                target_path,
                new_name,
                item["url"],
                item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到目标文件夹")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _paste_item_to_root(self):
        """将剪贴板中的项目粘贴到根目录"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        
        # 检查是否已经在根目录
        if not source_path:
            QMessageBox.warning(self, "粘贴失败", "项目已经在根目录")
            return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查根目录是否已存在同名项目
        if source_name in self.data_manager.data:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in self.data_manager.data:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, [], new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                [], new_name, item["url"], item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到根目录")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _copy_folder_recursive(self, source_path, source_name, target_path, new_name):
        """递归复制文件夹及其内容"""
        # 创建目标文件夹
        success = self.data_manager.add_folder(target_path, new_name)
        if not success:
            return False
        
        # 获取源文件夹的子项目
        source_children_path = source_path + [source_name]
        source_children = self.data_manager.get_item_at_path(source_children_path)
        if not source_children:
            return True  # 空文件夹复制成功
        
        # 复制子项目
        target_children_path = target_path + [new_name]
        for child_name, child_item in source_children.items():
            if child_item["type"] == "folder":
                # 递归复制子文件夹
                self._copy_folder_recursive(source_children_path, child_name, target_children_path, child_name)
            else:  # url
                # 复制URL
                self.data_manager.add_url(
                    target_children_path,
                    child_name,
                    child_item["url"],
                    child_item.get("icon", "")
                )
        
        return True

    def set_root_bar(self, bar):
        self.external_root_bar = bar
        self.refresh()

    def _create_root_shower(self, name):
        """创建根目录显示器，避免lambda闭包问题
        
        Args:
            name: 根目录名称
            
        Returns:
            callable: 用于连接到按钮点击事件的函数
        """
        def shower(checked=False):
            self._show_root(name)
        return shower
    
    def _show_root(self, root_name, select_path=None):
        """只显示指定根目录下内容"""
        self.clear()
        item = self.data_manager.data.get(root_name)
        if not item or item["type"] != "folder":
            return
        tree_item = QTreeWidgetItem(self)
        # 统计下一级子目录和所有下级网址卡片数量
        children = item["children"]
        subdir_count = sum(1 for v in children.values() if v["type"] == "folder")
        def count_urls(d):
            cnt = 0
            for v in d.values():
                if v["type"] == "url":
                    cnt += 1
                elif v["type"] == "folder":
                    cnt += count_urls(v["children"])
            return cnt
        url_count = count_urls(children)
        if subdir_count > 0:
            stat_text = f"{subdir_count}类{url_count}个"
        else:
            stat_text = f"{url_count}个"
        tree_item.setText(0, root_name)
        tree_item.setText(1, stat_text)
        tree_item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
        tree_item.setIcon(0, icon_provider.get_icon("folder"))
        tree_item.setData(0, Qt.UserRole, {"path": [], "name": root_name, "item": item})
        font = tree_item.font(0)
        font.setPointSizeF(font.pointSizeF() * 1.3)
        tree_item.setFont(0, font)
        self._add_folder_items(tree_item, item["children"], [root_name], font)
        self.setColumnCount(2)
        self.header().setSectionResizeMode(0, self.header().ResizeToContents)
        self.header().setSectionResizeMode(1, self.header().Fixed)
        self.setColumnWidth(1, 70)
        self.header().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._current_root = root_name
        # 恢复选中状态
        if select_path:
            self.select_path(select_path)

    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
        
    def set_locked_state(self, locked):
        """设置锁定状态
        
        Args:
            locked: 是否锁定
        """
        self.is_locked = locked
        logger.debug(f"文件夹树锁定状态: {locked}")
        
        # 更新右键菜单策略
        if locked:
            # 锁定状态下禁用右键菜单
            self.setContextMenuPolicy(Qt.NoContextMenu)
        else:
            # 解锁状态下恢复原有右键菜单
            self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 刷新视图
        self.refresh()

    def mousePressEvent(self, event):
        """处理鼠标按下事件，允许点击空白区域取消选择"""
        # 获取点击位置的项目
        item = self.itemAt(event.pos())
        
        # 如果点击在空白区域，清除选择
        if item is None:
            self.clearSelection()
            # 发送清除选择信号
            self.selection_cleared.emit()
            # 如果当前有选中的项目，发送路径变化信号，传递空路径
            if self.currentItem():
                self.setCurrentItem(None)
                self.path_changed.emit([])  # 返回根目录
        
        # 调用父类的事件处理
        super().mousePressEvent(event)

    def _add_root_folder(self):
        """添加根文件夹"""
        name, ok = QInputDialog.getText(self, "添加文件夹", "请输入文件夹名称:")
        if ok and name:
            success = self.data_manager.add_folder([], name)
            
            if success:
                self.data_manager.save()
            else:
                QMessageBox.warning(self, "添加失败", "无法添加文件夹，可能是名称已存在")

    def _copy_folder(self, data):
        """复制文件夹"""
        # 保存复制的项目数据
        self.clipboard_data = {
            "path": data["path"],
            "name": data["name"],
            "type": "folder"
        }
        QMessageBox.information(self, "复制成功", f"已复制文件夹 {data['name']} 到剪贴板")
    
    def _paste_item(self, target_data):
        """将剪贴板中的项目粘贴到目标文件夹"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        target_path = target_data["path"] + [target_data["name"]]
        
        # 检查是否为粘贴到自己或子文件夹中
        if self.clipboard_data["type"] == "folder":
            source_full_path = source_path + [source_name]
            is_subpath = False
            
            if len(target_path) >= len(source_full_path):
                is_subpath = True
                for i in range(len(source_full_path)):
                    if source_full_path[i] != target_path[i]:
                        is_subpath = False
                        break
            
            if is_subpath:
                QMessageBox.warning(self, "粘贴失败", "不能将文件夹粘贴到自己或其子文件夹中")
                return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查目标是否已存在同名项目
        target_items = self.data_manager.get_item_at_path(target_path)
        if source_name in target_items:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in target_items:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, target_path, new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                target_path,
                new_name,
                item["url"],
                item.get("icon", "")
            )
        
        if success:
            self.data_manager.save()
            QMessageBox.information(self, "粘贴成功", f"已粘贴项目 {source_name} 到目标文件夹")
        else:
            QMessageBox.warning(self, "粘贴失败", "无法粘贴项目")
    
    def _paste_item_to_root(self):
        """将剪贴板中的项目粘贴到根目录"""
        if not self.clipboard_data:
            return
        
        source_path = self.clipboard_data["path"]
        source_name = self.clipboard_data["name"]
        
        # 检查是否已经在根目录
        if not source_path:
            QMessageBox.warning(self, "粘贴失败", "项目已经在根目录")
            return
        
        # 复制项目
        source_item = self.data_manager.get_item_at_path(source_path)
        if not source_item or source_name not in source_item:
            QMessageBox.warning(self, "粘贴失败", "源项目不存在")
            return
        
        item = source_item[source_name]
        
        # 检查根目录是否已存在同名项目
        if source_name in self.data_manager.data:
            # 如果存在同名项目，添加复制标记
            i = 1
            new_name = f"{source_name} - 复制"
            while new_name in self.data_manager.data:
                i += 1
                new_name = f"{source_name} - 复制 ({i})"
        else:
            new_name = source_name
        
        # 根据类型执行不同的复制操作
        if item["type"] == "folder":
            # 递归复制文件夹
            success = self._copy_folder_recursive(source_path, source_name, [], new_name)
        else:  # url
            # 复制URL
            success = self.data_manager.add_url(
                [], new_name, item["url"], item["icon"])