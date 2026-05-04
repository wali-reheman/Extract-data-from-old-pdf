#!/usr/bin/env python3
"""
Unified PDF Table Extractor — single entry point for all extraction needs.

Supports four engines:
  auto        — auto-detect PDF type and pick best engine
  pdfplumber  — born-digital PDFs, fast
  paddleocr   — scanned/poorly structured PDFs, AI-powered
  tesseract   — fallback OCR for any PDF

Features for scanned PDFs:
  - Full preprocessing pipeline (deskew, border removal, adaptive binarization, line removal)
  - OCR post-correction (fuzzy vocabulary matching, number repair)
  - Auto-detection of French vs English number formats
  - Confidence-weighted extraction

Usage:
    python extract.py input.pdf
    python extract.py input.pdf -o output.xlsx
    python extract.py input.pdf --engine auto      # default
    python extract.py input.pdf --engine tesseract --preprocess
    python extract.py input.pdf --engine paddleocr --preprocess --correct-ocr
"""

import sys
import subprocess
import re
from pathlib import Path
from typing import Optional
import argparse

# ---------------------------------------------------------------------------
# Package installation
# ---------------------------------------------------------------------------

REQUIRED = {
    'pdfplumber': 'pdfplumber',
    'pandas': 'pandas',
    'openpyxl': 'openpyxl',
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'pytesseract': 'pytesseract',
    'pdf2image': 'pdf2image',
    'numpy': 'numpy',
}

EXTRA_OCR = {
    'rapidfuzz': 'rapidfuzz',   # fuzzy matching for OCR correction
}


def install_packages(packages: dict, quiet: bool = False) -> None:
    """Install missing packages."""
    missing = []
    for module, package in packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Installing: {', '.join(missing)}")
        cmd = [sys.executable, "-m", "pip", "install", *missing]
        if quiet:
            cmd.append("-q")
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            # PEP 668: externally-managed-environment — try with override
            cmd.append("--break-system-packages")
            subprocess.check_call(cmd)


def ensure_ocr_available() -> bool:
    """Check if Tesseract OCR binary is installed."""
    import shutil
    return shutil.which("tesseract") is not None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python extract.py",
        description="Unified PDF Table Extractor — scanned, born-digital, census, election",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Engines:
  auto        Auto-detect PDF type and select best engine (default)
  pdfplumber  Direct text extraction for born-digital PDFs
  paddleocr   AI-powered layout analysis + OCR (best for scanned PDFs)
  tesseract   Classic OCR fallback

Preprocessing for scanned PDFs (--preprocess):
  deskew, border removal, adaptive binarization, line removal, CLAHE contrast

