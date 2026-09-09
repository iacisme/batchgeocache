"""
Shared data models used throughout the project.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class LookupStatus(Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILURE = "FAILURE"


@dataclass
class LookupResult:
    """
    Result of a single address lookup.
    """

    # Original input
    address: str
    city: str
    province: str
    country: str

    # Address actually submitted to Nominatim
    normalized_address: str | None = None

    # Lookup outcome
    status: LookupStatus = LookupStatus.FAILURE

    postal_code: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    display_name: str | None = None

    error_type: str | None = None
    error_message: str | None = None


@dataclass(slots=True)
class PackageMetrics:
    """
    Pure processing metrics for one package.

    Produced by ``PackageProcessor.process_package()``. Deliberately
    contains NO file-path information: at the point a package has
    been processed, nothing has been saved to disk yet, so
    PackageProcessor (which owns only normalization/geocoding/
    splitting/summarizing) cannot know where results will end up.

    File paths are attached later, once ``io_utils.save_package_outputs()``
    has actually written the CSVs -- see ``PackageSummary``.
    """

    package_number: int

    total_packages: int

    total_rows: int

    success_count: int

    partial_count: int

    failure_count: int

    start_time: datetime

    end_time: datetime

    duration_seconds: float


@dataclass(slots=True)
class PackageSummary(PackageMetrics):
    """
    Full summary for one processed AND saved package.

    Everything from PackageMetrics, plus the on-disk locations of
    the success/partial/failure CSVs for this package. This is the
    object that should be logged via ``PipelineLogger``.
    """

    success_file: Path
    partial_file: Path
    failure_file: Path

    @classmethod
    def from_metrics(
        cls,
        metrics: PackageMetrics,
        success_file: Path,
        partial_file: Path,
        failure_file: Path,
    ) -> "PackageSummary":
        """
        Build a PackageSummary by combining processing metrics with
        the file paths produced by io_utils.save_package_outputs().

        This is the intended "assembly" point in the pipeline:

            metrics = processor.process_package(...)[0]
            paths = io_utils.save_package_outputs(config, pkg_num, ...)
            summary = PackageSummary.from_metrics(
                metrics,
                success_file=paths["success_file"],
                partial_file=paths["partial_file"],
                failure_file=paths["failure_file"],
            )
        """

        return cls(
            package_number=metrics.package_number,
            total_packages=metrics.total_packages,
            total_rows=metrics.total_rows,
            success_count=metrics.success_count,
            partial_count=metrics.partial_count,
            failure_count=metrics.failure_count,
            start_time=metrics.start_time,
            end_time=metrics.end_time,
            duration_seconds=metrics.duration_seconds,
            success_file=success_file,
            partial_file=partial_file,
            failure_file=failure_file,
        )


@dataclass(slots=True)
class ProcessingState:
    """
    Current ETL processing state (resume/checkpoint tracker).

    This is the single canonical ProcessingState for the project.
    Persisted to disk as JSON by StateManager. The three file-path
    fields are optional because a state can legitimately exist
    before any package has been saved (e.g. right after a fresh
    resume from a state file that predates this schema, or before
    the very first package completes).
    """

    current_package: int

    total_packages: int

    # ISO-8601 timestamp string (as produced by datetime.utcnow().isoformat()),
    # not a datetime object -- this is what actually round-trips through JSON.
    last_completed: str | None

    status: str  # e.g. RUNNING, COMPLETED

    success_file: Path | None = None

    partial_file: Path | None = None

    failure_file: Path | None = None


@dataclass(slots=True)
class LogEntry:
    """
    One row of the processing log.
    """

    timestamp: datetime

    package_number: int

    total_rows: int

    success_count: int

    partial_count: int

    failure_count: int

    duration_seconds: float

    status: str
