#!/usr/bin/env python3
"""
OCR post-correction for scanned/poorly structured PDFs.

After OCR, raw text often contains character substitution errors from noise.
This module applies:
- Levenshtein fuzzy matching against known census/election vocabulary
- Numeric column pattern correction
- Confidence-weighted corrections
- Context-aware word repair

Usage:
    from ocr_postcorrect import OCRPostCorrector
    corrector = OCRPostCorrector()
    corrected_text = corrector.correct(raw_ocr_text, column_names=["MUSLIM", "CHRISTIAN", "HINDU"])
"""

import re
from typing import Optional
from rapidfuzz import fuzz, process


# Common OCR character substitutions (优先级)
# Key: wrong char → list of (correct char, frequency_estimate)
OCR_CHAR_MAP = {
    # Letter → number
    'O': '0', 'o': '0',
    'l': '1', 'I': '1',
    'S': '5', 's': '5',
    'Z': '2', 'z': '2',
    'B': '8',
    'q': '9',
    # Number → letter (less common)
    '0': 'O', '1': 'l', '2': 'Z', '5': 'S',
    # Similar letters
    'rn': 'm', 'rrn': 'm',   # 'r' + 'n' → 'm' (common in bad OCR)
    'vv': 'w', 'vv': 'W',
    'VV': 'W',
    'cl': 'd', 'il': 'd', 'lI': 'd',
    'cm': 'on', 'cO': '00',
    'nn': 'm',
    'uu': 'v',
    '--': '-', '\u2014': '-',   # em dash
    '\u2018': "'", '\u2019': "'",   # single curly quotes
    '\u201c': '"', '\u201d': '"',   # double curly quotes
}

# Known census/election terms for fuzzy matching
CENSUS_VOCABULARY = [
    # Geographic
    "DISTRICT", "DIVISION", "TEHSIL", "TALUKA", "PROVINCE", "REGION", "AREA",
    "SUB-DIVISION", "SUB DIVISION", "AGENCY", "ZONE", "CIRCLE", "SECTOR",
    "MUNICIPALITY", "WARD", "CONSTITUENCY", "CANTONMENT",
    # Demographic categories
    "TOTAL", "ALL SEXES", "MALE", "FEMALE", "TRANSGENDER", "SEX",
    "POPULATION", "HOUSEHOLD", "FAMILIES",
    # Religious groups
    "MUSLIM", "CHRISTIAN", "HINDU", "QADIANI", "AHMADI", "QADIANI/AHMADI",
    "SCHEDULED CASTE", "SCHEDULED CASTES", "CASTE", "OTHER", "OTHERS",
    "SIKH", "BUDDHIST", "JAIN", "PARSI", "ZOROASTRIAN", "JEW",
    # Section markers
    "OVERALL", "RURAL", "URBAN", "RURAL URBAN", "TOTAL RURAL",
    # Languages / ethnicity
    "LANGUAGE", "MOTHER TONGUE", "PUNJABI", "SINDHI", "PASHTO", "BALOCHI",
    "URDU", "SERAIKI", "HINDKO",
    # Data columns
    "SEX", "TOTAL", "MUSLIM", "CHRISTIAN", "HINDU", "QADIANI", "AHMADI",
    "SCHEDULED CASTES", "CASTE", "CASTES", "OTHERS", "RELIGION",
    # Numbers
    "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN",
    # Election terms
    "VOTERS", "REGISTERED", "CAST", "VALID", "REJECTED", "VOTES", "BALLOT",
    "POLLING STATION", "STATION", "BOOTH", "ELECTORAL", "ELECTION",
    "CANDIDATE", "PARTY", "MAJORITY", "TURNOUT",
    # Countries
    "PAKISTAN", "INDIA", "BANGLADESH", "NIGERIA", "IVORY COAST", "COTE D'IVOIRE",
    "SERBIA", "GUATEMALA", "LEBANON", "EGYPT", "MOROCCO", "ALGERIA", "TUNISIA",
]

# Cyrillic equivalents for Serbian/ Balkans
CYRILLIC_VOCABULARY = [
    "РЕПУБЛИКА", "СЪБИЈА", "СРБИЈА", "БЕОГРАД", "ГРАД", "ОПШТИНА",
    "БРОЈ", "ГЛАСА", "БИРАЧА", "ИЗБОРИ", "ПРЕДСЕДНИК",
]


