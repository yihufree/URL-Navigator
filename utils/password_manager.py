# -*- coding: utf-8 -*-

import hashlib
import os
import json
import logging
from PyQt5.QtCore import QSettings

logger = logging.getLogger(__name__)

class PasswordManager:
    """密码管理器"""
    
    def __init__(self, app_name="URL Navigator"):
        """
        初始化密码管理器
        
        Args:
            app_name: 应用程序名称
        """
        self.app_name = app_name
        self.settings = QSettings(app_name, app_name)
        
    def _hash_password(self, password, salt=None):
        """
        对密码进行哈希加密
        
        Args:
            password: 原始密码
            salt: 盐值，如果为None则生成新的盐值
            
        Returns:
            tuple: (哈希值, 盐值)
        """
        if salt is None:
            salt = os.urandom(32)  # 生成32字节的随机盐值
        elif isinstance(salt, str):
            salt = bytes.fromhex(salt)
            
        # 使用PBKDF2进行密码哈希
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt, 
                                          100000)  # 100000次迭代
        
        return password_hash.hex(), salt.hex()
    
    def set_password(self, password):
        """
        设置密码
        
        Args:
            password: 新密码
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if not password or len(password.strip()) == 0:
                logger.error("密码不能为空")
                return False
                
            password_hash, salt = self._hash_password(password)
            
            # 保存到QSettings
            self.settings.setValue("security/password_hash", password_hash)
            self.settings.setValue("security/password_salt", salt)
            self.settings.setValue("security/password_enabled", True)
            self.settings.sync()
            
            logger.info("密码设置成功")
            return True
            
        except Exception as e:
            logger.error(f"设置密码失败: {e}")
            return False
    
    def verify_password(self, password):
        """
        验证密码
        
        Args:
            password: 待验证的密码
            
        Returns:
            bool: 验证是否成功
        """
        try:
            if not self.is_password_enabled():
                return True  # 如果未启用密码保护，直接返回True
                
            stored_hash = self.settings.value("security/password_hash", "")
            stored_salt = self.settings.value("security/password_salt", "")
            
            if not stored_hash or not stored_salt:
                logger.warning("未找到存储的密码信息")
                return False
                
            # 使用存储的盐值对输入密码进行哈希
            password_hash, _ = self._hash_password(password, stored_salt)
            
            # 比较哈希值
            is_valid = password_hash == stored_hash
            
            if is_valid:
                logger.info("密码验证成功")
            else:
                logger.warning("密码验证失败")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"验证密码失败: {e}")
            return False
    
    def is_password_enabled(self):
        """
        检查是否启用了密码保护
        
        Returns:
            bool: 是否启用密码保护
        """
        enabled = self.settings.value("security/password_enabled", False)
        if isinstance(enabled, str):
            enabled = enabled.lower() == "true"
        return bool(enabled)
    
    def disable_password(self):
        """
        禁用密码保护
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.settings.setValue("security/password_enabled", False)
            self.settings.sync()
            logger.info("密码保护已禁用")
            return True
        except Exception as e:
            logger.error(f"禁用密码保护失败: {e}")
            return False
    
    def clear_password(self):
        """
        清除密码（删除所有密码相关数据）
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.settings.remove("security/password_hash")
            self.settings.remove("security/password_salt")
            self.settings.remove("security/password_enabled")
            self.settings.remove("security/security_question")
            self.settings.remove("security/security_answer_hash")
            self.settings.remove("security/security_answer_salt")
            self.settings.sync()
            logger.info("密码数据已清除")
            return True
        except Exception as e:
            logger.error(f"清除密码数据失败: {e}")
            return False
    
    def set_security_question(self, question, answer):
        """
        设置密保问题和答案
        
        Args:
            question: 密保问题
            answer: 密保答案
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if not question or not answer:
                logger.error("密保问题和答案不能为空")
                return False
                
            # 对答案进行哈希加密（不区分大小写）
            answer_hash, salt = self._hash_password(answer.lower().strip())
            
            # 保存到QSettings
            self.settings.setValue("security/security_question", question)
            self.settings.setValue("security/security_answer_hash", answer_hash)
            self.settings.setValue("security/security_answer_salt", salt)
            self.settings.sync()
            
            logger.info("密保问题设置成功")
            return True
            
        except Exception as e:
            logger.error(f"设置密保问题失败: {e}")
            return False
    
    def get_security_question(self):
        """
        获取密保问题
        
        Returns:
            str: 密保问题，如果未设置则返回空字符串
        """
        return self.settings.value("security/security_question", "")
    
    def verify_security_answer(self, answer):
        """
        验证密保答案
        
        Args:
            answer: 待验证的答案
            
        Returns:
            bool: 验证是否成功
        """
        try:
            stored_hash = self.settings.value("security/security_answer_hash", "")
            stored_salt = self.settings.value("security/security_answer_salt", "")
            
            if not stored_hash or not stored_salt:
                logger.warning("未找到存储的密保答案信息")
                return False
                
            # 使用存储的盐值对输入答案进行哈希（不区分大小写）
            answer_hash, _ = self._hash_password(answer.lower().strip(), stored_salt)
            
            # 比较哈希值
            is_valid = answer_hash == stored_hash
            
            if is_valid:
                logger.info("密保答案验证成功")
            else:
                logger.warning("密保答案验证失败")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"验证密保答案失败: {e}")
            return False
    
    def has_security_question(self):
        """
        检查是否设置了密保问题
        
        Returns:
            bool: 是否设置了密保问题
        """
        question = self.get_security_question()
        return bool(question and question.strip())
    
    def reset_password_with_security(self, new_password, security_answer):
        """
        通过密保问题重置密码
        
        Args:
            new_password: 新密码
            security_answer: 密保答案
            
        Returns:
            bool: 重置是否成功
        """
        try:
            # 首先验证密保答案
            if not self.verify_security_answer(security_answer):
                logger.warning("密保答案验证失败，无法重置密码")
                return False
                
            # 设置新密码
            if self.set_password(new_password):
                logger.info("通过密保问题重置密码成功")
                return True
            else:
                logger.error("设置新密码失败")
                return False
                
        except Exception as e:
            logger.error(f"通过密保问题重置密码失败: {e}")
            return False