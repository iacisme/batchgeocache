"""
geocoder.py

Handles communication with the Nominatim API.

This module is intentionally responsible ONLY for geocoding.
It does NOT perform address normalization.
"""

from __future__ import annotations

import re

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from batchgeocache.config import GeocoderConfig
from batchgeocache.models import LookupResult, LookupStatus


# ============================================================
# Constants
# ============================================================

POSTAL_CODE_REGEX = re.compile(
    r"\b([A-Z]\d[A-Z]\s?\d[A-Z]\d)\b",
    re.IGNORECASE,
)


# ============================================================
# Geocoder
# ============================================================

class NominatimGeocoder:
    """
    Wrapper around geopy/Nominatim.
    """

    def __init__(self, config: GeocoderConfig):

        self.config = config

        self._geolocator = Nominatim(
            user_agent=config.user_agent,
            timeout=config.timeout,
        )

        self._geocode = RateLimiter(
            self._geolocator.geocode,
            min_delay_seconds=config.min_delay_seconds,
            max_retries=config.max_retries,
            error_wait_seconds=config.error_wait_seconds,
            swallow_exceptions=False,
        )

    # --------------------------------------------------------

    @staticmethod
    def _extract_postal_code(location) -> str | None:
        """
        Extract a Canadian postal code.

        Prefer the structured response (addressdetails=True).
        Fall back to regex if necessary.
        """

        if location is None:
            return None

        raw = getattr(location, "raw", {})

        address = raw.get("address")

        if isinstance(address, dict):

            postcode = address.get("postcode")

            if postcode:

                return postcode.upper()

        display_name = getattr(location, "address", "")

        match = POSTAL_CODE_REGEX.search(display_name)

        if match:

            return match.group(1).upper()

        return None

    # --------------------------------------------------------

    def lookup_address(
        self,
        address: str,
        city: str,
        province: str,
        country: str,
        normalized_address: str | None = None,
    ) -> LookupResult:
        """
        Lookup a single address.

        Parameters
        ----------
        address
            Original address from the source data.

        normalized_address
            Optional normalized address.
            If supplied, this is what will be submitted
            to Nominatim.
        """

        lookup_address = normalized_address or address

        full_address = (
            f"{lookup_address}, "
            f"{city}, "
            f"{province}, "
            f"{country}"
        )

        try:

            location = self._geocode(
                full_address,
                addressdetails=True,
            )

            if location is None:

                return LookupResult(
                    address=address,
                    city=city,
                    province=province,
                    country=country,
                    normalized_address=lookup_address,
                    status=LookupStatus.FAILURE,
                    error_type="NoMatch",
                    error_message="Address not found.",
                )

            postal_code = self._extract_postal_code(
                location
            )

            status = (
                LookupStatus.SUCCESS
                if postal_code
                else LookupStatus.PARTIAL
            )

            return LookupResult(
                address=address,
                city=city,
                province=province,
                country=country,
                normalized_address=lookup_address,
                status=status,
                postal_code=postal_code,
                latitude=location.latitude,
                longitude=location.longitude,
                display_name=location.address,
            )

        except Exception as exc:

            return LookupResult(
                address=address,
                city=city,
                province=province,
                country=country,
                normalized_address=lookup_address,
                status=LookupStatus.FAILURE,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )


# ============================================================
# Backward-compatible alias
#
# package_processor.py (and anything else already written against
# the shorter name) can keep using `Geocoder` -- it's the exact
# same class as NominatimGeocoder, just under its original name.
# ============================================================

Geocoder = NominatimGeocoder
