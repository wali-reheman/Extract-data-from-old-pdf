#!/usr/bin/env python3
"""Command-line interface for PDF data extraction"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from .config import Config
from .downloader import PDFDownloader
from .converter import PDFConverter
from .ocr_engine import OCREngine
from .parser import DataParser
from .exporter import DataExporter
from .utils import setup_logging, validate_tesseract, validate_config, print_summary, ensure_directories


logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Extract structured data from census and election PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline: download, convert, extract, export
  %(prog)s --download --config config.yaml

  # Process existing PDFs
  %(prog)s --input ./pdfs/*.pdf --output results.xlsx

  # Use local images (skip download and conversion)
  %(prog)s --images ./images/*.jpg --format csv

  # Generate example configuration
  %(prog)s --init-config my_config.yaml

For more information, visit: https://github.com/wali-reheman/Extract-data-from-old-pdf
        """
    )

    # Configuration
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to YAML configuration file"
    )

    parser.add_argument(
        "--init-config",
        type=str,
        metavar="PATH",
        help="Generate example configuration file at specified path"
    )

    # Input sources
    input_group = parser.add_mutually_exclusive_group()

    input_group.add_argument(
        "--download",
        action="store_true",
        help="Download PDFs from URL pattern specified in config"
    )

    input_group.add_argument(
        "--input", "-i",
        type=str,
        nargs="+",
        metavar="PDF",
        help="Input PDF files or glob patterns (e.g., ./pdfs/*.pdf)"
    )

    input_group.add_argument(
        "--images",
        type=str,
        nargs="+",
        metavar="IMAGE",
        help="Process existing images directly (skip PDF conversion)"
    )

    # Output
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (format inferred from extension)"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["excel", "csv", "json"],
        help="Output format (overrides config)"
    )

    # Processing options
    parser.add_argument(
        "--data-format",
        choices=["census", "election", "generic"],
        help="Data format type (overrides config)"
    )

    parser.add_argument(
        "--skip-conversion",
        action="store_true",
        help="Skip PDF to image conversion (use existing images)"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean temporary files after processing"
    )

    # Logging
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress console output (log to file only)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    return parser


def init_config(config_path: str):
    """Generate example configuration file

    Args:
        config_path: Path to save configuration
    """
    config = Config()
    config.save(config_path)
    print(f"Configuration file created: {config_path}")
    print("\nEdit this file to customize your extraction settings.")
    sys.exit(0)


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Handle init-config
    if args.init_config:
        init_config(args.init_config)

    # Load configuration
    config = Config(args.config)

    # Override config with CLI arguments
    if args.verbose:
        config.set("logging", "level", value="DEBUG")

    if args.quiet:
        config.set("logging", "console", value=False)

    if args.format:
        config.set("export", "format", value=args.format)

    if args.data_format:
        config.set("parsing", "data_format", value=args.data_format)

    if args.output:
        config.set("export", "output_dir", value=str(Path(args.output).parent))
        config.set("export", "output_filename", value=Path(args.output).stem)

    # Setup logging
    setup_logging(config)
    logger.info("PDF Data Extractor started")

    try:
        # Validate environment
        validate_tesseract()
        validate_config(config)
        ensure_directories(config)

        # Initialize components
        downloader = PDFDownloader(config)
        converter = PDFConverter(config)
        ocr_engine = OCREngine(config)
        parser_obj = DataParser(config)
        exporter = DataExporter(config)

        pdf_files = []
        image_files = []

        # Step 1: Get PDFs
        if args.download:
            logger.info("Downloading PDFs from configured source")
            pdf_files = downloader.download_from_url_pattern()

        elif args.input:
            logger.info(f"Processing input PDFs: {args.input}")
            from glob import glob
            for pattern in args.input:
                pdf_files.extend(glob(pattern))
            pdf_files = downloader.download_local_files(pdf_files)

        elif args.images:
            logger.info(f"Processing input images: {args.images}")
            from glob import glob
            for pattern in args.images:
                image_files.extend(glob(pattern))

        else:
            # No input specified, try to find existing files
            logger.info("No input specified, checking for existing files")
            pdf_files = downloader.get_downloaded_files()

            if not pdf_files:
                image_files = converter.get_converted_images()

                if not image_files:
                    logger.error("No input files found. Use --download, --input, or --images")
                    sys.exit(1)

        # Step 2: Convert PDFs to images
        if pdf_files and not args.skip_conversion:
            logger.info(f"Converting {len(pdf_files)} PDFs to images")
            conversion_results = converter.convert_pdfs(pdf_files)

            for pdf, images in conversion_results.items():
                image_files.extend(images)

        elif args.skip_conversion:
            logger.info("Skipping PDF conversion (using existing images)")
            image_files = converter.get_converted_images()

        if not image_files:
            logger.error("No images to process")
            sys.exit(1)

        # Step 3: Perform OCR
        logger.info(f"Performing OCR on {len(image_files)} images")
        ocr_results = ocr_engine.process_images(image_files)

        # Step 4: Parse data
        logger.info("Parsing extracted text into structured data")
        data = parser_obj.parse_ocr_results(ocr_results)

        if data.empty:
            logger.warning("No data extracted")
            sys.exit(1)

        # Step 5: Export data
        logger.info("Exporting data")
        output_path = exporter.export(data, args.output)

        # Step 6: Summary
        stats = exporter.get_summary_stats(data)
        stats["output_file"] = output_path
        stats["images_processed"] = len(image_files)

        if pdf_files:
            stats["pdfs_processed"] = len(pdf_files)

        print_summary(stats)

        # Step 7: Cleanup
        if args.clean:
            logger.info("Cleaning temporary files")
            converter.clean_output_dir()

        logger.info("Extraction complete!")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
