#!/usr/bin/env Rscript
################################################################################
# PDF Census Data Extractor - R Interface
################################################################################
#
# This R script provides an easy interface to extract census data from
# multi-page PDFs using the pdf_data_extractor Python package.
#
# Usage:
#   Rscript process_census_pdf.R input.pdf output.xlsx
#
# Or from R:
#   source("process_census_pdf.R")
#   extract_census_pdf("input.pdf", "output.xlsx")
#
################################################################################

library(reticulate)
library(readxl)
library(writexl)
library(dplyr)
library(tidyr)
library(stringr)

#' Extract Census Data from PDF
#'
#' @param pdf_path Path to input PDF file
#' @param output_path Path for output Excel file
#' @param data_format Type of data: "census", "election", or "generic"
#' @param extract_all If TRUE, extracts all rows; if FALSE, only summaries
#' @param verbose If TRUE, prints detailed progress
#' @return Path to output file
extract_census_pdf <- function(pdf_path,
                                output_path = NULL,
                                data_format = "census",
                                extract_all = TRUE,
                                verbose = TRUE) {

  # Validate inputs
  if (!file.exists(pdf_path)) {
    stop("PDF file not found: ", pdf_path)
  }

  # Set default output path
  if (is.null(output_path)) {
    output_path <- paste0(tools::file_path_sans_ext(pdf_path), "_extracted.xlsx")
  }

  if (verbose) {
    cat("=" %s+% rep("=", 60) %s+% "\n")
    cat("PDF CENSUS DATA EXTRACTOR\n")
    cat("=" %s+% rep("=", 60) %s+% "\n")
    cat("Input PDF:  ", pdf_path, "\n")
    cat("Output Excel:", output_path, "\n")
    cat("Data format:", data_format, "\n")
    cat("Extract all:", extract_all, "\n")
    cat("=" %s+% rep("=", 60) %s+% "\n\n")
  }

  # Import Python modules
  if (verbose) cat("Loading Python modules...\n")

  tryCatch({
    pdf_extractor <- import("pdf_data_extractor")
  }, error = function(e) {
    stop("Failed to import pdf_data_extractor. Please ensure it's installed:\n",
         "  pip install -e /path/to/Extract-data-from-old-pdf")
  })

  # Create configuration
  if (verbose) cat("Creating configuration...\n")
  config <- pdf_extractor$Config()

  # Initialize components
  if (verbose) cat("Initializing extraction components...\n")
  converter <- pdf_extractor$PDFConverter(config)
  ocr_engine <- pdf_extractor$OCREngine(config)
  exporter <- pdf_extractor$DataExporter(config)

  # Step 1: Convert PDF to images
  if (verbose) cat("\n[1/4] Converting PDF to images...\n")
  conversion_results <- converter$convert_pdf(pdf_path)
  image_paths <- conversion_results

  if (verbose) {
    cat("  ✓ Converted", length(image_paths), "pages\n")
  }

  # Step 2: Perform OCR
  if (verbose) cat("\n[2/4] Performing OCR on images...\n")
  ocr_results <- ocr_engine$process_images(image_paths)

  total_lines <- sum(sapply(ocr_results, function(x) length(x$lines)))
  if (verbose) {
    cat("  ✓ Extracted", total_lines, "lines of text\n")
  }

  # Step 3: Parse data
  if (verbose) cat("\n[3/4] Parsing extracted text...\n")

  if (extract_all) {
    # Custom complete extraction
    parsed_data <- parse_census_complete_r(ocr_results, verbose = verbose)
  } else {
    # Use default parser
    parser <- pdf_extractor$DataParser(config)
    parsed_data_py <- parser$parse_ocr_results(ocr_results)
    parsed_data <- py_to_r(parsed_data_py)
  }

  if (verbose) {
    cat("  ✓ Parsed", nrow(parsed_data), "rows\n")
  }

  # Step 4: Clean and export data
  if (verbose) cat("\n[4/4] Cleaning and exporting data...\n")

  # Clean the data
  cleaned_data <- clean_census_data(parsed_data, verbose = verbose)

  # Export to Excel
  write_xlsx(cleaned_data, output_path)

  if (verbose) {
    cat("  ✓ Exported to:", output_path, "\n")
    cat("\n" %s+% "=" %s+% rep("=", 60) %s+% "\n")
    cat("EXTRACTION COMPLETE!\n")
    cat("=" %s+% rep("=", 60) %s+% "\n")
    cat("\nSummary:\n")
    cat("  Rows extracted:", nrow(cleaned_data), "\n")
    cat("  Columns:", ncol(cleaned_data), "\n")
    cat("  File size:", file.size(output_path), "bytes\n")
  }

  return(output_path)
}


