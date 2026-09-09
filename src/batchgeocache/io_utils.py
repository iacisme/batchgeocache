"""
I/O utilities for the Postal Code Lookup ETL pipeline.

This module handles all file system interactions including:
- Directory creation
- Saving DataFrames to CSV
- Generating consistent file names
"""

from __future__ import annotations

import shutil
from pathlib import Path
from datetime import datetime

import zipfile 

import pandas as pd

from batchgeocache.config import GeocoderConfig


# ============================================================
# Directory Management
# ============================================================

def ensure_directories(config: GeocoderConfig) -> None:
    """
    Create required project directories if they do not exist.
    """

    dirs = [
        config.package_dir,
        config.log_dir,
        config.state_dir,
        config.output_dir,
    ]

    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# File Naming
# ============================================================

def build_package_filename(
    package_number: int,
    status: str,
) -> str:
    """
    Build a standardized filename for package outputs.

    Args:
        package_number:
            Package index (1-based).

        status:
            One of: SUCCESS, PARTIAL, FAILURE

    Returns:
        Filename string.
    """

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    return f"pkg_{package_number:04d}_{status.lower()}_{timestamp}.csv"


# ============================================================
# CSV Writing
# ============================================================

def save_dataframe(
    df: pd.DataFrame,
    path: Path,
) -> None:
    """
    Save a DataFrame to CSV.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def save_package_outputs(
    config: GeocoderConfig,
    package_number: int,
    success_df: pd.DataFrame,
    partial_df: pd.DataFrame,
    failure_df: pd.DataFrame,
) -> dict:
    """
    Save all outputs for a single package.

    Returns:
        Dictionary with file paths.
    """

    outputs = {}

    # -------------------------
    # SUCCESS
    # -------------------------
    success_file = config.package_dir / build_package_filename(
        package_number, "SUCCESS"
    )

    save_dataframe(success_df, success_file)
    outputs["success_file"] = success_file

    # -------------------------
    # PARTIAL
    # -------------------------
    partial_file = config.package_dir / build_package_filename(
        package_number, "PARTIAL"
    )

    save_dataframe(partial_df, partial_file)
    outputs["partial_file"] = partial_file

    # -------------------------
    # FAILURE
    # -------------------------
    failure_file = config.package_dir / build_package_filename(
        package_number, "FAILURE"
    )

    save_dataframe(failure_df, failure_file)
    outputs["failure_file"] = failure_file

    return outputs


# ============================================================
# Archiving
# ============================================================

def archive_package_dir(config: GeocoderConfig) -> Path | None:
    """
    Move all files currently in config.package_dir into a timestamped
    archive folder, leaving package_dir empty.

    Call this once a full run has genuinely completed (right after
    StateManager.mark_completed()), so a future run -- even one using
    an identically-named source file with entirely different data --
    starts from a clean package_dir.

    Without this, ResultCombiner.combine_all() would silently merge
    this run's per-package CSVs with a future run's: output filenames
    are timestamped (see build_package_filename) but otherwise carry
    no run identity, so nothing else distinguishes "this run's files"
    from "an old run's leftover files" once they're sitting in the
    same folder.

    Files are moved, not deleted -- nothing is lost, just relocated
    out of the way of future combine_all() calls.

    Returns:
        Path to the archive folder created, or None if there was
        nothing in package_dir to archive.
    """

    if not config.package_dir.exists():
        return None

    package_files = list(config.package_dir.glob("*.csv"))

    if not package_files:
        return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    archive_folder = config.archive_dir / timestamp
    archive_folder.mkdir(parents=True, exist_ok=True)

    for file in package_files:
        shutil.move(str(file), str(archive_folder / file.name))

    return archive_folder


# ============================================================
# Zipping
# ============================================================

def zip_latest_package_archive(config: GeocoderConfig) -> Path | None:
    """
    Create a ZIP of the most recently archived run's raw package CSVs.

    "Most recent" is determined by folder name, since archive
    subfolders are named with a UTC timestamp (see
    archive_package_dir) and therefore sort chronologically as
    strings -- the last one alphabetically is the newest.

    This only creates the .zip file on disk; it does not trigger a
    browser download. In a Colab notebook, follow this with:

        from google.colab import files
        files.download(str(zip_path))

    Returns:
        Path to the created .zip file, or None if no archived runs
        exist yet (i.e. archive_package_dir() has never been called).
    """

    if not config.archive_dir.exists():
        return None

    archive_folders = sorted(
        p for p in config.archive_dir.iterdir() if p.is_dir()
    )

    if not archive_folders:
        return None

    latest_folder = archive_folders[-1]

    zip_path_str = shutil.make_archive(
        base_name=str(config.archive_dir / latest_folder.name),
        format="zip",
        root_dir=str(latest_folder),
    )

    return Path(zip_path_str)


# ============================================================
# Zipping (combined outputs)
# ============================================================

def zip_combined_outputs(config: GeocoderConfig, combined_files: dict) -> Path | None:
    """
    Zip the final combined SUCCESS/PARTIAL/FAILURE CSVs produced by
    ResultCombiner.export_combined() into a single downloadable archive.

    Unlike zip_latest_package_archive(), which zips the raw per-package
    CSVs moved into config.archive_dir, this zips the combined
    FINAL_*.csv files sitting in config.output_dir.

    Args:
        combined_files: the dict returned by
            ResultCombiner.export_combined() -- {"success": Path, ...}

    Returns:
        Path to the created .zip file, or None if combined_files is empty.
    """

    if not combined_files:
        return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    zip_path = config.output_dir / f"combined_results_{timestamp}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in combined_files.values():
            zf.write(path, arcname=path.name)

    return zip_path

    
# ============================================================
# Full project reset
# ============================================================

def list_project_files(config: GeocoderConfig) -> list[Path]:
    """
    Enumerate every file this pipeline has ever written:
    per-package outputs, all archived runs, the combined FINAL
    outputs, the pipeline log, and the JSON state file.

    Used by reset_project_files() to show exactly what would be
    deleted before asking for confirmation.
    """

    all_files: list[Path] = []

    if config.package_dir.exists():
        all_files.extend(sorted(config.package_dir.glob("*.csv")))

    if config.archive_dir.exists():
        # rglob("*") also picks up the .zip files zip_latest_package_archive()
        # may have created, plus the (now-empty, since raw files were
        # moved out of them) per-run subfolders themselves -- filter
        # down to actual files only.
        all_files.extend(
            sorted(f for f in config.archive_dir.rglob("*") if f.is_file())
        )

    if config.output_dir.exists():
        all_files.extend(sorted(config.output_dir.glob("*.csv")))

    if config.log_dir.exists():
        all_files.extend(sorted(config.log_dir.glob("*.csv")))

    if config.state_dir.exists():
        all_files.extend(sorted(config.state_dir.glob("*.json")))

    # De-duplicate while preserving order, in case any glob patterns
    # above overlapped.
    seen = set()
    deduped = []
    for f in all_files:
        if f not in seen:
            seen.add(f)
            deduped.append(f)

    return deduped


def reset_project_files(
    config: GeocoderConfig,
    confirmation_phrase: str = "DELETE ALL FILES",
) -> None:
    """
    Interactive, destructive reset of every project-related file.

    Lists every file that would be deleted (package outputs, all
    archived runs, FINAL combined outputs, the pipeline log, and the
    JSON state file), then requires the user to type an exact
    confirmation phrase before anything is actually removed.

    Intended to be run in its own Colab cell, on its own -- not
    called automatically by anything else in the pipeline.

    Directories themselves are left in place (ensure_directories()
    will recreate any that are missing on the next run); only the
    files inside them are deleted.
    """

    files_to_delete = list_project_files(config)

    if not files_to_delete:
        print("No project files found -- nothing to delete.")
        return

    print(f"The following {len(files_to_delete)} file(s) will be PERMANENTLY deleted:\n")

    for f in files_to_delete:
        print(f"  {f}")

    print(
        f"\nThis cannot be undone. These files are not backed up anywhere else.\n"
        f"Type exactly: {confirmation_phrase}\n"
        f"(or anything else to cancel)"
    )

    confirmation = input("> ").strip()

    if confirmation != confirmation_phrase:
        print("\nCancelled -- no files were deleted.")
        return

    deleted_count = 0

    for f in files_to_delete:
        try:
            f.unlink()
            deleted_count += 1
        except OSError as exc:
            print(f"Could not delete {f}: {exc}")

    print(f"\nDeleted {deleted_count} of {len(files_to_delete)} file(s).")
    print("Project has been reset. Folders remain in place for the next run.")
