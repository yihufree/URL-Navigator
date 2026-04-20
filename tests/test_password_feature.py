#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
密码保护功能测试脚本

此脚本用于测试密码保护功能的各个组件：
1. 密码管理器基本功能
2. 密码对话框界面
3. 设置对话框中的密码选项卡
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.password_manager import PasswordManager
from ui.password_dialogs import PasswordInputDialog, PasswordSettingsWidget
from utils.language_manager import language_manager

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PasswordTestWindow(QMainWindow):
    """密码功能测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.password_manager = PasswordManager()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("密码保护功能测试")
        self.setGeometry(100, 100, 600, 400)
        
        # 中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("密码保护功能测试")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 状态显示
        self.status_label = QLabel()
        self.update_status()
        layout.addWidget(self.status_label)
        
        # 测试按钮
        self.test_password_manager_btn = QPushButton("测试密码管理器")
        self.test_password_manager_btn.clicked.connect(self.test_password_manager)
        layout.addWidget(self.test_password_manager_btn)
        
        self.test_password_input_btn = QPushButton("测试密码输入对话框")
        self.test_password_input_btn.clicked.connect(self.test_password_input_dialog)
        layout.addWidget(self.test_password_input_btn)
        
        self.test_password_settings_btn = QPushButton("测试密码设置界面")
        self.test_password_settings_btn.clicked.connect(self.test_password_settings)
        layout.addWidget(self.test_password_settings_btn)
        
        self.clear_password_btn = QPushButton("清除所有密码数据")
        self.clear_password_btn.clicked.connect(self.clear_password_data)
        layout.addWidget(self.clear_password_btn)
        
        self.refresh_btn = QPushButton("刷新状态")
        self.refresh_btn.clicked.connect(self.update_status)
        layout.addWidget(self.refresh_btn)
        
    def update_status(self):
        """更新状态显示"""
        try:
            is_enabled = self.password_manager.is_password_enabled()
            has_question = self.password_manager.has_security_question()
            question = self.password_manager.get_security_question()
            
            status_text = f"""当前状态：
密码保护：{'已启用' if is_enabled else '未启用'}
密保问题：{'已设置' if has_question else '未设置'}
密保问题内容：{question if question else '无'}"""
            
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
            
        except Exception as e:
            self.status_label.setText(f"获取状态失败: {e}")
            logger.error(f"更新状态失败: {e}")
    
    def test_password_manager(self):
        """测试密码管理器基本功能"""
        try:
            logger.info("开始测试密码管理器")
            
            # 测试设置密码
            test_password = "test123"
            if self.password_manager.set_password(test_password):
                logger.info("密码设置成功")
                
                # 测试验证密码
                if self.password_manager.verify_password(test_password):
                    logger.info("密码验证成功")
                else:
                    logger.error("密码验证失败")
                    
                # 测试错误密码
                if not self.password_manager.verify_password("wrong_password"):
                    logger.info("错误密码验证正确拒绝")
                else:
                    logger.error("错误密码验证应该失败但成功了")
                    
                # 测试密保问题
                test_question = "您的出生地是？"
                test_answer = "北京"
                if self.password_manager.set_security_question(test_question, test_answer):
                    logger.info("密保问题设置成功")
                    
                    # 验证密保答案
                    if self.password_manager.verify_security_answer(test_answer):
                        logger.info("密保答案验证成功")
                    else:
                        logger.error("密保答案验证失败")
                        
                    # 测试通过密保重置密码
                    new_password = "new123"
                    if self.password_manager.reset_password_with_security(new_password, test_answer):
                        logger.info("通过密保重置密码成功")
                        
                        # 验证新密码
                        if self.password_manager.verify_password(new_password):
                            logger.info("新密码验证成功")
                        else:
                            logger.error("新密码验证失败")
                    else:
                        logger.error("通过密保重置密码失败")
                else:
                    logger.error("密保问题设置失败")
            else:
                logger.error("密码设置失败")
                
            self.update_status()
            logger.info("密码管理器测试完成")
            
        except Exception as e:
            logger.error(f"测试密码管理器时发生错误: {e}")
    
    def test_password_input_dialog(self):
        """测试密码输入对话框"""
        try:
            logger.info("测试密码输入对话框")
            
            dialog = PasswordInputDialog(
                parent=self,
                language_manager=language_manager,
                password_manager=self.password_manager
            )
            
            result = dialog.exec_()
            if result:
                password = dialog.get_password()
                logger.info(f"用户输入密码: {password}")
            else:
                logger.info("用户取消了密码输入")
                
        except Exception as e:
            logger.error(f"测试密码输入对话框时发生错误: {e}")
    
    def test_password_settings(self):
        """测试密码设置界面"""
        try:
            logger.info("测试密码设置界面")
            
            from PyQt5.QtWidgets import QDialog, QVBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle("密码设置测试")
            dialog.setModal(True)
            dialog.resize(500, 600)
            
            layout = QVBoxLayout(dialog)
            
            password_widget = PasswordSettingsWidget(
                parent=dialog,
                language_manager=language_manager,
                password_manager=self.password_manager
            )
            
            layout.addWidget(password_widget)
            
            dialog.exec_()
            self.update_status()
            
        except Exception as e:
            logger.error(f"测试密码设置界面时发生错误: {e}")
    
    def clear_password_data(self):
        """清除所有密码数据"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self,
                "确认",
                "确定要清除所有密码数据吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.password_manager.clear_password():
                    logger.info("密码数据清除成功")
                    QMessageBox.information(self, "成功", "密码数据已清除")
                else:
                    logger.error("密码数据清除失败")
                    QMessageBox.warning(self, "错误", "密码数据清除失败")
                    
                self.update_status()
                
        except Exception as e:
            logger.error(f"清除密码数据时发生错误: {e}")

def main():
    """主函数"""
    try:
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("密码功能测试")
        
        # 创建测试窗口
        window = PasswordTestWindow()
        window.show()
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"程序运行时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()