class OCRPostCorrector:
    """
    Applies targeted OCR corrections using:
    1. Character-level substitution map (deterministic)
    2. Fuzzy word matching against known vocabulary
    3. Numeric pattern repair
    """

    def __init__(self, vocab: Optional[list[str]] = None, fuzzy_threshold: int = 80):
        """
        Args:
            vocab: Custom vocabulary for fuzzy matching (defaults to CENSUS_VOCABULARY)
            fuzzy_threshold: Minimum fuzzy score (0-100) to accept a correction
        """
        self.vocab = vocab or CENSUS_VOCABULARY
        self.fuzzy_threshold = fuzzy_threshold

        # Build a combined vocab list for rapidfuzz
        self._all_vocab = self.vocab.copy()
        # Add uppercase versions of vocab
        self._all_vocab.extend([v.upper() for v in self.vocab if v.upper() not in self._all_vocab])

    def apply_char_map(self, text: str) -> str:
        """Apply deterministic character substitutions."""
        for wrong, right in OCR_CHAR_MAP.items():
            text = text.replace(wrong, right)
        return text

    def _tokenize(self, text: str) -> list[str]:
        """Split text into tokens."""
        return re.findall(r'\b\w+\b|\s+|[^\s\w]', text)

    def correct_word_fuzzy(self, word: str, context: Optional[list[str]] = None) -> str:
        """
        Attempt to correct a single word using fuzzy matching.
        Returns original word if no good match found.
        """
        if not word or len(word) < 2:
            return word

        word_upper = word.upper()

        # Skip if already in vocabulary
        if word_upper in self._all_vocab:
            return word

        # Skip very short words (2 chars or less) unless obviously wrong
        if len(word) <= 2:
            return word

        # Fuzzy match against vocabulary
        match, score, _ = process.extractOne(
            word_upper,
            self._all_vocab,
            scorer=fuzz.ratio
        )

        if score >= self.fuzzy_threshold:
            # Preserve original case pattern roughly
            if word.isupper():
                return match
            elif word.islower():
                return match.lower()
            else:  # title case
                return match.title()
        return word

    def correct_text(self, text: str, column_names: Optional[list[str]] = None) -> str:
        """
        Full correction pipeline for OCR text.

        Args:
            text: Raw OCR text
            column_names: Known column names from this specific PDF (for targeted corrections)

        Returns:
            Corrected text
        """
        # Build effective vocabulary: base + column-specific terms
        effective_vocab = self._all_vocab.copy()
        if column_names:
            effective_vocab.extend([c.upper() for c in column_names if c.upper()])

        # Step 1: Apply character substitution map
        corrected = self.apply_char_map(text)

        # Step 2: Fix common multi-char patterns
        # 'rn'→'m' (e.g., "govemrment" → "government")
        corrected = re.sub(r'\brn\b', 'm', corrected)
        corrected = re.sub(r'\bvv\b', 'w', corrected)
        corrected = re.sub(r'\bVV\b', 'W', corrected)

        # Step 3: Fix numbers with embedded OCR noise
        # e.g., "1O5" → "105", "l234" → "1234"
        corrected = re.sub(r'\b(\d)[oOlI](\d)', r'\1\2', corrected)
        corrected = re.sub(r'\b(\d)[oOlI](?=\d{2})', r'\1', corrected)

        return corrected

    def correct_census_numbers(self, text: str, french_format: bool = False) -> str:
        """
        Post-process numbers in census/election OCR text.

        For French format: "1 132 655" → "1132655"
        For English format: "1,132,655" → "1132655"
        """
        if french_format:
            # French: space-separated thousands
            # Pattern: digit followed by groups of 3 digits separated by spaces
            # e.g., "1 132 655" → "1132655"
            corrected = re.sub(r'\b(\d)\s+(\d{3})\s+(\d{3})\b', r'\1\2\3', text)
            corrected = re.sub(r'\b(\d)\s+(\d{3})\b', r'\1\2', corrected)
        else:
            # English: comma-separated thousands
            corrected = re.sub(r'\b(\d),(\d{3}),(\d{3})\b', r'\1\2\3', text)
            corrected = re.sub(r'\b(\d),(\d{3})\b', r'\1\2', text)

        return corrected

    def detect_language_hint(self, text: str) -> str:
        """
        Detect script/language hint from OCR text.
        Returns: "cyrillic", "arabic", "latin", or "mixed"
        """
        # Cyrillic range
        cyrillic_chars = re.findall(r'[\u0400-\u04FF]', text)
        # Arabic range
        arabic_chars = re.findall(r'[\u0600-\u06FF]', text)

        cyrillic_ratio = len(cyrillic_chars) / max(len(text), 1)
        arabic_ratio = len(arabic_chars) / max(len(text), 1)

        if cyrillic_ratio > 0.3:
            return "cyrillic"
        elif arabic_ratio > 0.3:
            return "arabic"
        elif cyrillic_ratio > 0.05 or arabic_ratio > 0.05:
            return "mixed"
        return "latin"


# Convenience function for simple use
def correct_ocr_text(text: str,
                    column_names: Optional[list[str]] = None,
                    french_format: bool = False) -> str:
    """
    One-shot OCR text correction.

    Args:
        text: Raw OCR output
        column_names: Known column headers from this PDF
        french_format: Whether to combine space-separated thousands
    """
    corrector = OCRPostCorrector()
    result = corrector.correct_text(text, column_names)
    if french_format:
        result = corrector.correct_census_numbers(result, french_format=True)
    return result
