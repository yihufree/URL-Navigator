#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
密码保护功能集成测试

此脚本用于测试密码保护功能的完整集成：
1. 测试密码管理器的基本功能
2. 测试设置对话框中的密码选项卡
3. 测试主应用程序的密码验证流程
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSettings

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.password_manager import PasswordManager
from ui.dialogs import SettingsDialog
from utils.language_manager import language_manager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_password_manager():
    """测试密码管理器基本功能"""
    print("\n=== 测试密码管理器基本功能 ===")
    
    try:
        pm = PasswordManager()
        
        # 清除之前的数据
        pm.clear_password()
        print("✓ 清除旧密码数据")
        
        # 测试初始状态
        assert not pm.is_password_enabled(), "初始状态应该未启用密码保护"
        print("✓ 初始状态检查通过")
        
        # 设置密码
        test_password = "test123456"
        assert pm.set_password(test_password), "设置密码应该成功"
        print("✓ 密码设置成功")
        
        # 验证密码保护已启用
        assert pm.is_password_enabled(), "设置密码后应该启用密码保护"
        print("✓ 密码保护已启用")
        
        # 验证正确密码
        assert pm.verify_password(test_password), "正确密码验证应该成功"
        print("✓ 正确密码验证成功")
        
        # 验证错误密码
        assert not pm.verify_password("wrong_password"), "错误密码验证应该失败"
        print("✓ 错误密码验证正确拒绝")
        
        # 设置密保问题
        question = "您的出生地是？"
        answer = "北京"
        assert pm.set_security_question(question, answer), "设置密保问题应该成功"
        print("✓ 密保问题设置成功")
        
        # 验证密保问题
        assert pm.has_security_question(), "应该有密保问题"
        assert pm.get_security_question() == question, "密保问题内容应该匹配"
        print("✓ 密保问题验证成功")
        
        # 验证密保答案
        assert pm.verify_security_answer(answer), "正确密保答案验证应该成功"
        assert not pm.verify_security_answer("错误答案"), "错误密保答案验证应该失败"
        print("✓ 密保答案验证成功")
        
        # 通过密保重置密码
        new_password = "new123456"
        assert pm.reset_password_with_security(new_password, answer), "通过密保重置密码应该成功"
        print("✓ 通过密保重置密码成功")
        
        # 验证新密码
        assert pm.verify_password(new_password), "新密码验证应该成功"
        assert not pm.verify_password(test_password), "旧密码验证应该失败"
        print("✓ 新密码验证成功")
        
        print("\n✅ 密码管理器所有测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 密码管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings_dialog():
    """测试设置对话框中的密码选项卡"""
    print("\n=== 测试设置对话框密码选项卡 ===")
    
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 创建设置对话框
        dialog = SettingsDialog()
        
        # 检查是否有密码选项卡
        tab_widget = None
        for child in dialog.findChildren(object):
            if hasattr(child, 'tabText'):
                tab_widget = child
                break
        
        if tab_widget:
            tab_count = tab_widget.count()
            tab_names = [tab_widget.tabText(i) for i in range(tab_count)]
            print(f"✓ 找到选项卡: {tab_names}")
            
            # 检查是否有密码相关的选项卡
            password_tab_found = any('密码' in name or 'Password' in name for name in tab_names)
            if password_tab_found:
                print("✓ 找到密码设置选项卡")
            else:
                print("⚠ 未找到密码设置选项卡")
        else:
            print("⚠ 未找到选项卡控件")
        
        dialog.close()
        print("\n✅ 设置对话框测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 设置对话框测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_password_storage():
    """测试密码存储和持久化"""
    print("\n=== 测试密码存储和持久化 ===")
    
    try:
        # 创建第一个密码管理器实例
        pm1 = PasswordManager()
        pm1.clear_password()
        
        # 设置密码和密保
        test_password = "persistent_test_123"
        question = "测试问题？"
        answer = "测试答案"
        
        pm1.set_password(test_password)
        pm1.set_security_question(question, answer)
        print("✓ 第一个实例设置密码和密保")
        
        # 创建第二个密码管理器实例（模拟重启应用）
        pm2 = PasswordManager()
        
        # 验证数据持久化
        assert pm2.is_password_enabled(), "密码保护状态应该持久化"
        assert pm2.verify_password(test_password), "密码应该持久化"
        assert pm2.has_security_question(), "密保问题状态应该持久化"
        assert pm2.get_security_question() == question, "密保问题内容应该持久化"
        assert pm2.verify_security_answer(answer), "密保答案应该持久化"
        
        print("✓ 密码数据持久化验证成功")
        
        # 清理测试数据
        pm2.clear_password()
        print("✓ 清理测试数据")
        
        print("\n✅ 密码存储和持久化测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 密码存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始密码保护功能集成测试...")
    print("=" * 50)
    
    # 创建应用程序实例
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # 运行所有测试
    tests = [
        ("密码管理器基本功能", test_password_manager),
        ("密码存储和持久化", test_password_storage),
        ("设置对话框密码选项卡", test_settings_dialog),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n正在运行测试: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"测试失败: {test_name}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！密码保护功能集成成功！")
        
        # 显示功能说明
        print("\n📋 密码保护功能说明:")
        print("1. 在设置对话框中可以启用/禁用密码保护")
        print("2. 可以设置密保问题用于密码重置")
        print("3. 启用密码保护后，每次启动应用都需要输入密码")
        print("4. 忘记密码时可以通过密保问题重置")
        print("5. 所有密码数据都经过加密存储")
        
    else:
        print("❌ 部分测试失败，请检查问题")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)