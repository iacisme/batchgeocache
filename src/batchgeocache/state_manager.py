"""
State management for the Postal Code Lookup ETL pipeline.

This module handles saving and loading processing state to enable
resume capability across sessions (e.g., Colab restarts).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from batchgeocache.config import GeocoderConfig
from batchgeocache.models import ProcessingState


# ============================================================
# State Manager
# ============================================================

class StateManager:
    """
    Handles persistence of processing state.
    """

    def __init__(self, config: GeocoderConfig) -> None:
        self.config = config
        self.state_file = config.state_dir / "processing_state.json"

    # --------------------------------------------------------
    # Load state
    # --------------------------------------------------------

    def load_state(self) -> ProcessingState | None:
        """
        Load state from disk if it exists.

        Handles state files written before the file-path fields
        existed (older JSON without success_file/partial_file/
        failure_file keys) by defaulting them to None.
        """

        if not self.state_file.exists():
            return None

        with self.state_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return ProcessingState(
            current_package=data["current_package"],
            total_packages=data["total_packages"],
            last_completed=data.get("last_completed"),
            status=data.get("status", "RUNNING"),
            success_file=self._path_or_none(data.get("success_file")),
            partial_file=self._path_or_none(data.get("partial_file")),
            failure_file=self._path_or_none(data.get("failure_file")),
        )

    # --------------------------------------------------------
    # Save state
    # --------------------------------------------------------

    def save_state(self, state: ProcessingState) -> None:
        """
        Save state to disk.
        """

        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        with self.state_file.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "current_package": state.current_package,
                    "total_packages": state.total_packages,
                    "last_completed": state.last_completed,
                    "status": state.status,
                    "success_file": self._str_or_none(state.success_file),
                    "partial_file": self._str_or_none(state.partial_file),
                    "failure_file": self._str_or_none(state.failure_file),
                },
                f,
                indent=2,
            )

    # --------------------------------------------------------
    # Convenience update
    # --------------------------------------------------------

    def update_after_package(
        self,
        current_package: int,
        total_packages: int,
        success_file: Path | None = None,
        partial_file: Path | None = None,
        failure_file: Path | None = None,
    ) -> ProcessingState:
        """
        Update state after completing a package.

        The file-path arguments are optional so this can still be
        called exactly as before if you don't have them handy yet;
        pass them once you've assembled a PackageSummary
        (see models.PackageSummary.from_metrics) to make resume
        state aware of exactly which files the last package produced.
        """

        state = ProcessingState(
            current_package=current_package,
            total_packages=total_packages,
            last_completed=datetime.utcnow().isoformat(),
            status="RUNNING",
            success_file=success_file,
            partial_file=partial_file,
            failure_file=failure_file,
        )

        self.save_state(state)
        return state

    # --------------------------------------------------------
    # Mark completion
    # --------------------------------------------------------

    def mark_completed(self) -> None:
        """
        Mark the entire pipeline as completed.

        Clears all persisted state so the next run -- against this
        dataset or any other -- starts completely fresh at package 1,
        rather than risking a stale current_package/total_packages
        from this finished run being picked up by mistake.
        """

        self.clear_state()

    # --------------------------------------------------------
    # Clear state
    # --------------------------------------------------------

    def clear_state(self) -> None:
        """
        Delete any persisted processing state, if present.

        Safe to call even if no state file exists (idempotent) --
        useful both after a successful completion and as a manual
        "start over" reset.
        """

        if self.state_file.exists():
            self.state_file.unlink()

    # --------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------

    @staticmethod
    def _path_or_none(value: str | None) -> Path | None:
        return Path(value) if value else None

    @staticmethod
    def _str_or_none(value: Path | None) -> str | None:
        return str(value) if value else None
