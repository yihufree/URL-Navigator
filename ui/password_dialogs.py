# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox, QTabWidget,
    QWidget, QMessageBox, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)

class PasswordInputDialog(QDialog):
    """密码输入对话框"""
    
    def __init__(self, parent=None, language_manager=None, password_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.password_manager = password_manager
        self.password = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self.tr("输入密码"))
        self.setFixedSize(350, 200)
        self.setModal(True)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 提示标签
        info_label = QLabel(self.tr("请输入密码以继续："))
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # 密码输入框
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText(self.tr("请输入密码"))
        self.password_edit.returnPressed.connect(self.accept)
        layout.addWidget(self.password_edit)
        
        # 显示密码复选框
        self.show_password_cb = QCheckBox(self.tr("显示密码"))
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 确定按钮
        self.ok_button = QPushButton(self.tr("确定"))
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        # 取消按钮
        self.cancel_button = QPushButton(self.tr("取消 Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # 忘记密码按钮（如果有密保问题）
        if self.password_manager and self.password_manager.has_security_question():
            self.forgot_button = QPushButton(self.tr("忘记密码"))
            self.forgot_button.clicked.connect(self.show_security_dialog)
            button_layout.addWidget(self.forgot_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 设置焦点
        self.password_edit.setFocus()
        
    def toggle_password_visibility(self, checked):
        """切换密码可见性"""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
    
    def show_security_dialog(self):
        """显示密保问题对话框"""
        if not self.password_manager:
            return
            
        dialog = SecurityQuestionDialog(self, self.language_manager, self.password_manager)
        if dialog.exec_() == QDialog.Accepted:
            # 密保验证成功，关闭当前对话框
            self.accept()
    
    def accept(self):
        """确认输入"""
        password = self.password_edit.text()
        
        if not password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入密码！"))
            return
            
        # 验证密码
        if self.password_manager and not self.password_manager.verify_password(password):
            QMessageBox.warning(self, self.tr("错误"), self.tr("密码错误！"))
            self.password_edit.clear()
            self.password_edit.setFocus()
            return
            
        self.password = password
        super().accept()
    
    def get_password(self):
        """获取输入的密码"""
        return self.password

class SecurityQuestionDialog(QDialog):
    """密保问题对话框"""
    
    def __init__(self, parent=None, language_manager=None, password_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.password_manager = password_manager
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self.tr("密保问题"))
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 提示标签
        info_label = QLabel(self.tr("请回答密保问题以重置密码："))
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # 密保问题
        question = self.password_manager.get_security_question() if self.password_manager else ""
        question_label = QLabel(self.tr("密保问题："))
        layout.addWidget(question_label)
        
        question_text = QLabel(question)
        question_text.setWordWrap(True)
        question_text.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        layout.addWidget(question_text)
        
        # 答案输入
        answer_label = QLabel(self.tr("答案："))
        layout.addWidget(answer_label)
        
        self.answer_edit = QLineEdit()
        self.answer_edit.setPlaceholderText(self.tr("请输入答案"))
        layout.addWidget(self.answer_edit)
        
        # 新密码输入
        new_password_label = QLabel(self.tr("新密码："))
        layout.addWidget(new_password_label)
        
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setPlaceholderText(self.tr("请输入新密码"))
        layout.addWidget(self.new_password_edit)
        
        # 确认新密码
        confirm_password_label = QLabel(self.tr("确认新密码："))
        layout.addWidget(confirm_password_label)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText(self.tr("请再次输入新密码"))
        layout.addWidget(self.confirm_password_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 确定按钮
        self.ok_button = QPushButton(self.tr("确定"))
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        # 取消按钮
        self.cancel_button = QPushButton(self.tr("取消 Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 设置焦点
        self.answer_edit.setFocus()
    
    def accept(self):
        """确认重置"""
        answer = self.answer_edit.text().strip()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        if not answer:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入密保答案！"))
            return
            
        if not new_password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入新密码！"))
            return
            
        if new_password != confirm_password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("两次输入的密码不一致！"))
            return
            
        if len(new_password) < 4:
            QMessageBox.warning(self, self.tr("警告"), self.tr("密码长度至少为4位！"))
            return
            
        # 通过密保问题重置密码
        if self.password_manager and self.password_manager.reset_password_with_security(new_password, answer):
            QMessageBox.information(self, self.tr("成功"), self.tr("密码重置成功！"))
            super().accept()
        else:
            QMessageBox.warning(self, self.tr("错误"), self.tr("密保答案错误或重置失败！"))
            self.answer_edit.clear()
            self.answer_edit.setFocus()

class PasswordSettingsWidget(QWidget):
    """密码设置选项卡"""
    
    def __init__(self, parent=None, language_manager=None, password_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.password_manager = password_manager
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 密码保护组
        password_group = QGroupBox(self.tr("密码保护 Password Protection"))
        password_layout = QVBoxLayout()
        
        # 启用密码保护
        self.enable_password_cb = QCheckBox(self.tr("启用密码保护 Enable Password Protection"))
        self.enable_password_cb.toggled.connect(self.on_password_enabled_changed)
        password_layout.addWidget(self.enable_password_cb)
        
        # 密码设置区域
        self.password_widget = QWidget()
        password_form_layout = QFormLayout()
        
        # 当前密码（修改时需要）
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.Password)
        self.current_password_edit.setPlaceholderText(self.tr("请输入当前密码"))
        password_form_layout.addRow(self.tr("当前密码 Current Password："), self.current_password_edit)
        
        # 新密码
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setPlaceholderText(self.tr("请输入新密码（至少4位）"))
        password_form_layout.addRow(self.tr("新密码 New Password："), self.new_password_edit)
        
        # 确认密码
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText(self.tr("请再次输入新密码"))
        password_form_layout.addRow(self.tr("确认密码 Confirm Password："), self.confirm_password_edit)
        
        self.password_widget.setLayout(password_form_layout)
        password_layout.addWidget(self.password_widget)
        
        # 密码操作按钮
        password_button_layout = QHBoxLayout()
        
        self.set_password_button = QPushButton(self.tr("设置密码 Set Password"))
        self.set_password_button.clicked.connect(self.set_password)
        password_button_layout.addWidget(self.set_password_button)
        
        self.change_password_button = QPushButton(self.tr("修改密码 Change Password"))
        self.change_password_button.clicked.connect(self.change_password)
        password_button_layout.addWidget(self.change_password_button)
        
        self.remove_password_button = QPushButton(self.tr("移除密码 Remove Password"))
        self.remove_password_button.clicked.connect(self.remove_password)
        password_button_layout.addWidget(self.remove_password_button)
        
        password_button_layout.addStretch()
        password_layout.addLayout(password_button_layout)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # 密保问题组
        security_group = QGroupBox(self.tr("密保问题 Security Question"))
        security_layout = QVBoxLayout()
        
        # 密保问题输入
        security_form_layout = QFormLayout()
        
        self.security_question_edit = QLineEdit()
        self.security_question_edit.setPlaceholderText(self.tr("例如：您的出生地是？"))
        security_form_layout.addRow(self.tr("密保问题 Question："), self.security_question_edit)
        
        self.security_answer_edit = QLineEdit()
        self.security_answer_edit.setEchoMode(QLineEdit.Password)
        self.security_answer_edit.setPlaceholderText(self.tr("请输入答案"))
        security_form_layout.addRow(self.tr("答案 Answer："), self.security_answer_edit)
        
        security_layout.addLayout(security_form_layout)
        
        # 密保问题按钮
        security_button_layout = QHBoxLayout()
        
        self.set_security_button = QPushButton(self.tr("设置密保问题 Set Security Question"))
        self.set_security_button.clicked.connect(self.set_security_question)
        security_button_layout.addWidget(self.set_security_button)
        
        security_button_layout.addStretch()
        security_layout.addLayout(security_button_layout)
        
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        # 说明文本
        info_text = QLabel(self.tr(
            "说明：\n"
            "• 密码保护功能可以防止他人未经授权访问您的书签数据\n"
            "• 密保问题用于在忘记密码时重置密码\n"
            "• 建议设置一个容易记住但他人难以猜测的密保问题和答案\n"
            "• 此功能仅提供基本的隐私保护，不涉及书签数据的加密存储"
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("QLabel { color: #666; font-size: 12px; }")
        layout.addWidget(info_text)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_settings(self):
        """加载设置"""
        if not self.password_manager:
            return
            
        # 加载密码启用状态
        self.enable_password_cb.setChecked(self.password_manager.is_password_enabled())
        
        # 加载密保问题
        question = self.password_manager.get_security_question()
        if question:
            self.security_question_edit.setText(question)
            
        self.on_password_enabled_changed(self.password_manager.is_password_enabled())
        
    def on_password_enabled_changed(self, enabled):
        """密码启用状态改变"""
        self.password_widget.setEnabled(enabled)
        
        # 根据是否已设置密码来显示不同的界面
        has_password = self.password_manager and self.password_manager.is_password_enabled()
        
        self.current_password_edit.setVisible(has_password)
        self.set_password_button.setVisible(not has_password)
        self.change_password_button.setVisible(has_password)
        self.remove_password_button.setVisible(has_password)
        
    def set_password(self):
        """设置密码"""
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        if not new_password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入新密码！"))
            return
            
        if len(new_password) < 4:
            QMessageBox.warning(self, self.tr("警告"), self.tr("密码长度至少为4位！"))
            return
            
        if new_password != confirm_password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("两次输入的密码不一致！"))
            return
            
        if self.password_manager and self.password_manager.set_password(new_password):
            QMessageBox.information(self, self.tr("成功"), self.tr("密码设置成功！"))
            self.enable_password_cb.setChecked(True)
            self.clear_password_fields()
            self.on_password_enabled_changed(True)
        else:
            QMessageBox.warning(self, self.tr("错误"), self.tr("密码设置失败！"))
            
    def change_password(self):
        """修改密码"""
        current_password = self.current_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        if not current_password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入当前密码！"))
            return
            
        if not new_password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入新密码！"))
            return
            
        if len(new_password) < 4:
            QMessageBox.warning(self, self.tr("警告"), self.tr("密码长度至少为4位！"))
            return
            
        if new_password != confirm_password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("两次输入的密码不一致！"))
            return
            
        # 验证当前密码
        if not self.password_manager.verify_password(current_password):
            QMessageBox.warning(self, self.tr("错误"), self.tr("当前密码错误！"))
            return
            
        if self.password_manager.set_password(new_password):
            QMessageBox.information(self, self.tr("成功"), self.tr("密码修改成功！"))
            self.clear_password_fields()
        else:
            QMessageBox.warning(self, self.tr("错误"), self.tr("密码修改失败！"))
            
    def remove_password(self):
        """移除密码"""
        current_password = self.current_password_edit.text()
        
        if not current_password:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入当前密码！"))
            return
            
        # 验证当前密码
        if not self.password_manager.verify_password(current_password):
            QMessageBox.warning(self, self.tr("错误"), self.tr("当前密码错误！"))
            return
            
        # 确认移除
        reply = QMessageBox.question(
            self, 
            self.tr("确认"), 
            self.tr("确定要移除密码保护吗？这将删除所有密码相关数据。"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.password_manager.clear_password():
                QMessageBox.information(self, self.tr("成功"), self.tr("密码保护已移除！"))
                self.enable_password_cb.setChecked(False)
                self.clear_password_fields()
                self.security_question_edit.clear()
                self.security_answer_edit.clear()
                self.on_password_enabled_changed(False)
            else:
                QMessageBox.warning(self, self.tr("错误"), self.tr("移除密码失败！"))
                
    def set_security_question(self):
        """设置密保问题"""
        question = self.security_question_edit.text().strip()
        answer = self.security_answer_edit.text().strip()
        
        if not question:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入密保问题！"))
            return
            
        if not answer:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请输入密保答案！"))
            return
            
        if self.password_manager and self.password_manager.set_security_question(question, answer):
            QMessageBox.information(self, self.tr("成功"), self.tr("密保问题设置成功！"))
            self.security_answer_edit.clear()
        else:
            QMessageBox.warning(self, self.tr("错误"), self.tr("密保问题设置失败！"))
            
    def clear_password_fields(self):
        """清空密码输入框"""
        self.current_password_edit.clear()
        self.new_password_edit.clear()
        self.confirm_password_edit.clear()