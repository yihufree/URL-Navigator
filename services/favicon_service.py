#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
from ui.icons import resource_path

logger = logging.getLogger(__name__)

class FaviconService:
    """网站图标获取服务"""
    
    def __init__(self, cache_dir):
        """
        初始化图标获取服务
        
        Args:
            cache_dir: 图标缓存目录
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # 添加默认超时设置
        self.timeout = 10  # 默认超时10秒
        
        # 保存应用根目录，用于生成相对路径
        self.app_root = os.path.abspath(".")
        
        logger.info(f"图标缓存目录: {cache_dir}")
    
    def get_favicon(self, url, min_size=16, prefer_size=32, force_refresh=False):
        """
        获取网站图标
        
        Args:
            url: 网站URL
            min_size: 最小图标尺寸
            prefer_size: 首选图标尺寸
            force_refresh: 是否强制刷新，忽略缓存
            
        Returns:
            图标的路径 (相对路径或默认图标路径)
        """
        # 规范化URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
            
        # 从URL中提取域名
        domain = urlparse(url).netloc
        
        # 检查缓存
        cache_key = self._get_cache_key(domain)
        cached_path = os.path.join(self.cache_dir, cache_key)
        
        # 如果不强制刷新且缓存存在，使用缓存
        if not force_refresh and os.path.exists(cached_path):
            logger.info(f"使用缓存的图标: {cached_path}")
            return self._convert_to_relative_path(cached_path)
        
        # 如果强制刷新，记录日志
        if force_refresh and os.path.exists(cached_path):
            logger.info(f"强制刷新图标: {domain}")
        
        # 尝试获取图标
        icon_url = self._fetch_favicon(url, min_size, prefer_size)
        
        if not icon_url:
            # 使用Google的favicon服务作为后备
            icon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
            logger.info(f"使用Google favicon服务: {icon_url}")
        
        # 下载图标
        try:
            response = self.session.get(icon_url, stream=True, timeout=self.timeout)
            if response.status_code == 200:
                # 保存到缓存
                with open(cached_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
                logger.info(f"图标已保存到: {cached_path}")
                return self._convert_to_relative_path(cached_path)
        except Exception as e:
            logger.error(f"下载图标失败: {e}")
        
        # 如果下载失败，返回默认图标(使用相对路径)
        default_icon = "resources/icons/globe.png"
        logger.info(f"使用默认图标: {default_icon}")
        return default_icon
    
    def get_website_title(self, url):
        """
        获取网站标题
        
        Args:
            url: 网站URL
            
        Returns:
            网站标题，如果获取失败则返回None
        """
        try:
            # 规范化URL
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
                
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    return title_tag.text.strip()
        except Exception as e:
            logger.error(f"获取网站标题失败: {e}")
        
        return None
    
    def _fetch_favicon(self, url, min_size=16, prefer_size=32):
        """
        从网站获取favicon
        
        Args:
            url: 网站URL
            min_size: 最小图标尺寸
            prefer_size: 首选图标尺寸
            
        Returns:
            图标URL，如果获取失败则返回None
        """
        try:
            # 获取网站HTML
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(f"获取网站HTML失败: {response.status_code}")
                return self._try_default_favicon(url)
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 收集所有可能的图标
            icons = []
            
            # 查找link标签中的图标
            for link in soup.find_all('link', rel=True, href=True):
                rel = link['rel']
                if not isinstance(rel, list):
                    rel = [rel]
                
                rel_str = ' '.join(rel).lower()
                
                if 'icon' in rel_str or 'shortcut icon' in rel_str:
                    href = link['href']
                    icon_url = urljoin(url, href)
                    
                    # 获取尺寸信息
                    size = 0
                    if link.get('sizes'):
                        size_match = re.search(r'(\d+)x\d+', link['sizes'])
                        if size_match:
                            size = int(size_match.group(1))
                    
                    # 设置优先级
                    priority = 3
                    if 'shortcut icon' in rel_str or rel_str == 'icon':
                        priority = 3
                    elif rel_str == 'apple-touch-icon':
                        priority = 2
                    elif 'apple-touch-icon' in rel_str:
                        priority = 1
                    
                    icons.append({
                        'url': icon_url,
                        'size': size,
                        'priority': priority
                    })
            
            # 添加默认的favicon.ico位置
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            icons.append({
                'url': f"{base_url}/favicon.ico",
                'size': 0,
                'priority': 4
            })
            
            # 按优先级和尺寸排序图标
            icons.sort(key=lambda x: (-x['priority'], -x['size']))
            
            # 尝试获取每个图标
            for icon in icons:
                try:
                    # 检查图标是否存在
                    head_response = self.session.head(icon['url'], timeout=self.timeout)
                    if head_response.status_code == 200:
                        # 如果图标没有尺寸信息，尝试获取
                        if icon['size'] == 0:
                            try:
                                img_response = self.session.get(icon['url'], timeout=self.timeout)
                                if img_response.status_code == 200:
                                    img = Image.open(BytesIO(img_response.content))
                                    icon['size'] = min(img.width, img.height)
                            except (requests.RequestException, IOError, ValueError) as e:
                                logger.warning(f"获取图标尺寸失败: {e}")
                        
                        # 检查图标尺寸是否符合要求
                        if icon['size'] >= min_size:
                            logger.info(f"找到图标: {icon['url']} (尺寸: {icon['size']})")
                            return icon['url']
                except Exception as e:
                    logger.warning(f"检查图标失败: {icon['url']} - {e}")
            
            # 如果没有找到符合尺寸要求的图标，返回第一个可用的图标
            for icon in icons:
                try:
                    head_response = self.session.head(icon['url'], timeout=self.timeout)
                    if head_response.status_code == 200:
                        logger.info(f"使用备选图标: {icon['url']}")
                        return icon['url']
                except (requests.RequestException, IOError) as e:
                    logger.warning(f"检查图标可用性失败: {e}")
            
            # 如果所有尝试都失败，返回None
            return None
            
        except Exception as e:
            logger.error(f"获取图标失败: {e}")
            return self._try_default_favicon(url)
    
    def _try_default_favicon(self, url):
        """尝试获取默认的favicon.ico"""
        try:
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            favicon_url = f"{base_url}/favicon.ico"
            
            head_response = self.session.head(favicon_url, timeout=self.timeout)
            if head_response.status_code == 200:
                logger.info(f"使用默认favicon.ico: {favicon_url}")
                return favicon_url
        except Exception as e:
            logger.warning(f"获取默认favicon.ico失败: {e}")
        
        return None
    
    def _get_cache_key(self, domain):
        """生成缓存键"""
        # 移除非法文件名字符
        safe_domain = re.sub(r'[\\/*?:"<>|]', '_', domain)
        return f"{safe_domain}.png"
    
    def _convert_to_relative_path(self, absolute_path):
        """
        将绝对路径转换为相对于应用根目录的相对路径
        
        Args:
            absolute_path: 绝对路径
            
        Returns:
            相对路径，如果无法转换则返回原路径
        """
        try:
            # 如果是应用自带的默认图标，直接返回其相对路径
            if "resources/icons/globe.png" in absolute_path:
                return "resources/icons/globe.png"
                
            # 尝试将绝对路径转换为相对路径
            rel_path = os.path.relpath(absolute_path, self.app_root)
            logger.debug(f"转换图标路径: {absolute_path} -> {rel_path}")
            return rel_path
        except Exception as e:
            logger.warning(f"无法转换为相对路径: {absolute_path}, 错误: {e}")
            return absolute_path