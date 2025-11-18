"""
PDF Data Extractor - Extract structured data from census and election PDFs

A comprehensive tool for extracting tabular data from image-based PDF files,
specifically optimized for census and election data formats.
"""

__version__ = "1.0.0"
__author__ = "Wali Reheman"
__email__ = "rw8143a@american.edu"

from .downloader import PDFDownloader
from .converter import PDFConverter
from .ocr_engine import OCREngine
from .parser import DataParser
from .exporter import DataExporter
from .config import Config

__all__ = [
    "PDFDownloader",
    "PDFConverter",
    "OCREngine",
    "DataParser",
    "DataExporter",
    "Config",
]
