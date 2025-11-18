# 🍎 Quick Start Guide for MacOS

Get the PDF Data Extractor running on your Mac in 2 minutes!

## 📋 Prerequisites

1. **Python 3.8 or higher** (usually pre-installed on MacOS)
   - Check version: Open Terminal and type `python3 --version`
   - If not installed, download from [python.org](https://www.python.org/downloads/macos/)

2. **Tesseract OCR** (optional, for scanned PDFs)
   ```bash
   brew install tesseract
   ```

## 🚀 Installation

### Method 1: One-Click Launch (Recommended)

1. **Open Terminal** (Applications → Utilities → Terminal)

2. **Navigate to the project folder**:
   ```bash
   cd /path/to/Extract-data-from-old-pdf
   ```

3. **Make launcher executable** (one-time only):
   ```bash
   chmod +x launch_app.sh
   ```

4. **Double-click** `launch_app.sh` in Finder
   - OR run in Terminal: `./launch_app.sh`

5. **Your browser will open** automatically to http://localhost:8501

### Method 2: Manual Launch

1. **Open Terminal**

2. **Navigate to project**:
   ```bash
   cd /path/to/Extract-data-from-old-pdf
   ```

3. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Start the app**:
   ```bash
   streamlit run app.py
   ```

5. **Open browser** to http://localhost:8501

## 🎯 Using the App

### Upload PDF
- Click "Browse files" or drag & drop
- Supports: `.pdf` files

### Extract Data
1. Click "🚀 Extract Data" button
2. Wait 2-10 seconds for processing
3. See preview of extracted data

### Download Results
1. Choose format (Excel or CSV)
2. Click "⬇️ Download" button
3. File saves to Downloads folder

## 🛑 Stopping the App

Press `Ctrl + C` in the Terminal window where Streamlit is running.

## 💡 Tips for Mac Users

### Create Desktop Shortcut

1. Open **Automator** (Applications → Automator)
2. Create new **Application**
3. Add **Run Shell Script** action
4. Paste this code:
   ```bash
   cd /path/to/Extract-data-from-old-pdf
   source venv/bin/activate 2>/dev/null || true
   streamlit run app.py
   ```
5. Save as "PDF Extractor" to Desktop

### Enable Right-Click → Open With

1. Right-click any PDF file
2. Choose "Get Info"
3. Under "Open With", click dropdown
4. Select "Other..."
5. Navigate to your saved Automator app
6. Check "Always Open With"

### Add to Dock

Drag the launcher script or Automator app to your Dock for quick access!

## 🔧 Troubleshooting

### "python3: command not found"
Install Python from [python.org](https://www.python.org/downloads/macos/)

### "streamlit: command not found"
```bash
pip3 install streamlit
```

### "Permission denied" error
```bash
chmod +x launch_app.sh
```

### Port 8501 already in use
```bash
streamlit run app.py --server.port 8502
```

### App won't start
1. Update pip: `pip3 install --upgrade pip`
2. Reinstall: `pip3 install -r requirements.txt --force-reinstall`
3. Restart Terminal

## 📱 Using with Safari/Chrome

### Enable Auto-Open in Browser

Edit `~/.streamlit/config.toml`:
```toml
[server]
headless = true

[browser]
serverAddress = "localhost"
gatherUsageStats = false
serverPort = 8501
```

### Dark Mode

Streamlit auto-detects your system's dark mode setting!

## 🔒 Security & Privacy

- ✅ Runs 100% locally on your Mac
- ✅ No internet connection required
- ✅ Your PDF data never leaves your computer
- ✅ No tracking or analytics

## 🆘 Need Help?

- Check `UI_README.md` for full documentation
- Look at example PDFs in the repo
- Open an issue on GitHub

---

**Enjoy extracting! 🎉**
