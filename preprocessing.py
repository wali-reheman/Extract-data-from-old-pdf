#!/usr/bin/env python3
"""
Image preprocessing for scanned/poorly structured PDFs.

Applies transforms before OCR to maximize text recognition accuracy:
- Deskew: detect and correct page rotation
- Dewarp: correct barrel/pin cushion distortion from book scans
- Adaptive binarization: Otsu and adaptive threshold methods
- Border removal: crop scanner artifacts
- Line removal: eliminate table grid lines
- Denoise: gaussian blur for grainy scans
- Contrast enhancement: CLAHE for faded text

All transforms are PIL/numpy based — no heavy dependencies.
"""

import cv2
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class PreprocessConfig:
    deskew: bool = True
    dewarp: bool = False          # Book curvature correction (slow, off by default)
    binarize: str = "adaptive"   # "otsu" | "adaptive" | "none"
    border_removal: bool = True
    line_removal: bool = True
    denoise: bool = True
    clahe: bool = True           # Contrast Limited Adaptive Histogram Equalization
    resize_factor: float = 1.5   # Scale up before OCR for better accuracy
    dpi: int = 300               # Target DPI for conversion


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv2_img: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB))


def estimate_skew(img: np.ndarray) -> float:
    """
    Estimate skew angle using Hough line transform.
    Returns angle in degrees.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
    if lines is None:
        return 0.0

    angles = []
    for line in lines:
        rho, theta = line[0]
        angle = np.degrees(theta) - 90
        if -45 < angle < 45:
            angles.append(angle)

    if not angles:
        return 0.0

    # Median angle — robust to outliers
    return float(np.median(angles))


def deskew(img: np.ndarray, angle: Optional[float] = None) -> np.ndarray:
    """Rotate image to correct skew."""
    if angle is None:
        angle = estimate_skew(img)

    if abs(angle) < 0.3:  # Skip tiny angles
        return img

    h, w = img.shape[:2]
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Expand canvas to avoid clipping
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2

    return cv2.warpAffine(img, M, (new_w, new_h),
                           flags=cv2.INTER_CUBIC,
                           borderValue=(255, 255, 255))


def remove_borders(img: np.ndarray, thresh_val: int = 240) -> np.ndarray:
    """
    Detect and crop solid-color borders (scanner artifacts).
    Looks for large rectangular regions of near-white pixels.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)

    # Find largest white rectangle
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return img

    # Get the bounding rect of the largest white region (likely border)
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    # Only crop if border is substantial (>5% of image dimension)
    img_h, img_w = img.shape[:2]
    if w > img_w * 0.95 and h > img_h * 0.95:
        return img  # No significant border found

    # Crop with small padding
    pad = 3
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(img_w, x + w + pad)
    y2 = min(img_h, y + h + pad)

    return img[y1:y2, x1:x2]


def remove_lines(img: np.ndarray) -> np.ndarray:
    """
    Detect horizontal and vertical lines (table grids) and inpaint them.
    Helps OCR parse table cells correctly.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # Morphological operations to isolate lines
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 30))

    # Detect horizontal lines
    extracted_h = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel_h)
    _, thresh_h = cv2.threshold(extracted_h, 30, 255, cv2.THRESH_BINARY)

    # Detect vertical lines
    extracted_v = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel_v)
    _, thresh_v = cv2.threshold(extracted_v, 30, 255, cv2.THRESH_BINARY)

    # Combine
    lines = cv2.add(thresh_h, thresh_v)

    # Dilate slightly to connect broken line segments
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    lines = cv2.dilate(lines, kernel_dilate, iterations=1)

    # Inpaint: fill lines with surrounding color (TEBCEA inpainting)
    if lines.sum() > 0:
        mask = (lines > 0).astype(np.uint8) * 255
        img_clean = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
        return img_clean

    return img


def binarize_otsu(img: np.ndarray) -> np.ndarray:
    """Classic Otsu global threshold binarization."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def binarize_adaptive(img: np.ndarray, block_size: int = 15, c: int = 2) -> np.ndarray:
    """Adaptive local threshold — better for uneven illumination (faded pages)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, block_size, c)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def apply_clahe(img: np.ndarray, clip_limit: float = 2.0, tile_grid: int = 8) -> np.ndarray:
    """CLAHE — improves contrast on faded or low-contrast scanned text."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid, tile_grid))
    enhanced = clahe.apply(gray)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)


