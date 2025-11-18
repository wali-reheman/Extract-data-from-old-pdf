"""PDF file downloader with retry logic and progress tracking"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
from .config import Config


logger = logging.getLogger(__name__)


class PDFDownloader:
    """Download PDF files from remote sources"""

    def __init__(self, config: Config):
        """Initialize PDF downloader

        Args:
            config: Configuration object
        """
        self.config = config
        self.output_dir = Path(config.get("download", "output_dir", default="./downloads"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_from_url_pattern(self) -> List[str]:
        """Download PDFs using URL pattern from config

        Returns:
            List of successfully downloaded file paths
        """
        base_url = self.config.get("download", "base_url")
        file_pattern = self.config.get("download", "file_pattern")
        district_range = self.config.get("download", "district_range")
        data_type = self.config.get("download", "data_type")
        delay = self.config.get("download", "delay_seconds", default=3)

        district_codes = ["%.3d" % i for i in range(district_range[0], district_range[1] + 1)]

        logger.info(f"Starting download of {len(district_codes)} PDFs")
        downloaded_files = []

        for district_code in tqdm(district_codes, desc="Downloading PDFs"):
            filename = file_pattern.format(district_code=district_code, data_type=data_type)
            url = f"{base_url}{filename}"
            output_path = self.output_dir / filename

            try:
                success = self.download_file(url, output_path)
                if success:
                    downloaded_files.append(str(output_path))
                    logger.debug(f"Downloaded: {filename}")
                else:
                    logger.warning(f"Failed to download: {filename}")

                # Rate limiting
                time.sleep(delay)

            except Exception as e:
                logger.error(f"Error downloading {filename}: {e}")
                continue

        logger.info(f"Download complete: {len(downloaded_files)}/{len(district_codes)} files")
        return downloaded_files

    def download_file(self, url: str, output_path: Path, max_retries: 3) -> bool:
        """Download a single file with retry logic

        Args:
            url: URL to download from
            output_path: Path to save file
            max_retries: Maximum number of retry attempts

        Returns:
            True if download successful, False otherwise
        """
        verify_ssl = self.config.get("download", "verify_ssl", default=True)
        timeout = self.config.get("download", "timeout", default=30)

        for attempt in range(max_retries):
            try:
                response = requests.get(url, verify=verify_ssl, timeout=timeout, stream=True)

                if response.status_code == 200:
                    total_size = int(response.headers.get('content-length', 0))

                    with open(output_path, 'wb') as f:
                        if total_size > 0:
                            # Write with progress
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        else:
                            f.write(response.content)

                    return True

                elif response.status_code == 404:
                    logger.debug(f"File not found (404): {url}")
                    return False

                else:
                    logger.warning(f"HTTP {response.status_code} for {url}, attempt {attempt + 1}/{max_retries}")

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {url}: {e}, attempt {attempt + 1}/{max_retries}")

                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        return False

    def download_local_files(self, file_paths: List[str]) -> List[str]:
        """Process already-downloaded local PDF files

        Args:
            file_paths: List of local PDF file paths

        Returns:
            List of valid file paths
        """
        valid_files = []

        for file_path in file_paths:
            path = Path(file_path)
            if path.exists() and path.suffix.lower() == '.pdf':
                valid_files.append(str(path))
                logger.debug(f"Found valid PDF: {path}")
            else:
                logger.warning(f"Invalid or missing PDF: {file_path}")

        logger.info(f"Found {len(valid_files)} valid PDF files")
        return valid_files

    def get_downloaded_files(self) -> List[str]:
        """Get list of already downloaded PDF files

        Returns:
            List of PDF file paths in output directory
        """
        pdf_files = list(self.output_dir.glob("*.pdf"))
        return [str(f) for f in pdf_files]
