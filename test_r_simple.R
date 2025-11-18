#!/usr/bin/env Rscript
# Simplified R test using system Python

cat("Testing R → Python interface...\n\n")

# Install and load reticulate
if (!require("reticulate", quietly = TRUE)) {
  install.packages("reticulate", repos = "https://cloud.r-project.org", quiet = TRUE)
}
library(reticulate)

# Use system Python (where our package is installed)
use_python("/usr/local/bin/python3", required = TRUE)

cat("Python configuration:\n")
py_config()

# Test import
cat("\nTesting import...\n")
pdf_extractor <- import("pdf_data_extractor")
cat("✓ Successfully imported!\n")
cat("Package version:", pdf_extractor$`__version__`, "\n")

# Test a simple function
cat("\nTesting Config...\n")
config <- pdf_extractor$Config()
cat("✓ Config created successfully!\n")

cat("\n=== R INTERFACE WORKS! ===\n")
