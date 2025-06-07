#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize

logger = logging.getLogger(__name__)

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包后环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class IconManager:
    """图标管理器"""
    
    def __init__(self, resources_path="resources"):
        """
        初始化图标管理器
        
        Args:
            resources_path: 资源文件夹路径
        """
        self.resources_path = resources_path
        self.icons_path = os.path.join(resources_path, "icons")
        self.icon_cache = {}
        
        # 确保图标目录存在
        if not os.path.exists(self.icons_path):
            os.makedirs(self.icons_path)
        
        # 初始化默认图标
        self._init_default_icons()
    
    def _init_default_icons(self):
        """初始化默认图标"""
        # 定义默认图标列表
        self.default_icons = {
            "app": "app_icon.png",
            "folder": "folder.png",
            "folder_open": "folder-open.png",
            "folder_add": "folder-add.png",
            "folder_large": "folder-large.png",
            "url": "globe.png",
            "edit": "edit.png",
            "delete": "delete.png",
            "import": "import.png",
            "export": "export.png",
            "search": "search.png",
            "settings": "settings.png",
            "refresh": "refresh.png",
            "add": "add.png",
            "back": "back.png",
            "forward": "forward.png",
            "home": "home.png",
            "favorite": "favorite.png",
            "unfavorite": "unfavorite.png",
            "default_favicon": "default_favicon.png",
            "editurl": "resources/icons/editurl.png"
        }
        
        # 检查默认图标是否存在，如果不存在则创建一个空图标
        for icon_name, icon_file in self.default_icons.items():
            icon_path = os.path.join(self.icons_path, icon_file)
            if not os.path.exists(icon_path):
                logger.warning(f"默认图标不存在: {icon_path}")
                self._create_empty_icon(icon_path)
    
    def _create_empty_icon(self, icon_path, size=32):
        """
        创建空图标
        
        Args:
            icon_path: 图标路径
            size: 图标大小
        """
        try:
            from PIL import Image, ImageDraw
            
            # 创建透明图像
            img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
            
            # 绘制简单边框
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, size-1, size-1], outline=(200, 200, 200, 128))
            
            # 保存图像
            img.save(icon_path)
            logger.info(f"已创建空图标: {icon_path}")
        except Exception as e:
            logger.error(f"创建空图标失败: {e}")
    
    def get_icon(self, icon_name, fallback=None):
        """
        获取图标
        
        Args:
            icon_name: 图标名称或路径
            fallback: 备用图标名称
            
        Returns:
            QIcon对象
        """
        # 检查缓存
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]
        
        icon = None
        
        # 如果是默认图标名称
        if icon_name in self.default_icons:
            icon_path = os.path.join(self.icons_path, self.default_icons[icon_name])
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
        
        # 如果是文件路径
        elif os.path.exists(icon_name):
            icon = QIcon(icon_name)
        
        # 如果图标加载失败，使用备用图标
        if icon is None or icon.isNull():
            if fallback and fallback in self.default_icons:
                icon_path = os.path.join(self.icons_path, self.default_icons[fallback])
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
            
            # 如果备用图标也失败，使用默认图标
            if icon is None or icon.isNull():
                default_icon = "url" if "favicon" in icon_name.lower() else "folder"
                icon_path = os.path.join(self.icons_path, self.default_icons[default_icon])
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                else:
                    # 最后的备用方案：创建一个空图标
                    icon = QIcon()
        
        # 缓存图标
        self.icon_cache[icon_name] = icon
        
        return icon
    
    def get_pixmap(self, icon_name, size=32, fallback=None):
        """
        获取图标的像素图
        
        Args:
            icon_name: 图标名称或路径
            size: 图标大小
            fallback: 备用图标名称
            
        Returns:
            QPixmap对象
        """
        icon = self.get_icon(icon_name, fallback)
        return icon.pixmap(QSize(size, size))
    
    def clear_cache(self):
        """清除图标缓存"""
        self.icon_cache.clear()
        logger.info("图标缓存已清除")
    
    def create_colored_icon(self, icon_name, color, size=32):
        """
        创建彩色图标
        
        Args:
            icon_name: 图标名称
            color: 颜色 (r, g, b)
            size: 图标大小
            
        Returns:
            彩色图标路径
        """
        try:
            from PIL import Image, ImageOps
            
            # 获取原始图标路径
            if icon_name in self.default_icons:
                icon_path = os.path.join(self.icons_path, self.default_icons[icon_name])
            else:
                icon_path = icon_name
            
            if not os.path.exists(icon_path):
                logger.error(f"图标不存在: {icon_path}")
                return None
            
            # 生成彩色图标的文件名
            r, g, b = color
            colored_icon_name = f"{os.path.splitext(os.path.basename(icon_path))[0]}_{r}_{g}_{b}.png"
            colored_icon_path = os.path.join(self.icons_path, colored_icon_name)
            
            # 如果彩色图标已存在，直接返回
            if os.path.exists(colored_icon_path):
                return colored_icon_path
            
            # 打开原始图标
            img = Image.open(icon_path).convert("RGBA")
            
            # 调整大小
            if img.width != size or img.height != size:
                img = img.resize((size, size), Image.LANCZOS)
            
            # 创建彩色版本
            r, g, b = color
            colored_img = ImageOps.colorize(
                ImageOps.grayscale(img), 
                (0, 0, 0), 
                (r, g, b)
            ).convert("RGBA")
            
            # 保留原始透明度
            colored_img.putalpha(img.getchannel("A"))
            
            # 保存彩色图标
            colored_img.save(colored_icon_path)
            
            # 清除缓存中的旧图标
            if colored_icon_path in self.icon_cache:
                del self.icon_cache[colored_icon_path]
            
            return colored_icon_path
        
        except Exception as e:
            logger.error(f"创建彩色图标失败: {e}")
            return None
    
    def get_system_icon(self, name):
        """
        获取系统图标
        
        Args:
            name: 图标名称
            
        Returns:
            QIcon对象
        """
        # 尝试从系统主题获取图标
        icon = QIcon.fromTheme(name)
        
        # 如果系统主题没有该图标，使用默认图标
        if icon.isNull():
            if name in self.default_icons:
                icon_path = os.path.join(self.icons_path, self.default_icons[name])
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
            else:
                # 映射常见的系统图标名称到默认图标
                icon_map = {
                    "document-new": "add",
                    "document-open": "import",
                    "document-save": "export",
                    "edit-delete": "delete",
                    "edit-find": "search",
                    "go-home": "home",
                    "go-previous": "back",
                    "go-next": "forward",
                    "folder-new": "folder_add",
                    "preferences-system": "settings"
                }
                
                if name in icon_map and icon_map[name] in self.default_icons:
                    icon_path = os.path.join(self.icons_path, self.default_icons[icon_map[name]])
                    if os.path.exists(icon_path):
                        icon = QIcon(icon_path)
        
        return icon
    
    def generate_favicon_placeholder(self, domain, size=32):
        """
        为域名生成占位图标
        
        Args:
            domain: 域名
            size: 图标大小
            
        Returns:
            占位图标路径
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import hashlib
            
            # 生成文件名
            hash_obj = hashlib.md5(domain.encode())
            filename = f"favicon_placeholder_{hash_obj.hexdigest()[:8]}.png"
            icon_path = os.path.join(self.icons_path, filename)
            
            # 如果已存在，直接返回
            if os.path.exists(icon_path):
                return icon_path
            
            # 从域名生成颜色
            hash_bytes = hash_obj.digest()
            hue = hash_bytes[0] / 255.0
            saturation = 0.5 + hash_bytes[1] / 512.0
            value = 0.7 + hash_bytes[2] / 512.0
            
            # HSV转RGB
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            background_color = (int(r * 255), int(g * 255), int(b * 255))
            
            # 创建图像
            img = Image.new('RGBA', (size, size), background_color)
            draw = ImageDraw.Draw(img)
            
            # 获取域名首字母
            letter = domain[0].upper() if domain else "?"
            
            # 尝试加载字体
            try:
                # 尝试使用系统字体
                font_size = int(size * 0.6)
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                try:
                    # 尝试使用PIL默认字体
                    font = ImageFont.load_default()
                except Exception:
                    # 如果字体加载失败，使用简单绘制
                    draw.rectangle([size//3, size//3, 2*size//3, 2*size//3], fill=(255, 255, 255))
                    img.save(icon_path)
                    return icon_path
            
            # 计算文本大小和位置
            text_width, text_height = draw.textsize(letter, font=font)
            position = ((size - text_width) // 2, (size - text_height) // 2)
            
            # 绘制文本
            draw.text(position, letter, fill=(255, 255, 255), font=font)
            
            # 保存图像
            img.save(icon_path)
            
            return icon_path
        
        except Exception as e:
            logger.error(f"生成占位图标失败: {e}")
            return None

class IconProvider:
    """图标提供器，处理应用中所有图标的加载"""
    
    # 图标名称到文件路径的映射
    ICON_MAP = {
        "folder": "resources/icons/folder.png",
        "folder-large": "resources/icons/folder-large.png",
        "folder-open": "resources/icons/folder-open.png",
        "folder-add": "resources/icons/folder-add.png",
        "globe": "resources/icons/globe.png",
        "import": "resources/icons/import.png",
        "export": "resources/icons/export.png",
        "search": "resources/icons/search.png",
        "edit": "resources/icons/edit.png",
        "delete": "resources/icons/delete.png",
        "paste": "resources/icons/Paste.png",
        "copy": "resources/icons/copy.png",
        "settings": "resources/icons/settings.png",
        "refresh": "resources/icons/refresh.png",
        "app_icon": "resources/icons/app_icon.png"
    }
    
    @classmethod
    def get_icon(cls, icon_name):
        """
        获取指定名称的图标
        
        Args:
            icon_name: 图标名称或路径
            
        Returns:
            QIcon 对象
        """
        # 如果是已知图标名称，使用映射的路径
        if icon_name in cls.ICON_MAP:
            icon_path = resource_path(cls.ICON_MAP[icon_name])
            return QIcon(icon_path)
        
        # 如果是相对路径
        if icon_name.startswith("resources/") or not os.path.isabs(icon_name):
            # 尝试使用相对路径查找
            rel_path = resource_path(icon_name)
            if os.path.exists(rel_path):
                return QIcon(rel_path)
            
            # 如果找不到，尝试从当前目录查找
            if os.path.exists(icon_name):
                return QIcon(icon_name)
            
            # 如果都找不到，使用默认图标
            logger.warning(f"找不到图标: {icon_name}，使用默认图标")
            return QIcon(resource_path("resources/icons/globe.png"))
        
        # 如果是完整路径或其他情况
        if os.path.exists(icon_name):
            return QIcon(icon_name)
        else:
            # 如果绝对路径不存在，尝试作为相对路径解析
            rel_path = resource_path(icon_name)
            if os.path.exists(rel_path):
                return QIcon(rel_path)
            
            logger.warning(f"图标文件不存在: {icon_name}，使用默认图标")
            return QIcon(resource_path("resources/icons/globe.png"))

# 创建全局图标提供器实例以便导入使用
icon_provider = IconProvider()