
"""Route deviation checks for the TrackBus prototype."""

import math
from datetime import datetime, timedelta, timezone

from app.core.firebase import get_database
from app.services.route_config import (
    MAX_FUTURE_GPS_SECONDS,
    MAX_GPS_AGE_SECONDS,
    ROUTE_CORRIDOR_M,
)
from app.services.route_service import distance_to_route_m


def check_route_deviation(bus_id: str) -> dict:
    """Check the latest GPS point against the configured prototype route."""
    try:
        location = (
            get_database()
            .child("buses")
            .child(bus_id)
            .child("location")
            .get()
        )
    except Exception as exc:
        raise RuntimeError(
            "Could not read bus location from Firebase"
        ) from exc

    if not isinstance(location, dict):
        return {
            "bus_id": bus_id,
            "status": "unavailable",
            "reason": "location_missing",
        }

    try:
        latitude = float(location["latitude"])
        longitude = float(location["longitude"])
        timestamp = datetime.fromisoformat(
            str(location["timestamp"]).replace("Z", "+00:00")
        )
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        return {
            "bus_id": bus_id,
            "status": "unavailable",
            "reason": "invalid_location",
        }

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        return {
            "bus_id": bus_id,
            "status": "unavailable",
            "reason": "invalid_coordinates",
        }

    age_seconds = (
        datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)
    ).total_seconds()

    if age_seconds < -MAX_FUTURE_GPS_SECONDS:
        return {
            "bus_id": bus_id,
            "status": "unavailable",
            "reason": "timestamp_in_future",
        }

    if age_seconds > MAX_GPS_AGE_SECONDS:
        return {
            "bus_id": bus_id,
            "status": "unavailable",
            "reason": "stale_location",
        }

    distance_m = distance_to_route_m(latitude, longitude)
    status = (
        "on_route"
        if distance_m <= ROUTE_CORRIDOR_M
        else "deviated"
    )

    return {
        "bus_id": bus_id,
        "status": status,
        "distance_from_route_m": round(distance_m, 2),
        "threshold_m": ROUTE_CORRIDOR_M,
        "location_timestamp": timestamp.isoformat(),
        "model": "straight_segment_approximation",
    }
