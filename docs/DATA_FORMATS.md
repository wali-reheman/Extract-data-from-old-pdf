# Data Format Guide

This document describes the supported data formats and how to configure extraction for different types of census and election PDFs.

## Overview

The PDF Data Extractor supports three main data format types:

1. **Census Data** - Population census data with demographic breakdowns
2. **Election Data** - Election results with polling station details
3. **Generic Data** - Any tabular data with custom parsing rules

## Census Data Format

### Characteristics

Census PDFs typically have:
- Hierarchical geographic divisions (District, Tehsil, Division, etc.)
- Demographic categories (Religion, Language, Age, Gender)
- Tabular data with multiple columns for different groups
- Subtotals and aggregates

### Example Structure

```
DISTRICT LAHORE
SEX    TOTAL    MUSLIM    CHRISTIAN    HINDU    OTHERS
Both   1234567  1200000   25000        5000     4567
Male   654321   640000    12000        2000     321
Female 580246   560000    13000        3000     4246
```

### Configuration

```yaml
parsing:
  data_format: "census"
  keywords:
    census:
      - "DISTRICT"
      - "TEHSIL"
      - "DIVISION"
      - "AGENCY"
      - "TALUKA"
  column_mappings:
    census_religion_7:
      - "SEX"
      - "TOTAL"
      - "MUSLIM"
      - "CHRISTIAN"
      - "HINDU"
      - "QADIANI/AHMADI"
      - "CASTE/SCHEDULED"
  filters:
    - "OVERALL"
    - "RURAL"
    - "URBAN"
```

### Column Mapping Strategy

The parser automatically detects the number of columns and selects the appropriate mapping:

- **census_religion_7**: 7 columns (basic religion breakdown)
- **census_religion_8**: 8 columns (includes "OTHERS")
- **census_religion_9**: 9 columns (includes extra column)

### Customizing for Your Census Data

1. **Identify keywords** that mark the start of data rows:
   ```yaml
   keywords:
     census:
       - "YOUR_DISTRICT_MARKER"
       - "YOUR_REGION_MARKER"
   ```

2. **Define column headers** based on your PDF structure:
   ```yaml
   column_mappings:
     census_custom_5:
       - "REGION"
       - "POPULATION"
       - "MALE"
       - "FEMALE"
       - "DENSITY"
   ```

3. **Add filters** to remove unwanted rows:
   ```yaml
   filters:
     - "TOTAL"
     - "SUMMARY"
   ```

## Election Data Format

### Characteristics

Election PDFs typically have:
- Polling station identifiers
- Voter registration numbers
- Vote counts by candidate/party
- Turnout percentages

### Example Structure

```
CONSTITUENCY: NA-123 LAHORE-IV

POLLING STATION              REGISTERED    CAST    VALID    REJECTED
PS-001 Govt School          1500          1200    1180     20
PS-002 Community Center     2000          1800    1750     50
```

### Configuration

```yaml
parsing:
  data_format: "election"
  keywords:
    election:
      - "CONSTITUENCY"
      - "POLLING"
      - "STATION"
      - "WARD"
  column_mappings:
    election_standard:
      - "POLLING_STATION"
      - "REGISTERED_VOTERS"
      - "VOTES_CAST"
      - "VALID_VOTES"
      - "REJECTED_VOTES"
```

### Parsing Differences

Election data parsing differs from census:
- Uses 2+ spaces as column delimiter (handles station names with spaces)
- Looks for all keyword-containing lines (not paired region/data)
- Supports multiple result tables per constituency

### Customizing for Your Election Data

1. **Define polling station markers**:
   ```yaml
   keywords:
     election:
       - "PS-"      # If stations are coded as PS-001, PS-002
       - "BOOTH"    # If called "BOOTH" instead of "STATION"
       - "WARD"     # For municipal elections
   ```

