"""
Logging utilities for the Postal Code Lookup ETL pipeline.

This module writes structured logs for each processed package,
enabling auditing and debugging of pipeline execution.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from batchgeocache.config import GeocoderConfig
from batchgeocache.models import PackageSummary


# ============================================================
# Logger
# ============================================================

class PipelineLogger:
    """
    Handles CSV-based logging of pipeline execution.
    """

    def __init__(self, config: GeocoderConfig) -> None:
        self.config = config
        self.log_file = config.log_dir / "pipeline_log.csv"

    # --------------------------------------------------------
    # Initialize log file
    # --------------------------------------------------------

    def initialize_log(self) -> None:
        """
        Create log file with headers if it does not exist.
        """

        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.log_file.exists():
            with self.log_file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "package_number",
                        "total_rows",
                        "success_count",
                        "partial_count",
                        "failure_count",
                        "duration_seconds",
                        "status",
                    ]
                )

    # --------------------------------------------------------
    # Log one package
    # --------------------------------------------------------

    def log_package(self, summary: PackageSummary) -> None:
        """
        Append one package summary to the log file.
        """

        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        with self.log_file.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(
                [
                    datetime.utcnow().isoformat(),
                    summary.package_number,
                    summary.total_rows,
                    summary.success_count,
                    summary.partial_count,
                    summary.failure_count,
                    summary.duration_seconds,
                    "COMPLETED",
                ]
            )

    # --------------------------------------------------------
    # Convenience method
    # --------------------------------------------------------

    def log_from_summary(self, summary: PackageSummary) -> None:
        """
        Alias for log_package (kept for readability in pipeline code).
        """
        self.log_package(summary)
