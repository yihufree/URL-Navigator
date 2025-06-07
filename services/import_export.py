#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import traceback
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class ImportExportService(QObject):
    """书签导入导出服务"""
    
    # 定义信号
    import_progress = pyqtSignal(int, str)
    export_progress = pyqtSignal(int, str)
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
    
    def import_json(self, file_path):
        """
        从JSON文件导入书签
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            导入的书签数量
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                self.import_progress.emit(100, "导入失败: 文件不存在")
                return 0
                
            self.import_progress.emit(0, "正在读取JSON文件...")
            
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    imported_data = json.load(f)
                except json.JSONDecodeError:
                    logger.error("文件不是有效的JSON格式")
                    self.import_progress.emit(100, "导入失败: 文件不是有效的JSON格式")
                    return 0
            
            # 验证数据结构
            self.import_progress.emit(20, "正在验证数据结构...")
            if not isinstance(imported_data, dict):
                logger.error("JSON数据结构不正确，预期是对象/字典")
                self.import_progress.emit(100, "导入失败: JSON数据结构不正确")
                return 0
            
            # 检查数据是否有效
            valid_structure = False
            for item in imported_data.values():
                if isinstance(item, dict) and item.get("type") in ["folder", "url"]:
                    valid_structure = True
                    break
            
            if not valid_structure:
                logger.error("JSON数据结构不符合书签格式")
                self.import_progress.emit(100, "导入失败: JSON数据结构不符合书签格式")
                return 0
            
            # 导入到数据结构
            self.import_progress.emit(50, "正在导入数据...")
            
            # 在已导入文件夹下导入
            base_name = "已导入(JSON)"
            folder_name = base_name
            counter = 2
            while folder_name in self.data_manager.data:
                folder_name = f"{base_name}({counter})"
                counter += 1
            
            # 添加到数据管理器
            self.data_manager.data[folder_name] = {
                "type": "folder",
                "children": imported_data
            }
            
            # 保存并刷新
            self.data_manager.data_changed.emit()
            
            # 计算导入项目数量
            count = self._count_items(imported_data)
            
            self.import_progress.emit(100, f"导入完成，共导入 {count} 个项目")
            logger.info(f"从 {file_path} 导入了 {count} 个书签")
            return count
            
        except Exception as e:
            logger.error(f"导入JSON书签失败: {e}")
            logger.error(traceback.format_exc())
            self.import_progress.emit(100, f"导入失败: {str(e)}")
            return 0
    
    def import_html(self, file_path):
        """
        从HTML文件导入书签（平铺+重建层级兜底方案，含调试输出，修复同名文件夹KeyError）
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                self.import_progress.emit(100, "导入失败: 文件不存在")
                return 0
                
            self.import_progress.emit(0, "正在读取文件...")
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024*1024)
            logger.info(f"导入文件大小: {file_size_mb:.2f} MB")
            logger.info(f"导入文件路径: {file_path}")
            
            # 文件大小限制检查
            MAX_FILE_SIZE_MB = 3  # 3MB
            if file_size_mb > MAX_FILE_SIZE_MB:
                logger.error(f"文件太大: {file_size_mb:.2f} MB，超过 {MAX_FILE_SIZE_MB} MB 限制")
                self.import_progress.emit(100, f"导入失败: 文件太大 ({file_size_mb:.2f} MB)，超过 {MAX_FILE_SIZE_MB} MB 限制")
                return 0
                
            if file_size == 0:
                logger.error("文件为空")
                self.import_progress.emit(100, "导入失败: 文件为空")
                return 0
                
            # 只读取一次文件内容
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            html_content = None
            used_encoding = None
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        html_content = f.read()
                    used_encoding = encoding
                    logger.info(f"成功使用 {encoding} 编码读取文件")
                    break
                except Exception as e:
                    logger.warning(f"使用 {encoding} 编码读取文件失败: {e}")
            if not html_content:
                logger.error("无法读取文件内容")
                self.import_progress.emit(100, "导入失败: 无法读取文件内容")
                return 0
            logger.info(f"文件内容前500字符: {html_content[:500]}")
            
            # HTML安全验证
            self.import_progress.emit(5, "正在验证HTML结构...")
            
            # 基本结构验证
            if not self._is_valid_html_structure(html_content):
                logger.error("HTML结构无效或可能存在安全风险")
                self.import_progress.emit(100, "导入失败: HTML结构无效或可能存在安全风险")
                return 0
            
            # 检查DL标签
            if '<DL>' not in html_content.upper() and '<DL ' not in html_content.upper():
                logger.warning("文件中未找到DL标签，尝试用通用解析方式")
                return self._import_html_chunked(file_path)
                
            self.import_progress.emit(10, "正在解析HTML...")
            
            # 使用更安全的HTML解析方式
            try:
                from lxml.html.clean import Cleaner
                from lxml import etree
                
                # 创建一个安全的HTML清洗器
                cleaner = Cleaner(
                    scripts=True,        # 移除script标签
                    javascript=True,     # 移除内联JavaScript
                    style=True,          # 移除style标签
                    inline_style=True,   # 移除内联样式
                    forms=True,          # 移除表单
                    frames=True,         # 移除框架
                    embedded=True,       # 移除嵌入式标签
                    meta=True,           # 移除meta标签
                    links=False,         # 保留链接
                    remove_tags=['object', 'embed']  # 移除其他危险标签
                )
                
                # 清理HTML
                try:
                    clean_html = cleaner.clean_html(html_content)
                    soup = BeautifulSoup(clean_html, 'html.parser')
                except Exception as e:
                    # 如果lxml清理失败，回退到传统方式
                    logger.warning(f"高级HTML清理失败，使用传统方式: {str(e)}")
                    soup = BeautifulSoup(html_content, 'html.parser')
                    soup = self._manual_clean_html(soup)
            except ImportError:
                # 如果没有lxml库，使用传统方式
                logger.warning("未找到lxml库，使用传统HTML解析")
                soup = BeautifulSoup(html_content, 'html.parser')
                # 手动清理危险内容
                soup = self._manual_clean_html(soup)
            except Exception as e:
                # 捕获任何其他异常，确保程序不会崩溃
                logger.warning(f"使用lxml发生错误: {str(e)}，回退到传统方式")
                soup = BeautifulSoup(html_content, 'html.parser')
                soup = self._manual_clean_html(soup)
            
            dl = soup.find('dl')
            logger.info(f"soup.find('dl') 结果: {dl}")
            if not dl:
                logger.error("未找到<DL>结构，尝试正则兜底...")
                # 兜底：用正则提取所有链接
                links = re.findall(r'<A[^>]*HREF="([^"]*)"[^>]*>(.*?)</A>', html_content, re.IGNORECASE)
                logger.info(f"正则兜底提取到 {len(links)} 个链接")
                if links:
                    imported_data = {"未分类导入链接": {"type": "folder", "children": {}}}
                    container = imported_data["未分类导入链接"]["children"]
                    for url, name in links:
                        url_item = {
                            "type": "url",
                            "url": url,
                            "name": name.strip() or url,
                            "icon": ""
                        }
                        final_name = name.strip() or url
                        counter = 1
                        while final_name in container:
                            final_name = f"{name.strip() or url} ({counter})"
                            counter += 1
                        container[final_name] = url_item
                    # === 修正：所有导入内容放入"已导入"文件夹 ===
                    base_name = "已导入(HTML)"
                    folder_name = base_name
                    counter = 2
                    while folder_name in self.data_manager.data:
                        folder_name = f"{base_name}({counter})"
                        counter += 1
                    self.data_manager.data[folder_name] = {
                        "type": "folder",
                        "children": imported_data
                    }
                    self.data_manager.data_changed.emit()
                    count = len(links)
                    self.import_progress.emit(100, f"导入完成，共导入 {count} 个链接")
                    return count
                self.import_progress.emit(100, "导入失败: 未找到书签结构")
                return 0
            # 步骤1：平铺收集所有文件夹和链接
            flat_folders = []  # (folder_name, dt)
            flat_links = []    # (name, url, a, dt)
            def collect_all_items(dl):
                items = dl.find_all('dt')
                for dt in items:
                    h3 = dt.find('h3')
                    if h3:
                        folder_name = h3.text.strip() or "未命名文件夹"
                        flat_folders.append((folder_name, dt))
                    a = dt.find('a')
                    if a and a.get('href'):
                        url = a['href']
                        name = a.text.strip() or url
                        flat_links.append((name, url, a, dt))
                    # 递归子DL
                    sub_dl = dt.find('dl')
                    if sub_dl:
                        collect_all_items(sub_dl)
            collect_all_items(dl)
            logger.info(f"平铺收集到文件夹数: {len(flat_folders)}，链接数: {len(flat_links)}")
            # 步骤2：初步平铺导入所有文件夹（用dt做key）
            imported_data = {}  # dt: folder dict
            folder_map = {}     # dt: container dict
            dt_to_name = {}     # dt: folder_name
            for folder_name, dt in flat_folders:
                folder = {"type": "folder", "children": {}}
                imported_data[dt] = folder
                folder_map[dt] = folder["children"]
                dt_to_name[dt] = folder_name
            # 步骤3：将链接放入其最近的父文件夹
            for name, url, a, dt in flat_links:
                parent = dt.parent
                found = False
                while parent:
                    if parent in folder_map:
                        container = folder_map[parent]
                        found = True
                        break
                    parent = getattr(parent, 'parent', None)
                if not found:
                    # 没有父文件夹，放到所有根文件夹外层
                    continue
                icon = a.get('icon', '')
                url_item = {
                    "type": "url",
                    "url": url,
                    "name": name,
                    "icon": icon
                }
                final_name = name
                counter = 1
                while final_name in container:
                    final_name = f"{name} ({counter})"
                    counter += 1
                container[final_name] = url_item
            # 步骤4：重建文件夹层级
            root_folders = set(imported_data.keys())
            for dt, folder in list(imported_data.items()):
                parent = dt.parent
                found = False
                while parent:
                    if parent in folder_map:
                        parent_container = folder_map[parent]
                        folder_name = dt_to_name[dt]
                        new_name = folder_name
                        counter = 1
                        while new_name in parent_container:
                            new_name = f"{folder_name} ({counter})"
                            counter += 1
                        parent_container[new_name] = folder
                        found = True
                        if dt in root_folders:
                            root_folders.remove(dt)
                        break
                    parent = getattr(parent, 'parent', None)
            # 步骤5：将所有根文件夹转为名字为key的dict
            final_data = {}
            for dt in root_folders:
                folder = imported_data[dt]
                folder_name = dt_to_name[dt]
                new_name = folder_name
                counter = 1
                while new_name in final_data:
                    new_name = f"{folder_name} ({counter})"
                    counter += 1
                final_data[new_name] = folder
            logger.info(f"最终导入数据结构: {final_data}")
            # === 修正：所有导入内容放入"已导入"文件夹 ===
            base_name = "已导入(HTML)"
            folder_name = base_name
            counter = 2
            while folder_name in self.data_manager.data:
                folder_name = f"{base_name}({counter})"
                counter += 1
            self.data_manager.data[folder_name] = {
                "type": "folder",
                "children": final_data
            }
            self.data_manager.data_changed.emit()
            count = self._count_items(final_data)
            self.import_progress.emit(100, f"导入完成，共导入 {count} 个项目")
            return count
        except Exception as e:
            logger.error(f"导入书签失败: {e}")
            logger.error(traceback.format_exc())
            self.import_progress.emit(100, f"导入失败: {str(e)}")
            return 0
    
    def _process_raw_links(self, links):
        """直接处理A标签链接列表"""
        imported_data = {"未分类导入链接": {"type": "folder", "children": {}}}
        container = imported_data["未分类导入链接"]["children"]
        
        for i, a in enumerate(links):
            if i % 50 == 0:
                self.import_progress.emit(20 + min(60, int(60 * (i / len(links)))), 
                                         f"正在处理链接 ({i}/{len(links)})...")
            
            url = a.get('href', '')
            if not url or url.startswith('javascript:') or url.startswith('#'):
                continue
                
            name = a.text.strip() or url
            
            # 创建URL项目
            url_item = {
                "type": "url",
                "url": url,
                "name": name,
                "icon": ""
            }
            
            # 处理重名
            final_name = name
            counter = 1
            while final_name in container:
                final_name = f"{name} ({counter})"
                counter += 1
            
            container[final_name] = url_item
        
        return imported_data
    
    def _import_html_chunked(self, file_path):
        """
        分块处理大型HTML文件
        
        Args:
            file_path: HTML文件路径
            
        Returns:
            导入的书签数量
        """
        try:
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024*1024)
            logger.info(f"分块导入文件大小: {file_size_mb:.2f} MB")
            
            # 文件大小限制检查
            MAX_FILE_SIZE_MB = 3  # 3MB
            if file_size_mb > MAX_FILE_SIZE_MB:
                logger.error(f"文件太大: {file_size_mb:.2f} MB，超过 {MAX_FILE_SIZE_MB} MB 限制")
                self.import_progress.emit(100, f"导入失败: 文件太大 ({file_size_mb:.2f} MB)，超过 {MAX_FILE_SIZE_MB} MB 限制")
                return 0
                
            # 尝试多种编码方式读取文件头
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            header = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        # 读取前20KB来分析文件格式
                        header = f.read(20480)
                    logger.info(f"成功使用 {encoding} 编码读取文件头")
                    break
                except Exception as e:
                    logger.warning(f"使用 {encoding} 编码读取文件头失败: {e}")
            
            if header is None:
                logger.error("无法读取文件头")
                self.import_progress.emit(100, "导入失败：无法读取文件内容")
                return 0
                
            # 检查是否包含书签相关标记
            has_dl_tag = '<DL>' in header.upper() or '<DL ' in header.upper()
            has_dt_tag = '<DT>' in header.upper() or '<DT ' in header.upper()
            has_h3_tag = '<H3>' in header.upper()
            has_bookmark_doctype = 'NETSCAPE-Bookmark-file' in header
            has_a_tags = '<A HREF' in header.upper() or '<A\nHREF' in header.upper() or 'HREF=' in header.upper()
            is_chrome_bookmarks = has_bookmark_doctype or 'chrome://bookmarks' in header
            
            logger.info(f"文件分析: DL标签:{has_dl_tag}, DT标签:{has_dt_tag}, H3标签:{has_h3_tag}, " +
                        f"书签文件声明:{has_bookmark_doctype}, A标签:{has_a_tags}, Chrome书签:{is_chrome_bookmarks}")
            
            # 如果没有任何书签相关标记，可能不是有效的书签文件
            if not (has_dl_tag or has_dt_tag or has_a_tags):
                logger.error("文件格式不符合书签格式要求")
                self.import_progress.emit(100, "导入失败：文件不是书签格式")
                return 0
            
            self.import_progress.emit(10, "正在分段解析书签文件...")
            
            # 创建临时数据结构
            imported_data = {}
            bookmark_count = 0
            
            # 使用正确的编码重新打开文件，逐行读取并处理
            current_encoding = 'utf-8'
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        test_line = f.readline()
                    current_encoding = encoding
                    logger.info(f"使用 {encoding} 编码进行主解析")
                    break
                except Exception:
                    continue
            
            with open(file_path, 'r', encoding=current_encoding, errors='replace') as f:
                # 使用简化的状态机解析器处理HTML
                in_dt = False
                folder_stack = [{"导入的书签": {"type": "folder", "children": {}}}]
                current_folder = folder_stack[0]["导入的书签"]["children"]
                current_path = ["导入的书签"]
                
                # 记录当前处理的行号和内容，用于调试
                line_num = 0
                buffer = ""
                
                for line in f:
                    line_num += 1
                    if line_num % 1000 == 0:  # 每1000行更新一次进度
                        progress = 10 + min(70, int(70 * (line_num / 100000)))  # 假设最多10万行
                        self.import_progress.emit(progress, f"正在解析书签, 已处理 {line_num} 行...")
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 将当前行添加到缓冲区，以处理跨行的标签
                    buffer += line + " "
                    
                    # 每隔几行处理一次缓冲区内容
                    if line_num % 10 == 0 or '</DL>' in buffer.upper() or '</H3>' in buffer.upper() or '</A>' in buffer.upper():
                        # 处理缓冲区中的文件夹和链接
                        self._process_buffer(buffer, folder_stack, current_folder, current_path, bookmark_count)
                        buffer = ""
            
            # 处理最后的缓冲区内容
            if buffer:
                self._process_buffer(buffer, folder_stack, current_folder, current_path, bookmark_count)
            
            self.import_progress.emit(80, "正在处理导入数据...")
            
            # 检查导入结果
            if bookmark_count == 0:
                logger.error("未找到有效书签，尝试备用解析方法")
                
                # 尝试使用更宽松的解析方法
                try:
                    # 重新打开文件，使用正则表达式提取所有链接
                    with open(file_path, 'r', encoding=current_encoding, errors='replace') as f:
                        content = f.read()
                        
                    # 使用正则表达式直接提取所有链接
                    links = re.findall(r'<A[^>]*HREF="([^"]*)"[^>]*>(.*?)</A>', content, re.IGNORECASE)
                    
                    if links:
                        logger.info(f"使用备用方法找到 {len(links)} 个链接")
                        
                        imported_data = {"导入的链接": {"type": "folder", "children": {}}}
                        for i, (url, name) in enumerate(links):
                            if not name:
                                name = url
                            
                            # 跳过 javascript: 链接
                            if url.startswith('javascript:'):
                                continue
                            
                            url_item = {
                                "type": "url",
                                "url": url,
                                "name": name,
                                "icon": ""
                            }
                            
                            # 处理重名
                            final_name = name
                            counter = 1
                            while final_name in imported_data["导入的链接"]["children"]:
                                final_name = f"{name} ({counter})"
                                counter += 1
                            
                            imported_data["导入的链接"]["children"][final_name] = url_item
                        
                        bookmark_count = len(links)
                    else:
                        logger.error("备用方法也未找到有效链接")
                        self.import_progress.emit(100, "导入失败：未找到有效书签")
                        return 0
                        
                except Exception as e:
                    logger.error(f"备用解析方法失败: {e}")
                    self.import_progress.emit(100, "导入失败：未找到有效书签")
                    return 0
            
            # 合并到主数据
            self.data_manager.data.update(imported_data)
            self.data_manager.data_changed.emit()
            
            self.import_progress.emit(100, f"导入完成，共导入 {bookmark_count} 个书签")
            logger.info(f"从 {file_path} 导入了 {bookmark_count} 个书签")
            return bookmark_count
            
        except Exception as e:
            logger.error(f"分块导入书签失败: {e}")
            logger.error(traceback.format_exc())
            self.import_progress.emit(100, f"导入失败: {str(e)}")
            return 0
    
    def _process_buffer(self, buffer, folder_stack, current_folder, current_path, bookmark_count):
        """处理缓冲区中的内容，提取文件夹和链接"""
        # 1. 检查文件夹(H3标签)
        h3_matches = re.finditer(r'<H3[^>]*>(.*?)</H3>', buffer, re.IGNORECASE)
        for match in h3_matches:
            folder_name = match.group(1).strip()
            if not folder_name:
                folder_name = f"未命名文件夹_{len(folder_stack)}"
            
            # 创建新文件夹
            new_folder = {"type": "folder", "children": {}}
            
            # 处理重名
            final_name = folder_name
            counter = 1
            while final_name in current_folder:
                final_name = f"{folder_name} ({counter})"
                counter += 1
            
            current_folder[final_name] = new_folder
            folder_stack.append(new_folder["children"])
            current_folder = new_folder["children"]
            current_path.append(final_name)
        
        # 2. 检查链接(A标签)
        a_matches = re.finditer(r'<A[^>]*HREF="([^"]*)"[^>]*>(.*?)</A>', buffer, re.IGNORECASE)
        for match in a_matches:
            url = match.group(1).strip()
            name = match.group(2).strip()
            
            # 跳过 javascript: 链接
            if url.startswith('javascript:'):
                continue
                
            if not name:
                name = url
            
            # 创建URL项目
            url_item = {
                "type": "url",
                "url": url,
                "name": name,
                "icon": ""
            }
            
            # 处理重名
            final_name = name
            counter = 1
            while final_name in current_folder:
                final_name = f"{name} ({counter})"
                counter += 1
            
            current_folder[final_name] = url_item
            bookmark_count += 1
        
        # 3. 检查文件夹结束(</DL>标签)
        dl_end_count = buffer.upper().count('</DL>')
        for _ in range(dl_end_count):
            if len(folder_stack) > 1:
                folder_stack.pop()
                current_folder = folder_stack[-1]
                if current_path:
                    current_path.pop()
    
    def export_html(self, file_path):
        """
        导出书签到HTML文件
        
        Args:
            file_path: 保存的HTML文件路径
            
        Returns:
            导出的书签数量
        """
        try:
            self.export_progress.emit(0, "正在准备导出...")
            
            # 生成HTML内容
            html_content = self._generate_bookmark_html(self.data_manager.data)
            
            self.export_progress.emit(50, "正在写入文件...")
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            count = self._count_items(self.data_manager.data)
            
            self.export_progress.emit(100, f"导出完成，共导出 {count} 个项目")
            logger.info(f"已导出 {count} 个书签到 {file_path}")
            return count
            
        except Exception as e:
            logger.error(f"导出书签失败: {e}")
            self.export_progress.emit(100, f"导出失败: {str(e)}")
            return 0
    
    def export_specific_folder_html(self, file_path, folder_path):
        """
        导出特定文件夹的书签到HTML文件
        
        Args:
            file_path: 保存的HTML文件路径
            folder_path: 要导出的文件夹路径
            
        Returns:
            导出的书签数量
        """
        try:
            self.export_progress.emit(0, "正在准备导出特定文件夹...")
            
            # 获取指定路径的文件夹数据
            folder_data = self.data_manager.get_folder_data(folder_path)
            if not folder_data:
                logger.error(f"找不到路径 {folder_path} 的文件夹")
                self.export_progress.emit(100, f"导出失败: 找不到指定文件夹")
                return 0
            
            # 将文件夹数据转换为包含该文件夹作为根的数据结构
            export_data = {folder_path[-1]: folder_data}
            
            # 生成HTML内容
            html_content = self._generate_bookmark_html(export_data)
            
            self.export_progress.emit(50, "正在写入文件...")
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            count = self._count_items(export_data)
            
            self.export_progress.emit(100, f"导出完成，共导出 {count} 个项目")
            logger.info(f"已导出 {count} 个书签到 {file_path}")
            return count
            
        except Exception as e:
            logger.error(f"导出特定文件夹书签失败: {e}")
            self.export_progress.emit(100, f"导出失败: {str(e)}")
            return 0
    
    def export_json(self, file_path):
        """
        导出书签到JSON文件
        
        Args:
            file_path: 保存的JSON文件路径
            
        Returns:
            导出的书签数量或0表示失败
        """
        try:
            self.export_progress.emit(0, "正在准备导出...")
            
            # 复制数据以避免修改原数据
            import copy
            export_data = copy.deepcopy(self.data_manager.data)
            
            self.export_progress.emit(50, "正在写入JSON文件...")
            
            # 写入JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            count = self._count_items(export_data)
            
            self.export_progress.emit(100, f"导出完成，共导出 {count} 个项目")
            logger.info(f"已导出 {count} 个书签到JSON文件: {file_path}")
            return count
            
        except Exception as e:
            logger.error(f"导出JSON书签失败: {e}")
            self.export_progress.emit(100, f"导出失败: {str(e)}")
            return 0
            
    def export_specific_folder_json(self, file_path, folder_path):
        """
        导出特定文件夹的书签到JSON文件
        
        Args:
            file_path: 保存的JSON文件路径
            folder_path: 要导出的文件夹路径
            
        Returns:
            导出的书签数量或0表示失败
        """
        try:
            self.export_progress.emit(0, "正在准备导出特定文件夹...")
            
            # 获取指定路径的文件夹数据
            folder_data = self.data_manager.get_folder_data(folder_path)
            if not folder_data:
                logger.error(f"找不到路径 {folder_path} 的文件夹")
                self.export_progress.emit(100, f"导出失败: 找不到指定文件夹")
                return 0
            
            # 复制数据以避免修改原数据
            import copy
            folder_name = folder_path[-1]
            export_data = {folder_name: copy.deepcopy(folder_data)}
            
            self.export_progress.emit(50, "正在写入JSON文件...")
            
            # 写入JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            count = self._count_items(export_data)
            
            self.export_progress.emit(100, f"导出完成，共导出 {count} 个项目")
            logger.info(f"已导出 {count} 个书签到JSON文件: {file_path}")
            return count
            
        except Exception as e:
            logger.error(f"导出特定文件夹JSON书签失败: {e}")
            self.export_progress.emit(100, f"导出失败: {str(e)}")
            return 0
    
    def _process_bookmark_folder(self, dl, container, depth=0):
        from bs4 import Tag
        if depth > 50:
            logger.warning("书签嵌套层级过深，忽略更深层级内容")
            return

        # 只遍历当前DL的直接子节点
        items = dl.find_all('dt', recursive=False)

        for dt in items:
            h3 = dt.find('h3')
            if h3:
                folder_name = h3.text.strip() or "未命名文件夹"
                # 直接查找当前DT下的DL，兼容所有主流导出格式
                next_dl = dt.find('dl', recursive=False)
                if next_dl:
                    folder = {"type": "folder", "children": {}}
                    self._process_bookmark_folder(next_dl, folder["children"], depth + 1)
                    final_name = folder_name
                    counter = 1
                    while final_name in container:
                        final_name = f"{folder_name} ({counter})"
                        counter += 1
                    container[final_name] = folder
            else:
                a = dt.find('a')
                if a and a.get('href'):
                    url = a['href']
                    name = a.text.strip() or url
                    icon = a.get('icon', '')
                    url_item = {
                        "type": "url",
                        "url": url,
                        "name": name,
                        "icon": icon
                    }
                    final_name = name
                    counter = 1
                    while final_name in container:
                        final_name = f"{name} ({counter})"
                        counter += 1
                    container[final_name] = url_item
    
    def _generate_bookmark_html(self, data):
        """生成书签HTML内容"""
        html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
