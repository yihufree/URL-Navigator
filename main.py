#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QWidget, QCheckBox, QHBoxLayout, QLineEdit, QPushButton
from PyQt5.QtGui import QIcon, QFont
from app import UrlNavigatorApp
from ui.icons import resource_path, icon_provider
import re
from bs4 import Tag
from config import Config
from PyQt5.QtCore import Qt, QSettings, QThreadPool, QRunnable, pyqtSignal, QObject, QTimer, QTime
import json
from logging.handlers import RotatingFileHandler
from threading import Lock

# 配置日志
def setup_logging():
    # 优先从环境变量读取日志路径
    log_file = os.environ.get("URLNAV_LOG_FILE")
    if not log_file:
        try:
            from PyQt5.QtCore import QSettings
            settings = QSettings("URL Navigator", "URL Navigator")
            log_file = settings.value("custom/log_file", None)
        except Exception:
            log_file = None
    if not log_file:
        log_dir = os.path.join(os.path.expanduser("~"), ".url_navigator", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "url_navigator.log")
    else:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 创建循环文件处理器，限制单个日志文件大小为5MB，最多保留3个备份
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    
    # 设置处理器
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

def main():
    try:
        # 设置日志
        setup_logging()
        
        # 设置高DPI支持 - 移到QApplication创建前
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("URL Navigator")
        app.setApplicationDisplayName("URL Navigator")
        app.setWindowIcon(icon_provider.get_icon("app_icon"))
        
        # 从应用设置中加载语言设置
        settings = QSettings("URL Navigator", "URL Navigator")
        language_code = settings.value("language", "zh")  # 默认使用中文
        
        # 加载语言文件
        if language_code:
            from utils.language_manager import language_manager
            language_manager.set_language(language_code)
            logger.info(f"已从设置加载语言: {language_code}")
        
        # 设置样式表
        style_path = resource_path("resources/styles/style.qss")
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        
        # 创建并显示主窗口
        window = UrlNavigatorApp()
        window.show()
        
        # 设置全局异常处理钩子
        def exception_hook(exctype, value, traceback_obj):
            logger.error("未捕获的异常", exc_info=(exctype, value, traceback_obj))
            try:
                # 直接打印错误信息到控制台
                print(f"程序发生严重错误: {value}")
                traceback.print_exc()
            except Exception as e:
                # 如果连打印都失败，则忽略
                pass
        
        # 设置全局异常钩子
        sys._excepthook = sys.excepthook
        sys.excepthook = exception_hook
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        # 捕获所有未处理的异常
        logger.error(f"程序发生未处理的异常: {e}", exc_info=True)
        try:
            # 尝试显示错误对话框
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("程序错误")
            msg.setText(f"程序发生错误: {str(e)}")
            msg.setDetailedText(f"详细错误信息:\n{traceback.format_exc()}")
            msg.exec_()
        except Exception as ex:
            # 如果连错误对话框都无法显示，则直接打印到控制台
            print(f"程序发生严重错误: {ex}")
            logger.critical(f"无法显示错误对话框: {ex}")
            traceback.print_exc()
        
        # 确保程序正常退出
        sys.exit(1)

def show_info(parent, text):
    QMessageBox.information(parent, "提示", text)

def show_warning(parent, text):
    QMessageBox.warning(parent, "警告", text)

def show_confirm(parent, text):
    return QMessageBox.question(parent, "确认", text, QMessageBox.Yes | QMessageBox.No)

def connect_signals(signal_map):
    for signal, slot in signal_map.items():
        signal.connect(slot)

class BaseDialog(QDialog):
    # 通用对话框逻辑
    pass

class BaseCardWidget(QWidget):
    # 通用卡片逻辑
    pass

class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)

class IconLoadWorker(QRunnable):
    def __init__(self, url, favicon_service, widget_id):
        super().__init__()
        self.url = url
        self.favicon_service = favicon_service
        self.widget_id = widget_id  # Add reference ID to track widgets
        self.signals = WorkerSignals()
        
    def run(self):
        try:
            # 获取图标
            icon_path = self.favicon_service.get_favicon(self.url)
            self.signals.finished.emit((self.url, icon_path, self.widget_id))
        except Exception as e:
            self.signals.error.emit(e)



def _on_icon_loaded(self, result):
    url, icon_path, widget_id = result
    # Check if widget still exists by ID before updating
    if widget_id in self.active_widgets:
        widget = self.active_widgets[widget_id]
        widget.set_icon(icon_path)

