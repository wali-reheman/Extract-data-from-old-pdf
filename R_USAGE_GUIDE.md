# R Interface for PDF Census Data Extractor

This guide shows how to use the PDF data extractor from R.

## Quick Start

### 1. Prerequisites

Install R packages:

```r
install.packages(c("reticulate", "readxl", "writexl", "dplyr", "tidyr", "stringr"))
```

Ensure the Python package is installed:

```bash
pip install -e .
```

### 2. Basic Usage

#### Command Line

```bash
Rscript process_census_pdf.R input.pdf output.xlsx
```

#### From R Console

```r
source("process_census_pdf.R")

# Extract all data from PDF
extract_census_pdf(
  pdf_path = "example pdf.pdf",
  output_path = "output.xlsx",
  extract_all = TRUE
)
```

## Functions

### `extract_census_pdf()`

Main function to extract census data from a PDF file.

**Parameters:**
- `pdf_path` - Path to input PDF file (required)
- `output_path` - Path for output Excel file (optional, auto-generated if NULL)
- `data_format` - Type of data: "census", "election", or "generic" (default: "census")
- `extract_all` - If TRUE, extracts all rows; if FALSE, only summaries (default: TRUE)
- `verbose` - If TRUE, prints detailed progress (default: TRUE)

**Returns:** Path to output Excel file

**Example:**

```r
# Extract complete data
result <- extract_census_pdf("census.pdf", "output.xlsx", extract_all = TRUE)

# Extract summary only (faster)
result <- extract_census_pdf("census.pdf", "summary.xlsx", extract_all = FALSE)
```

---

### `batch_process_pdfs()`

Process multiple PDF files in a directory.

**Parameters:**
- `input_dir` - Directory containing PDF files (required)
- `output_dir` - Directory for output Excel files (optional, default: input_dir/extracted)
- `pattern` - File pattern to match (default: "\\.pdf$")
- `extract_all` - Extract all rows or summaries only (default: TRUE)

**Returns:** Data frame with processing results

**Example:**

```r
# Process all PDFs in a directory
results <- batch_process_pdfs(
  input_dir = "./census_pdfs",
  output_dir = "./extracted_data",
  extract_all = TRUE
)

# View results
print(results)
```

---

### `clean_census_data()`

Performs data cleaning and validation.

**Parameters:**
- `data` - Raw extracted data frame
- `verbose` - Print cleaning steps (default: TRUE)

**Returns:** Cleaned data frame

**Example:**

```r
# Manually clean data
raw_data <- read_excel("raw_extraction.xlsx")
clean_data <- clean_census_data(raw_data)
write_xlsx(clean_data, "cleaned_data.xlsx")
```

## Complete Workflow Example

```r
# Load libraries
library(readxl)
library(dplyr)
library(ggplot2)

# 1. Extract data from PDF
source("process_census_pdf.R")
extract_census_pdf("example pdf.pdf", "census_data.xlsx")

# 2. Read extracted data
data <- read_excel("census_data.xlsx")

# 3. Analyze data
summary_stats <- data %>%
  filter(SEX == "ALL", SECTION == "OVERALL") %>%
  group_by(REGION) %>%
  summarise(
    Total_Population = sum(TOTAL, na.rm = TRUE),
    Muslim_Pct = round(sum(MUSLIM, na.rm = TRUE) / Total_Population * 100, 2),
    Christian_Pct = round(sum(CHRISTIAN, na.rm = TRUE) / Total_Population * 100, 2)
  )

print(summary_stats)

# 4. Create visualization
ggplot(summary_stats, aes(x = reorder(REGION, Total_Population),
                          y = Total_Population)) +
  geom_bar(stat = "identity", fill = "steelblue") +
  coord_flip() +
  labs(title = "Population by Region", x = "Region", y = "Population") +
  theme_minimal()
```

## Data Structure

The extracted Excel file contains the following columns:

| Column | Description |
|--------|-------------|
| REGION | Geographic region (District or Sub-Division) |
| SECTION | Data section (OVERALL, RURAL, or URBAN) |
| SEX | Sex category (ALL, MALE, FEMALE, or TRANSGENDER) |
| TOTAL | Total population |
| MUSLIM | Muslim population |
| CHRISTIAN | Christian population |
| HINDU | Hindu population |
| QADIANI_AHMADI | Qadiani/Ahmadi population |
| SCHEDULED_CASTES | Scheduled Castes population |
| OTHERS | Other religions |
| SOURCE_IMAGE | Source image file (for tracking) |

## Common Analysis Tasks

### Filter by Section

```r
# Get only OVERALL data
overall_data <- data %>% filter(SECTION == "OVERALL")

# Get only RURAL data
rural_data <- data %>% filter(SECTION == "RURAL")

# Get only URBAN data
urban_data <- data %>% filter(SECTION == "URBAN")
```

### Filter by Sex Category

```r
# Get ALL SEXES data
total_data <- data %>% filter(SEX == "ALL")

# Get MALE data
male_data <- data %>% filter(SEX == "MALE")

# Get FEMALE data
female_data <- data %>% filter(SEX == "FEMALE")
```

### Calculate Percentages

```r
data_with_pct <- data %>%
  mutate(
    Muslim_Pct = round(MUSLIM / TOTAL * 100, 2),
    Christian_Pct = round(CHRISTIAN / TOTAL * 100, 2),
    Hindu_Pct = round(HINDU / TOTAL * 100, 2)
  )
```

### Aggregate by Region

```r
region_totals <- data %>%
  filter(SEX == "ALL", SECTION == "OVERALL") %>%
  group_by(REGION) %>%
  summarise(
    Total = sum(TOTAL, na.rm = TRUE),
    Muslim = sum(MUSLIM, na.rm = TRUE),
    Christian = sum(CHRISTIAN, na.rm = TRUE),
    Hindu = sum(HINDU, na.rm = TRUE)
  )
```

## Troubleshooting

### Python module not found

If you get "Failed to import pdf_data_extractor", ensure:

1. Python package is installed: `pip install -e .`
2. Reticulate is using correct Python: `reticulate::py_config()`

### Specify Python environment

```r
library(reticulate)
use_python("/usr/bin/python3")  # Adjust path as needed
source("process_census_pdf.R")
```

### Check Python configuration

```r
library(reticulate)
py_config()  # Shows which Python is being used
```

## Performance Tips

1. **Use `extract_all = FALSE` for summaries only** - Faster processing, smaller files
2. **Process PDFs in batches** - Use `batch_process_pdfs()` for multiple files
3. **Filter early** - Filter data before calculations to improve performance
4. **Cache results** - Save intermediate results to avoid re-processing

## Examples

See `example_r_usage.R` for complete working examples including:
- Single PDF extraction
- Data analysis and summarization
- Batch processing
- Data visualization
- Creating charts and reports

Run examples:

```bash
Rscript example_r_usage.R
```

## Support

For issues or questions:
- Check the main README.md
- Review docs/USAGE.md
- Review docs/DATA_FORMATS.md
- Contact: rw8143a@american.edu
