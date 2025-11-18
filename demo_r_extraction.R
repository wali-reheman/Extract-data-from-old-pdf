#!/usr/bin/env Rscript
################################################################################
# DEMO: PDF Census Data Extraction using R
################################################################################

cat("\n")
cat(rep("=", 70), "\n")
cat("PDF CENSUS DATA EXTRACTOR - R DEMO\n")
cat(rep("=", 70), "\n\n")

# Install required packages if needed
cat("[1/6] Installing R packages...\n")
if (!require("reticulate", quietly = TRUE)) {
  install.packages("reticulate", repos = "https://cloud.r-project.org", quiet = TRUE)
}
if (!require("writexl", quietly = TRUE)) {
  install.packages("writexl", repos = "https://cloud.r-project.org", quiet = TRUE)
}

library(reticulate)
library(writexl)

# Configure Python
cat("[2/6] Configuring Python environment...\n")
use_python("/usr/local/bin/python3", required = TRUE)

# Import Python package
cat("[3/6] Importing PDF extractor package...\n")
pdf_extractor <- import("pdf_data_extractor")

# Initialize components
cat("[4/6] Initializing extraction components...\n")
config <- pdf_extractor$Config()
converter <- pdf_extractor$PDFConverter(config)
ocr_engine <- pdf_extractor$OCREngine(config)

# Process the example PDF
cat("[5/6] Processing example PDF...\n")
pdf_file <- "example pdf.pdf"

# Convert PDF to images (if not already done)
if (!file.exists("images/example pdf_page_0.jpeg")) {
  cat("  - Converting PDF to images...\n")
  conversion_results <- converter$convert_pdf(pdf_file)
} else {
  cat("  - Using existing images...\n")
}

# Perform OCR
cat("  - Performing OCR...\n")
image_files <- list.files("images", pattern = "example pdf.*\\.jpeg$", full.names = TRUE)
ocr_results <- ocr_engine$process_images(image_files)

# Parse data - Complete extraction
cat("  - Parsing data (complete extraction)...\n")
all_data <- list()

for (img_name in names(ocr_results)) {
  result <- ocr_results[[img_name]]
  lines <- result$lines
  
  current_region <- NA
  current_section <- NA
  
  for (line in lines) {
    line <- trimws(line)
    
    # Detect region headers
    if (grepl("DISTRICT|SUB-DIVISION", line, ignore.case = TRUE)) {
      current_region <- line
      next
    }
    
    # Detect section headers
    if (line %in% c("OVERALL", "RURAL", "URBAN")) {
      current_section <- line
      next
    }
    
    # Parse data rows
    if (grepl("^(ALL SEXES|MALE|FEMALE|TRANSGENDER)", line)) {
      
      # Extract sex category
      if (startsWith(line, "ALL SEXES")) {
        sex <- "ALL"
        data_part <- sub("^ALL SEXES\\s+", "", line)
      } else if (startsWith(line, "TRANSGENDER")) {
        sex <- "TRANSGENDER"
        data_part <- sub("^TRANSGENDER\\s+", "", line)
      } else if (startsWith(line, "MALE")) {
        sex <- "MALE"
        data_part <- sub("^MALE\\s+", "", line)
      } else if (startsWith(line, "FEMALE")) {
        sex <- "FEMALE"
        data_part <- sub("^FEMALE\\s+", "", line)
      } else {
        next
      }
      
      # Extract numbers
      parts <- strsplit(data_part, "\\s+")[[1]]
      
      # Clean numbers
      numbers <- sapply(parts, function(x) {
        clean <- gsub(",", "", x)
        clean <- gsub("[Zz]", "2", clean)
        clean <- gsub("[Ss]", "5", clean)
        clean <- gsub("[Oo]", "0", clean)
        if (clean == "-") return(NA)
        if (grepl("^[0-9]+$", clean)) return(as.numeric(clean))
        return(NA)
      })
      
      numbers <- numbers[!is.na(numbers)]
      
      # Build row
      if (length(numbers) >= 7) {
        row_data <- data.frame(
          REGION = current_region,
          SECTION = current_section,
          SEX = sex,
          TOTAL = numbers[1],
          MUSLIM = numbers[2],
          CHRISTIAN = numbers[3],
          HINDU = numbers[4],
          QADIANI_AHMADI = numbers[5],
          SCHEDULED_CASTES = numbers[6],
          OTHERS = if(length(numbers) >= 7) numbers[7] else NA,
          stringsAsFactors = FALSE
        )
        all_data[[length(all_data) + 1]] <- row_data
      }
    }
  }
}

# Combine into data frame
census_data <- do.call(rbind, all_data)

# Export to Excel
cat("[6/6] Exporting to Excel...\n")
output_file <- "census_data_from_R.xlsx"
write_xlsx(census_data, output_file)

# Summary
cat("\n", rep("=", 70), "\n")
cat("EXTRACTION COMPLETE!\n")
cat(rep("=", 70), "\n")
cat("Rows extracted:", nrow(census_data), "\n")
cat("Columns:", ncol(census_data), "\n")
cat("Output file:", output_file, "\n")
cat("\nFirst 5 rows:\n")
print(head(census_data, 5))

cat("\n", rep("=", 70), "\n")
cat("SUCCESS! You can now open", output_file, "\n")
cat(rep("=", 70), "\n\n")
