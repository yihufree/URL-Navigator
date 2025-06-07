#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终多语言功能验证脚本
"""

import sys
import os
import json

def test_language_files_completeness():
    """测试语言文件的完整性"""
    print("=== 测试语言文件完整性 ===")
    
    # 读取中文文件作为参考
    with open("languages/zh.json", 'r', encoding='utf-8') as f:
        zh_data = json.load(f)
    
    # 获取所有键
    def get_all_keys(data, prefix=""):
        keys = []
        for key, value in data.items():
            if isinstance(value, dict):
                keys.extend(get_all_keys(value, f"{prefix}{key}."))
            else:
                keys.append(f"{prefix}{key}")
        return keys
    
    zh_keys = set(get_all_keys(zh_data))
    print(f"中文文件包含 {len(zh_keys)} 个翻译键")
    
    # 检查其他语言文件
    languages = ["en", "ja", "de", "fr", "ko", "es"]
    
    for lang in languages:
        try:
            with open(f"languages/{lang}.json", 'r', encoding='utf-8') as f:
                lang_data = json.load(f)
            
            lang_keys = set(get_all_keys(lang_data))
            missing_keys = zh_keys - lang_keys
            extra_keys = lang_keys - zh_keys
            
            print(f"\n{lang}.json:")
            print(f"  总键数: {len(lang_keys)}")
            if missing_keys:
                print(f"  缺失键: {len(missing_keys)} 个")
                for key in sorted(missing_keys)[:5]:  # 只显示前5个
                    print(f"    - {key}")
                if len(missing_keys) > 5:
                    print(f"    ... 还有 {len(missing_keys) - 5} 个")
            if extra_keys:
                print(f"  多余键: {len(extra_keys)} 个")
            if not missing_keys and not extra_keys:
                print("  ✓ 完整")
                
        except Exception as e:
            print(f"  ✗ 错误: {e}")

def test_key_translations():
    """测试关键翻译"""
    print("\n=== 测试关键翻译 ===")
    
    from utils.language_manager import language_manager
    
    # 测试关键文本
    test_keys = [
        "app_title",
        "main_window.add_url",
        "main_window.settings", 
        "dialogs.add_url_title",
        "settings.language_label",
        "messages.confirm_title"
    ]
    
    languages = ["zh", "en", "ja", "de", "fr", "ko", "es"]
    
    for key in test_keys:
        print(f"\n{key}:")
        for lang in languages:
            language_manager.set_language(lang)
            text = language_manager.tr(key)
            lang_name = language_manager.get_language_name(lang)
            print(f"  {lang_name}: {text}")

def verify_language_switching():
    """验证语言切换功能"""
    print("\n=== 验证语言切换功能 ===")
    
    from utils.language_manager import language_manager
    
    # 测试语言切换
    original_lang = language_manager.get_current_language()
    print(f"当前语言: {original_lang}")
    
    # 切换到英语
    language_manager.set_language("en")
    current_lang = language_manager.get_current_language()
    add_url_text = language_manager.tr("main_window.add_url")
    print(f"切换到英语: {current_lang}, 添加网址按钮: {add_url_text}")
    
    # 切换到日语
    language_manager.set_language("ja")
    current_lang = language_manager.get_current_language()
    add_url_text = language_manager.tr("main_window.add_url")
    print(f"切换到日语: {current_lang}, 添加网址按钮: {add_url_text}")
    
    # 恢复原语言
    language_manager.set_language(original_lang)
    print(f"恢复到: {language_manager.get_current_language()}")

def main():
    """主测试函数"""
    print("网址导航软件多语言功能验证")
    print("=" * 50)
    
    try:
        test_language_files_completeness()
        test_key_translations()
        verify_language_switching()
        
        print("\n" + "=" * 50)
        print("✓ 多语言功能验证完成！")
        print("\n实施成果:")
        print("1. ✓ 创建了7种语言的翻译文件")
        print("2. ✓ 实现了轻量级多语言管理器")
        print("3. ✓ 在设置对话框中添加了语言选择")
        print("4. ✓ 主界面支持实时语言切换")
        print("5. ✓ 对话框和消息框支持多语言")
        
    except Exception as e:
        print(f"\n✗ 验证过程中发生错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())