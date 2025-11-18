#!/usr/bin/env python3
"""
Smart PDF Census Data Extractor - AI-Enhanced Layout Detection

This script uses intelligent layout detection to extract data from PDFs:
1. Tries pdfplumber for born-digital PDFs (fast, accurate)
2. Falls back to PaddleOCR for scanned PDFs (AI-powered)
3. Final fallback to Tesseract OCR

All methods are completely free and run locally (no API keys needed).

Usage:
    python extract_smart_pdf.py input.pdf output.xlsx
    python extract_smart_pdf.py input.pdf  # auto-generates output name

Features:
- Automatic package installation
- Intelligent method selection
- AI-powered table detection
- Multi-page PDF support
- Clean Excel output
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple


def install_packages():
    """Install required packages if not available"""
    required_packages = {
        'pdfplumber': 'pdfplumber',
        'paddleocr': 'paddleocr',
        'paddlepaddle': 'paddlepaddle',
        'pdf2image': 'pdf2image',
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'pytesseract': 'pytesseract',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'tqdm': 'tqdm',
    }

    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        print("This may take a few minutes for AI packages...\n")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", *missing, "-q"
        ])
        print("✓ Packages installed successfully\n")


def is_scanned_pdf(pdf_path: str) -> bool:
    """
    Detect if PDF is scanned (image-based) or born-digital (text-based)

    Returns:
        True if scanned, False if born-digital
    """
    import pdfplumber

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check first page
            page = pdf.pages[0]
            text = page.extract_text()

            # If we can extract meaningful text, it's born-digital
            if text and len(text.strip()) > 100:
                return False
            else:
                return True
    except Exception:
        # If pdfplumber fails, assume scanned
        return True


def extract_with_pdfplumber(pdf_path: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract data using pdfplumber (for born-digital PDFs)

    Returns:
        (data_rows, method_used)
    """
    import pdfplumber
    import re

    print("  Method: pdfplumber (direct PDF text extraction)")

    all_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Try table extraction first
            tables = page.extract_tables()

            if tables:
                # Process detected tables
                for table in tables:
                    for row in table:
                        if row and any(row):  # Skip empty rows
                            all_data.append({
                                'page': page_num,
                                'method': 'table',
                                'row': row
                            })
            else:
                # Fall back to text extraction
                text = page.extract_text()
                if text:
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    for line in lines:
                        all_data.append({
                            'page': page_num,
                            'method': 'text',
                            'line': line
                        })

    return all_data, "pdfplumber"


