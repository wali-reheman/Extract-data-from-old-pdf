################################################################################
# Example Usage of PDF Census Data Extractor in R
################################################################################
#
# This file demonstrates different ways to use the R interface for extracting
# census data from PDFs.
#
################################################################################

# Load the extraction functions
source("process_census_pdf.R")

# Example 1: Extract data from a single PDF
# ==========================================
cat("\n=== EXAMPLE 1: Single PDF Extraction ===\n")

result <- extract_census_pdf(
  pdf_path = "example pdf.pdf",
  output_path = "census_data_R.xlsx",
  extract_all = TRUE,
  verbose = TRUE
)

cat("Output file:", result, "\n")


# Example 2: Read and analyze the extracted data
# ===============================================
cat("\n=== EXAMPLE 2: Analyze Extracted Data ===\n")

library(readxl)
library(dplyr)

# Read the extracted data
data <- read_excel("census_data_R.xlsx")

# Display structure
cat("\nData structure:\n")
str(data)

# Show first few rows
cat("\nFirst 10 rows:\n")
print(head(data, 10))

# Calculate summary statistics
cat("\nSummary by Region:\n")
summary_by_region <- data %>%
  filter(SEX == "ALL", SECTION == "OVERALL") %>%
  select(REGION, TOTAL, MUSLIM, CHRISTIAN, HINDU) %>%
  arrange(desc(TOTAL))

print(summary_by_region)

# Calculate percentages
cat("\nReligious composition (%):\n")
composition <- data %>%
  filter(SEX == "ALL", SECTION == "OVERALL") %>%
  mutate(
    Muslim_pct = round(MUSLIM / TOTAL * 100, 2),
    Christian_pct = round(CHRISTIAN / TOTAL * 100, 2),
    Hindu_pct = round(HINDU / TOTAL * 100, 2)
  ) %>%
  select(REGION, Muslim_pct, Christian_pct, Hindu_pct)

print(composition)


# Example 3: Batch process multiple PDFs
# =======================================
cat("\n=== EXAMPLE 3: Batch Processing (if you have multiple PDFs) ===\n")

# Uncomment to run batch processing
# results <- batch_process_pdfs(
#   input_dir = "./pdfs",
#   output_dir = "./output",
#   extract_all = TRUE
# )
# print(results)


# Example 4: Extract only summary data (not all sex categories)
# ==============================================================
cat("\n=== EXAMPLE 4: Extract Summary Only ===\n")

# Extract only summary rows (faster, smaller output)
summary_result <- extract_census_pdf(
  pdf_path = "example pdf.pdf",
  output_path = "census_summary_R.xlsx",
  extract_all = FALSE,  # Only summaries
  verbose = TRUE
)


# Example 5: Create visualizations
# =================================
cat("\n=== EXAMPLE 5: Create Visualizations ===\n")

library(ggplot2)

# Read data
data <- read_excel("census_data_R.xlsx")

# Plot 1: Population by region
plot_data <- data %>%
  filter(SEX == "ALL", SECTION == "OVERALL") %>%
  arrange(desc(TOTAL))

p1 <- ggplot(plot_data, aes(x = reorder(REGION, TOTAL), y = TOTAL)) +
  geom_bar(stat = "identity", fill = "steelblue") +
  coord_flip() +
  labs(
    title = "Total Population by Region",
    x = "Region",
    y = "Population"
  ) +
  theme_minimal()

ggsave("population_by_region.png", p1, width = 10, height = 6)
cat("Saved: population_by_region.png\n")

# Plot 2: Religious composition
religion_data <- data %>%
  filter(SEX == "ALL", SECTION == "OVERALL", REGION == "LOWER DIR DISTRICT") %>%
  select(MUSLIM, CHRISTIAN, HINDU, QADIANI_AHMADI, SCHEDULED_CASTES, OTHERS) %>%
  tidyr::pivot_longer(everything(), names_to = "Religion", values_to = "Population") %>%
  filter(!is.na(Population), Population > 0)

p2 <- ggplot(religion_data, aes(x = Religion, y = Population, fill = Religion)) +
  geom_bar(stat = "identity") +
  labs(
    title = "Religious Composition - Lower Dir District",
    x = "Religion",
    y = "Population"
  ) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

ggsave("religious_composition.png", p2, width = 10, height = 6)
cat("Saved: religious_composition.png\n")


cat("\n=== ALL EXAMPLES COMPLETE ===\n")
