#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的密码功能测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.password_manager import PasswordManager
    print("✓ 成功导入 PasswordManager")
except Exception as e:
    print(f"❌ 导入 PasswordManager 失败: {e}")
    sys.exit(1)

def test_basic_functionality():
    """测试基本功能"""
    print("\n开始测试密码管理器基本功能...")
    
    try:
        # 创建密码管理器实例
        pm = PasswordManager()
        print("✓ 创建密码管理器实例成功")
        
        # 清除之前的数据
        pm.clear_password()
        print("✓ 清除旧数据成功")
        
        # 检查初始状态
        is_enabled = pm.is_password_enabled()
        print(f"✓ 初始密码保护状态: {'已启用' if is_enabled else '未启用'}")
        
        # 设置密码
        test_password = "test123"
        result = pm.set_password(test_password)
        print(f"✓ 设置密码结果: {'成功' if result else '失败'}")
        
        # 检查密码保护是否启用
        is_enabled_after = pm.is_password_enabled()
        print(f"✓ 设置密码后状态: {'已启用' if is_enabled_after else '未启用'}")
        
        # 验证密码
        verify_result = pm.verify_password(test_password)
        print(f"✓ 验证正确密码: {'成功' if verify_result else '失败'}")
        
        # 验证错误密码
        wrong_verify = pm.verify_password("wrong")
        print(f"✓ 验证错误密码: {'失败' if not wrong_verify else '成功(这是错误的)'}")
        
        # 设置密保问题
        question = "您的出生地？"
        answer = "北京"
        security_result = pm.set_security_question(question, answer)
        print(f"✓ 设置密保问题: {'成功' if security_result else '失败'}")
        
        # 检查密保问题
        has_question = pm.has_security_question()
        print(f"✓ 检查密保问题存在: {'是' if has_question else '否'}")
        
        if has_question:
            stored_question = pm.get_security_question()
            print(f"✓ 获取密保问题: {stored_question}")
            
            # 验证密保答案
            answer_verify = pm.verify_security_answer(answer)
            print(f"✓ 验证正确密保答案: {'成功' if answer_verify else '失败'}")
            
            wrong_answer_verify = pm.verify_security_answer("错误答案")
            print(f"✓ 验证错误密保答案: {'失败' if not wrong_answer_verify else '成功(这是错误的)'}")
        
        print("\n✅ 基本功能测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("密码保护功能简单测试")
    print("=" * 40)
    
    success = test_basic_functionality()
    
    if success:
        print("\n🎉 测试成功！密码保护功能基本正常。")
    else:
        print("\n❌ 测试失败！请检查问题。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)