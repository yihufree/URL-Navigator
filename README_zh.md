# URL Navigator 网址导航

[![License](https://img.shields.io/badge/license-Custom-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)

一款现代化、功能丰富的桌面书签管理应用程序，具有直观的用户界面。

[English Version](README.md) | [User Guide](docs/user_guide.md) | [用户指南](docs/用户指南.md)

## ✨ 主要特性

- 📁 **层次化组织**：使用文件夹和子文件夹组织书签
- 🔍 **强大搜索**：快速搜索所有书签，支持过滤器
- 🌐 **网站图标支持**：自动获取和缓存网站图标
- 📥 **导入/导出**：支持 Chrome、Firefox、HTML 和 JSON 格式
- 🎲 **盲盒功能**：随机书签发现功能
- 📚 **历史记录**：跟踪访问过的书签
- 🔒 **编辑锁定模式**：防止意外修改
- 🌍 **多语言支持**：支持中文、英文、日文、德文、法文、韩文和西班牙文
- 💾 **自动备份**：自动数据备份和恢复
- 🎨 **可定制界面**：主题和布局自定义

## 🖼️ 截图

*注：截图将在后续版本中添加*

## 🚀 快速开始

### 系统要求

- Python 3.7 或更高版本
- Windows、macOS 或 Linux

### 安装方法

1. **克隆仓库**
   
   ```bash
   git clone https://github.com/yourusername/url-navigator.git
   cd url-navigator
   ```

2. 安装依赖
   
   ```
   pip install -r requirements.txt
   ```

3. 运行应用程序
   
   ```
   python main.py
   ```
   
   ### 替代方案：下载预编译可执行文件
   
   从 Releases 页面下载最新版本。

## 📖 使用方法

### 基本操作

1. 添加书签 ：点击"添加"按钮或从浏览器拖拽 URL
2. 创建文件夹 ：在侧边栏右键点击创建新文件夹
3. 搜索 ：使用 Ctrl+F 或点击搜索图标
4. 导入/导出 ：通过文件菜单访问
5. 开魔盒：也叫开盲盒，通过点击右上角的圆形魔盒按钮打开。可直接选择数字（1-5）或输入数字（>5）随机浏览。
   详细说明请参阅 用户指南 。

## 🛠️ 开发

### 项目结构

```
url-navigator/
├── main.py              # 应用程序入口
├── app.py               # 主应用程序类
├── config.py            # 配置管理
├── requirements.txt     # Python 依赖
├── ui/                  # 用户界面模块
│   ├── main_window.py   # 主窗口
│   ├── dialogs.py       # 对话框窗口
│   └── ...
├── models/              # 数据模型
│   ├── data_manager.py  # 数据持久化
│   └── ...
├── services/            # 业务逻辑服务
│   ├── favicon_service.py
│   ├── import_export.py
│   └── ...
├── utils/               # 工具模块
├── resources/           # 静态资源
├── languages/           # 国际化文件
└── docs/                # 文档
```

### 从源码构建

1. 安装开发依赖
   
   ```
   pip install pyinstaller
   ```

2. 

3.

### 下载体验版

[URL Navigator单EXE体验版](https://github.com/yihufree/URL-Navigator/releases/download/V0.5/URLNav_20250608.zip)

## 🌐 国际化

   应用程序支持多种语言。语言文件位于 languages/ 目录：

- zh.json - 中文（简体）

- en.json - 英文

- ja.json - 日文

- de.json - 德文

- fr.json - 法文

- ko.json - 韩文

- es.json - 西班牙文
  
  ## 🤝 贡献
  
  我们欢迎贡献！请查看我们的 贡献指南 了解详情。

### 如何贡献

1. Fork 仓库

2. 创建功能分支 ( git checkout -b feature/amazing-feature )

3. 提交更改 ( git commit -m 'Add amazing feature' )

4. 推送到分支 ( git push origin feature/amazing-feature )

5. 打开 Pull Request
   
   ## 📝 许可证
   
   本项目采用自定义许可证 - 详情请参阅 LICENSE 文件。

## 🐛 错误报告和功能请求

请使用 GitHub Issues 页面报告错误或请求功能。

## 📞 支持

- 📖 用户指南

- 🐛 问题跟踪器

- 💬 讨论区
  
  ## 🙏 致谢

- 使用 PyQt5 构建

- 图标来自各种开源图标集

- 感谢所有贡献者和用户
  ⭐ 如果您觉得这个项目有用，请考虑给它一个星标！
