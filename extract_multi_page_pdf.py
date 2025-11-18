#!/usr/bin/env python3
"""
Complete PDF Census Data Extractor - Standalone Script

This script extracts ALL data from multi-page census/election PDFs and outputs
clean Excel files.

Usage:
    python extract_multi_page_pdf.py input.pdf output.xlsx
    python extract_multi_page_pdf.py input.pdf  # auto-generates output name

Features:
- Automatic package installation check
- Multi-page PDF support
- Complete data extraction (all rows)
- Clean Excel output
- Progress tracking
"""

import sys
import subprocess
import os
from pathlib import Path


def install_packages():
    """Install required packages if not available"""
    required_packages = {
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
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", *missing
        ])
        print("✓ Packages installed successfully\n")


def main(pdf_path, output_path=None):
    """
    Extract census data from multi-page PDF

    Args:
        pdf_path: Path to input PDF file
        output_path: Path for output Excel file (optional)
    """

    # Install packages if needed
    print("Checking dependencies...")
    install_packages()

    # Now import after ensuring packages are installed
    import cv2
    import pytesseract
    import pandas as pd
    import re
    from pdf2image import convert_from_path
    from tqdm import tqdm

    print("\n" + "=" * 70)
    print("PDF CENSUS DATA EXTRACTOR")
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

    print(f"Input PDF:   {pdf_path}")
    print(f"Output Excel: {output_path}")
    print("=" * 70 + "\n")

    # Step 1: Convert PDF to images
    print("[1/4] Converting PDF to images...")
    try:
        images = convert_from_path(str(pdf_path), dpi=300)
        print(f"  ✓ Converted {len(images)} pages\n")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("\n  Make sure poppler is installed:")
        print("    Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("    macOS: brew install poppler")
        sys.exit(1)

    # Step 2: Perform OCR on each page
    print("[2/4] Performing OCR...")
    all_ocr_results = []

    for i, image in enumerate(tqdm(images, desc="  Processing pages")):
        # Preprocess image
        import numpy as np
        img_array = np.array(image.convert('L'))  # Convert to grayscale
        img_resized = cv2.resize(img_array, None, fx=1.2, fy=1.2,
                                  interpolation=cv2.INTER_CUBIC)

        # Perform OCR
        text = pytesseract.image_to_string(img_resized, config='--psm 6 --oem 1')
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        all_ocr_results.append({
            'page': i + 1,
            'lines': lines
        })

    total_lines = sum(len(r['lines']) for r in all_ocr_results)
    print(f"  ✓ Extracted {total_lines} lines from {len(images)} pages\n")

    # Step 3: Parse data
    print("[3/4] Parsing data...")
    all_data = []

    for page_result in all_ocr_results:
        lines = page_result['lines']
        page_num = page_result['page']

        current_region = None
        current_section = None

        for line in lines:
            # Detect region headers
            if any(keyword in line.upper() for keyword in
                   ['DISTRICT', 'SUB-DIVISION', 'CONSTITUENCY', 'DIVISION']):
                current_region = line
                continue

            # Detect section headers
            if line.upper() in ['OVERALL', 'RURAL', 'URBAN']:
                current_section = line.upper()
                continue

            # Parse data rows (starts with sex category)
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

                    if clean == '-':
                        numbers.append(None)
                    elif clean.isdigit():
                        numbers.append(int(clean))

                # Build row if we have enough numbers
                if len(numbers) >= 7:
                    row = {
                        'PAGE': page_num,
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
                    all_data.append(row)

    print(f"  ✓ Parsed {len(all_data)} rows\n")

    # Step 4: Create DataFrame and export
    print("[4/4] Creating Excel file...")
    df = pd.DataFrame(all_data)

    if df.empty:
        print("  WARNING: No data extracted!")
        sys.exit(1)

    # Clean and sort
    df = df.drop_duplicates()
    df = df.sort_values(['PAGE', 'REGION', 'SECTION', 'SEX'])

    # Export to Excel
    df.to_excel(output_path, index=False)

    file_size = output_path.stat().st_size
    print(f"  ✓ Exported to {output_path}\n")

    # Summary
    print("=" * 70)
    print("EXTRACTION COMPLETE!")
    print("=" * 70)
    print(f"Pages processed:  {len(images)}")
    print(f"Rows extracted:   {len(df)}")
    print(f"Columns:          {len(df.columns)}")
    print(f"Output file:      {output_path}")
    print(f"File size:        {file_size:,} bytes")
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
        print("Usage: python extract_multi_page_pdf.py <input.pdf> [output.xlsx]")
        print("\nExamples:")
        print("  python extract_multi_page_pdf.py example.pdf")
        print("  python extract_multi_page_pdf.py example.pdf output.xlsx")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    main(input_file, output_file)
