"""
Result combiner for Postal Code Lookup ETL pipeline.

This module aggregates per-package CSV outputs into final
consolidated datasets for SUCCESS, PARTIAL, and FAILURE results.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from batchgeocache.config import GeocoderConfig


# ============================================================
# File Discovery
# ============================================================

def _collect_files(folder: Path, keyword: str) -> List[Path]:
    """
    Collect all files in a folder matching a keyword.
    """

    if not folder.exists():
        return []

    return sorted(folder.glob(f"*{keyword}*.csv"))


# ============================================================
# Loading
# ============================================================

def _load_csv_files(files: List[Path]) -> pd.DataFrame:
    """
    Load and concatenate a list of CSV files.
    """

    if not files:
        return pd.DataFrame()
        
    dfs = []

    for file in files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except pd.errors.EmptyDataError:
            print(
                f"Skipping empty file: "
                f"{file.name}"
            )

    if not dfs:
        # Every matched file was empty (0 bytes / header-only-with-no-rows
        # can still parse fine via read_csv; this only triggers when
        # ALL files raised EmptyDataError). Avoid crashing pd.concat([]).
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


# ============================================================
# Public API
# ============================================================

class ResultCombiner:
    """
    Combines all package-level outputs into final datasets.
    """

    def __init__(self, config: GeocoderConfig) -> None:
        self.config = config

    # --------------------------------------------------------
    # Main combine function
    # --------------------------------------------------------

    def combine_all(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Combine all package outputs into final DataFrames.

        Returns:
            success_df, partial_df, failure_df
        """

        package_dir = self.config.package_dir

        # -------------------------
        # Collect files
        # -------------------------
        success_files = _collect_files(package_dir, "success")
        partial_files = _collect_files(package_dir, "partial")
        failure_files = _collect_files(package_dir, "failure")

        # -------------------------
        # Load + concatenate
        # -------------------------
        success_df = _load_csv_files(success_files)
        partial_df = _load_csv_files(partial_files)
        failure_df = _load_csv_files(failure_files)

        return success_df, partial_df, failure_df

    # --------------------------------------------------------
    # Optional export
    # --------------------------------------------------------

    def export_combined(
        self,
        success_df: pd.DataFrame,
        partial_df: pd.DataFrame,
        failure_df: pd.DataFrame,
    ) -> dict:
        """
        Export final combined datasets to disk.

        Returns:
            Dictionary of output file paths.
        """

        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        outputs = {}

        success_path = self.config.output_dir / "FINAL_success.csv"
        partial_path = self.config.output_dir / "FINAL_partial.csv"
        failure_path = self.config.output_dir / "FINAL_failure.csv"

        success_df.to_csv(success_path, index=False)
        partial_df.to_csv(partial_path, index=False)
        failure_df.to_csv(failure_path, index=False)

        outputs["success"] = success_path
        outputs["partial"] = partial_path
        outputs["failure"] = failure_path

        return outputs
