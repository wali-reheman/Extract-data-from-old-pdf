"""Custom parser for complete census data extraction"""

import pandas as pd
import re
from pdf_data_extractor import Config, OCREngine

def parse_census_complete(ocr_result):
    """Parse complete census data including all sex categories and sections"""
    lines = ocr_result['lines']
    data = []

    current_region = None
    current_section = None  # OVERALL, RURAL, or URBAN

    for line in lines:
        line = line.strip()

        # Detect region headers
        if 'DISTRICT' in line or 'SUB-DIVISION' in line:
            current_region = line
            continue

        # Detect section headers
        if line in ['OVERALL', 'RURAL', 'URBAN']:
            current_section = line
            continue

        # Parse data rows (starts with ALL SEXES, MALE, FEMALE, or TRANSGENDER)
        if line.startswith(('ALL SEXES', 'MALE', 'FEMALE', 'TRANSGENDER')):
            parts = line.split()

            if len(parts) < 2:
                continue

            # Extract sex category
            if line.startswith('ALL SEXES'):
                sex = 'ALL'
                data_parts = parts[2:]  # Skip "ALL SEXES"
            elif line.startswith('TRANSGENDER'):
                sex = 'TRANSGENDER'
                data_parts = parts[1:]
            else:
                sex = parts[0]  # MALE or FEMALE
                data_parts = parts[1:]

            # Extract numeric columns (handle dashes and commas)
            numbers = []
            for part in data_parts:
                # Clean up the number
                clean = part.replace(',', '').replace('Z', '2').replace('s', '5').replace('o', '0')
                if clean == '-':
                    numbers.append('')
                elif clean.isdigit():
                    numbers.append(clean)

            # Build row
            if len(numbers) >= 7:
                row = {
                    'REGION': current_region or '',
                    'SECTION': current_section or '',
                    'SEX': sex,
                    'TOTAL': numbers[0] if len(numbers) > 0 else '',
                    'MUSLIM': numbers[1] if len(numbers) > 1 else '',
                    'CHRISTIAN': numbers[2] if len(numbers) > 2 else '',
                    'HINDU': numbers[3] if len(numbers) > 3 else '',
                    'QADIANI_AHMADI': numbers[4] if len(numbers) > 4 else '',
                    'SCHEDULED_CASTES': numbers[5] if len(numbers) > 5 else '',
                    'OTHERS': numbers[6] if len(numbers) > 6 else '',
                }
                data.append(row)

    return pd.DataFrame(data)

# Run the custom parser
config = Config()
ocr = OCREngine(config)
result = ocr.process_image("images/example pdf_page_0.jpeg")

df = parse_census_complete(result)
print(f"\n=== COMPLETE EXTRACTION ===")
print(f"Total rows extracted: {len(df)}\n")
print(df.to_string(index=False))

# Save to Excel
df.to_excel('complete_census_data.xlsx', index=False)
print(f"\n✅ Saved to complete_census_data.xlsx")