def extract_with_paddleocr(pdf_path: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract data using PaddleOCR with table structure recognition

    Returns:
        (data_rows, method_used)
    """
    from paddleocr import PaddleOCR, PPStructure
    from pdf2image import convert_from_path
    import numpy as np
    from PIL import Image
    from tqdm import tqdm

    print("  Method: PaddleOCR (AI-powered layout + OCR)")

    # Initialize PaddleOCR with table structure recognition
    # use_angle_cls=True helps with rotated text
    # show_log=False to reduce noise
    ocr = PPStructure(show_log=False, use_angle_cls=True, lang='en')

    # Convert PDF to images
    print("  Converting PDF to images...")
    images = convert_from_path(str(pdf_path), dpi=300)

    all_data = []

    print("  Processing with AI layout detection...")
    for page_num, image in enumerate(tqdm(images, desc="  Pages"), 1):
        # Convert PIL Image to numpy array
        img_array = np.array(image)

        # Run structure analysis (detects tables, text regions, etc.)
        result = ocr(img_array)

        for item in result:
            item_type = item.get('type', 'unknown')

            if item_type == 'table':
                # Extract table structure
                table_cells = item.get('res', {}).get('html', '')
                all_data.append({
                    'page': page_num,
                    'type': 'table',
                    'content': item,
                    'bbox': item.get('bbox', [])
                })
            elif item_type == 'text':
                # Extract text region
                text_result = item.get('res', [])
                for text_item in text_result:
                    if 'text' in text_item:
                        all_data.append({
                            'page': page_num,
                            'type': 'text',
                            'text': text_item['text'],
                            'bbox': text_item.get('bbox', []),
                            'confidence': text_item.get('confidence', 0)
                        })

    return all_data, "PaddleOCR"


def extract_with_tesseract(pdf_path: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract data using Tesseract OCR (fallback method)

    Returns:
        (data_rows, method_used)
    """
    import cv2
    import pytesseract
    import numpy as np
    from pdf2image import convert_from_path
    from tqdm import tqdm

    print("  Method: Tesseract OCR (fallback)")

    # Convert PDF to images
    images = convert_from_path(str(pdf_path), dpi=300)

    all_data = []

    for page_num, image in enumerate(tqdm(images, desc="  Processing pages"), 1):
        # Preprocess image
        img_array = np.array(image.convert('L'))
        img_resized = cv2.resize(img_array, None, fx=1.2, fy=1.2,
                                  interpolation=cv2.INTER_CUBIC)

        # Perform OCR
        text = pytesseract.image_to_string(img_resized, config='--psm 6 --oem 1')
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        for line in lines:
            all_data.append({
                'page': page_num,
                'type': 'text',
                'text': line
            })

    return all_data, "Tesseract"


def parse_census_data(raw_data: List[Dict], method: str) -> List[Dict]:
    """
    Parse extracted data into structured census format

    Args:
        raw_data: Raw extracted data from any method
        method: Which extraction method was used

    Returns:
        List of structured data rows
    """
    import re

    parsed_data = []
    current_region = None
    current_section = None

    # Extract text lines based on method
    if method == "pdfplumber":
        lines = []
        for item in raw_data:
            if item.get('method') == 'text':
                lines.append(item['line'])
            elif item.get('method') == 'table':
                # Join table row elements
                row = item['row']
                line = ' '.join([str(cell) for cell in row if cell])
                lines.append(line)
    else:  # PaddleOCR or Tesseract
        lines = [item.get('text', '') for item in raw_data if item.get('text')]

    for line in lines:
        # Detect region headers
        if any(keyword in line.upper() for keyword in
               ['DISTRICT', 'SUB-DIVISION', 'CONSTITUENCY', 'DIVISION', 'TEHSIL', 'TALUKA']):
            current_region = line
            continue

        # Detect section headers
        if line.upper() in ['OVERALL', 'RURAL', 'URBAN']:
            current_section = line.upper()
            continue

        # Parse data rows
        if any(line.upper().startswith(sex) for sex in
               ['ALL SEXES', 'MALE', 'FEMALE', 'TRANSGENDER']):

            # Extract sex category
            if line.upper().startswith('ALL SEXES'):
                sex = 'ALL'
                data_part = re.sub(r'^ALL SEXES\s+', '', line, flags=re.IGNORECASE)
            elif line.upper().startswith('TRANSGENDER'):
                sex = 'TRANSGENDER'
                data_part = re.sub(r'^TRANSGENDER\s+', '', line, flags=re.IGNORECASE)
            elif line.upper().startswith('MALE'):
                sex = 'MALE'
                data_part = re.sub(r'^MALE\s+', '', line, flags=re.IGNORECASE)
            elif line.upper().startswith('FEMALE'):
                sex = 'FEMALE'
                data_part = re.sub(r'^FEMALE\s+', '', line, flags=re.IGNORECASE)
            else:
                continue

            # Extract numbers
            parts = data_part.split()
            numbers = []

            for part in parts:
                # Clean the number
                clean = part.replace(',', '').replace('O', '0').replace('o', '0')
                clean = clean.replace('Z', '2').replace('z', '2')
                clean = clean.replace('S', '5').replace('s', '5')
                clean = clean.replace('l', '1').replace('I', '1')

                if clean == '-' or clean == '—':
                    numbers.append(None)
                elif clean.isdigit():
                    numbers.append(int(clean))

            # Build row if we have enough numbers
            if len(numbers) >= 7:
                row = {
                    'REGION': current_region or '',
                    'SECTION': current_section or '',
                    'SEX': sex,
                    'TOTAL': numbers[0] if len(numbers) > 0 else None,
                    'MUSLIM': numbers[1] if len(numbers) > 1 else None,
                    'CHRISTIAN': numbers[2] if len(numbers) > 2 else None,
                    'HINDU': numbers[3] if len(numbers) > 3 else None,
                    'QADIANI_AHMADI': numbers[4] if len(numbers) > 4 else None,
                    'SCHEDULED_CASTES': numbers[5] if len(numbers) > 5 else None,
                    'OTHERS': numbers[6] if len(numbers) > 6 else None,
                }
                parsed_data.append(row)

    return parsed_data


def main(pdf_path: str, output_path: str = None):
    """
    Smart extraction with automatic method selection

    Args:
        pdf_path: Path to input PDF file
        output_path: Path for output Excel file (optional)
    """

    # Install packages if needed
    print("Checking dependencies...")
    install_packages()

    # Import after installation
    import pandas as pd

    print("\n" + "=" * 70)
    print("SMART PDF CENSUS DATA EXTRACTOR")
    print("=" * 70)

    # Validate input
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: PDF file not found: {pdf_path}")
        sys.exit(1)

    # Set output path
    if output_path is None:
        output_path = pdf_path.with_suffix('').with_suffix('.xlsx')
    else:
        output_path = Path(output_path)

    print(f"Input PDF:    {pdf_path}")
    print(f"Output Excel: {output_path}")
    print("=" * 70 + "\n")

    # Step 1: Detect PDF type
    print("[1/4] Analyzing PDF type...")
    is_scanned = is_scanned_pdf(str(pdf_path))

    if is_scanned:
        print("  ✓ Detected: Scanned/Image-based PDF")
        print("  → Will use AI-powered OCR methods\n")
    else:
        print("  ✓ Detected: Born-digital PDF (contains text)")
        print("  → Will use direct text extraction\n")

    # Step 2: Extract data with appropriate method
    print("[2/4] Extracting data...")

    try:
        if not is_scanned:
            # Try pdfplumber for born-digital PDFs
            raw_data, method = extract_with_pdfplumber(str(pdf_path))
            print(f"  ✓ Extracted {len(raw_data)} items using {method}\n")
        else:
            # Try PaddleOCR for scanned PDFs
            try:
                raw_data, method = extract_with_paddleocr(str(pdf_path))
                print(f"  ✓ Extracted {len(raw_data)} items using {method}\n")
            except Exception as e:
                print(f"  PaddleOCR failed: {e}")
                print("  Falling back to Tesseract...\n")
                raw_data, method = extract_with_tesseract(str(pdf_path))
                print(f"  ✓ Extracted {len(raw_data)} items using {method}\n")

    except Exception as e:
        print(f"  Primary method failed: {e}")
        print("  Trying fallback method...\n")
        raw_data, method = extract_with_tesseract(str(pdf_path))
        print(f"  ✓ Extracted {len(raw_data)} items using {method}\n")

    # Step 3: Parse data
    print("[3/4] Parsing data...")
    parsed_data = parse_census_data(raw_data, method)
    print(f"  ✓ Parsed {len(parsed_data)} data rows\n")

    # Step 4: Create DataFrame and export
    print("[4/4] Creating Excel file...")
    df = pd.DataFrame(parsed_data)

    if df.empty:
        print("  WARNING: No data extracted!")
        print("  The PDF may have an unusual format.")
        sys.exit(1)

    # Clean and sort
    df = df.drop_duplicates()
    df = df.sort_values(['REGION', 'SECTION', 'SEX'])

    # Export to Excel
    df.to_excel(output_path, index=False)

    file_size = output_path.stat().st_size
    print(f"  ✓ Exported to {output_path}\n")

    # Summary
    print("=" * 70)
    print("EXTRACTION COMPLETE!")
    print("=" * 70)
    print(f"Extraction method: {method}")
    print(f"Rows extracted:    {len(df)}")
    print(f"Columns:           {len(df.columns)}")
    print(f"Output file:       {output_path}")
    print(f"File size:         {file_size:,} bytes")
    print("=" * 70)

    # Show sample
    print("\nFirst 5 rows:\n")
    print(df.head().to_string(index=False))
    print("\n" + "=" * 70)
    print(f"SUCCESS! Open {output_path} to view all data")
    print("=" * 70 + "\n")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_smart_pdf.py <input.pdf> [output.xlsx]")
        print("\nExamples:")
        print("  python extract_smart_pdf.py example.pdf")
        print("  python extract_smart_pdf.py example.pdf output.xlsx")
        print("\nFeatures:")
        print("  - Automatic detection of PDF type (scanned vs born-digital)")
        print("  - Intelligent method selection for best results")
        print("  - AI-powered table detection (PaddleOCR)")
        print("  - Direct text extraction (pdfplumber)")
        print("  - OCR fallback (Tesseract)")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    main(input_file, output_file)