def load_data(self):
    """加载数据"""
    try:
        self.data_manager.load()
        logger.info("数据加载成功")
    except FileNotFoundError:
        logger.warning("数据文件不存在，将创建新的数据文件")
        self.data_manager.load_default_data()
    except json.JSONDecodeError:
        logger.error("数据文件格式错误，将创建备份并使用默认数据")
        self._backup_corrupted_file(self.data_file)
        self.data_manager.load_default_data()
    except Exception as e:
        logger.error(f"加载数据失败: {e}")
        QMessageBox.warning(
            self, 
            "数据加载失败", 
            f"无法加载书签数据: {str(e)}\n将使用默认数据。"
        )
        self.data_manager.load_default_data()

def _paste_selected(self):
    """粘贴选中的项目"""
    if self.is_locked:
        self._show_locked_message()
        return
        
    clipboard_data = self.app.clipboard().text()
    if not clipboard_data:
        return
        
    try:
        # 尝试解析JSON数据
        import json
        data = json.loads(clipboard_data)
        
        # 检查数据是否有效
        if not isinstance(data, dict) or "type" not in data:
            QMessageBox.warning(self, "粘贴失败", "剪贴板中没有有效的书签数据")
            return
            
        # 获取当前文件夹路径
        current_path = self.folder_tree.get_current_path()
        
        # 保存撤销快照
        self._save_undo_snapshot()
        
        # 执行粘贴操作...
    except json.JSONDecodeError:
        QMessageBox.warning(self, "粘贴失败", "剪贴板中的数据不是有效的JSON格式")
    except Exception as e:
        QMessageBox.warning(self, "粘贴失败", f"粘贴操作失败: {str(e)}")

def _setup_accessibility(self):
    """设置辅助功能"""
    # 添加工具提示
    self.add_url_action.setToolTip("添加新网址 (Ctrl+N)")
    self.add_folder_action.setToolTip("添加新文件夹 (Ctrl+Shift+N)")
    self.delete_action.setToolTip("删除选中的项目 (Delete)")
    self.cut_action.setToolTip("剪切选中的项目 (Ctrl+X)")
    self.copy_action.setToolTip("复制选中的项目 (Ctrl+C)")
    self.paste_action.setToolTip("粘贴到当前位置 (Ctrl+V)")
    self.search_action.setToolTip("搜索 (Ctrl+F)")
    self.lock_action.setToolTip("锁定编辑 (Alt+L)")  # 改为Alt+L避免冲突
    self.undo_action.setToolTip("撤销上一步操作 (Ctrl+Z)")
    
    # 添加快捷键
    self.add_url_action.setShortcut("Ctrl+N")
    self.add_folder_action.setShortcut("Ctrl+Shift+N")
    self.delete_action.setShortcut("Delete")
    self.cut_action.setShortcut("Ctrl+X")
    self.copy_action.setShortcut("Ctrl+C")
    self.paste_action.setShortcut("Ctrl+V")
    self.search_action.setShortcut("Ctrl+F")
    self.lock_action.setShortcut("Alt+L")  # 改为Alt+L避免冲突
    self.undo_action.setShortcut("Ctrl+Z")
    
    # 可调整字体大小
    font_size = self.app.config.get("view", "font_size", 10)
    app_font = QFont()
    app_font.setPointSize(font_size)
    self.app.setFont(app_font)
# This software was developed by Fan Huiyong, and all rights belong to Fan Huiyong himself. This software is only allowed for personal non-commercial use; it is prohibited for any organization or individual to use it for profit-making purposes without authorization.
def _search(self):
    """执行搜索"""
    query = self.search_edit.text().strip()
    if not query:
        return
        
    search_options = {
        "case_sensitive": False,
        "search_urls": True,
        "search_names": True,
        "search_descriptions": True,
        "search_tags": True,
        "max_results": 100,
        "current_folder_only": False  # 新增选项：仅搜索当前文件夹
    }
    
    # 如果选择了搜索当前文件夹，设置搜索范围
    if search_options["current_folder_only"]:
        search_options["search_root"] = self.folder_tree.get_current_path()
    
    # 执行搜索并显示结果
    results = self.app.search_service.search(query, search_options)
    
    # 创建并显示搜索对话框
    dialog = SearchDialog(results, self)
    dialog.setWindowTitle(f"搜索结果 - 找到 {len(results)} 项")
    # ...

