#!/usr/bin/env python3
"""
Advanced PDF Table Extractor with Proper Column Detection
Handles hierarchical structure and multi-word names correctly
"""

import sys
import pdfplumber
import pandas as pd
import re


def extract_hierarchical_table(pdf_path: str) -> pd.DataFrame:
    """
    Extract hierarchical table data with proper column alignment
    """

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()

    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Find header and data start
    data_start_idx = 0
    for i, line in enumerate(lines):
        if re.match(r'^1\s+2\s+3\s+4', line):
            data_start_idx = i + 1
            break

    # Process data rows
    rows = []
    current_region = None
    current_section = None

    for line in lines[data_start_idx:]:
        # Check for region headers
        if 'DISTRICT' in line or 'SUB-DIVISION' in line:
            current_region = line
            continue

        # Check for section headers
        if line in ['OVERALL', 'RURAL', 'URBAN']:
            current_section = line
            continue

        # Check for data rows (start with sex category)
        sex_categories = ['ALL SEXES', 'MALE', 'FEMALE', 'TRANSGENDER']
        found_sex = None
        for sex in sex_categories:
            if line.startswith(sex):
                found_sex = sex
                break

        if found_sex:
            # Remove the sex category from the line to get just the data
            data_part = line[len(found_sex):].strip()

            # Split by whitespace
            tokens = data_part.split()

            # Clean and parse numbers (handle commas and dashes)
            values = []
            for token in tokens:
                token = token.replace(',', '')
                if token == '-' or token == '':
                    values.append(None)
                else:
                    try:
                        values.append(int(token))
                    except:
                        try:
                            values.append(float(token))
                        except:
                            # If it's text, it might be part of the sex category (skip)
                            continue

            # Ensure we have exactly 7 data columns (TOTAL through OTHERS)
            while len(values) < 7:
                values.append(None)

            # Take only first 7 values
            values = values[:7]

            # Create row
            row = [current_region, current_section, found_sex] + values
            rows.append(row)

    # Create DataFrame
    headers = ['REGION', 'SECTION', 'AREA/SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN',
               'HINDU', 'QADIANI/AHMADI', 'SCHEDULED CASTES', 'OTHERS']
    df = pd.DataFrame(rows, columns=headers)

    # Forward fill hierarchical columns
    df['REGION'] = df['REGION'].ffill()
    df['SECTION'] = df['SECTION'].ffill()

    return df


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_hierarchical.py input.pdf [output.xlsx]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_pdf.replace('.pdf', '_hierarchical.xlsx')

    print("=" * 70)
    print("HIERARCHICAL TABLE EXTRACTOR")
    print("=" * 70)
    print(f"\nInput:  {input_pdf}")
    print(f"Output: {output_file}")
    print()

    # Extract data
    print("[1/3] Extracting hierarchical table...")
    df = extract_hierarchical_table(input_pdf)
    print(f"✓ Extracted {len(df)} rows")

    # Save to Excel
    print("\n[2/3] Saving to Excel...")
    df.to_excel(output_file, index=False)
    print(f"✓ Saved to {output_file}")

    # Display preview
    print("\n[3/3] Quality check...")
    print(f"\nShape: {df.shape}")
    print(f"\nColumn alignment check:")
    print(f"  REGION column NaN: {df['REGION'].isna().sum()}")
    print(f"  SECTION column NaN: {df['SECTION'].isna().sum()}")
    print(f"  AREA/SEX column NaN: {df['AREA/SEX'].isna().sum()}")

    print(f"\nNull counts in data columns:")
    data_cols = ['TOTAL', 'MUSLIM', 'CHRISTIAN', 'HINDU', 'QADIANI/AHMADI', 'SCHEDULED CASTES', 'OTHERS']
    for col in data_cols:
        null_count = df[col].isna().sum()
        print(f"  {col:20s}: {null_count:3d} null values")

    print(f"\nFirst 10 rows:")
    print(df.head(10).to_string())

    print(f"\nLast 5 rows:")
    print(df.tail(5).to_string())

    # Check for any misaligned data
    print(f"\n✓ Quality Check:")
    print(f"  Total rows: {len(df)}")
    print(f"  Expected: ~60 rows (5 regions × 3 sections × 4 sex categories)")

    print("\n" + "=" * 70)
    print("✓ EXTRACTION COMPLETE - Open Excel file to verify alignment")
    print("=" * 70)


if __name__ == "__main__":
    main()