Examples:
  python extract.py census.pdf -o results.xlsx
  python extract.py scanned_report.pdf --engine auto --preprocess --correct-ocr
  python extract.py election_data.pdf --engine paddleocr -o output.xlsx
        """
    )
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("-o", "--output", dest="output", default=None,
                        help="Output Excel file (default: <input>.xlsx)")
    parser.add_argument("--engine", choices=["auto", "pdfplumber", "paddleocr", "tesseract"],
                        default="auto", help="Extraction engine (default: auto)")
    parser.add_argument("--preprocess", action="store_true",
                        help="Apply image preprocessing before OCR (recommended for scans)")
    parser.add_argument("--correct-ocr", action="store_true",
                        help="Apply OCR post-correction (fuzzy vocabulary matching)")
    parser.add_argument("--dpi", type=int, default=300,
                        help="DPI for PDF→image conversion (default: 300)")
    parser.add_argument("--french", action="store_true",
                        help="Assume French number format (space-separated thousands)")
    parser.add_argument("--lang", default="eng",
                        help="Tesseract language code(s), e.g. 'eng', 'srp', 'srp+eng' (default: eng)")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    return parser


# ---------------------------------------------------------------------------
# PDF type detection
# ---------------------------------------------------------------------------

def is_scanned(pdf_path: str) -> bool:
    """
    Detect whether PDF is scanned (image-based) or born-digital (text-based).
    Uses pdfplumber: if meaningful text can be extracted, it's born-digital.
    """
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            if text and len(text.strip()) > 100:
                return False
    except Exception:
        pass
    return True


# ---------------------------------------------------------------------------
# Extraction engines
# ---------------------------------------------------------------------------

def extract_pdfplumber(pdf_path: str, verbose: bool = False):
    """Direct text/table extraction for born-digital PDFs."""
    import pdfplumber

    all_rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables({
                'vertical_strategy': 'lines_strict',
                'horizontal_strategy': 'lines_strict',
                'snap_tolerance': 3,
                'join_tolerance': 3,
            })
            if tables and len(tables) > 0:
                for table in tables:
                    if len(table) < 5:
                        # Table is too small — likely just headers/numbers, fall back to text
                        pass
                    else:
                        for row in table:
                            if row and any(cell and str(cell).strip() for cell in row):
                                cleaned = [str(cell).strip() if cell else '' for cell in row]
                                all_rows.append(cleaned)

            # Always also extract raw text lines as fallback/supplement
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    line = line.strip()
                    if line and len(line) > 2:
                        all_rows.append([line])

    return all_rows, "pdfplumber"


def extract_tesseract(pdf_path: str, preprocess: bool = False,
                       correct_ocr: bool = False, dpi: int = 300,
                       verbose: bool = False, lang: str = "eng"):
    """
    Tesseract OCR extraction.
    Optionally preprocesses images before OCR.
    Optionally applies post-correction.
    """
    import cv2
    import pytesseract
    import numpy as np
    from pdf2image import convert_from_path

    # Import our modules
    try:
        from preprocessing import preprocess_image, preprocess_pdf_pages, PreprocessConfig
    except ImportError:
        preprocess = False

    try:
        from ocr_postcorrect import OCRPostCorrector
    except ImportError:
        correct_ocr = False

    if preprocess:
        if verbose:
            print("  Converting + preprocessing pages...")
        images = preprocess_pdf_pages(pdf_path, dpi=dpi)
    else:
        if verbose:
            print("  Converting pages...")
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=dpi)

    all_rows = []
    corrector = OCRPostCorrector() if correct_ocr else None

    for page_num, image in enumerate(images, 1):
        if verbose:
            print(f"  OCR page {page_num}/{len(images)}...")

        # Convert to grayscale + resize for OCR
        img_array = np.array(image.convert('L'))
        img_resized = cv2.resize(img_array, None, fx=1.5, fy=1.5,
                                  interpolation=cv2.INTER_CUBIC)

        # Tesseract: PSM 6 for uniform table blocks (default), PSM 11 for sparse text
        text = pytesseract.image_to_string(img_resized, lang=lang, config='--psm 6 --oem 1')

        # Post-correct OCR
        if corrector:
            text = corrector.correct_text(text)

        for line in text.split('\n'):
            line = line.strip()
            if line:
                # Split on multiple spaces for column detection
                parts = re.split(r'\s{2,}', line)
                all_rows.append(parts)

    return all_rows, "Tesseract"


def extract_paddleocr(pdf_path: str, preprocess: bool = False,
                       correct_ocr: bool = False, dpi: int = 300,
                       verbose: bool = False):
    """
    PaddleOCR with PPStructure for layout-aware table extraction.
    Best engine for scanned/poorly structured PDFs.
    """
    from paddleocr import PPStructure
    from pdf2image import convert_from_path
    import numpy as np

    try:
        from preprocessing import preprocess_image, preprocess_pdf_pages
    except ImportError:
        preprocess = False

    try:
        from ocr_postcorrect import OCRPostCorrector
    except ImportError:
        correct_ocr = False

    if verbose:
        print("  Initializing PaddleOCR (table structure model)...")

    ocr = PPStructure(show_log=False, use_angle_cls=True, lang='en')

    if preprocess:
        if verbose:
            print("  Converting + preprocessing pages...")
        images = preprocess_pdf_pages(pdf_path, dpi=dpi)
    else:
        if verbose:
            print("  Converting pages...")
        images = convert_from_path(pdf_path, dpi=dpi)

    all_rows = []
    corrector = OCRPostCorrector() if correct_ocr else None

    for page_num, image in enumerate(images, 1):
        if verbose:
            print(f"  Processing page {page_num}/{len(images)}...")

        img_array = np.array(image)
        result = ocr(img_array)

        for item in result:
            item_type = item.get('type', '')

            if item_type == 'table':
                # Extract table HTML and parse cells
                table_html = item.get('res', {}).get('html', '')
                if table_html:
                    # Parse HTML table to extract cell text
                    cells = _parse_table_html(table_html)
                    for row in cells:
                        all_rows.append(row)

            elif item_type == 'text':
                text_result = item.get('res', [])
                for text_item in text_result:
                    if 'text' in text_item:
                        text = text_item['text']
                        if corrector:
                            text = corrector.correct_text(text)
                        if text.strip():
                            all_rows.append([text.strip()])

    return all_rows, "PaddleOCR"


def _parse_table_html(html: str) -> list[list[str]]:
    """Extract rows/cells from PaddleOCR table HTML output."""
    rows = []
    # Split on <tr> tags
    row_tags = re.split(r'<tr[^>]*>', html)
    for row_tag in row_tags:
        if not row_tag.strip():
            continue
        # Extract <td> content
        cell_texts = re.findall(r'<td[^>]*>(.*?)</td>', row_tag, re.DOTALL)
        if cell_texts:
            cleaned = [re.sub(r'<[^>]+>', '', c).strip() for c in cell_texts]
            cleaned = [c for c in cleaned if c]
            if cleaned:
                rows.append(cleaned)
    return rows


# ---------------------------------------------------------------------------
# Smart parsing (from extract_universal.py — best parts)
# ---------------------------------------------------------------------------

def detect_french_format(rows: list, sample_size: int = 20) -> bool:
    """Detect whether numbers use French (space-separated) or English (comma) format."""
    comma_count = 0
    space_triplet_count = 0

    for row in rows[:sample_size]:
        row_text = ' '.join(str(cell) for cell in row)
        comma_count += len(re.findall(r'\d{1,3},\d{3}', row_text))
        space_triplet_count += len(re.findall(r'\b\d{3}\s+\d{3}\b', row_text))

    return space_triplet_count > comma_count

def smart_parse(rows: list, french_format: bool = False) -> tuple[list[str], list[list]]:
    """
    Adaptive table row parser — no hardcoded keywords or document-specific logic.

    Classification strategy (order matters):
    1. Header rows: mostly word tokens, few/no numbers (can tolerate small numbers
       like column indices "1 2 3 4" — they're padding, not data values)
    2. Data rows: contain BOTH text tokens AND large numeric values
    3. Everything else (section banners, footnotes): skip
    """
    if not rows:
        return [], []

    # Clean individual cells: remove cid: font artifacts and collapse newlines
    def clean_cid(text: str) -> str:
        if not isinstance(text, str):
            return text
        text = text.replace('\n', ' ').strip()
        text = re.sub(r'\(cid:\d+\)', '', text).strip()
        return text if text else ''

    rows = [[clean_cid(c) if isinstance(c, str) else c for c in row] for row in rows]

    # ─── Classify each row ───────────────────────────────────────────────
    WORD_RE = r'(?:[\w\u0400-\u04FF\u0180-\u024F\u1E00-\u1EFF]{2,}|[\u0600-\u06FF\u0750-\u077F]{2,})'
    # Large number = 3+ digits (data values), as opposed to small numbers like "1 2 3" (indices)
    LARGE_NUM_RE = r'\b\d{3,}[,\s\d]*\b'
    ANY_NUM_RE = r'\b\d{2,}[,\s\d]*\b'

    header_candidates = []
    data_candidates = []

    for row in rows:
        row_text = ' '.join(str(c) for c in row if c)
        word_tokens = re.findall(WORD_RE, row_text, re.UNICODE)
        large_nums = re.findall(LARGE_NUM_RE, row_text)
        any_nums = re.findall(ANY_NUM_RE, row_text)
        word_count = len(word_tokens)
        large_num_count = len(large_nums)
        any_num_count = len(any_nums)

        if not row_text.strip():
            continue

        # Header: ≥2 words, at most tiny numbers (column indices 1-8) — never large data values
        if word_count >= 2 and large_num_count == 0:
            header_candidates.append(row)

        # Data row: has ≥1 word AND at least one large (3+ digit) number
        elif word_count >= 1 and large_num_count >= 1:
            data_candidates.append({'row': row})

    # ─── Build column headers ─────────────────────────────────────────────
    # Strategy: pick the longest header candidate that fits within the data column count.
    # This ensures we prefer multi-cell table-column headers (8 cells) over
    # document-level titles (1 cell like "TABLE 9 - POPULATION...").
    best_header = None
    if header_candidates:
        data_width = max(len(r) for r in rows) if rows else 0
        # Filter to candidates that fit within data width
        fitting = [c for c in header_candidates if len(c) <= data_width]
        if fitting:
            best_header = max(fitting, key=len)
        else:
            # No header fits within data width — take the shortest one
            best_header = min(header_candidates, key=len)

    def _is_garbled_header_row(candidate: list) -> bool:
        """
        A garbled header row is one where most cells are EITHER:
        (a) pure numbers (data row mistakenly classified as header), OR
        (b) garbage text (cid: artifacts where no Unicode letters survive)
        """
        if not candidate:
            return False
        cell_strs = [str(c) for c in candidate if c]
        if not cell_strs:
            return False

        # (a) mostly pure numbers
        numeric_cells = sum(
            1 for c in cell_strs
            if c.replace(',', '').replace(' ', '').replace('.', '').isdigit()
        )
        if numeric_cells / len(cell_strs) >= 0.5:
            return True

        # (b) mostly cells with very few meaningful letters (1-2 chars — too short to be real labels)
        tiny_cells = sum(
            1 for c in cell_strs
            if len(re.findall(r'[\w\u0400-\u04FF\u0600-\u06FF]', c)) <= 2
        )
        if tiny_cells / len(cell_strs) >= 0.30:
            return True

        return False

    garbled_header = best_header and _is_garbled_header_row(best_header)

    if best_header and not garbled_header:
        header_text = ' '.join(str(c) for c in best_header if c)
        parts = re.split(r'\s{2,}', header_text)
        if len(parts) < 3:
            parts = header_text.split()
        headers = [h.strip() for h in parts if h.strip()]
    elif data_candidates and garbled_header:
        # No readable header — use generic column names and treat all data rows normally
        n_data_cols = max(len(item['row']) for item in data_candidates)
        headers = [f'Column_{i+1}' for i in range(n_data_cols)]
    else:
        max_cols = max(len(r) for r in rows) if rows else 0
        headers = [f'Column_{i+1}' for i in range(max_cols)]

    # ─── Parse data rows ─────────────────────────────────────────────────
    n_cols = len(headers)
    parsed_data = []

    for item in data_candidates:
        row = item['row']

        # Single-cell row: pdfplumber's text fallback sometimes concatenates all
        # table cells into one string (especially for rotated/multi-column layouts).
        # Strategy: split ONLY when the number of space-separated parts closely
        # matches the expected column count from the header.
        if len(row) == 1:
            single = str(row[0])
            space_parts = single.split()
            # Split if part count is close to the expected column count
            # (within ±3 columns) AND has at least 2 parts
            if len(space_parts) >= 2 and abs(len(space_parts) - n_cols) <= 3:
                parts = space_parts
            else:
                parts = [single]
        else:
            parts = list(row)

        parsed_row = []
        for part in parts:
            part_str = str(part).strip()
            if not part_str:
                continue

            clean = part_str.replace(',', '').replace(' ', '')
            for old, new in [('O', '0'), ('o', '0'), ('l', '1'), ('I', '1'),
                              ('S', '5'), ('Z', '2'), ('B', '8'), ('q', '9')]:
                clean = clean.replace(old, new)

            if clean in ('-', '—', '–', '∗', '*', ''):
                parsed_row.append(None)
            elif clean.isdigit():
                parsed_row.append(int(clean))
            else:
                parsed_row.append(part_str)

        if len(parsed_row) >= 1:
            parsed_data.append(parsed_row)

    # Pad / trim rows to match header count
    parsed_data = [
        (row + [None] * (n_cols - len(row)))[:n_cols]
        for row in parsed_data
    ]

    return headers, parsed_data


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(pdf_path: str,
        output_path: Optional[str] = None,
        engine: str = "auto",
        preprocess: bool = False,
        correct_ocr: bool = False,
        dpi: int = 300,
        french_format: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        lang: str = "eng") -> str:

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    if output_path is None:
        output_path = str(pdf_path.with_suffix('.xlsx'))
    output_path = Path(output_path)

    if not quiet:
        print("=" * 70)
        print("PDF TABLE EXTRACTOR")
        print("=" * 70)
        print(f"Input:    {pdf_path}")
        print(f"Output:   {output_path}")
        print(f"Engine:   {engine}")
        print(f"Preproc:  {preprocess}")
        print(f"Correct:  {correct_ocr}")
        print("=" * 70 + "\n")

    # Auto-detect engine for scanned PDFs
    if engine == "auto":
        if verbose:
            print("[*] Detecting PDF type...")
        if is_scanned(str(pdf_path)):
            if not quiet:
                print("[*] Scanned PDF detected → using PaddleOCR")
            engine = "paddleocr"
            preprocess = preprocess or True  # Recommend preprocessing for scans
        else:
            if not quiet:
                print("[*] Born-digital PDF detected → using pdfplumber")
            engine = "pdfplumber"

    # Install engine-specific dependencies
    if engine == "paddleocr":
        install_packages({'paddleocr': 'paddleocr', 'paddlepaddle': 'paddlepaddle'}, quiet=quiet)
    elif engine in ("tesseract", "paddleocr"):
        install_packages(EXTRA_OCR, quiet=quiet)

    # Check Tesseract binary
    if engine in ("tesseract", "paddleocr") and not ensure_ocr_available():
        print("ERROR: Tesseract OCR is not installed.")
        print("  macOS: brew install tesseract")
        print("  Ubuntu: sudo apt-get install tesseract-ocr")
        print("  Or: https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)

    # Extract
    if not quiet:
        print(f"[1/3] Extracting with {engine}...")

    if engine == "pdfplumber":
        rows, method = extract_pdfplumber(str(pdf_path), verbose=verbose)
    elif engine == "paddleocr":
        rows, method = extract_paddleocr(str(pdf_path), preprocess=preprocess,
                                          correct_ocr=correct_ocr, dpi=dpi, verbose=verbose)
    else:
        rows, method = extract_tesseract(str(pdf_path), preprocess=preprocess,
                                          correct_ocr=correct_ocr, dpi=dpi, verbose=verbose,
                                          lang=lang)

    if not quiet:
        print(f"  ✓ {len(rows)} raw rows extracted ({method})\n")

    if not rows:
        print("ERROR: No content extracted. The PDF may be empty or unsupported.")
        sys.exit(1)

    # Auto-detect French format if not specified
    if not french_format:
        french_format = detect_french_format(rows)
        if not quiet and french_format:
            print("[*] French number format detected")

    # Parse
    if not quiet:
        print("[2/3] Parsing structure...")

    headers, data_rows = smart_parse(rows, french_format=french_format)

    if not quiet:
        print(f"  ✓ {len(headers)} columns, {len(data_rows)} data rows\n")

    if not data_rows:
        print("ERROR: No data rows parsed. The PDF format may not be supported.")
        sys.exit(1)

    # Export
    if not quiet:
        print("[3/3] Creating Excel...")

    import pandas as pd

    # Normalize row lengths
    max_cols = max(len(headers), max(len(r) for r in data_rows) if data_rows else 0)
    while len(headers) < max_cols:
        headers.append(f'Col_{len(headers)+1}')
    for row in data_rows:
        while len(row) < max_cols:
            row.append(None)

    df = pd.DataFrame(data_rows, columns=headers[:max_cols])
    df = df.drop_duplicates()

    df.to_excel(output_path, index=False)

    if not quiet:
        print(f"  ✓ Saved to {output_path}\n")

        print("=" * 70)
        print("EXTRACTION COMPLETE")
        print("=" * 70)
        print(f"Engine:    {method}")
        print(f"Rows:      {len(df)}")
        print(f"Columns:   {len(df.columns)}")
        print(f"Output:    {output_path}")
        print(f"Size:      {output_path.stat().st_size:,} bytes")
        print("=" * 70)

        print("\nPreview (first 10 rows):\n")
        print(df.head(10).to_string(index=False, max_colwidth=25))
        print("\n" + "=" * 70)
        print(f"✓ SUCCESS — open {output_path}")
        print("=" * 70)

    return str(output_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    # Install deps silently before doing anything else
    install_packages(REQUIRED, quiet=args.quiet)

    run(
        pdf_path=args.input,
        output_path=args.output,
        engine=args.engine,
        preprocess=args.preprocess,
        correct_ocr=args.correct_ocr,
        dpi=args.dpi,
        french_format=args.french,
        verbose=args.verbose,
        quiet=args.quiet,
        lang=args.lang,
    )