def init_ui(self):
    # ...existing code...
    
    # 保存分割器为类成员变量以便后续访问
    self.splitter = splitter
    
    # 从设置恢复分割器位置
    splitter_state = self.app.settings.value("splitter_state")
    if splitter_state:
        self.splitter.restoreState(splitter_state)
    else:
        # 设置默认尺寸比例 (20% 给左侧, 80% 给右侧)
        width = self.width()
        self.splitter.setSizes([int(width * 0.2), int(width * 0.8)])
    
    # 连接splitter的splitterMoved信号，用于监听分割器移动
    self.splitter.splitterMoved.connect(self._on_splitter_moved)
    
    # 工具栏分隔符和搜索框
    toolbar.addSeparator()
    search_widget = QWidget()
    search_layout = QHBoxLayout(search_widget)
    search_layout.setContentsMargins(0, 0, 0, 0)
    search_layout.setSpacing(5)

    self.search_edit = QLineEdit()
    self.search_edit.setPlaceholderText("搜索...")
    self.search_edit.returnPressed.connect(self._search)
    self.search_edit.setMinimumWidth(150)  # 设置最小宽度

    # 添加搜索按钮在搜索框右侧
    search_btn = QPushButton()
    search_btn.setIcon(icon_provider.get_icon("search"))
    search_btn.setFixedSize(32, 32)
    search_btn.clicked.connect(self._search)
    search_btn.setToolTip("点击搜索 (Ctrl+F)")

    search_layout.addWidget(self.search_edit, 1)  # 让搜索框占据所有可用空间
    search_layout.addWidget(search_btn, 0)  # 固定大小的搜索按钮

    toolbar.addWidget(search_widget, 1)  # 让搜索控件占据工具栏的剩余空间

def _on_splitter_moved(self, pos, index):
    """当分割器移动时保存状态"""
    self.app.settings.setValue("splitter_state", self.splitter.saveState())
    
def resizeEvent(self, event):
    """窗口大小变化时触发刷新"""
    super().resizeEvent(event)
    
    # 获取当前宽度
    current_width = self.viewport().width()
    
    # 取消之前的定时器（如果存在）
    if hasattr(self, '_resize_timer') and self._resize_timer.isActive():
        self._resize_timer.stop()
    
    # 只有当宽度变化可能影响布局时才刷新
    if not hasattr(self, 'last_width') or abs(current_width - self.last_width) > 50:
        # 创建单次触发的定时器，在调整结束后才刷新
        self._resize_timer = QtCore.QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._do_delayed_resize)
        self._resize_timer.start(300)  # 300ms延迟，等待用户完成调整
    
    self.last_width = current_width

def _do_delayed_resize(self):
    """延迟执行的重新布局"""
    logger.debug(f"执行延迟布局刷新, 当前宽度: {self.viewport().width()}")
    # 计算新的列数
    new_columns = self._calculate_max_columns()
    # 只有列数发生变化时才真正刷新
    if not hasattr(self, 'last_columns') or new_columns != self.last_columns:
        self.refresh()
        self.last_columns = new_columns

def set_paths(self, data_file, icons_dir, log_file, backup_dir):
    """安全地设置文件路径"""
    # 验证路径是否安全
    def sanitize_path(path):
        # 检查路径是否包含可疑序列
        if '..' in path or '~' in path:
            return None
        # 确保路径是绝对路径并存在
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        return path if os.path.exists(os.path.dirname(path)) else None
    
    # 验证并设置各个路径
    if data_file:
        safe_path = sanitize_path(data_file)
        if safe_path:
            self.data_file = safe_path
            self.settings.setValue("data_file", safe_path)
    
    # 类似地处理其他路径...

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
        # Ctrl多选 - 保持现有逻辑
        if (name, typ) in self.selected_items:
            self.selected_items.remove((name, typ))
        else:
            self.selected_items.append((name, typ))
        self.last_selected_index = idx
    elif event.modifiers() & Qt.ShiftModifier and self.last_selected_index is not None:
        # Shift区间多选 - 修复逻辑
        start = min(self.last_selected_index, idx)
        end = max(self.last_selected_index, idx)
        # 保留现有选择，添加区间内的项目
        current_selection = self.selected_items.copy()
        range_selection = [(n, t) for _, n, t in self._item_widgets[start:end+1]]
        # 合并两个列表，确保不重复
        self.selected_items = list(set(current_selection + range_selection))
    else:
        # 单选
        self.selected_items = [(name, typ)]
        self.last_selected_index = idx
    self.refresh()

