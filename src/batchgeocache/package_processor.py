"""
package_processor.py

Processes a single package of addresses.

Responsibilities
----------------
1. Normalize addresses
2. Geocode addresses
3. Split results into Success / Partial / Failure
4. Produce PackageMetrics

Note: this module intentionally does NOT save anything to disk and
therefore does NOT know the final output file paths. Saving is
io_utils's job. Once the caller has saved the returned DataFrames
via io_utils.save_package_outputs(), combine the resulting paths
with the PackageMetrics returned here using
models.PackageSummary.from_metrics() to get a full PackageSummary
for logging.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from tqdm.auto import tqdm

from batchgeocache.address_normalizer import AddressNormalizer
from batchgeocache.geocoder import Geocoder
from batchgeocache.models import LookupStatus, PackageMetrics


class PackageProcessor:
    """
    Processes one address package.
    """

    def __init__(self, geocoder: Geocoder):

        self.geocoder = geocoder
        self.normalizer = AddressNormalizer()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def process_package(
        self,
        package_df: pd.DataFrame,
        package_number: int,
        total_packages: int,
        show_progress: bool = True,
        progress_every: int = 10,
    ):
        """
        Process a single dataframe of addresses.

        Parameters
        ----------
        show_progress:
            If True (default), display a live tqdm progress bar for
            this package's rows. Works in both notebook and plain
            terminal contexts (tqdm.auto picks the right renderer).
        progress_every:
            When show_progress is False, print a plain-text status
            line every N rows instead (useful for headless/logged
            runs where a tqdm bar isn't useful). Ignored when
            show_progress is True.

        Returns
        -------
        (
            metrics,       # PackageMetrics -- no file paths yet
            success_df,
            partial_df,
            failure_df,
        )
        """

        start_time = datetime.now()

        success_rows = []
        partial_rows = []
        failure_rows = []

        row_iterator = package_df.iterrows()

        if show_progress:
            row_iterator = tqdm(
                row_iterator,
                total=len(package_df),
                desc=f"Package {package_number}/{total_packages}",
                unit="address",
            )

        for row_index, (_, row) in enumerate(row_iterator, start=1):

            if not show_progress and row_index % progress_every == 0:
                print(
                    f"  Package {package_number}/{total_packages}: "
                    f"{row_index}/{len(package_df)} addresses processed"
                )

            # ---------------------------------------------
            # Normalize address
            # ---------------------------------------------

            normalized = self.normalizer.normalize(
                row["Address"]
            )

            # ---------------------------------------------
            # Geocode
            # ---------------------------------------------

            result = self.geocoder.lookup_address(
                address=row["Address"],
                city=row["City"],
                province=row["Province"],
                country=row["Country"],
                normalized_address=normalized.normalized,
            )

            output_row = {

                "address": result.address,
                "normalized_address": result.normalized_address,

                "city": result.city,
                "province": result.province,
                "country": result.country,

                "status": result.status.value,

                "postal_code": result.postal_code,

                "latitude": result.latitude,
                "longitude": result.longitude,

                "display_name": result.display_name,

                "error_type": result.error_type,
                "error_message": result.error_message,

                # Optional but useful for auditing
                "normalization_changes":
                    "; ".join(normalized.changes),
            }

            if result.status == LookupStatus.SUCCESS:

                success_rows.append(output_row)

            elif result.status == LookupStatus.PARTIAL:

                partial_rows.append(output_row)

            else:

                failure_rows.append(output_row)

        # -------------------------------------------------
        # Create DataFrames
        # -------------------------------------------------

        columns = [
            "address",
            "normalized_address",
            "city",
            "province",
            "country",
            "status",
            "postal_code",
            "latitude",
            "longitude",
            "display_name",
            "error_type",
            "error_message",
            "normalization_changes",
        ]

        success_df = pd.DataFrame(
            success_rows,
            columns=columns,
        )

        partial_df = pd.DataFrame(
            partial_rows,
            columns=columns,
        )

        failure_df = pd.DataFrame(
            failure_rows,
            columns=columns,
        )

        end_time = datetime.now()

        metrics = PackageMetrics(

            package_number=package_number,
            total_packages=total_packages,

            total_rows=len(package_df),

            success_count=len(success_df),
            partial_count=len(partial_df),
            failure_count=len(failure_df),

            start_time=start_time,
            end_time=end_time,

            duration_seconds=(
                end_time - start_time
            ).total_seconds(),
        )

        return (
            metrics,
            success_df,
            partial_df,
            failure_df,
        )
