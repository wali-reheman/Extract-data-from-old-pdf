"""Utility functions for PDF data extraction"""

import logging
import sys
from pathlib import Path
from typing import Optional
from .config import Config


def setup_logging(config: Config) -> logging.Logger:
    """Setup logging configuration

    Args:
        config: Configuration object

    Returns:
        Configured logger
    """
    log_level = config.get("logging", "level", default="INFO")
    log_file = config.get("logging", "file", default="pdf_extractor.log")
    console = config.get("logging", "console", default=True)

    # Convert string level to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    level = level_map.get(log_level.upper(), logging.INFO)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def validate_tesseract():
    """Validate that Tesseract is installed and accessible

    Raises:
        RuntimeError: If Tesseract is not found
    """
    import pytesseract

    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR is not installed or not in PATH. "
            "Please install Tesseract:\n"
            "  - Ubuntu/Debian: sudo apt-get install tesseract-ocr\n"
            "  - macOS: brew install tesseract\n"
            "  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
        )


def validate_config(config: Config) -> bool:
    """Validate configuration

    Args:
        config: Configuration to validate

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    # Check download config
    base_url = config.get("download", "base_url")
    if not base_url:
        raise ValueError("download.base_url is required")

    # Check data format
    data_format = config.get("parsing", "data_format")
    if data_format not in ["census", "election", "generic"]:
        raise ValueError(f"Invalid data_format: {data_format}")

    # Check export format
    export_format = config.get("export", "format")
    if export_format not in ["excel", "csv", "json"]:
        raise ValueError(f"Invalid export format: {export_format}")

    return True


def print_summary(stats: dict):
    """Print extraction summary statistics

    Args:
        stats: Statistics dictionary
    """
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"\n{key.upper()}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")

    print("=" * 60 + "\n")


def ensure_directories(config: Config):
    """Ensure all required directories exist

    Args:
        config: Configuration object
    """
    directories = [
        config.get("download", "output_dir"),
        config.get("conversion", "output_dir"),
        config.get("export", "output_dir"),
    ]

    for directory in directories:
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)
