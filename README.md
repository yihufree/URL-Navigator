# URL Navigator

[![License](https://img.shields.io/badge/license-Custom-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)

A modern, feature-rich desktop application for managing and organizing your bookmarks with an intuitive interface.

[中文版本](README_zh.md) | [User Guide](docs/user_guide.md) | [用户指南](docs/用户指南.md)

## ✨ Features

- 📁 **Hierarchical Organization**: Organize bookmarks in folders and subfolders
- 🔍 **Powerful Search**: Quick search across all bookmarks with filters
- 🌐 **Favicon Support**: Automatic favicon fetching and caching
- 📥 **Import/Export**: Support for Chrome, Firefox, HTML, and JSON formats
- 🎲 **Blind Box**: Random bookmark discovery feature
- 📚 **History Tracking**: Keep track of accessed bookmarks
- 🔒 **Password Protection**: Secure your bookmarks with password authentication
- 🔒 **Edit Lock Mode**: Prevent accidental modifications
- 🌍 **Multi-language**: Support for Chinese, English, Japanese, German, French, Korean, and Spanish
- 💾 **Auto-backup**: Automatic data backup and restore

## 🖼️ Screenshots

![Main Interface](docs/images/screenshot.png)

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Windows（not test in macOS or Linux)

### Installation

1. **Clone the repository**
   
   ```bash
   git clone https://github.com/yourusername/url-navigator.git
   cd url-navigator
   ```

2. Install dependencies
   
   ```
   pip install -r requirements.txt
   ```

3. Run the application
   
   ```
   python main.py
   ```
   
   ### Alternative: Download Pre-built Executable
   
   Download the latest release from the Releases page.
   [URLNav_20260401](https://github.com/yihufree/URL-Navigator/releases/download/V0.60/URLNav_20260401.exe)

## 📖 Usage

### Basic Operations

1. **Adding Bookmarks**: Click the "Add" button or drag URLs from your browser
2. **Creating Folders**: Right-click in the sidebar to create new folders
3. **Searching**: Use Ctrl+F or click the search icon
4. **Import/Export**: Access through the File menu
5. **Password Protection**: Set up password protection in Settings → Password Settings
   - Enable password protection and set your password
   - Configure security questions for password recovery
   - Password will be required on next startup

For detailed instructions, see the User Guide.

## 🛠️ Development

### Project Structure

```
url-navigator/
├── main.py              # Application entry point
├── app.py               # Main application class
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── ui/                  # User interface modules
│   ├── main_window.py   # Main window
│   ├── dialogs.py       # Dialog windows
│   └── ...
├── models/              # Data models
│   ├── data_manager.py  # Data persistence
│   └── ...
├── services/            # Business logic services
│   ├── favicon_service.py
│   ├── import_export.py
│   └── ...
├── utils/               # Utility modules
├── resources/           # Static resources
├── languages/           # Internationalization files
└── docs/                # Documentation
```

### Building from Source

1. Install development dependencies
   
   ```
   pip install pyinstaller
   ```

2. 

3. 

### Downolad trial version 

[URL Navigator单EXE体验版](https://github.com/yihufree/URL-Navigator/releases/download/V0.60/URLNav_20250611.zip)

## 🌐 Internationalization

   The application supports multiple languages. Language files are located in the languages/ directory:

- zh.json - Chinese (Simplified)

- en.json - English

- ja.json - Japanese

- de.json - German

- fr.json - French

- ko.json - Korean

- es.json - Spanish
  
  ## 🤝 Contributing
  
  We welcome contributions! Please see our Contributing Guidelines for details.

### How to Contribute

1. Fork the repository

2. Create a feature branch ( git checkout -b feature/amazing-feature )

3. Commit your changes ( git commit -m 'Add amazing feature' )

4. Push to the branch ( git push origin feature/amazing-feature )

5. Open a Pull Request
   
   ## 📝 License
   
   This project is licensed under a Custom License - see the LICENSE file for details.

## 🐛 Bug Reports & Feature Requests

Please use the GitHub Issues page to report bugs or request features.

## 📞 Support

- 📖 User Guide

- 🐛 Issue Tracker

- 💬 Discussions
  
  ## 🙏 Acknowledgments

- Built with PyQt5

- Icons from various open source icon sets

- Thanks to all contributors and users
  ⭐ If you find this project useful, please consider giving it a star!