def denoise(img: np.ndarray, strength: int = 3) -> np.ndarray:
    """Gaussian blur to reduce scanner noise."""
    return cv2.GaussianBlur(img, (strength * 2 + 1, strength * 2 + 1), 0)


def resize_for_ocr(img: np.ndarray, factor: float = 1.5) -> np.ndarray:
    """Scale up image for better OCR accuracy on small text."""
    if factor <= 1.0:
        return img
    h, w = img.shape[:2]
    new_w = int(w * factor)
    new_h = int(h * factor)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)


def preprocess_image(img: Image.Image, config: Optional[PreprocessConfig] = None) -> Image.Image:
    """
    Apply full preprocessing pipeline to a PIL Image.

    Args:
        img: Input PIL Image
        config: Preprocessing configuration (uses defaults if None)

    Returns:
        Preprocessed PIL Image ready for OCR
    """
    if config is None:
        config = PreprocessConfig()

    img_cv = pil_to_cv2(img)

    # Step 1: Border removal (before deskew — clean edges help)
    if config.border_removal:
        img_cv = remove_borders(img_cv)

    # Step 2: Deskew
    if config.deskew:
        img_cv = deskew(img_cv)

    # Step 3: Denoise
    if config.denoise:
        img_cv = denoise(img_cv)

    # Step 4: CLAHE contrast enhancement (on grayscale — before binarization)
    if config.clahe:
        img_cv = apply_clahe(img_cv)

    # Step 5: Binarization
    if config.binarize == "otsu":
        img_cv = binarize_otsu(img_cv)
    elif config.binarize == "adaptive":
        img_cv = binarize_adaptive(img_cv)
    # "none" → keep grayscale

    # Step 6: Line removal (after binarization works best)
    if config.line_removal:
        img_cv = remove_lines(img_cv)

    # Step 7: Resize for OCR
    img_cv = resize_for_ocr(img_cv, config.resize_factor)

    return cv2_to_pil(img_cv)


def preprocess_pdf_pages(pdf_path: str, dpi: int = 300,
                         config: Optional[PreprocessConfig] = None,
                         output_dir: Optional[str] = None) -> list[Image.Image]:
    """
    Convert PDF pages to preprocessed images.

    Args:
        pdf_path: Path to PDF file
        dpi: DPI for PDF to image conversion
        config: Preprocessing configuration
        output_dir: Optional directory to save preprocessed images

    Returns:
        List of preprocessed PIL Images (one per page)
    """
    from pdf2image import convert_from_path

    if config is None:
        config = PreprocessConfig()
    else:
        # Override DPI in config
        config = PreprocessConfig(
            deskew=config.deskew,
            dewarp=config.dewarp,
            binarize=config.binarize,
            border_removal=config.border_removal,
            line_removal=config.line_removal,
            denoise=config.denoise,
            clahe=config.clahe,
            resize_factor=config.resize_factor,
            dpi=dpi,
        )

    raw_images = convert_from_path(pdf_path, dpi=dpi)
    processed = [preprocess_image(img, config) for img in raw_images]

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        for i, img in enumerate(processed, 1):
            img.save(output_path / f"page_{i:03d}.png")

    return processed


def diagnose_image(img: Image.Image) -> dict:
    """
    Analyze a scanned image and return quality diagnostics.
    Useful for determining which preprocessing path to use.
    """
    img_cv = pil_to_cv2(img)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv

    stats = {
        "width": img.width,
        "height": img.height,
        "aspect_ratio": round(img.width / img.height, 2),
        "mean_brightness": round(float(gray.mean()), 1),
        "std_brightness": round(float(gray.std()), 1),
        "estimated_skew": round(estimate_skew(img_cv), 2),
        "has_borders": False,  # computed below
    }

    # Check for dark borders
    border_pixels = 0
    border_size = max(1, min(img.width, img.height) // 20)
    for x in range(border_size):
        border_pixels += (gray[:, x] < 128).sum()
        border_pixels += (gray[:, -(x+1)] < 128).sum()
        border_pixels += (gray[x, :] < 128).sum()
        border_pixels += (gray[-(x+1), :] < 128).sum()

    total_border = 4 * border_size * max(img.width, img.height)
    stats["has_borders"] = border_pixels / max(total_border, 1) > 0.1

    # Check for low contrast (faded page)
    stats["is_faded"] = stats["std_brightness"] < 30

    # Check for heavy noise
    stats["is_noisy"] = stats["std_brightness"] > 80

    return stats
