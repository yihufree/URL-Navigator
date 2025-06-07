#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QDialogButtonBox,
    QMessageBox, QWidget, QGridLayout, QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor, QBrush, QPen, QPalette, QPixmap, QIntValidator
from ui.icons import icon_provider, resource_path
from utils.language_manager import language_manager

logger = logging.getLogger(__name__)

class WebsiteBlindBoxDialog(QDialog):
    """网站盲盒对话框，用于选择随机打开的网站数量"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_count = 0
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 设置窗口标题和大小
        self.setWindowTitle(language_manager.tr("blind_box.title", "网站盲盒"))
        self.setFixedSize(400, 350)
        
        # 设置窗口样式
        numberbg_image_path = resource_path("resources/bgimages/numberbg.jpg").replace("\\", "/")
        self.setStyleSheet(f"""
            QDialog {{
                background-image: url({numberbg_image_path});
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
                border: 2px solid #4682b4;
                border-radius: 10px;
            }}
            QDialog::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(240, 248, 255, 0.8);
                border-radius: 10px;
            }}
            QPushButton {{
                background-color: #4682b4;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5c9bd1;
            }}
            QPushButton:pressed {{
                background-color: #3a6d99;
            }}
            QLabel {{
                color: #2c3e50;
                font-weight: bold;
            }}
            QLineEdit {{
                border: 1px solid #4682b4;
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 添加标题标签
        title_label = QLabel(language_manager.tr("blind_box.description", "请选择或输入要随机打开的网站数量（1-30）："))
        title_font = title_label.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 添加数字选择按钮网格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # 创建1-5的数字按钮，按照新的布局排列
        button_positions = {
            1: (0, 0),  # 第一行第一列
            5: (0, 4),  # 第一行第五列
            3: (1, 2),  # 第二行第三列（中间）
            2: (2, 1),  # 第三行第二列
            4: (2, 3)   # 第三行第四列
        }
        
        for number in range(1, 6):
            number_btn = QPushButton(str(number))
            number_btn.setFixedSize(60, 60)
            number_btn.setProperty("number", number)
            number_btn.clicked.connect(self.on_number_selected)
            
            # 设置按钮样式
            number_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4682b4;
                    color: white;
                    border-radius: 30px;
                    font-size: 18px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5c9bd1;
                }
                QPushButton:pressed {
                    background-color: #3a6d99;
                }
            """)
            
            row, col = button_positions[number]
            grid_layout.addWidget(number_btn, row, col)
        
        main_layout.addLayout(grid_layout)
        
        # 添加分隔线
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        separator.setStyleSheet("background-color: #4682b4;")
        main_layout.addWidget(separator)
        
        # 添加自定义数量输入
        input_layout = QHBoxLayout()
        
        custom_label = QLabel(language_manager.tr("blind_box.custom", "自定义数量："))
        # 设置自定义数量标签样式：字号增加一倍（200%），颜色改为白色
        custom_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        input_layout.addWidget(custom_label)
        
        self.count_edit = QLineEdit()
        self.count_edit.setPlaceholderText(language_manager.tr("blind_box.input_placeholder", "输入数字"))
        self.count_edit.setValidator(QIntValidator(1, 100))
        input_layout.addWidget(self.count_edit)
        
        main_layout.addLayout(input_layout)
        
        # 添加确认和取消按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        
        # 设置按钮文本
        button_box.button(QDialogButtonBox.Ok).setText(language_manager.tr("dialogs.ok_button", "确定"))
        button_box.button(QDialogButtonBox.Cancel).setText(language_manager.tr("dialogs.cancel_button", "取消"))
        
        main_layout.addWidget(button_box)
        
        # 设置布局
        self.setLayout(main_layout)
    
    def on_number_selected(self):
        """数字按钮被点击时的处理"""
        sender = self.sender()
        if sender:
            self.selected_count = sender.property("number")
            self.count_edit.clear()  # 清除输入框
            self.accept()
    
    def validate_and_accept(self):
        """验证输入并接受对话框"""
        # 检查输入框是否有值
        text = self.count_edit.text().strip()
        if text:
            try:
                count = int(text)
                if count <= 0:
                    QMessageBox.warning(self, language_manager.tr("blind_box.invalid_input", "无效输入"), 
                                      language_manager.tr("blind_box.positive_number_required", "请输入大于0的数字"))
                    return
                self.selected_count = count
                super().accept()
            except ValueError:
                QMessageBox.warning(self, language_manager.tr("blind_box.invalid_input", "无效输入"), 
                                  language_manager.tr("blind_box.number_required", "请输入有效的数字"))
        else:
            # 如果没有通过按钮选择数字，也没有输入自定义数量
            if self.selected_count <= 0:
                QMessageBox.warning(self, language_manager.tr("blind_box.no_selection", "未选择数量"), 
                                  language_manager.tr("blind_box.select_or_input_required", "请选择或输入要打开的网站数量"))
            else:
                super().accept()
    
    def get_website_count(self):
        """获取选择的网站数量"""
        return self.selected_count