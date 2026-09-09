"""
Project configuration.

This module contains the configuration dataclass used throughout
the BatchGeoCache ETL project.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GeocoderConfig:
    """
    Global project configuration.
    """

    # ------------------------------------------------------------------
    # Project
    # ------------------------------------------------------------------

    project_root: Path

    # ------------------------------------------------------------------
    # Nominatim Settings
    # ------------------------------------------------------------------

    user_agent: str = "batchgeocache"

    timeout: int = 10

    min_delay_seconds: float = 1.2

    max_retries: int = 3

    error_wait_seconds: int = 5

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    package_size: int = 100

    # ------------------------------------------------------------------
    # Derived Paths
    # ------------------------------------------------------------------

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def temp_dir(self) -> Path:
        return (
            self.data_dir /
            "00_Inputs(Raw Data)" /
            "temp_files"
        )

    @property
    def package_dir(self) -> Path:
        return self.temp_dir / "packages"

    @property
    def log_dir(self) -> Path:
        return self.temp_dir / "logs"

    @property
    def state_dir(self) -> Path:
        return self.temp_dir / "state"

    @property
    def archive_dir(self) -> Path:
        return self.temp_dir / "archive"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "outputs"

