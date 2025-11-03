# Quick Start Guide

## First Time Setup

### Windows
```powershell
# Navigate to project directory
cd Heic2Png

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the application
python converter.py
```

### macOS/Linux
```bash
# Navigate to project directory
cd Heic2Png

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python converter.py
```

## Subsequent Runs

### Windows
```powershell
cd Heic2Png
.\venv\Scripts\Activate.ps1
python converter.py
```

### macOS/Linux
```bash
cd Heic2Png
source venv/bin/activate
python converter.py
```

## Troubleshooting

### Permission Issues (PowerShell)
If you get an execution policy error on Windows:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found
Make sure Python 3.7+ is installed:
```bash
python --version
# or
python3 --version
```

Download from: https://www.python.org/downloads/

### Dependencies Won't Install
Try upgrading pip first:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Features Overview

1. **Select Directories**: Choose input (HEIC files) and output folders
2. **Choose Format**: PNG, JPEG, WEBP, or BMP
3. **Set Quality**: Slider from 1-100 (higher = better quality)
4. **Configure Threads**: Default is optimal, adjust if needed
5. **Convert**: Click "Start Conversion" and wait
6. **View Results**: Click "Open Output Folder" when done

## Tips

- Place your HEIC files in the `input` folder for quick access
- Converted files appear in the `output` folder by default
- Check `heic_converter.log` for detailed conversion information
- Settings are saved automatically in `config.json`

Enjoy converting! 🎉
