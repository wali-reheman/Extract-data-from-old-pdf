# PDF Data Extractor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A comprehensive Python tool for extracting structured data from image-based PDF files, specifically optimized for **census** and **election** data formats.

## Overview

Extracting tables from old, image-based PDFs is challenging. This tool provides a complete pipeline to:

1. **Download** PDFs from remote sources or process local files
2. **Convert** PDF pages to high-quality images
3. **Extract** text using OCR (Optical Character Recognition)
4. **Parse** extracted text into structured tabular data
5. **Export** results to Excel, CSV, or JSON formats

Originally developed for Pakistan census data, it's now generalized to handle various census and election PDF formats.

## Features

- ✅ **Flexible Input**: Download from URLs, process local PDFs, or use existing images
- ✅ **Smart Parsing**: Optimized for census and election data structures
- ✅ **Multiple Formats**: Export to Excel, CSV, or JSON
- ✅ **Configurable**: YAML-based configuration for easy customization
- ✅ **CLI & API**: Use via command line or as a Python library
- ✅ **Robust**: Retry logic, error handling, and progress tracking
- ✅ **Well-Documented**: Comprehensive guides and examples
- 🆕 **Web UI**: Beautiful drag-and-drop interface powered by Streamlit
- 🆕 **Standalone App**: Create a double-click macOS application

## 🎯 NEW: Web Interface & Standalone App

### Interactive Web UI

A user-friendly web interface for easy PDF data extraction:

```bash
streamlit run app.py
```

**Features:**
- 🖱️ Drag & drop PDF upload
- 👁️ Live data preview
- 📊 Statistics dashboard
- 💾 Download as Excel or CSV
- 🌍 Supports English, French, and Cyrillic text
- 🚀 100% local - your data never leaves your computer

**Quick Start:** See [UI_README.md](UI_README.md) or [QUICKSTART_MACOS.md](QUICKSTART_MACOS.md)

### macOS Standalone Application

Create a double-click `.app` with all dependencies embedded:

```bash
bash create_standalone_app.sh
```

This creates `PDF Data Extractor.app` that:
- ✅ Works like any Mac app - just double-click
- ✅ Includes all dependencies - no installation needed
- ✅ Can be shared with others or moved to Applications folder

**Full Guide:** See [CREATE_STANDALONE_APP.md](CREATE_STANDALONE_APP.md)

---

## Quick Start (Command Line)

### Installation

```bash
# Clone the repository
git clone https://github.com/wali-reheman/Extract-data-from-old-pdf.git
cd Extract-data-from-old-pdf

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR (system dependency)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows:
# Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Basic Usage

```bash
# Generate a configuration file
python -m pdf_data_extractor.cli --init-config my_config.yaml

# Edit the configuration to match your data source
vim my_config.yaml

