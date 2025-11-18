#!/usr/bin/env python3
"""
Improved PDF Table Extractor with Hierarchical Structure Recognition
Handles nested headers and hierarchical data properly
"""

import sys
import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List, Tuple
import re


def extract_hierarchical_table(pdf_path: str) -> pd.DataFrame:
    """
    Extract hierarchical table data from PDF
    Understands nested structure: Region → Section → Sex → Data
    """

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()

    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Find where data starts (after the header with column numbers)
    data_start_idx = 0
    for i, line in enumerate(lines):
        if re.match(r'^1\s+2\s+3\s+4', line):  # Column numbers line
            data_start_idx = i + 1
            break

    # Find header line (AREA/SEX TOTAL MUSLIM...)
    header_idx = data_start_idx - 2
    headers = ['REGION', 'SECTION', 'AREA/SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN', 'HINDU', 'QADIANI/AHMADI', 'SCHEDULED CASTES', 'OTHERS']

    # Parse hierarchical data
    rows = []
    current_region = None
    current_section = None

    for line in lines[data_start_idx:]:
        # Skip empty lines
        if not line or line == '-':
            continue

        # Check if this is a region header (contains "DISTRICT" or "SUB-DIVISION")
        if 'DISTRICT' in line or 'SUB-DIVISION' in line:
            current_region = line
            continue

        # Check if this is a section header (OVERALL, RURAL, URBAN)
        if line in ['OVERALL', 'RURAL', 'URBAN']:
            current_section = line
            continue

        # Check if this is a sex category
        sex_categories = ['ALL SEXES', 'MALE', 'FEMALE', 'TRANSGENDER']
        for sex in sex_categories:
            if line.startswith(sex):
                # Extract the data values after the sex category
                data_part = line[len(sex):].strip()
                # Split by whitespace and clean
                values = data_part.split()

                # Convert numbers (handle commas and dashes)
                cleaned_values = []
                for v in values:
                    v = v.replace(',', '')
                    if v == '-' or v == '':
                        cleaned_values.append(None)
                    else:
                        try:
                            cleaned_values.append(int(v))
                        except:
                            cleaned_values.append(v)

                # Ensure we have exactly 7 data columns
                while len(cleaned_values) < 7:
                    cleaned_values.append(None)

                # Create row with hierarchy
                row = [current_region, current_section, sex] + cleaned_values[:7]
                rows.append(row)
                break

    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)

    # Fill forward the region and section columns
    df['REGION'] = df['REGION'].fillna(method='ffill')
    df['SECTION'] = df['SECTION'].fillna(method='ffill')

    return df


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_improved.py input.pdf [output.xlsx]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_pdf.replace('.pdf', '_improved.xlsx')

    print(f"Extracting hierarchical data from: {input_pdf}")

    # Extract data
    df = extract_hierarchical_table(input_pdf)

    # Save to Excel
    df.to_excel(output_file, index=False)

    print(f"✓ Extracted {len(df)} rows")
    print(f"✓ Saved to: {output_file}")
    print(f"\nPreview (first 10 rows):")
    print(df.head(10).to_string())
    print(f"\nNull counts:")
    print(df.isnull().sum())


if __name__ == "__main__":
    main()
