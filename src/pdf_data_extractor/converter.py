"""Convert PDF files to images for OCR processing"""

import os
import logging
from pathlib import Path
from typing import List, Dict
from pdf2image import convert_from_path
from tqdm import tqdm
from .config import Config


logger = logging.getLogger(__name__)


class PDFConverter:
    """Convert PDF files to images"""

    def __init__(self, config: Config):
        """Initialize PDF converter

        Args:
            config: Configuration object
        """
        self.config = config
        self.output_dir = Path(config.get("conversion", "output_dir", default="./images"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_format = config.get("conversion", "image_format", default="JPEG")
        self.dpi = config.get("conversion", "dpi", default=300)

    def convert_pdfs(self, pdf_paths: List[str]) -> Dict[str, List[str]]:
        """Convert multiple PDF files to images

        Args:
            pdf_paths: List of PDF file paths to convert

        Returns:
            Dictionary mapping PDF path to list of image paths
        """
        results = {}

        logger.info(f"Converting {len(pdf_paths)} PDF files to images")

        for pdf_path in tqdm(pdf_paths, desc="Converting PDFs"):
            try:
                image_paths = self.convert_pdf(pdf_path)
                results[pdf_path] = image_paths
                logger.debug(f"Converted {pdf_path}: {len(image_paths)} pages")

            except Exception as e:
                logger.error(f"Error converting {pdf_path}: {e}")
                results[pdf_path] = []

        total_images = sum(len(imgs) for imgs in results.values())
        logger.info(f"Conversion complete: {total_images} images from {len(pdf_paths)} PDFs")

        return results

    def convert_pdf(self, pdf_path: str) -> List[str]:
        """Convert a single PDF file to images

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of paths to generated images
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"Not a PDF file: {pdf_path}")

        try:
            # Convert PDF to images
            images = convert_from_path(
                str(pdf_path),
                dpi=self.dpi,
                fmt=self.image_format.lower()
            )

            image_paths = []
            base_name = pdf_path.stem

            for i, image in enumerate(images):
                # Create output filename: original_name_page_0.jpg
                image_filename = f"{base_name}_page_{i}.{self.image_format.lower()}"
                image_path = self.output_dir / image_filename

                # Save image
                image.save(str(image_path), self.image_format)
                image_paths.append(str(image_path))

            return image_paths

        except Exception as e:
            logger.error(f"Failed to convert {pdf_path}: {e}")
            raise

    def get_converted_images(self) -> List[str]:
        """Get list of already converted image files

        Returns:
            List of image file paths in output directory
        """
        format_lower = self.image_format.lower()
        extensions = [f"*.{format_lower}", f"*.{format_lower.upper()}"]

        image_files = []
        for ext in extensions:
            image_files.extend(self.output_dir.glob(ext))

        return [str(f) for f in sorted(image_files)]

    def clean_output_dir(self):
        """Remove all images from output directory"""
        images = self.get_converted_images()

        logger.info(f"Cleaning {len(images)} images from {self.output_dir}")

        for image_path in images:
            try:
                Path(image_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete {image_path}: {e}")

        logger.info("Cleanup complete")