# Run extraction
python -m pdf_data_extractor.cli --config my_config.yaml --download
```

### Quick Example: Pakistan Census

```bash
# Use the provided example configuration
python -m pdf_data_extractor.cli --config examples/config_pakistan_census.yaml --download --verbose
```

Output: `output/pakistan_census_religion.xlsx` with structured data

## Usage Examples

### 1. Download and Extract Census Data

```bash
pdf-extract --config examples/config_pakistan_census.yaml --download
```

### 2. Process Local PDF Files

```bash
pdf-extract --input ./my_pdfs/*.pdf --output results.xlsx --data-format census
```

### 3. Process Existing Images

```bash
pdf-extract --images ./images/*.jpg --format csv --output election_results.csv
```

### 4. Use as Python Library

```python
from pdf_data_extractor import Config, PDFDownloader, PDFConverter, OCREngine, DataParser, DataExporter

# Load configuration
config = Config("config.yaml")

# Run extraction pipeline
downloader = PDFDownloader(config)
converter = PDFConverter(config)
ocr = OCREngine(config)
parser = DataParser(config)
exporter = DataExporter(config)

# Execute pipeline
pdf_files = downloader.download_from_url_pattern()
images_dict = converter.convert_pdfs(pdf_files)
all_images = [img for imgs in images_dict.values() for img in imgs]
ocr_results = ocr.process_images(all_images)
data = parser.parse_ocr_results(ocr_results)
output_path = exporter.export(data)

print(f"Extracted data saved to: {output_path}")
```

## Project Structure

```
Extract-data-from-old-pdf/
├── src/
│   └── pdf_data_extractor/
│       ├── __init__.py          # Package initialization
│       ├── cli.py               # Command-line interface
│       ├── config.py            # Configuration management
│       ├── downloader.py        # PDF download module
│       ├── converter.py         # PDF to image conversion
│       ├── ocr_engine.py        # OCR processing
│       ├── parser.py            # Data parsing (census/election)
│       ├── exporter.py          # Export to various formats
│       └── utils.py             # Utility functions
├── examples/
│   ├── config_pakistan_census.yaml
│   ├── config_election_data.yaml
│   └── config_local_files.yaml
├── docs/
│   ├── USAGE.md                 # Detailed usage guide
│   └── DATA_FORMATS.md          # Data format specifications
├── requirements.txt
├── setup.py
├── pyproject.toml
├── LICENSE
└── README.md
```

## Configuration

Configuration files use YAML format. See `examples/` for templates.

### Key Configuration Sections

#### Download Settings
```yaml
download:
  base_url: "https://example.com/pdfs/"
  file_pattern: "{district_code}{data_type}.pdf"
  district_range: [1, 100]
  delay_seconds: 3
```

#### OCR Settings
```yaml
ocr:
  engine: "tesseract"
  tesseract_config: "--psm 6 --oem 1"
  preprocessing:
    grayscale: true
    resize_factor: 1.2
```

#### Parsing Settings
```yaml
parsing:
  data_format: "census"  # or "election" or "generic"
  keywords:
    census: ["DISTRICT", "TEHSIL", "DIVISION"]
  column_mappings:
    census_religion_7:
      - "SEX"
      - "TOTAL"
      - "MUSLIM"
      # ... more columns
```

## Supported Data Formats

### Census Data
- Geographic hierarchies (District, Tehsil, Division, etc.)
- Demographic breakdowns (Religion, Language, Age, Gender)
- Multi-column tabular data
- Example: Pakistan Census 2017

### Election Data
- Polling station data
- Voter registration and turnout
- Vote counts by candidate/party
- Example: Election Commission results

### Generic Tabular Data
- Any structured tabular data in PDFs
- Configurable column detection
- Custom parsing rules

See [docs/DATA_FORMATS.md](docs/DATA_FORMATS.md) for detailed specifications.

## Documentation

- **[Usage Guide](docs/USAGE.md)** - Comprehensive CLI and API usage
- **[Data Formats](docs/DATA_FORMATS.md)** - Census and election format specifications
- **[Examples](examples/)** - Configuration templates for common use cases

## CLI Reference

```
usage: pdf-extract [-h] [--config CONFIG] [--init-config PATH]
                   [--download | --input PDF [PDF ...] | --images IMAGE [IMAGE ...]]
                   [--output OUTPUT] [--format {excel,csv,json}]
                   [--data-format {census,election,generic}]
                   [--skip-conversion] [--clean] [--verbose] [--quiet]

Extract structured data from census and election PDFs

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to YAML configuration file
  --init-config PATH    Generate example configuration file
  --download            Download PDFs from URL pattern
  --input PDF [PDF ...], -i PDF [PDF ...]
                        Input PDF files or patterns
  --images IMAGE [IMAGE ...]
                        Process existing images
  --output OUTPUT, -o OUTPUT
                        Output file path
  --format {excel,csv,json}, -f {excel,csv,json}
                        Output format
  --data-format {census,election,generic}
                        Data format type
  --skip-conversion     Skip PDF to image conversion
  --clean               Clean temporary files
  --verbose, -v         Enable debug logging
  --quiet, -q           Suppress console output
```

## Requirements

### Python Dependencies
- Python 3.8+
- requests
- pdf2image
- Pillow
- opencv-python
- pytesseract
- pandas
- openpyxl
- PyYAML
- tqdm

### System Dependencies
- **Tesseract OCR** (must be installed separately)
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)

## Development

### Install in Development Mode

```bash
pip install -e .
```

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
```

## Troubleshooting

### Poor OCR Quality
- Increase DPI in conversion settings
- Adjust resize_factor in OCR preprocessing
- Try different Tesseract PSM modes

### Missing Data
- Verify keywords match your PDF content
- Check column mappings
- Enable debug logging with `--verbose`

### Performance Issues
- Process in smaller batches
- Use `--skip-conversion` for existing images
- Export to CSV instead of Excel for speed

See [docs/USAGE.md#troubleshooting](docs/USAGE.md#troubleshooting) for more details.

## Use Cases

This tool is ideal for:

- **Researchers** digitizing historical census data
- **Election analysts** extracting polling station results
- **Data journalists** working with government PDFs
- **Academics** studying demographic trends
- **Government agencies** modernizing legacy data
- **NGOs** analyzing public data

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this tool in your research, please cite:

```
Reheman, W. (2025). PDF Data Extractor: A tool for extracting structured data
from census and election PDFs. GitHub repository.
https://github.com/wali-reheman/Extract-data-from-old-pdf
```

## Contact

**Wali Reheman**
- Email: rw8143a@american.edu
- GitHub: [@wali-reheman](https://github.com/wali-reheman)

## Acknowledgments

- Pakistan Bureau of Statistics for census data
- Tesseract OCR team for the OCR engine
- OpenCV and pdf2image communities

## Future Enhancements

- [ ] Support for more OCR engines (EasyOCR, Cloud APIs)
- [ ] Web interface for non-technical users
- [ ] Auto-detection of table structures
- [ ] Machine learning-based column detection
- [ ] Parallel processing for large batches
- [ ] Docker container for easy deployment
- [ ] Support for scanned handwritten forms

---

**Star ⭐ this repository if you find it useful!**