"""
        
        # 添加所有书签
        html += self._generate_folder_html(data, 1)
        
        html += "</DL><p>\n"
        return html
    
    def _generate_folder_html(self, items, indent_level):
        """生成文件夹HTML内容"""
        html = ""
        indent = "    " * indent_level
        
        for name, item in items.items():
            if item["type"] == "folder":
                # 生成文件夹HTML
                html += f"{indent}<DT><H3>{self._escape_html(name)}</H3>\n"
                html += f"{indent}<DL><p>\n"
                html += self._generate_folder_html(item["children"], indent_level + 1)
                html += f"{indent}</DL><p>\n"
            else:
                # 生成URL HTML
                icon_attr = f" ICON=\"{self._escape_html(item['icon'])}\"" if item.get('icon') else ""
                html += f"{indent}<DT><A HREF=\"{self._escape_html(item['url'])}\"{icon_attr}>{self._escape_html(item['name'])}</A>\n"
        
        return html
    
    def _escape_html(self, text):
        """转义HTML特殊字符"""
        if not text:
            return ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&#039;")
    
    def _count_items(self, data):
        """计算项目数量"""
        count = 0
        
        for item in data.values():
            count += 1
            if item["type"] == "folder":
                count += self._count_items(item["children"])
        
        return count
    
    def _is_valid_html_structure(self, html_content):
        """
        验证HTML结构是否合法且安全
        
        Args:
            html_content: HTML内容
            
        Returns:
            布尔值，表示结构是否有效
        """
        # 1. 检查是否为空
        if not html_content:
            return False
            
        # 2. 检查是否包含常见的HTML结构
        has_html_tag = '<html' in html_content.lower()
        has_body_tag = '<body' in html_content.lower()
        
        # 3. 检查常见的书签标记
        has_dl_tag = '<dl' in html_content.lower()
        has_a_tag = '<a ' in html_content.lower()
        
        # 4. 检查危险内容
        has_script = '<script' in html_content.lower()
        has_iframe = '<iframe' in html_content.lower()
        has_embed = '<embed' in html_content.lower()
        has_object = '<object' in html_content.lower()
        
        # 检测恶意内容的pattern
        dangerous_patterns = [
            'javascript:',     # JavaScript协议
            'data:text/html',  # 数据URI嵌入HTML
            'vbscript:',       # VBScript协议
            'document.cookie',  # Cookie操作
            'eval(',           # 执行代码
            'document.write',  # 直接写入页面
        ]
        
        has_dangerous_pattern = any(pattern in html_content.lower() for pattern in dangerous_patterns)
        
        # 记录分析结果
        logger.info(f"HTML分析: HTML标签:{has_html_tag}, BODY标签:{has_body_tag}, " +
                   f"DL标签:{has_dl_tag}, A标签:{has_a_tag}")
        
        if has_script or has_iframe or has_embed or has_object:
            logger.warning(f"HTML包含潜在危险元素: Script:{has_script}, Iframe:{has_iframe}, " +
                          f"Embed:{has_embed}, Object:{has_object}")
        
        if has_dangerous_pattern:
            logger.warning("HTML包含可疑模式或恶意代码指示")
            
        # 如果是书签文件，应该至少包含链接标签，并且可能有DL结构
        is_valid = has_a_tag and not has_dangerous_pattern
        return is_valid
    
    def _manual_clean_html(self, soup):
        """
        手动清理HTML，移除潜在危险内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            清理后的BeautifulSoup对象
        """
        # 移除所有script标签
        for tag in soup.find_all('script'):
            tag.decompose()
            
        # 移除所有iframe标签
        for tag in soup.find_all('iframe'):
            tag.decompose()
            
        # 移除所有object标签
        for tag in soup.find_all('object'):
            tag.decompose()
            
        # 移除所有embed标签
        for tag in soup.find_all('embed'):
            tag.decompose()
            
        # 移除所有style标签
        for tag in soup.find_all('style'):
            tag.decompose()
            
        # 移除所有form标签
        for tag in soup.find_all('form'):
            tag.decompose()
            
        # 移除所有事件属性
        dangerous_attrs = [
            'onclick', 'onmouseover', 'onmouseout', 'onload', 'onerror',
            'onkeyup', 'onkeydown', 'onkeypress', 'onblur', 'onfocus',
            'onsubmit', 'onchange', 'onmousedown', 'onmouseup'
        ]
        
        for tag in soup.find_all(True):  # 查找所有标签
            for attr in dangerous_attrs:
                if tag.has_attr(attr):
                    del tag[attr]
                    
            # 清理使用javascript:协议的链接
            if tag.name == 'a' and tag.has_attr('href'):
                href = tag['href'].lower()
                if href.startswith('javascript:') or href.startswith('data:'):
                    tag['href'] = '#'
                    
        return soup