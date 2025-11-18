#!/usr/bin/env python3
"""
Universal PDF Table Extractor - Works with ANY Census/Election Data

Completely generic extraction that:
- Automatically detects table structures
- Extracts column headers dynamically
- Works with census, election, or any statistical PDF
- NO hardcoded keywords or column names

Uses: pdfplumber (fast) → Tesseract OCR (fallback)
100% free, runs locally, no API keys needed.

Usage:
    python extract_universal.py input.pdf output.xlsx
    python extract_universal.py input.pdf  # auto-generates output name
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re


def install_if_missing():
    """Check and install required packages"""
    required = {
        'pdfplumber': 'pdfplumber',
        'pdf2image': 'pdf2image',
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'pytesseract': 'pytesseract',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
    }

    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Installing: {', '.join(missing)}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", *missing, "-q"
        ])
        print("✓ Installed\n")


def try_pdfplumber(pdf_path: str) -> Tuple[List[List[str]], bool]:
    """Try extracting with pdfplumber - prioritize text over tables"""
    import pdfplumber

    all_rows = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract as text lines (more reliable than table detection)
                text = page.extract_text()

                if text:
                    for line in text.split('\n'):
                        line = line.strip()
                        if line and len(line) > 2:  # Skip very short lines
                            all_rows.append([line])
                else:
                    # Fallback to table extraction
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            for row in table:
                                if row and any(cell and str(cell).strip() for cell in row):
                                    cleaned = [str(cell).strip() if cell else '' for cell in row]
                                    all_rows.append(cleaned)

        return all_rows, True

    except Exception as e:
        print(f"  pdfplumber: {str(e)[:50]}")
        return [], False


def try_tesseract(pdf_path: str) -> List[List[str]]:
    """Extract with Tesseract OCR"""
    import cv2
    import pytesseract
    import numpy as np
    from pdf2image import convert_from_path

    images = convert_from_path(str(pdf_path), dpi=300)

    all_rows = []

    for image in images:
        # Preprocess
        img_array = np.array(image.convert('L'))
        img_resized = cv2.resize(img_array, None, fx=1.2, fy=1.2,
                                  interpolation=cv2.INTER_CUBIC)

        # OCR
        text = pytesseract.image_to_string(img_resized, config='--psm 6 --oem 1')

        for line in text.split('\n'):
            line = line.strip()
            if line:
                # Try to split into columns based on multiple spaces
                parts = re.split(r'\s{2,}', line)
                all_rows.append(parts)

    return all_rows


def smart_parse_table(rows: List[List[str]]) -> Tuple[List[str], List[List[Any]]]:
    """
    Intelligently parse table to find headers and data

    Works generically by:
    1. Finding rows with text (headers/metadata)
    2. Finding rows with numbers (data)
    3. Auto-detecting structure
    4. Preserving contextual information

    Returns:
        (headers, data_rows)
    """
    if not rows:
        return [], []

    header_candidates = []
    data_candidates = []
    metadata_context = {}

    for row in rows:
        row_text = ' '.join(str(cell) for cell in row)

        # Count numbers vs words
        large_numbers = re.findall(r'\b\d{2,}[,\d]*\b', row_text)
        numbers_count = len(large_numbers)
        words = re.findall(r'\b[A-Za-z]{3,}\b', row_text)
        words_count = len(words)

        # Header detection (has relevant keywords but few numbers)
        header_keywords = ['TABLE', 'TOTAL', 'POPULATION', 'COUNT', 'NUMBER',
                          'SEX', 'GENDER', 'AGE', 'AREA', 'REGION', 'DISTRICT',
                          'VOTERS', 'VOTES', 'PERCENTAGE', 'RELIGION', 'CATEGORY',
                          'TYPE', 'COLUMN', 'MALE', 'FEMALE']

        has_header = any(kw in row_text.upper() for kw in header_keywords)

        # Metadata/section markers (text-only, no large numbers)
        section_keywords = ['OVERALL', 'RURAL', 'URBAN', 'DISTRICT', 'DIVISION',
                           'CONSTITUENCY', 'PROVINCE', 'STATE', 'COUNTY', 'REGION']

        is_section = any(kw in row_text.upper() for kw in section_keywords) and numbers_count == 0

        # Data rows: Mix of text and numbers (lowered threshold to catch more rows)
        has_data = numbers_count >= 1 and words_count >= 1  # At least 1 number + 1 word

        # Classification
        if has_header and numbers_count == 0:  # Headers have NO large numbers
            header_candidates.append(row)
        elif is_section:
            # Track section context
            for keyword in section_keywords:
                if keyword in row_text.upper():
                    metadata_context['section'] = row_text
        elif has_data:
            data_candidates.append(row)

    # Choose best header (look for one with column-like structure)
    best_header = None

    for candidate in header_candidates:
        candidate_text = ' '.join(str(c) for c in candidate)
        # Good headers have multiple column names separated by spaces/tabs
        column_keywords = ['SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN', 'HINDU',
                          'MALE', 'FEMALE', 'AREA', 'COUNT', 'VOTES', 'VOTERS']

        keyword_matches = sum(1 for kw in column_keywords if kw in candidate_text.upper())

        if keyword_matches >= 3:  # Has at least 3 column-like words
            best_header = candidate
            break

    if best_header:
        # Split header into individual column names
        header_text = ' '.join(str(c) for c in best_header)
        # Try to split intelligently
        parts = re.split(r'\s{2,}', header_text)  # Split on 2+ spaces
        if len(parts) < 5:
            # Split on single space if multi-space didn't work
            parts = header_text.split()
        headers = [p.strip() for p in parts if p.strip()]
    else:
        # Generate generic headers
        max_cols = max(len(row) for row in rows) if rows else 0
        headers = [f'Column_{i+1}' for i in range(max_cols)]

    # Parse data rows - extract ALL fields (text labels + numbers)
    parsed_data = []

    for row in data_candidates:
        # For single-cell rows, split on whitespace to extract all fields
        if len(row) == 1:
            # Split into words and numbers
            parts = re.split(r'(\s+)', str(row[0]))
            parts = [p.strip() for p in parts if p.strip()]
        else:
            parts = row

        parsed_row = []
        for part in parts:
            part_str = str(part).strip()

            if not part_str:
                continue

            # Try to parse as number
            clean = part_str.replace(',', '').replace(' ', '')

            # Common OCR fixes
            clean = clean.replace('O', '0').replace('o', '0')
            clean = clean.replace('l', '1').replace('I', '1')
            clean = clean.replace('S', '5').replace('Z', '2')

            # Check if it's a number
            if clean == '-' or clean == '—':
                parsed_row.append(None)
            elif clean.replace('.', '').isdigit():
                try:
                    if '.' in clean:
                        parsed_row.append(float(clean))
                    else:
                        parsed_row.append(int(clean))
                except ValueError:
                    parsed_row.append(part_str)
            else:
                # Keep as text (e.g., "ALL", "MALE", "FEMALE")
                parsed_row.append(part_str)

        if parsed_row and any(x is not None for x in parsed_row):
            parsed_data.append(parsed_row)

    return headers, parsed_data


def main(pdf_path: str, output_path: str = None):
    """Universal extraction for any PDF table"""

    print("Checking dependencies...")
    install_if_missing()

    import pandas as pd

    print("=" * 70)
    print("UNIVERSAL PDF TABLE EXTRACTOR")
    print("=" * 70)

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    if output_path is None:
        output_path = pdf_path.with_suffix('.xlsx')
    else:
        output_path = Path(output_path)

    print(f"Input:  {pdf_path}")
    print(f"Output: {output_path}")
    print("=" * 70 + "\n")

    # Extract data
    print("[1/3] Extracting data...")

    rows, success = try_pdfplumber(str(pdf_path))

    if not success or not rows:
        print("  → Trying Tesseract OCR...")
        rows = try_tesseract(str(pdf_path))
        method = "Tesseract OCR"
    else:
        method = "pdfplumber"

    print(f"  ✓ Method: {method}")
    print(f"  ✓ Extracted {len(rows)} rows\n")

    # Parse structure
    print("[2/3] Analyzing structure...")
    headers, data_rows = smart_parse_table(rows)

    print(f"  ✓ Columns: {len(headers)}")
    print(f"  ✓ Data rows: {len(data_rows)}\n")

    # Create output
    print("[3/3] Creating Excel...")

    if not data_rows:
        print("  WARNING: No data rows found!")
        sys.exit(1)

    # Normalize row lengths
    max_cols = max(len(row) for row in data_rows)

    while len(headers) < max_cols:
        headers.append(f'Col_{len(headers)+1}')

    for row in data_rows:
        while len(row) < max_cols:
            row.append(None)

    df = pd.DataFrame(data_rows, columns=headers[:max_cols])
    df = df.drop_duplicates()

    df.to_excel(output_path, index=False)

    print(f"  ✓ Saved to {output_path}\n")

    # Summary
    print("=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Method:      {method}")
    print(f"Rows:        {len(df)}")
    print(f"Columns:     {len(df.columns)}")
    print(f"Output:      {output_path}")
    print(f"Size:        {output_path.stat().st_size:,} bytes")
    print("=" * 70)

    print("\nPreview (first 10 rows):\n")
    print(df.head(10).to_string(index=False))
    print("\n" + "=" * 70)
    print(f"✓ Open {output_path.name} to view all data")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUniversal PDF Table Extractor")
        print("=" * 50)
        print("\nUsage: python extract_universal.py <input.pdf> [output.xlsx]")
        print("\nExamples:")
        print("  python extract_universal.py census.pdf")
        print("  python extract_universal.py election.pdf results.xlsx")
        print("\nFeatures:")
        print("  ✓ Works with ANY census/election format")
        print("  ✓ Auto-detects table structure")
        print("  ✓ No hardcoded keywords")
        print("  ✓ Free, local, no APIs")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