2. **Map your result columns**:
   ```yaml
   column_mappings:
     election_detailed:
       - "STATION_CODE"
       - "STATION_NAME"
       - "CANDIDATE_A"
       - "CANDIDATE_B"
       - "CANDIDATE_C"
       - "TOTAL"
   ```

## Generic Data Format

### When to Use

Use generic format when:
- Your data doesn't fit census or election patterns
- You have simple tabular data
- You want basic extraction without custom parsing

### Configuration

```yaml
parsing:
  data_format: "generic"
  keywords:
    generic: []  # Empty to process all lines
  column_mappings: {}  # Auto-generates COL_0, COL_1, etc.
```

### Output

Generic parsing creates columns named `COL_0`, `COL_1`, `COL_2`, etc.

You can post-process with pandas:
```python
import pandas as pd

data = pd.read_excel("generic_output.xlsx")
data.columns = ["Region", "Value1", "Value2", "Value3"]
data.to_excel("renamed_output.xlsx", index=False)
```

## OCR Preprocessing by Data Type

Different data types may need different OCR settings.

### Census Data
- Usually high-quality scans
- Dense text
- Standard settings work well:
  ```yaml
  ocr:
    preprocessing:
      grayscale: true
      resize_factor: 1.2
      interpolation: "cubic"
  ```

### Election Data
- Often poor-quality photocopies
- Handwritten annotations
- May need enhancement:
  ```yaml
  ocr:
    preprocessing:
      grayscale: true
      resize_factor: 1.5  # Higher magnification
      interpolation: "lanczos4"  # Better quality
  ```

### Old Documents
- Faded text
- Yellowed paper
- May benefit from:
  ```yaml
  ocr:
    preprocessing:
      grayscale: true
      resize_factor: 2.0  # Significant enlargement
      interpolation: "cubic"
  ```

## Output Schema

### Census Output

| Column | Description |
|--------|-------------|
| SEX | Gender category (Male/Female/Both) |
| TOTAL | Total population |
| MUSLIM, CHRISTIAN, etc. | Population by religion |
| REGION | Geographic region name |
| SOURCE_IMAGE | Source image filename |

### Election Output

| Column | Description |
|--------|-------------|
| POLLING_STATION | Station identifier |
| REGISTERED_VOTERS | Number of registered voters |
| VOTES_CAST | Total votes cast |
| VALID_VOTES | Valid votes counted |
| REJECTED_VOTES | Rejected ballots |
| SOURCE_IMAGE | Source image filename |

## Common Patterns

### Multi-level Headers

If your PDFs have multi-level headers:

```
                 RELIGION
         MUSLIM    CHRISTIAN    HINDU
MALE     1000      100          50
FEMALE   900       90           45
```

You may need to:
1. Manually inspect OCR output
2. Adjust keywords to skip header rows
3. Create custom column mappings

### Merged Cells

Tables with merged cells can be tricky:
- OCR may not preserve structure
- Consider manual intervention for complex tables
- Use generic parsing and post-process

### Footnotes and Annotations

To filter out footnotes:

```yaml
parsing:
  filters:
    - "Note:"
    - "Source:"
    - "*"
    - "Provisional"
```

## Testing Your Configuration

1. Start with a small sample (1-2 PDFs)
2. Use `--verbose` to see debug output
3. Check the log file for parsing details
4. Adjust keywords and column mappings iteratively
5. Validate output against source PDFs

## Examples by Country/Region

### Pakistan Census
- See `examples/config_pakistan_census.yaml`
- Keywords: DISTRICT, TEHSIL, DIVISION
- 7-9 column religion data

### India Census
```yaml
parsing:
  keywords:
    census: ["STATE", "DISTRICT", "TAHSIL", "VILLAGE"]
```

### US Census
```yaml
parsing:
  keywords:
    census: ["COUNTY", "TRACT", "BLOCK GROUP"]
```

### UK Elections
```yaml
parsing:
  keywords:
    election: ["WARD", "POLLING DISTRICT", "CONSTITUENCY"]
```