#' Parse Census Data - Complete Extraction (R version)
#'
#' Extracts ALL data from OCR results including all sex categories and sections
#'
#' @param ocr_results List of OCR results from Python
#' @param verbose Print progress
#' @return Data frame with complete census data
parse_census_complete_r <- function(ocr_results, verbose = TRUE) {

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
          clean <- gsub("[Zz]", "2", clean)  # OCR corrections
          clean <- gsub("[Ss]", "5", clean)
          clean <- gsub("[Oo]", "0", clean)
          if (clean == "-") return(NA)
          if (grepl("^[0-9]+$", clean)) return(as.numeric(clean))
          return(NA)
        })

        numbers <- numbers[!is.na(numbers)]

        # Build row
        if (length(numbers) >= 7) {
          row_data <- list(
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
            SOURCE_IMAGE = img_name
          )
          all_data[[length(all_data) + 1]] <- row_data
        }
      }
    }
  }

  # Convert to data frame
  if (length(all_data) == 0) {
    warning("No data extracted!")
    return(data.frame())
  }

  df <- bind_rows(all_data)
  return(df)
}


#' Clean Census Data
#'
#' Performs data cleaning and validation
#'
#' @param data Raw extracted data
#' @param verbose Print cleaning steps
#' @return Cleaned data frame
clean_census_data <- function(data, verbose = TRUE) {

  if (verbose) cat("  - Removing duplicates...\n")
  data <- distinct(data)

  if (verbose) cat("  - Sorting by region and section...\n")
  if ("REGION" %in% names(data) && "SECTION" %in% names(data)) {
    data <- data %>%
      arrange(REGION,
              factor(SECTION, levels = c("OVERALL", "RURAL", "URBAN")),
              factor(SEX, levels = c("ALL", "MALE", "FEMALE", "TRANSGENDER")))
  }

  if (verbose) cat("  - Converting numeric columns...\n")
  numeric_cols <- c("TOTAL", "MUSLIM", "CHRISTIAN", "HINDU",
                    "QADIANI_AHMADI", "SCHEDULED_CASTES", "OTHERS")

  for (col in numeric_cols) {
    if (col %in% names(data)) {
      data[[col]] <- as.numeric(data[[col]])
    }
  }

  if (verbose) cat("  - Removing rows with all NA values...\n")
  data <- data %>%
    filter(!if_all(all_of(numeric_cols), is.na))

  return(data)
}


#' Batch Process Multiple PDFs
#'
#' Process multiple PDF files in a directory
#'
#' @param input_dir Directory containing PDF files
#' @param output_dir Directory for output Excel files
#' @param pattern File pattern to match (default: "\\.pdf$")
#' @param extract_all Extract all rows (TRUE) or summaries only (FALSE)
#' @return Data frame with processing results
batch_process_pdfs <- function(input_dir,
                                output_dir = NULL,
                                pattern = "\\.pdf$",
                                extract_all = TRUE) {

  # Set default output directory
  if (is.null(output_dir)) {
    output_dir <- file.path(input_dir, "extracted")
  }

  # Create output directory
  dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

  # Find PDF files
  pdf_files <- list.files(input_dir, pattern = pattern, full.names = TRUE)

  if (length(pdf_files) == 0) {
    stop("No PDF files found in: ", input_dir)
  }

  cat("Found", length(pdf_files), "PDF files to process\n\n")

  # Process each file
  results <- list()

  for (i in seq_along(pdf_files)) {
    pdf_file <- pdf_files[i]
    base_name <- tools::file_path_sans_ext(basename(pdf_file))
    output_file <- file.path(output_dir, paste0(base_name, "_extracted.xlsx"))

    cat("\n[", i, "/", length(pdf_files), "] Processing:", basename(pdf_file), "\n")
    cat(rep("-", 70), "\n")

    tryCatch({
      extract_census_pdf(pdf_file, output_file, extract_all = extract_all, verbose = TRUE)
      results[[i]] <- list(
        input = pdf_file,
        output = output_file,
        status = "SUCCESS"
      )
    }, error = function(e) {
      cat("ERROR:", e$message, "\n")
      results[[i]] <- list(
        input = pdf_file,
        output = NA,
        status = paste("ERROR:", e$message)
      )
    })
  }

  # Summary
  results_df <- bind_rows(results)

  cat("\n", rep("=", 70), "\n")
  cat("BATCH PROCESSING COMPLETE\n")
  cat(rep("=", 70), "\n")
  cat("Successful:", sum(results_df$status == "SUCCESS"), "/", nrow(results_df), "\n")
  cat("Failed:", sum(results_df$status != "SUCCESS"), "/", nrow(results_df), "\n")

  return(results_df)
}


#' Helper: String concatenation operator
`%s+%` <- function(x, y) paste0(x, y)


################################################################################
# Command Line Interface
################################################################################

if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)

  if (length(args) == 0) {
    cat("Usage: Rscript process_census_pdf.R <input.pdf> [output.xlsx]\n")
    cat("\nExample:\n")
    cat("  Rscript process_census_pdf.R example.pdf output.xlsx\n")
    cat("  Rscript process_census_pdf.R example.pdf\n")
    quit(status = 1)
  }

  input_pdf <- args[1]
  output_xlsx <- if (length(args) >= 2) args[2] else NULL

  # Run extraction
  result <- extract_census_pdf(input_pdf, output_xlsx, extract_all = TRUE, verbose = TRUE)

  cat("\nOutput saved to:", result, "\n")
}
