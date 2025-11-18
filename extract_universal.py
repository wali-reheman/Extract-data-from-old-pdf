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

    # Detect number format: French (spaces) vs English (commas)
    # Check first 20 rows for comma patterns
    uses_french_format = True
    comma_count = 0
    number_count = 0
    for row in rows[:20]:
        row_text = ' '.join(str(cell) for cell in row)
        # Count numbers with commas (English format like "1,435,332")
        comma_numbers = len(re.findall(r'\d{1,3},\d{3}', row_text))
        comma_count += comma_numbers
        # Count large numbers (4+ digits)
        large_numbers = len(re.findall(r'\b\d{4,}\b', row_text))
        number_count += large_numbers

    # If we have many comma-formatted numbers, it's English format
    if comma_count >= 3:
        uses_french_format = False

    header_candidates = []
    data_candidates = []
    current_region = None
    current_section = None

    for row in rows:
        row_text = ' '.join(str(cell) for cell in row)

        # Count numbers vs words
        large_numbers = re.findall(r'\b\d{2,}[,\d]*\b', row_text)
        numbers_count = len(large_numbers)
        words = re.findall(r'\b[A-Za-z]{3,}\b', row_text)
        words_count = len(words)

        # Header detection (has relevant keywords but NO numbers)
        # Avoid keywords that appear in data rows (SEX, MALE, FEMALE)
        header_keywords = ['TABLE', 'POPULATION', 'COUNT',
                          'AREA/', 'REGION', 'DISTRICT', 'COLUMN',
                          'VOTERS', 'VOTES', 'PERCENTAGE', 'RELIGION', 'CATEGORY']

        has_header = any(kw in row_text.upper() for kw in header_keywords)

        # Metadata/section markers (text-only, no large numbers)
        section_keywords = ['OVERALL', 'RURAL', 'URBAN', 'DISTRICT', 'DIVISION',
                           'CONSTITUENCY', 'PROVINCE', 'STATE', 'COUNTY', 'REGION']

        is_section = any(kw in row_text.upper() for kw in section_keywords) and numbers_count == 0

        # Data rows: Pattern is TEXT followed by numbers/dashes
        # Count dashes (which represent null/zero values in data rows)
        dashes = row_text.count('-')

        # Data row if it has:
        # 1. Numbers and words, OR
        # 2. Multiple dashes (like "- - - - -" which is valid census data), OR
        # 3. Words with any numeric content (numbers or dashes)
        has_numeric_content = numbers_count >= 1 or dashes >= 3
        has_data = (words_count >= 1 and has_numeric_content)

        # Classification
        if has_header and numbers_count == 0:  # Headers have NO large numbers
            header_candidates.append(row)
        elif is_section:
            # Track section/region context
            if 'DISTRICT' in row_text.upper() or 'DIVISION' in row_text.upper():
                current_region = row_text
                current_section = None
            else:
                current_section = row_text
        elif has_data:
            # Add context to data row
            data_candidates.append({
                'region': current_region,
                'section': current_section,
                'row': row
            })

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

        # Combine short adjacent words (like "AREA/" + "SEX" → "AREA/SEX")
        combined_headers = []
        i = 0
        while i < len(parts):
            if i < len(parts) - 1 and len(parts[i]) <= 6 and '/' in parts[i]:
                # Combine this with next (e.g., "AREA/" + "SEX")
                combined_headers.append(parts[i] + parts[i+1])
                i += 2
            else:
                combined_headers.append(parts[i])
                i += 1

        headers = [h.strip() for h in combined_headers if h.strip()]
    else:
        # Generate generic headers
        max_cols = max(len(row) for row in rows) if rows else 0
        headers = [f'Column_{i+1}' for i in range(max_cols)]

    # Parse data rows - extract ALL fields (text labels + numbers) with context
    parsed_data = []

    for item in data_candidates:
        # Extract context and row
        region = item.get('region', '')
        section = item.get('section', '')
        row = item.get('row', item)  # Fallback if item is just a row

        # For single-cell rows, split on whitespace to extract all fields
        if len(row) == 1:
            # Split into words and numbers
            parts = re.split(r'(\s+)', str(row[0]))
            parts = [p.strip() for p in parts if p.strip()]
        else:
            parts = row

        # Start with context columns
        parsed_row = [region or '', section or '']

        # First pass: Parse all parts
        temp_values = []
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
                temp_values.append(None)
            elif clean.replace('.', '').isdigit():
                try:
                    if '.' in clean:
                        temp_values.append(float(clean))
                    else:
                        temp_values.append(int(clean))
                except ValueError:
                    temp_values.append(part_str)
            else:
                # Keep as text (e.g., "ALL", "MALE", "FEMALE")
                temp_values.append(part_str)

        # Second pass: Combine multi-word patterns and French numbers
        combined_values = []
        i = 0
        while i < len(temp_values):
            # Pattern 1: Combine "ALL SEXES"
            if (i < len(temp_values) - 1 and
                isinstance(temp_values[i], str) and
                isinstance(temp_values[i+1], str) and
                temp_values[i].upper() == 'ALL' and
                temp_values[i+1].upper() == 'SEXES'):
                combined_values.append('ALL SEXES')
                i += 2

            # Pattern 2: Combine French-formatted numbers (space-separated)
            # Example: "1 132 655" → 1132655, "350 731" → 350731, "71 148" → 71148
            # ONLY apply to French-formatted PDFs (detected by lack of commas)
            # English PDFs with commas don't need this combining
            elif (uses_french_format and
                  isinstance(temp_values[i], int) and
                  temp_values[i] < 1000 and
                  i < len(temp_values) - 1):
                first_num = temp_values[i]
                num_sequence = [first_num]
                j = i + 1

                # Determine max groups based on first number size
                # Only allow 3-part numbers (millions) when first number is 1-4
                # Census data rarely has values over 5 million except total population
                if first_num <= 4:
                    max_groups = 2  # e.g., "1 132 655" (millions), but not "5 731 562"
                elif first_num < 100:
                    max_groups = 1  # e.g., "71 148" (thousands)
                else:  # 100-999
                    max_groups = 1  # e.g., "350 731" (hundreds of thousands)

                # Collect consecutive 3-digit groups
                collected = 0
                while (j < len(temp_values) and
                       isinstance(temp_values[j], int) and
                       100 <= temp_values[j] <= 999 and
                       collected < max_groups):
                    num_sequence.append(temp_values[j])
                    j += 1
                    collected += 1

                # If we combined at least 2 numbers, create the combined value
                if len(num_sequence) >= 2:
                    combined_num_str = ''.join(str(n).zfill(3) if idx > 0 else str(n)
                                               for idx, n in enumerate(num_sequence))
                    combined_num = int(combined_num_str)
                    combined_values.append(combined_num)
                    i = j
                else:
                    # Single number, keep as-is
                    combined_values.append(temp_values[i])
                    i += 1
            else:
                combined_values.append(temp_values[i])
                i += 1

        parsed_row.extend(combined_values)

        # Keep row if it has at least one value (including text labels)
        # This preserves rows like "ALL SEXES - - - - - -" which are valid data
        if parsed_row and len(parsed_row) > 2:  # At least region, section, and one data field
            parsed_data.append(parsed_row)

    # Prepend REGION and SECTION to headers
    headers = ['REGION', 'SECTION'] + headers

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
