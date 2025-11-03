# HEIC Converter Pro v2.0

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

A professional-grade, multi-threaded HEIC/HEIF to image converter with an intuitive GUI interface.

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Configuration](#configuration) • [Troubleshooting](#troubleshooting)

</div>

---

## 🌟 Features

### Core Functionality
- **Multi-Format Support**: Convert HEIC/HEIF files to PNG, JPEG, WEBP, or BMP
- **Batch Processing**: Convert multiple files simultaneously
- **Multi-Threading**: Configurable thread pool for optimal performance
- **Quality Control**: Adjustable output quality (1-100)
- **Progress Tracking**: Real-time progress bar and statistics

### User Experience
- **Intuitive GUI**: Clean, modern interface built with Tkinter
- **Drag & Drop**: Drag folders directly into input/output fields (optional feature)
- **Persistent Settings**: Remembers your preferences between sessions
- **Error Handling**: Comprehensive error reporting and logging
- **Cross-Platform**: Works on Windows, macOS, and Linux

### Advanced Features
- **Configuration Management**: JSON-based settings with automatic persistence
- **Detailed Logging**: Complete conversion history saved to `heic_converter.log`
- **Automatic Optimization**: Smart compression for optimal file sizes
- **Error Recovery**: Continues processing even if individual files fail
- **RGBA Support**: Proper handling of images with transparency

---

## 📋 Requirements

- **Python**: 3.7 or higher
- **Operating System**: Windows, macOS, or Linux
- **Dependencies**: See [requirements.txt](requirements.txt)

---

## 🚀 Installation

### Method 1: Quick Install (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Devinance/Heic2Png.git
   cd Heic2Png
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python converter.py
   ```

### Method 2: Virtual Environment (Best Practice)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Devinance/Heic2Png.git
   cd Heic2Png
   ```

2. **Create virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python converter.py
   ```

### Optional: Drag and Drop Support

For drag-and-drop functionality, install the optional dependency:
```bash
pip install tkinterdnd2
```

*Note: Drag-and-drop is not required; the application works perfectly without it.*

---

## 📖 Usage

### Basic Workflow

1. **Launch the application**:
   ```bash
   python converter.py
   ```

2. **Select directories**:
   - Click "Browse..." to select your input folder containing HEIC files
   - Choose an output folder for converted images
   - *Or* drag folders directly into the fields (if tkinterdnd2 is installed)

3. **Configure settings**:
   - **Output Format**: Choose PNG, JPEG, WEBP, or BMP
   - **Quality**: Adjust slider (1-100, higher = better quality)
   - **Thread Count**: Set based on your CPU (default is optimal)

4. **Convert**:
   - Click "Start Conversion"
   - Monitor progress in real-time
   - Click "Open Output Folder" when complete

---

## ⚙️ Configuration

The application creates a `config.json` file automatically to remember your settings.

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `input_dir` | Default input directory | `"input"` |
| `output_dir` | Default output directory | `"output"` |
| `quality` | Output quality (1-100) | `90` |
| `thread_count` | Number of worker threads | `CPU cores - 1` |
| `batch_size` | Files per batch | `10` |
| `output_format` | Default output format | `"PNG"` |

---

## 📊 Performance Tips

### Optimal Thread Count
- **Recommended**: Number of CPU cores minus 1
- **Low-end systems**: 2-4 threads
- **High-end systems**: 8-16 threads

### Quality vs. File Size
- **90-100**: Maximum quality, larger files (recommended for photos)
- **70-89**: Good quality, balanced size (recommended for web)
- **50-69**: Acceptable quality, smaller files

---

## 🐛 Troubleshooting

### Common Issues

#### "No HEIC/HEIF files found"
- **Solution**: Verify your input folder contains `.heic` or `.heif` files

#### Import Errors
- **Solution**: Run `pip install -r requirements.txt` again

#### Some Files Fail to Convert
- **Solution**: Check `heic_converter.log` for specific error messages

### Logs

All conversion activity is logged to `heic_converter.log` for debugging.

---

## 🤝 Contributing

Contributions are welcome! Please check out our [Contributing Guidelines](CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2024 Cafer Tuleyp Demirci

---

## 🙏 Acknowledgments

- **pillow-heif**: For excellent HEIC file support
- **Pillow (PIL)**: For robust image processing capabilities
- **Python Community**: For outstanding documentation and support

---

<div align="center">

Made with ❤️ by [Cafer Tuleyp Demirci](https://github.com/Devinance)

⭐ Star this repo if you find it helpful!

</div>
