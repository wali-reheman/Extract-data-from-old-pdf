"""Parse extracted text into structured data for census and election formats"""

import re
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from .config import Config


logger = logging.getLogger(__name__)


class DataParser:
    """Parse OCR text into structured data"""

    def __init__(self, config: Config):
        """Initialize data parser

        Args:
            config: Configuration object
        """
        self.config = config
        self.data_format = config.get("parsing", "data_format", default="census")
        self.keywords = config.get("parsing", "keywords", self.data_format, default=[])
        self.column_mappings = config.get("parsing", "column_mappings", default={})
        self.filters = config.get("parsing", "filters", default=[])

    def parse_ocr_results(self, ocr_results: Dict[str, Dict]) -> pd.DataFrame:
        """Parse OCR results into structured DataFrame

        Args:
            ocr_results: Dictionary of OCR results from OCREngine

        Returns:
            Pandas DataFrame with structured data
        """
        logger.info(f"Parsing {len(ocr_results)} OCR results")

        all_data = []

        for image_path, result in ocr_results.items():
            if "error" in result:
                logger.warning(f"Skipping {image_path}: {result['error']}")
                continue

            try:
                parsed_data = self.parse_single_result(result, image_path)
                all_data.extend(parsed_data)

            except Exception as e:
                logger.error(f"Error parsing {image_path}: {e}")

        if not all_data:
            logger.warning("No data extracted from any images")
            return pd.DataFrame()

        # Combine all data
        df = pd.DataFrame(all_data)
        logger.info(f"Parsing complete: {len(df)} rows extracted")

        return df

    def parse_single_result(self, ocr_result: Dict, image_path: str) -> List[Dict]:
        """Parse a single OCR result

        Args:
            ocr_result: OCR result dictionary
            image_path: Path to source image

        Returns:
            List of parsed data dictionaries
        """
        lines = ocr_result.get("lines", [])

        if not lines:
            return []

        # Filter out noise
        lines = self._filter_lines(lines)

        # Find starting point based on keywords
        lines = self._trim_to_keywords(lines)

        # Extract regions and data
        if self.data_format == "census":
            return self._parse_census_data(lines, image_path)
        elif self.data_format == "election":
            return self._parse_election_data(lines, image_path)
        else:
            return self._parse_generic_data(lines, image_path)

    def _filter_lines(self, lines: List[str]) -> List[str]:
        """Filter out unwanted lines

        Args:
            lines: List of text lines

        Returns:
            Filtered list of lines
        """
        filtered = []

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip lines in filter list
            if line in self.filters:
                continue

            # Skip single characters (often OCR noise)
            if len(line) == 1 and line.isalpha():
                continue

            filtered.append(line)

        return filtered

    def _trim_to_keywords(self, lines: List[str]) -> List[str]:
        """Trim lines to start from first keyword match

        Args:
            lines: List of text lines

        Returns:
            Trimmed list of lines
        """
        for i, line in enumerate(lines):
            for keyword in self.keywords:
                if keyword in line.upper():
                    return lines[i:]

        return lines

    def _parse_census_data(self, lines: List[str], image_path: str) -> List[Dict]:
        """Parse census-specific data format

        Args:
            lines: Filtered and trimmed lines
            image_path: Source image path

        Returns:
            List of parsed data rows
        """
        matchers = ['ALL'] + self.keywords
        matching_lines = [
            line for line in lines
            if any(matcher in line.upper() for matcher in matchers)
        ]

        regions = []
        data_lines = []

        # Extract region names and their corresponding data
        for i, line in enumerate(matching_lines):
            if any(keyword in line.upper() for keyword in self.keywords):
                regions.append(line)

                # Try to get the next line as data
                if i + 1 < len(matching_lines):
                    data_lines.append(matching_lines[i + 1])
                else:
                    data_lines.append("")

        # Clean and parse data lines
        parsed_rows = []

        for region, data_line in zip(regions, data_lines):
            # Clean data line
            data_line = re.sub(r"( SEXE.|SEXE.)", "", data_line)
            data_line = re.sub(r"\s+", " ", data_line).strip()

            # Split into columns
            columns = data_line.split()

            if not columns:
                continue

            # Determine column mapping based on number of columns
            column_count = len(columns)
            column_names = self._get_column_names(column_count)

            if not column_names:
                logger.warning(f"Unknown column count {column_count} for: {data_line}")
                continue

            # Create row dictionary
            row = {}
            for i, col_name in enumerate(column_names):
                if i < len(columns):
                    row[col_name] = columns[i]
                else:
                    row[col_name] = ""

            row['REGION'] = region
            row['SOURCE_IMAGE'] = image_path

            parsed_rows.append(row)

        return parsed_rows

    def _parse_election_data(self, lines: List[str], image_path: str) -> List[Dict]:
        """Parse election-specific data format

        Args:
            lines: Filtered and trimmed lines
            image_path: Source image path

        Returns:
            List of parsed data rows
        """
        # Similar structure to census but with election-specific logic
        matchers = self.keywords
        matching_lines = [
            line for line in lines
            if any(matcher in line.upper() for matcher in matchers)
        ]

        parsed_rows = []

        for line in matching_lines:
            # Split into columns
            columns = re.split(r'\s{2,}', line)  # Split on 2+ spaces

            if not columns:
                continue

            column_count = len(columns)
            column_names = self._get_column_names(column_count, prefix="election")

            if not column_names:
                # Use generic column names
                column_names = [f"COL_{i}" for i in range(column_count)]

            row = {}
            for i, col_name in enumerate(column_names):
                if i < len(columns):
                    row[col_name] = columns[i]

            row['SOURCE_IMAGE'] = image_path
            parsed_rows.append(row)

        return parsed_rows

    def _parse_generic_data(self, lines: List[str], image_path: str) -> List[Dict]:
        """Parse generic tabular data

        Args:
            lines: Filtered and trimmed lines
            image_path: Source image path

        Returns:
            List of parsed data rows
        """
        parsed_rows = []

        for line in lines:
            columns = line.split()

            if not columns:
                continue

            row = {f"COL_{i}": val for i, val in enumerate(columns)}
            row['SOURCE_IMAGE'] = image_path
            parsed_rows.append(row)

        return parsed_rows

    def _get_column_names(self, column_count: int, prefix: str = "census") -> Optional[List[str]]:
        """Get column names based on column count

        Args:
            column_count: Number of columns
            prefix: Prefix for mapping key (e.g., 'census', 'election')

        Returns:
            List of column names or None if no mapping found
        """
        # Try exact match
        mapping_key = f"{prefix}_religion_{column_count}"
        if mapping_key in self.column_mappings:
            return self.column_mappings[mapping_key]

        # Try standard mapping
        mapping_key = f"{prefix}_standard"
        if mapping_key in self.column_mappings:
            return self.column_mappings[mapping_key]

        # Try column count match
        for key, columns in self.column_mappings.items():
            if len(columns) == column_count:
                return columns

        return None
