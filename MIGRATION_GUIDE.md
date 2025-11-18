# Migration Guide: Old Scripts → New Package

This guide shows how to migrate from the old standalone scripts to the new modular package.

## Old Way (2 separate scripts)

### Step 1: Edit hardcoded paths in `download_files.py`
```python
# Line 29: Replace with your actual path
file_path = "/Users/..."
```

### Step 2: Run download script
```bash
python download_files.py
```

### Step 3: Edit hardcoded paths in `extract_text.py`
```python
# Line 27: Replace with your actual path
path = "your_path/Pakistan/Religion"
```

### Step 4: Run extraction script
```bash
python extract_text.py
```

**Issues with old approach:**
- ❌ Hardcoded paths need manual editing
- ❌ No configuration file
- ❌ No CLI options
- ❌ SSL verification disabled
- ❌ Limited error handling
- ❌ Only supports one specific format
- ❌ No flexibility for different data sources

---

## New Way (Single configurable command)

### Step 1: Create configuration (one-time setup)
```bash
python -m pdf_data_extractor.cli --init-config census_config.yaml
```

### Step 2: Run entire pipeline
```bash
python -m pdf_data_extractor.cli --config census_config.yaml --download --verbose
```

**That's it!** The new tool handles everything:
- ✅ Downloads PDFs with retry logic
- ✅ Converts to images
- ✅ Performs OCR
- ✅ Parses data
- ✅ Exports to Excel/CSV/JSON

**Benefits of new approach:**
- ✅ All settings in one config file
- ✅ Flexible CLI with many options
- ✅ Proper error handling and logging
- ✅ Progress bars
- ✅ Multiple output formats
- ✅ Can process local files too
- ✅ Can skip steps (e.g., use existing images)
- ✅ Secure by default (SSL verification)

---

## Comparison Table

| Feature | Old Scripts | New Package |
|---------|-------------|-------------|
| Configuration | Hardcoded | YAML config file |
| CLI Options | None | 15+ options |
| Input Sources | Download only | Download, local PDFs, images |
| Output Formats | Excel only | Excel, CSV, JSON |
| Error Handling | Basic | Comprehensive with retry |
| Progress Tracking | Print statements | Progress bars |
| Logging | Basic | Configurable levels |
| SSL Security | Disabled | Enabled (configurable) |
| Modularity | Monolithic | 9 separate modules |
| Reusability | Scripts only | CLI + Python API |
| Documentation | Basic README | Full docs + examples |
| Package Installation | No | `pip install` ready |

---

## Code Equivalents

### Old: Download PDFs
```python
# download_files.py
import requests
for district_code in districts:
    pdf_link = f"{base_path}{district_code}{religion}.pdf"
    response = requests.get(pdf_link, verify=False)  # Insecure!
    # ... rest of code
```

### New: Download PDFs
```python
from pdf_data_extractor import Config, PDFDownloader

config = Config("config.yaml")
downloader = PDFDownloader(config)
pdf_files = downloader.download_from_url_pattern()
# Automatic retry, SSL verification, progress bars, error handling
```

---

### Old: Extract Text
```python
# extract_text.py
import pytesseract
import cv2

image = cv2.imread(full_path, cv2.IMREAD_GRAYSCALE)
image = cv2.resize(image, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
text = pytesseract.image_to_string(image, config="--psm 6 --oem 1")
# ... manual parsing
```

### New: Extract Text
```python
from pdf_data_extractor import Config, OCREngine, DataParser

config = Config("config.yaml")
ocr = OCREngine(config)
parser = DataParser(config)

ocr_results = ocr.process_images(image_files)
data = parser.parse_ocr_results(ocr_results)
# Automatic preprocessing, parsing, progress tracking
```

---

## Migration Checklist

- [x] ✅ New package structure created
- [x] ✅ Old scripts preserved (download_files.py, extract_text.py still available)
- [x] ✅ Configuration system added
- [x] ✅ CLI tool created
- [x] ✅ Documentation written
- [x] ✅ Example configs provided

You can still use the old scripts if needed, but the new package offers significant improvements!

---

## Quick Start Examples

### Example 1: Pakistan Census (same as old scripts)
```bash
# Using the exact same data source as the old scripts
python -m pdf_data_extractor.cli \\
  --config examples/config_pakistan_census.yaml \\
  --download \\
  --verbose
```

### Example 2: Process Local Files
```bash
# If you already downloaded PDFs manually
python -m pdf_data_extractor.cli \\
  --input *.pdf \\
  --output results.xlsx \\
  --data-format census
```

### Example 3: Export to Multiple Formats
```python
from pdf_data_extractor import Config, DataExporter
import pandas as pd

config = Config("config.yaml")
exporter = DataExporter(config)

# Load existing data
data = pd.read_excel("Pakistan_religion.xlsx")

# Export to all formats
results = exporter.export_all_formats(data)
print(results)
# {'excel': './output/data.xlsx',
#  'csv': './output/data.csv',
#  'json': './output/data.json'}
```
