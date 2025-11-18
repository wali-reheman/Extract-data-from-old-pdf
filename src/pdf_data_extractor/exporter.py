"""Export parsed data to various formats"""

import json
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
from .config import Config


logger = logging.getLogger(__name__)


class DataExporter:
    """Export data to various formats"""

    def __init__(self, config: Config):
        """Initialize data exporter

        Args:
            config: Configuration object
        """
        self.config = config
        self.output_dir = Path(config.get("export", "output_dir", default="./output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.format = config.get("export", "format", default="excel")
        self.output_filename = config.get("export", "output_filename", default="extracted_data")

    def export(self, data: pd.DataFrame, output_path: Optional[str] = None) -> str:
        """Export data using configured format

        Args:
            data: DataFrame to export
            output_path: Optional custom output path

        Returns:
            Path to exported file
        """
        if data.empty:
            logger.warning("No data to export")
            return ""

        if output_path:
            file_path = Path(output_path)
        else:
            file_path = self._get_output_path()

        logger.info(f"Exporting {len(data)} rows to {file_path}")

        if self.format == "excel":
            return self.export_excel(data, file_path)
        elif self.format == "csv":
            return self.export_csv(data, file_path)
        elif self.format == "json":
            return self.export_json(data, file_path)
        else:
            raise ValueError(f"Unsupported export format: {self.format}")

    def export_excel(self, data: pd.DataFrame, output_path: Path) -> str:
        """Export data to Excel format

        Args:
            data: DataFrame to export
            output_path: Output file path

        Returns:
            Path to exported file
        """
        if not str(output_path).endswith('.xlsx'):
            output_path = output_path.with_suffix('.xlsx')

        try:
            data.to_excel(str(output_path), index=False, engine='openpyxl')
            logger.info(f"Excel export complete: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            raise

    def export_csv(self, data: pd.DataFrame, output_path: Path) -> str:
        """Export data to CSV format

        Args:
            data: DataFrame to export
            output_path: Output file path

        Returns:
            Path to exported file
        """
        if not str(output_path).endswith('.csv'):
            output_path = output_path.with_suffix('.csv')

        try:
            data.to_csv(str(output_path), index=False)
            logger.info(f"CSV export complete: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise

    def export_json(self, data: pd.DataFrame, output_path: Path) -> str:
        """Export data to JSON format

        Args:
            data: DataFrame to export
            output_path: Output file path

        Returns:
            Path to exported file
        """
        if not str(output_path).endswith('.json'):
            output_path = output_path.with_suffix('.json')

        try:
            # Convert to records format for better readability
            data.to_json(str(output_path), orient='records', indent=2)
            logger.info(f"JSON export complete: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise

    def export_all_formats(self, data: pd.DataFrame) -> dict:
        """Export data to all supported formats

        Args:
            data: DataFrame to export

        Returns:
            Dictionary mapping format to file path
        """
        results = {}

        for fmt in ['excel', 'csv', 'json']:
            try:
                self.format = fmt
                output_path = self._get_output_path()
                exported_path = self.export(data, output_path)
                results[fmt] = exported_path

            except Exception as e:
                logger.error(f"Failed to export as {fmt}: {e}")
                results[fmt] = None

        return results

    def _get_output_path(self) -> Path:
        """Get output file path based on format

        Returns:
            Path object for output file
        """
        extension_map = {
            "excel": ".xlsx",
            "csv": ".csv",
            "json": ".json",
        }

        extension = extension_map.get(self.format, ".txt")
        return self.output_dir / f"{self.output_filename}{extension}"

    def get_summary_stats(self, data: pd.DataFrame) -> dict:
        """Get summary statistics of exported data

        Args:
            data: DataFrame to analyze

        Returns:
            Dictionary with summary statistics
        """
        if data.empty:
            return {"rows": 0, "columns": 0}

        stats = {
            "rows": len(data),
            "columns": len(data.columns),
            "column_names": list(data.columns),
            "memory_usage": data.memory_usage(deep=True).sum(),
        }

        # Add null counts
        null_counts = data.isnull().sum()
        if null_counts.sum() > 0:
            stats["null_counts"] = null_counts[null_counts > 0].to_dict()

        return stats
