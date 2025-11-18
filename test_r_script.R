#!/usr/bin/env Rscript
# Simple test of R interface

cat("Testing R interface for PDF extraction...\n\n")

# Test 1: Check R version
cat("[1/5] Checking R version...\n")
cat("  R version:", R.version.string, "\n\n")

# Test 2: Load reticulate
cat("[2/5] Loading reticulate package...\n")
if (!require("reticulate", quietly = TRUE)) {
  cat("  Installing reticulate...\n")
  install.packages("reticulate", repos = "https://cloud.r-project.org", quiet = TRUE)
  library(reticulate)
}
cat("  ✓ reticulate loaded\n\n")

# Test 3: Check Python
cat("[3/5] Checking Python...\n")
py_config()

# Test 4: Import Python package
cat("\n[4/5] Importing pdf_data_extractor...\n")
tryCatch({
  pdf_extractor <- import("pdf_data_extractor")
  cat("  ✓ Successfully imported pdf_data_extractor\n")
  cat("  Version:", pdf_extractor$`__version__`, "\n\n")
}, error = function(e) {
  cat("  ERROR:", e$message, "\n")
  quit(status = 1)
})

# Test 5: Run extraction
cat("[5/5] Running extraction test...\n")
config <- pdf_extractor$Config()
ocr <- pdf_extractor$OCREngine(config)

result <- ocr$process_image("images/example pdf_page_0.jpeg")
cat("  ✓ OCR processed successfully\n")
cat("  Lines extracted:", length(result$lines), "\n\n")

cat("=" %s% rep("=", 60) %s% "\n")
cat("ALL TESTS PASSED!\n")
cat("=" %s% rep("=", 60) %s% "\n")
cat("\nYou can now use process_census_pdf.R for full extraction.\n")

`%s%` <- function(x, y) paste0(x, y)
