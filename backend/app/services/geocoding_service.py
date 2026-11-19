"""Nominatim reverse geocoding with process-local caching and throttling.

The bounded cache and one-request-per-second limiter are process-local. Cache
entries reset on restart and are not shared across multiple workers/instances.
"""

import math
import os
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from time import monotonic, sleep

import httpx

NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT_ENV = "TRACKBUS_NOMINATIM_USER_AGENT"
DEFAULT_USER_AGENT = "TrackBus/1.0 (+https://trackbus-oibk.onrender.com)"
REQUEST_TIMEOUT_SECONDS = 5.0
REQUEST_INTERVAL_SECONDS = 1.0
CACHE_TTL_SECONDS = 24 * 60 * 60
CACHE_MAX_ENTRIES = 2048
CACHE_COORDINATE_DECIMALS = 4


class GeocodingError(RuntimeError):
    """Raised when the reverse-geocoding provider cannot return a result."""


class GeocodingTimeoutError(GeocodingError):
    """Raised when the reverse-geocoding provider times out."""


@dataclass(frozen=True)
class GeocodingResult:
    address: str
    source: str = "nominatim"


_cache: OrderedDict[tuple[float, float], tuple[float, str]] = OrderedDict()
_request_lock = Lock()
_last_request_at: float | None = None


def _validate_coordinates(latitude: float, longitude: float) -> None:
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")


def _cache_key(latitude: float, longitude: float) -> tuple[float, float]:
    return (
        round(latitude, CACHE_COORDINATE_DECIMALS),
        round(longitude, CACHE_COORDINATE_DECIMALS),
    )


def _get_cached_address(
    key: tuple[float, float],
    current_time: float,
) -> str | None:
    cached = _cache.get(key)
    if cached is None:
        return None

    expires_at, address = cached
    if expires_at <= current_time:
        del _cache[key]
        return None

    _cache.move_to_end(key)
    return address


def reverse_geocode(
    latitude: float,
    longitude: float,
) -> GeocodingResult | None:
    """Return a cached or Nominatim address for valid coordinates.

    Coordinates are rounded to four decimal places for cache keys, so nearby
    points (roughly 11 metres at the equator) may share an address result.
    Only successful address results are cached.
    """
    _validate_coordinates(latitude, longitude)
    key = _cache_key(latitude, longitude)

    global _last_request_at
    with _request_lock:
        current_time = monotonic()
        cached_address = _get_cached_address(key, current_time)
        if cached_address is not None:
            return GeocodingResult(address=cached_address)

        if _last_request_at is not None:
            wait_seconds = REQUEST_INTERVAL_SECONDS - (
                current_time - _last_request_at
            )
            if wait_seconds > 0:
                sleep(wait_seconds)

        _last_request_at = monotonic()
        user_agent = os.getenv(USER_AGENT_ENV, "").strip() or DEFAULT_USER_AGENT

        try:
            response = httpx.get(
                NOMINATIM_REVERSE_URL,
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "format": "jsonv2",
                },
                headers={"User-Agent": user_agent},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException:
            raise GeocodingTimeoutError(
                "Reverse-geocoding provider timed out"
            ) from None
        except (httpx.HTTPError, ValueError):
            raise GeocodingError(
                "Reverse-geocoding provider returned an invalid response"
            ) from None

        if not isinstance(payload, dict):
            raise GeocodingError(
                "Reverse-geocoding provider returned an invalid response"
            )

        address = payload.get("display_name")
        if not isinstance(address, str) or not address.strip():
            return None

        address = address.strip()
        _cache[key] = (monotonic() + CACHE_TTL_SECONDS, address)
        _cache.move_to_end(key)

        while len(_cache) > CACHE_MAX_ENTRIES:
            _cache.popitem(last=False)

        return GeocodingResult(address=address)
