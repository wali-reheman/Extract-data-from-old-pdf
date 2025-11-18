# 📊 PDF Data Extractor - Interactive UI

A beautiful, user-friendly web interface for extracting census and election data from PDF files.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

## ✨ Features

- 🌐 **Web-based interface** - Runs in your browser, no installation needed
- 🖱️ **Drag & drop** - Simple file upload
- 👁️ **Live preview** - See your data before downloading
- 📊 **Statistics** - Get insights about your extracted data
- 💾 **Multiple formats** - Download as Excel or CSV
- 🌍 **Universal support** - Works with English and French number formats
- 🚀 **100% local** - Your data never leaves your computer

## 🚀 Quick Start (MacOS)

### Option 1: Double-Click Launch (Easiest)

1. **Make the launcher executable** (one-time setup):
   ```bash
   chmod +x launch_app.sh
   ```

2. **Double-click** `launch_app.sh`

3. Your browser will automatically open to http://localhost:8501

### Option 2: Manual Launch

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   streamlit run app.py
   ```

3. **Open your browser** to http://localhost:8501

## 📖 How to Use

### Step 1: Upload PDF
- Click "Browse files" or drag and drop your PDF
- Supported formats: Census data, election results, statistical reports

### Step 2: Extract Data
- Click the "🚀 Extract Data" button
- Wait for processing (usually 2-10 seconds)

### Step 3: Review Results
- **Table View**: See your extracted data
- **Statistics**: Get numeric summaries
- **Column Info**: Check data types and completeness

### Step 4: Download
- Choose format (Excel or CSV)
- Click "⬇️ Download" button
- File is saved to your Downloads folder

## 🖼️ Screenshots

### Main Interface
- Clean, modern design
- Easy file upload
- Real-time progress tracking

### Data Preview
- Table view with customizable row count
- Statistics dashboard
- Column information panel

### Download Options
- Excel (.xlsx) format
- CSV (.csv) format
- Automatic filename generation

## 🛠️ System Requirements

- **Operating System**: macOS 10.14+, Windows 10+, Linux
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for dependencies

## 📦 Dependencies

The app uses these main libraries:
- **Streamlit** - Web interface
- **pandas** - Data processing
- **pdfplumber** - PDF text extraction
- **openpyxl** - Excel file creation

All dependencies are installed automatically when you run the launcher.

## 🔧 Configuration

### Custom Port
By default, the app runs on port 8501. To use a different port:

```bash
streamlit run app.py --server.port 8080
```

### Dark Mode
Streamlit supports dark mode! Toggle it in Settings (top-right menu).

### Preview Rows
Adjust the number of preview rows using the slider in the Options section.

## 📝 Supported PDF Formats

### Number Formats
- ✅ **English**: 1,435,332 (comma separators)
- ✅ **French**: 1 132 655 (space separators)
- ✅ **Mixed**: Automatic detection

### Document Types
- ✅ Census data
- ✅ Election results
- ✅ Demographic tables
- ✅ Statistical reports
- ✅ Multi-page PDFs
- ✅ Scanned documents (with OCR)

## ❓ Troubleshooting

### App won't start
1. Check Python version: `python3 --version` (should be 3.8+)
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Try clearing Streamlit cache: `streamlit cache clear`

### Browser doesn't open
- Manually navigate to http://localhost:8501
- Check if port 8501 is already in use

### Extraction fails
- Ensure PDF is not password-protected
- Check PDF file isn't corrupted
- Try with a different PDF to isolate the issue

### Slow performance
- Large PDFs (50+ pages) may take longer
- Close other applications to free up RAM
- Try extracting one page at a time

## 🔐 Privacy & Security

- ✅ **100% local processing** - Data never leaves your computer
- ✅ **No internet required** - Works completely offline
- ✅ **No data collection** - We don't track or store anything
- ✅ **Temporary files** - Cleaned up automatically

## 🎨 Customization

### Custom Theme
Edit `.streamlit/config.toml` to customize colors:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Custom Logo
Add your logo in the sidebar by editing `app.py`:

```python
st.sidebar.image("your_logo.png")
```

## 📚 Advanced Usage

### Batch Processing
The UI currently supports one file at a time. For batch processing, use the command-line tool:

```bash
python extract_universal.py input.pdf output.xlsx
```

### Custom Output Path
Output files are downloaded to your browser's default Downloads folder. Change this in your browser settings.

### API Integration
The extraction functions can be imported and used in your own code:

```python
from extract_universal import try_pdfplumber, smart_parse_table

rows, success = try_pdfplumber("input.pdf")
headers, data = smart_parse_table(rows)
```

## 🤝 Contributing

Found a bug or have a feature request? Please open an issue on GitHub!

## 📄 License

MIT License - feel free to use this tool for any purpose.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- PDF processing by [pdfplumber](https://github.com/jsvine/pdfplumber)
- Data manipulation with [pandas](https://pandas.pydata.org/)

---

**Need help?** Check the troubleshooting section or open an issue on GitHub.

**Happy extracting! 📊✨**
