"""Configuration management for PDF data extraction"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for PDF data extraction"""

    DEFAULT_CONFIG = {
        "download": {
            "base_url": "https://www.pbs.gov.pk/sites/default/files/population/2017/results/",
            "file_pattern": "{district_code}{data_type}.pdf",
            "district_range": [1, 135],
            "data_type": "09",  # 09 for religion, 11 for language
            "output_dir": "./downloads",
            "delay_seconds": 3,
            "verify_ssl": True,
            "timeout": 30,
        },
        "conversion": {
            "output_dir": "./images",
            "image_format": "JPEG",
            "dpi": 300,
        },
        "ocr": {
            "engine": "tesseract",  # tesseract or easyocr
            "tesseract_config": "--psm 6 --oem 1",
            "preprocessing": {
                "grayscale": True,
                "resize_factor": 1.2,
                "interpolation": "cubic",
            },
        },
        "parsing": {
            "data_format": "census",  # census or election
            "keywords": {
                "census": ["FR", "DISTRICT", "TEHSIL", "DIVISION", "AGENCY", "TALUKA", "MUSAKHEL", "DE-EXCLUDED", "F.R"],
                "election": ["CONSTITUENCY", "POLLING", "STATION", "WARD", "DISTRICT", "DIVISION"],
            },
            "column_mappings": {
                "census_religion_7": ["SEX", "TOTAL", "MUSLIM", "CHRISTIAN", "HINDU", "QADIANI/AHMADI", "CASTE/SCHEDULED"],
                "census_religion_8": ["SEX", "TOTAL", "MUSLIM", "CHRISTIAN", "HINDU", "QADIANI/AHMADI", "CASTE/SCHEDULED", "OTHERS"],
                "census_religion_9": ["SEX", "TOTAL", "MUSLIM", "CHRISTIAN", "HINDU", "QADIANI/AHMADI", "CASTE/SCHEDULED", "OTHERS", "EXTRACOL"],
                "election_standard": ["POLLING_STATION", "REGISTERED_VOTERS", "VOTES_CAST", "VALID_VOTES", "REJECTED_VOTES"],
            },
            "filters": ["OVERALL", "RURAL", "URBAN"],
        },
        "export": {
            "output_dir": "./output",
            "format": "excel",  # excel, csv, json
            "output_filename": "extracted_data",
        },
        "logging": {
            "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
            "file": "pdf_extractor.log",
            "console": True,
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration

        Args:
            config_path: Path to YAML configuration file. If None, uses defaults.
        """
        self.config = self.DEFAULT_CONFIG.copy()

        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)

    def load_from_file(self, config_path: str):
        """Load configuration from YAML file

        Args:
            config_path: Path to YAML configuration file
        """
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)

        # Deep merge user config with defaults
        self._deep_merge(self.config, user_config)

    def _deep_merge(self, base: Dict, update: Dict):
        """Recursively merge two dictionaries

        Args:
            base: Base dictionary to update
            update: Dictionary with updates
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, *keys, default=None) -> Any:
        """Get configuration value using dot notation

        Args:
            *keys: Nested keys to access
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys, value):
        """Set configuration value using dot notation

        Args:
            *keys: Nested keys to access (last key is the one to set)
            value: Value to set
        """
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value

    def save(self, output_path: str):
        """Save current configuration to YAML file

        Args:
            output_path: Path to save configuration
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

    def __repr__(self):
        return f"Config({self.config})"
