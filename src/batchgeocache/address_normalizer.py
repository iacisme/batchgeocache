"""
Address normalization utilities.

Version 1:
- Standardizes formatting
- Expands common Canadian street abbreviations
- Normalizes directional indicators

Future versions may add:
- Unit parsing
- PO Box handling
- Address component extraction
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re


# ============================================================
# Constants
# ============================================================

STREET_TYPE_MAP = {
    "AVE": "AVENUE",
    "AV": "AVENUE",

    "BLVD": "BOULEVARD",
    "BV": "BOULEVARD",

    "CIR": "CIRCLE",
    "CI": "CIRCLE",

    "COMMON": "COMMON",
    "CM": "COMMON",

    "COURT": "COURT",
    "CT": "COURT",
    "CO": "COURT",

    "CRES": "CRESCENT",
    "CR": "CRESCENT",

    "DR": "DRIVE",

    "GREEN": "GREEN",
    "GR": "GREEN",

    "GROVE": "GROVE",
    "GV": "GROVE",

    "HEIGHTS": "HEIGHTS",
    "HE": "HEIGHTS",

    "MANOR": "MANOR",
    "MR": "MANOR",

    "ROAD": "ROAD",
    "RD": "ROAD",

    "STREET": "STREET",
    "ST": "STREET",

    "TRAIL": "TRAIL",
    "TR": "TRAIL",

    "VIEW": "VIEW",
    "VI": "VIEW",

    "WAY": "WAY",
    "WY": "WAY",
}


DIRECTIONAL_MAP = {
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",

    "NORTHEAST": "NE",
    "NORTHWEST": "NW",
    "SOUTHEAST": "SE",
    "SOUTHWEST": "SW",
}


# ============================================================
# Data Model
# ============================================================

@dataclass
class NormalizedAddress:
    """
    Result of address normalization.
    """

    original: str

    normalized: str

    changes: list[str] = field(
        default_factory=list
    )


# ============================================================
# Normalizer
# ============================================================

class AddressNormalizer:
    """
    Performs address cleanup before geocoding.
    """

    def normalize(
        self,
        address: str,
    ) -> NormalizedAddress:
        """
        Normalize an address.

        Args:
            address:
                Raw address string.

        Returns:
            NormalizedAddress
        """

        original = address

        changes = []

        normalized = address

        normalized, changed = self._normalize_case(
            normalized
        )

        if changed:
            changes.append(
                "Normalized capitalization"
            )

        normalized, changed = self._normalize_spaces(
            normalized
        )

        if changed:
            changes.append(
                "Normalized whitespace"
            )

        normalized, changed = self._normalize_punctuation(
            normalized
        )

        if changed:
            changes.append(
                "Normalized punctuation"
            )

        normalized, suffix_changes = (
            self._expand_street_types(
                normalized
            )
        )

        changes.extend(
            suffix_changes
        )

        normalized, directional_changes = (
            self._normalize_directionals(
                normalized
            )
        )

        changes.extend(
            directional_changes
        )

        return NormalizedAddress(
            original=original,
            normalized=normalized,
            changes=changes,
        )

    # ========================================================
    # Internal methods
    # ========================================================

    @staticmethod
    def _normalize_case(
        address: str,
    ) -> tuple[str, bool]:

        normalized = address.upper()

        return (
            normalized,
            normalized != address,
        )

    @staticmethod
    def _normalize_spaces(
        address: str,
    ) -> tuple[str, bool]:

        normalized = re.sub(
            r"\s+",
            " ",
            address,
        ).strip()

        return (
            normalized,
            normalized != address,
        )

    @staticmethod
    def _normalize_punctuation(
        address: str,
    ) -> tuple[str, bool]:

        normalized = re.sub(
            r"[,.]",
            "",
            address,
        )

        return (
            normalized,
            normalized != address,
        )

    @staticmethod
    def _expand_street_types(
        address: str,
    ) -> tuple[str, list[str]]:

        changes = []

        tokens = address.split()

        updated_tokens = []

        for token in tokens:

            replacement = STREET_TYPE_MAP.get(
                token
            )

            if replacement and replacement != token:

                updated_tokens.append(
                    replacement
                )

                changes.append(
                    f"Expanded street type: "
                    f"{token} -> {replacement}"
                )

            else:

                updated_tokens.append(
                    token
                )

        return (
            " ".join(updated_tokens),
            changes,
        )

    @staticmethod
    def _normalize_directionals(
        address: str,
    ) -> tuple[str, list[str]]:

        changes = []

        tokens = address.split()

        updated_tokens = []

        for token in tokens:

            replacement = DIRECTIONAL_MAP.get(
                token
            )

            if replacement:

                updated_tokens.append(
                    replacement
                )

                changes.append(
                    f"Expanded directional: "
                    f"{token} -> {replacement}"
                )

            else:

                updated_tokens.append(
                    token
                )

        return (
            " ".join(updated_tokens),
            changes,
        )
