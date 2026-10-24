import math
from datetime import datetime, timezone

from app.core.firebase import get_database
from app.schemas.eta import ETAResponse
from app.services.route_config import (
    MAX_ETA_SPEED_KMPH,
    MAX_FUTURE_GPS_SECONDS,
    MAX_GPS_AGE_SECONDS,
    MIN_ETA_SPEED_KMPH,
    ROUTE_CORRIDOR_M,
    ROUTE_LENGTH_M,
    STOP_COORDINATES,
)
from app.services.route_service import (
    distance_to_route_m,
    distance_to_stop_m,
    route_progress_fraction,
)

def _unavailable(bus_id: str, stop_id: str) -> ETAResponse:
    return ETAResponse(
        bus_id=bus_id,
        stop_id=stop_id,
        status="unavailable",
    )


def estimate_arrival(bus_id: str, stop_id: str) -> ETAResponse:
    """Estimate arrival using fresh GPS, route progress, and reported speed."""
    normalized_stop_id = stop_id.upper()

    if normalized_stop_id not in STOP_COORDINATES:
        raise ValueError(f"Unknown stop: {stop_id}")

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
        return _unavailable(bus_id, normalized_stop_id)

    try:
        latitude = float(location["latitude"])
        longitude = float(location["longitude"])
        speed_kmph = float(location["speed_kmph"])
        timestamp = datetime.fromisoformat(
            str(location["timestamp"]).replace("Z", "+00:00")
        )
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        return _unavailable(bus_id, normalized_stop_id)

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
        and math.isfinite(speed_kmph)
        and MIN_ETA_SPEED_KMPH <= speed_kmph <= MAX_ETA_SPEED_KMPH
    ):
        return _unavailable(bus_id, normalized_stop_id)

    age_seconds = (
        datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)
    ).total_seconds()

    if (
        age_seconds < -MAX_FUTURE_GPS_SECONDS
        or age_seconds > MAX_GPS_AGE_SECONDS
    ):
        return _unavailable(bus_id, normalized_stop_id)

    progress = route_progress_fraction(latitude, longitude)
    stop_distance = distance_to_stop_m(
        latitude,
        longitude,
        normalized_stop_id,
    )

    # Prototype assumption: the bus travels from STOP_A to STOP_B.
    # Do not estimate arrival at STOP_A after the bus has departed it.
    if normalized_stop_id == "STOP_A":
        if progress > 0.05:
            return _unavailable(bus_id, normalized_stop_id)
        remaining_route_m = 0.0
    else:
        remaining_route_m = (1.0 - progress) * ROUTE_LENGTH_M

    # Avoid returning a route-based estimate for a point far from the
    # provisional segment. A future version can use actual road geometry.


    if distance_to_route_m(latitude, longitude) > ROUTE_CORRIDOR_M:
        return _unavailable(bus_id, normalized_stop_id)

    eta_seconds = round(remaining_route_m / (speed_kmph / 3.6))

    return ETAResponse(
        bus_id=bus_id,
        stop_id=normalized_stop_id,
        eta_seconds=eta_seconds,
        distance_m=round(min(stop_distance, ROUTE_LENGTH_M), 2),
        status="available",
    )
