"""
inspect_results.py

Run this as a Colab cell (or `python inspect_results.py`) after any
batch of packages has completed, to sanity-check the data itself --
not just whether the pipeline crashed.

Assumes `config` (a GeocoderConfig) is already defined in your
notebook. Uses ResultCombiner, so it reads directly from
config.package_dir -- no need to re-run the pipeline.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pandas as pd

from batchgeocache.result_combiner import ResultCombiner


# ------------------------------------------------------------------
# Geographic boundaries
#
# Boundary definitions (bounding box + optional FSA prefix hints)
# live in boundaries.toml, next to this module, so a new boundary
# (a different city, a province, etc.) can be added without touching
# this code -- see boundaries.toml for the schema.
#
# The FSA-prefix check is a SECONDARY, weaker signal than the lat/lon
# bounding-box check -- treat anything it flags as "worth a manual
# look", not as a confirmed error. The bounding box is the more
# trustworthy of the two.
# ------------------------------------------------------------------

BOUNDARIES_FILE = Path(__file__).parent / "boundaries.toml"

POSTAL_CODE_PATTERN = re.compile(r"^[A-Za-z]\d[A-Za-z] ?\d[A-Za-z]\d$")


def _load_boundary(name: str) -> dict | None:
    """
    Load one named boundary definition from boundaries.toml.

    Returns None if the file doesn't exist or has no entry under
    `name`, so callers can skip the geographic sanity check
    gracefully rather than crashing on a boundary that hasn't been
    defined yet.
    """

    if not BOUNDARIES_FILE.exists():
        return None

    with BOUNDARIES_FILE.open("rb") as f:
        boundaries = tomllib.load(f)

    return boundaries.get(name)


def inspect_results(config, boundary_name: str | None = "calgary") -> None:
    """
    Parameters
    ----------
    boundary_name
        Key to look up in boundaries.toml for the geographic sanity
        check (see section 4 below). Pass None to skip that section
        entirely. Defaults to "calgary" -- the only boundary defined
        so far.
    """

    combiner = ResultCombiner(config)
    success_df, partial_df, failure_df = combiner.combine_all()

    total_rows = len(success_df) + len(partial_df) + len(failure_df)

    print("=" * 60)
    print("OVERALL COUNTS")
    print("=" * 60)
    print(f"Success : {len(success_df):>7}")
    print(f"Partial : {len(partial_df):>7}")
    print(f"Failure : {len(failure_df):>7}")
    print(f"Total   : {total_rows:>7}")

    if total_rows > 0:
        success_rate = len(success_df) / total_rows * 100
        print(f"\nOverall success rate: {success_rate:.1f}%")

    # --------------------------------------------------------
    # 1. Failure reason breakdown
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FAILURE BREAKDOWN BY error_type")
    print("=" * 60)

    if len(failure_df) > 0 and "error_type" in failure_df.columns:
        print(
            failure_df["error_type"]
            .fillna("(no error_type / not found)")
            .value_counts()
            .to_string()
        )
    else:
        print("No failures to break down.")

    # --------------------------------------------------------
    # 2. Null / missing postal codes among "successes"
    #
    # A row landing in success_df but with a null postal_code
    # would indicate a bug in the status classification logic --
    # this should always be zero.
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("NULL CHECK: successes with missing postal_code")
    print("=" * 60)

    if len(success_df) > 0:
        null_postal = success_df["postal_code"].isna().sum()
        print(f"{null_postal} of {len(success_df)} success rows have a null postal_code")
        if null_postal > 0:
            print(">>> UNEXPECTED -- investigate status classification logic.")
    else:
        print("No success rows yet.")

    # --------------------------------------------------------
    # 3. Postal code format validity
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FORMAT CHECK: postal codes matching Canadian pattern")
    print("=" * 60)

    if len(success_df) > 0:
        valid_format = success_df["postal_code"].astype(str).str.match(
            POSTAL_CODE_PATTERN
        )
        invalid_count = (~valid_format).sum()
        print(f"{invalid_count} of {len(success_df)} postal codes do NOT match A1A 1A1 format")
        if invalid_count > 0:
            print("\nSample of malformed postal codes:")
            print(
                success_df.loc[~valid_format, ["address", "postal_code", "display_name"]]
                .head(10)
                .to_string(index=False)
            )

    # --------------------------------------------------------
    # 4. Geographic sanity: does this fall within the expected
    #    boundary?
    #
    # Catches cases where Nominatim confidently returned a
    # postal code for a similarly-named street in a different
    # city/province. Boundary is looked up from boundaries.toml
    # by `boundary_name` -- see that file to add a new one.
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("GEOGRAPHIC SANITY CHECK")
    print("=" * 60)

    if not boundary_name:
        print("No boundary_name given -- skipping geographic sanity check.")

    elif len(success_df) > 0:

        boundary = _load_boundary(boundary_name)

        if boundary is None:
            print(
                f"No boundary named '{boundary_name}' found in "
                f"{BOUNDARIES_FILE.name} -- skipping geographic sanity check."
            )
        else:
            lat_range = tuple(boundary["lat_range"])
            lon_range = tuple(boundary["lon_range"])
            fsa_prefixes = tuple(boundary.get("fsa_prefixes", ()))

            lat_ok = success_df["latitude"].between(*lat_range)
            lon_ok = success_df["longitude"].between(*lon_range)
            outside_bbox = ~(lat_ok & lon_ok)

            if fsa_prefixes:
                postal_prefix2 = success_df["postal_code"].astype(str).str[:2]
                postal_prefix3 = success_df["postal_code"].astype(str).str[:3]

                wrong_fsa = ~(
                    postal_prefix2.isin(fsa_prefixes)
                    | postal_prefix3.isin(fsa_prefixes)
                )

                print(
                    f"Postal codes outside expected '{boundary_name}' FSAs "
                    f"(soft signal): {wrong_fsa.sum()}"
                )
            else:
                wrong_fsa = pd.Series(False, index=success_df.index)

            print(
                f"Coordinates outside '{boundary_name}' bounding box "
                f"(stronger signal): {outside_bbox.sum()}"
            )

            suspicious = success_df[wrong_fsa | outside_bbox]

            if len(suspicious) > 0:
                print("\nSample of results worth a manual look:")
                print(
                    suspicious[
                        ["address", "postal_code", "latitude", "longitude", "display_name"]
                    ]
                    .head(10)
                    .to_string(index=False)
                )

    # --------------------------------------------------------
    # 5. Duplicate detection
    #
    # Catches the "re-ran the same package twice" scenario --
    # io_utils timestamps filenames, so a re-run creates a new
    # file rather than overwriting, which ResultCombiner would
    # then double-count.
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("DUPLICATE CHECK")
    print("=" * 60)

    non_empty_frames = [df for df in (success_df, partial_df, failure_df) if len(df) > 0]
    all_rows = (
        pd.concat(non_empty_frames, ignore_index=True)
        if non_empty_frames
        else pd.DataFrame()
    )

    if len(all_rows) > 0:
        dup_count = all_rows.duplicated(subset=["address"]).sum()
        print(f"{dup_count} duplicate address rows found across all results")

        if dup_count > 0:
            print(">>> Check config.package_dir for leftover files from repeated runs")
            print(
                all_rows[all_rows.duplicated(subset=["address"], keep=False)]
                .sort_values("address")
                .head(10)
                .to_string(index=False)
            )

    # --------------------------------------------------------
    # 6. Normalizer impact
    #
    # How much is AddressNormalizer actually changing? If it's
    # near-zero, it's not contributing to your success rate yet.
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("NORMALIZER IMPACT")
    print("=" * 60)

    if len(all_rows) > 0 and "normalization_changes" in all_rows.columns:
        changed = all_rows["normalization_changes"].fillna("").str.len() > 0
        print(f"{changed.sum()} of {len(all_rows)} addresses were modified by AddressNormalizer")


if __name__ == "__main__":
    # Example standalone usage -- adjust project_root as needed.
    from pathlib import Path
    from batchgeocache.config import GeocoderConfig

    config = GeocoderConfig(project_root=Path("."))
    inspect_results(config)
