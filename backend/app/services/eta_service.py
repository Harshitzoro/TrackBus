
"""Single-stop and route-wide ETA services for TrackBus."""

import math
from datetime import datetime, timezone

from app.core.firebase import get_database
from app.schemas.eta import ETAResponse, RouteETAResponse, StopETA
from app.services.route_config import (
    MAX_ETA_SPEED_KMPH,
    MAX_FUTURE_GPS_SECONDS,
    MAX_GPS_AGE_SECONDS,
    ROUTE_CORRIDOR_M,
    ROUTE_STOPS,
)
from app.services.route_service import (
    distance_to_route_m,
    route_position,
    upcoming_stops,
)


def _unavailable(bus_id: str, stop_id: str = "") -> ETAResponse:
    return ETAResponse(
        bus_id=bus_id,
        stop_id=stop_id,
        status="unavailable",
    )


def _get_validated_location(bus_id: str) -> dict | None:
    """Read fresh, valid GPS coordinates and optional speed from Firebase."""
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
        return None

    try:
        latitude = float(location["latitude"])
        longitude = float(location["longitude"])
        timestamp = datetime.fromisoformat(
            str(location["timestamp"]).replace("Z", "+00:00")
        )
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        return None

    age_seconds = (
        datetime.now(timezone.utc)
        - timestamp.astimezone(timezone.utc)
    ).total_seconds()

    if (
        age_seconds < -MAX_FUTURE_GPS_SECONDS
        or age_seconds > MAX_GPS_AGE_SECONDS
    ):
        return None

    speed_kmph = None
    raw_speed = location.get("speed_kmph")

    if raw_speed is not None:
        try:
            candidate = float(raw_speed)
            if (
                math.isfinite(candidate)
                and 0 <= candidate <= MAX_ETA_SPEED_KMPH
            ):
                speed_kmph = candidate
        except (TypeError, ValueError):
            pass

    return {
        "latitude": latitude,
        "longitude": longitude,
        "speed_kmph": speed_kmph,
    }


def _route_location_is_valid(location: dict) -> bool:
    """Check whether the GPS coordinates lie within the route corridor."""
    return (
        distance_to_route_m(
            location["latitude"],
            location["longitude"],
        )
        <= ROUTE_CORRIDOR_M
    )


def _seconds_for_distance(
    distance_m: float,
    speed_kmph: float | None,
) -> int | None:
    """Return no ETA when speed is missing or the bus is stopped."""
    if speed_kmph is None or speed_kmph <= 0:
        return None
    if distance_m <= 0:
        return 0
    return round(distance_m / (speed_kmph / 3.6))


def estimate_route_arrivals(bus_id: str) -> RouteETAResponse:
    """Return route progress, upcoming stops, distances, and possible ETAs."""
    location = _get_validated_location(bus_id)

    if location is None or not _route_location_is_valid(location):
        return RouteETAResponse(
            bus_id=bus_id,
            status="unavailable",
        )

    latitude = location["latitude"]
    longitude = location["longitude"]
    speed_kmph = location["speed_kmph"]

    position = route_position(latitude, longitude)
    stops = upcoming_stops(latitude, longitude)

    upcoming = [
        StopETA(
            stop_id=stop["stop_id"],
            name=stop["name"],
            latitude=stop["latitude"],
            longitude=stop["longitude"],
            distance_remaining_m=round(
                stop["distance_remaining_m"], 2
            ),
            eta_seconds=_seconds_for_distance(
                stop["distance_remaining_m"],
                speed_kmph,
            ),
        )
        for stop in stops
    ]

    total_route_m = position["total_route_m"]
    along_route_m = position["along_route_m"]

    progress = (
        min(1.0, max(0.0, along_route_m / total_route_m))
        if total_route_m > 0
        else 0.0
    )

    return RouteETAResponse(
        bus_id=bus_id,
        status="available",
        route_progress_fraction=round(progress, 6),
        distance_remaining_m=round(
            max(0.0, total_route_m - along_route_m), 2
        ),
        next_stop_id=stops[0]["stop_id"] if stops else None,
        upcoming_stops=upcoming,
    )


def estimate_arrival(bus_id: str, stop_id: str) -> ETAResponse:
    """Estimate arrival at one configured stop on the complete route."""
    normalized_stop_id = stop_id.strip().upper()

    target = next(
        (
            stop for stop in ROUTE_STOPS
            if stop["stop_id"].upper() == normalized_stop_id
        ),
        None,
    )
    if target is None:
        raise ValueError(f"Unknown stop: {stop_id}")

    location = _get_validated_location(bus_id)
    if location is None or not _route_location_is_valid(location):
        return _unavailable(bus_id, normalized_stop_id)

    stops = upcoming_stops(
        location["latitude"],
        location["longitude"],
    )
    upcoming_target = next(
        (
            stop for stop in stops
            if stop["stop_id"].upper() == normalized_stop_id
        ),
        None,
    )

    if upcoming_target is None:
        return _unavailable(bus_id, normalized_stop_id)

    distance_m = round(upcoming_target["distance_remaining_m"], 2)
    eta_seconds = _seconds_for_distance(
        upcoming_target["distance_remaining_m"],
        location["speed_kmph"],
    )

    return ETAResponse(
        bus_id=bus_id,
        stop_id=normalized_stop_id,
        eta_seconds=eta_seconds,
        distance_m=distance_m,
        status="available" if eta_seconds is not None else "unavailable",
    )
