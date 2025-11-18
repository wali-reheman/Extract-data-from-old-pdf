"""OCR engine for extracting text from images"""

import logging
import cv2
import numpy as np
import pytesseract
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
from .config import Config


logger = logging.getLogger(__name__)


class OCREngine:
    """Extract text from images using OCR"""

    def __init__(self, config: Config):
        """Initialize OCR engine

        Args:
            config: Configuration object
        """
        self.config = config
        self.engine = config.get("ocr", "engine", default="tesseract")
        self.tesseract_config = config.get("ocr", "tesseract_config", default="--psm 6 --oem 1")

        # Preprocessing settings
        self.preprocess_config = config.get("ocr", "preprocessing", default={})
        self.grayscale = self.preprocess_config.get("grayscale", True)
        self.resize_factor = self.preprocess_config.get("resize_factor", 1.2)
        self.interpolation = self.preprocess_config.get("interpolation", "cubic")

    def process_images(self, image_paths: List[str]) -> Dict[str, Dict]:
        """Process multiple images with OCR

        Args:
            image_paths: List of image file paths

        Returns:
            Dictionary mapping image path to OCR results
        """
        results = {}

        logger.info(f"Processing {len(image_paths)} images with OCR")

        for image_path in tqdm(image_paths, desc="OCR Processing"):
            try:
                result = self.process_image(image_path)
                results[image_path] = result
                logger.debug(f"Processed {image_path}: {len(result['lines'])} lines extracted")

            except Exception as e:
                logger.error(f"Error processing {image_path}: {e}")
                results[image_path] = {"text": "", "lines": [], "error": str(e)}

        logger.info(f"OCR processing complete: {len(results)} images")
        return results

    def process_image(self, image_path: str) -> Dict:
        """Process a single image with OCR

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with extracted text and metadata
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Read and preprocess image
        image = self._preprocess_image(str(image_path))

        # Perform OCR
        if self.engine == "tesseract":
            text = self._ocr_tesseract(image)
        else:
            raise ValueError(f"Unsupported OCR engine: {self.engine}")

        # Process lines
        lines = text.strip().split("\n")
        lines = [line.strip() for line in lines if line.strip()]

        return {
            "text": text,
            "lines": lines,
            "image_path": str(image_path),
            "engine": self.engine,
        }

    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results

        Args:
            image_path: Path to image file

        Returns:
            Preprocessed image as numpy array
        """
        # Read image
        if self.grayscale:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        else:
            image = cv2.imread(image_path)

        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Resize for better OCR
        if self.resize_factor != 1.0:
            interpolation_map = {
                "nearest": cv2.INTER_NEAREST,
                "linear": cv2.INTER_LINEAR,
                "cubic": cv2.INTER_CUBIC,
                "area": cv2.INTER_AREA,
                "lanczos4": cv2.INTER_LANCZOS4,
            }

            interpolation = interpolation_map.get(
                self.interpolation.lower(),
                cv2.INTER_CUBIC
            )

            image = cv2.resize(
                image,
                None,
                fx=self.resize_factor,
                fy=self.resize_factor,
                interpolation=interpolation
            )

        return image

    def _ocr_tesseract(self, image: np.ndarray) -> str:
        """Perform OCR using Tesseract

        Args:
            image: Preprocessed image

        Returns:
            Extracted text
        """
        try:
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            return text

        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not found. Please install Tesseract-OCR.")
            raise

        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            raise

    def get_confidence(self, image: np.ndarray) -> Dict:
        """Get OCR confidence scores

        Args:
            image: Preprocessed image

        Returns:
            Dictionary with confidence information
        """
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            confidences = [int(conf) for conf in data['conf'] if conf != '-1']

            if confidences:
                return {
                    "mean": np.mean(confidences),
                    "min": np.min(confidences),
                    "max": np.max(confidences),
                    "std": np.std(confidences),
                }
            else:
                return {"mean": 0, "min": 0, "max": 0, "std": 0}

        except Exception as e:
            logger.warning(f"Failed to get confidence scores: {e}")
            return {"mean": 0, "min": 0, "max": 0, "std": 0}