class DataManager:
    def __init__(self):
        self.data_lock = Lock()
        self.data_file = None
        self.data = {}
        # 若有初始化参数，需补充

    def save(self):
        """保存数据"""
        with self.data_lock:
            try:
                if self.data_file:
                    with open(self.data_file, 'w', encoding='utf-8') as f:
                        import json
                        json.dump(self.data, f, indent=4, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"保存数据失败: {e}")
                return False

    def update_item(self, path, old_name, new_name, new_data):
        """更新项目"""
        with self.data_lock:
            item = self.get_item_at_path(path)
            if not item or old_name not in item:
                return False
            if new_name != old_name and new_name in item:
                return False
            if new_name != old_name:
                item[new_name] = item[old_name]
                del item[old_name]
            for key, value in new_data.items():
                item[new_name][key] = value
            return True

    def get_item_at_path(self, path):
        """获取指定路径的项目"""
        with self.data_lock:
            current = self.data
            for segment in path:
                if segment in current and isinstance(current[segment], dict) and current[segment].get("type") == "folder":
                    current = current[segment]["children"]
                else:
                    return None
            return current

    def add_url(self, path, name, url, icon=""):
        """添加URL"""
        with self.data_lock:
            parent = self.get_item_at_path(path)
            if parent is None:
                return False
            if name in parent:
                return False
            parent[name] = {
                "type": "url",
                "url": url,
                "name": name,
                "icon": icon
            }
            return True

def update_status_bar(self):
    """更新状态栏信息"""
    # 保持原有统计逻辑
    
    # 添加锁定状态显示
    status_text = f"总计: {url_count}个网址, {folder_count}个文件夹"
    
    # 添加锁定状态显示
    if self.is_locked:
        status_text += " | 状态: 已锁定(编辑功能已禁用)"
    
    # 添加当前路径显示
    if self.bookmark_grid.current_path:
        current_path_str = " > ".join(self.bookmark_grid.current_path)
        status_text += f" | 当前位置: {current_path_str}"
    else:
        status_text += " | 当前位置: 根目录"
    
    self.status_bar.showMessage(status_text)
    
    # 如果需要更复杂的状态栏，可以添加多个状态标签

def keyPressEvent(self, event):
    """处理键盘事件，增强可访问性"""
    if not self.selected_items:
        # 如果没有选中项，选择第一个
        if self._item_widgets and event.key() in (Qt.Key_Right, Qt.Key_Down):
            first_widget = self._item_widgets[0][0]
            name = self._item_widgets[0][1]
            typ = self._item_widgets[0][2]
            self.selected_items = [(name, typ)]
            self.last_selected_index = 0
            self.refresh()
            return
    
    # 获取当前选中的索引
    current_index = self.last_selected_index if hasattr(self, 'last_selected_index') else None
    if current_index is not None and self._item_widgets:
        # 计算新索引
        new_index = current_index
        cols = self._calculate_max_columns()
        
        if event.key() == Qt.Key_Right:
            new_index = min(len(self._item_widgets) - 1, current_index + 1)
        elif event.key() == Qt.Key_Left:
            new_index = max(0, current_index - 1)
        elif event.key() == Qt.Key_Down:
            new_index = min(len(self._item_widgets) - 1, current_index + cols)
        elif event.key() == Qt.Key_Up:
            new_index = max(0, current_index - cols)
        elif event.key() == Qt.Key_Home:
            new_index = 0
        elif event.key() == Qt.Key_End:
            new_index = len(self._item_widgets) - 1
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # 打开当前选中项
            if self.selected_items:
                name, typ = self.selected_items[0]
                for w, n, t in self._item_widgets:
                    if n == name and t == typ:
                        w._open_url()
                        break
            return
        
        # 如果索引变化了，更新选择
        if new_index != current_index:
            name = self._item_widgets[new_index][1]
            typ = self._item_widgets[new_index][2]
            self.selected_items = [(name, typ)]
            self.last_selected_index = new_index
            self.refresh()
            return
    
    # 其他键盘事件交给父类处理
    super().keyPressEvent(event)

if __name__ == "__main__":
    main()