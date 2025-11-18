# Usage Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Command Line Interface](#command-line-interface)
- [Configuration](#configuration)
- [Python API](#python-api)
- [Common Workflows](#common-workflows)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure Tesseract OCR is installed:
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### 2. Generate Configuration

```bash
python -m pdf_data_extractor.cli --init-config my_config.yaml
```

### 3. Run Extraction

```bash
python -m pdf_data_extractor.cli --config my_config.yaml --download
```

## Command Line Interface

### Basic Usage

```bash
# Full pipeline: download → convert → extract → export
pdf-extract --config config.yaml --download

# Process existing PDFs
pdf-extract --input ./pdfs/*.pdf --output results.xlsx

# Process existing images (skip conversion)
pdf-extract --images ./images/*.jpg --format csv
```

### Options

#### Input Options

- `--download`: Download PDFs using URL pattern from config
- `--input PDF [PDF ...]`: Process local PDF files
- `--images IMAGE [IMAGE ...]`: Process existing images

#### Output Options

- `--output PATH`: Output file path
- `--format {excel,csv,json}`: Output format
- `--data-format {census,election,generic}`: Data format type

#### Processing Options

- `--skip-conversion`: Skip PDF to image conversion
- `--clean`: Clean temporary files after processing
- `--config PATH`: Configuration file path

#### Logging Options

- `--verbose, -v`: Enable debug logging
- `--quiet, -q`: Suppress console output

## Configuration

Configuration files use YAML format. See `examples/` directory for templates.

### Key Sections

#### Download Configuration

```yaml
download:
  base_url: "https://example.com/pdfs/"
  file_pattern: "{district_code}{data_type}.pdf"
  district_range: [1, 100]
  data_type: "09"
  output_dir: "./downloads"
  delay_seconds: 3
```

#### OCR Configuration

```yaml
ocr:
  engine: "tesseract"
  tesseract_config: "--psm 6 --oem 1"
  preprocessing:
    grayscale: true
    resize_factor: 1.2
    interpolation: "cubic"
```

#### Parsing Configuration

```yaml
parsing:
  data_format: "census"
  keywords:
    census: ["DISTRICT", "TEHSIL", "DIVISION"]
  column_mappings:
    census_religion_7:
      - "SEX"
      - "TOTAL"
      - "MUSLIM"
      # ... more columns
```

## Python API

You can also use the package programmatically:

```python
from pdf_data_extractor import Config, PDFDownloader, PDFConverter, OCREngine, DataParser, DataExporter

# Load configuration
config = Config("config.yaml")

# Initialize components
downloader = PDFDownloader(config)
converter = PDFConverter(config)
ocr = OCREngine(config)
parser = DataParser(config)
exporter = DataExporter(config)

# Process pipeline
pdf_files = downloader.download_from_url_pattern()
images = converter.convert_pdfs(pdf_files)
all_images = [img for img_list in images.values() for img in img_list]
ocr_results = ocr.process_images(all_images)
data = parser.parse_ocr_results(ocr_results)
output_path = exporter.export(data)

print(f"Data exported to: {output_path}")
```

## Common Workflows

### Workflow 1: Pakistan Census Data

```bash
# Copy example config
cp examples/config_pakistan_census.yaml my_census.yaml

# Edit if needed
vim my_census.yaml

# Run extraction
pdf-extract --config my_census.yaml --download --verbose
```

### Workflow 2: Process Local PDFs

```bash
# Create config
pdf-extract --init-config local_config.yaml

# Edit to set data_format and column mappings
vim local_config.yaml

# Process PDFs in a directory
pdf-extract --config local_config.yaml --input ./my_pdfs/*.pdf --output results.xlsx
```

### Workflow 3: Re-process Existing Images

If you already converted PDFs to images:

```bash
pdf-extract --config config.yaml --images ./images/*.jpg --format csv
```

### Workflow 4: Export in Multiple Formats

```python
from pdf_data_extractor import Config, DataExporter
import pandas as pd

config = Config("config.yaml")
exporter = DataExporter(config)

# Load your data
data = pd.read_excel("temp_results.xlsx")

# Export in all formats
results = exporter.export_all_formats(data)
print(results)
# {'excel': './output/data.xlsx', 'csv': './output/data.csv', 'json': './output/data.json'}
```

## Troubleshooting

### OCR Quality Issues

If OCR results are poor:

1. Increase image DPI in config:
   ```yaml
   conversion:
     dpi: 400  # or higher
   ```

2. Adjust resize factor:
   ```yaml
   ocr:
     preprocessing:
       resize_factor: 1.5  # try different values
   ```

3. Try different Tesseract PSM modes:
   - `--psm 6`: Uniform block of text (default)
   - `--psm 4`: Single column of text
   - `--psm 11`: Sparse text

### Missing Data

If data extraction is incomplete:

1. Check keywords match your PDFs:
   ```yaml
   parsing:
     keywords:
       census: ["YOUR", "ACTUAL", "KEYWORDS"]
   ```

2. Enable debug logging:
   ```bash
   pdf-extract --config config.yaml --verbose
   ```

3. Check column mappings match your data structure

### Performance

For large datasets:

1. Process in batches
2. Use `--skip-conversion` if images already exist
3. Use CSV format instead of Excel for faster export
