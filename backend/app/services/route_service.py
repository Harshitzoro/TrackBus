
"""Geometry helpers for the TrackBus prototype route."""

import math

from app.services.route_config import STOP_COORDINATES
from app.utils.distance import haversine_meters


def distance_to_route_m(latitude: float, longitude: float) -> float:
    """Estimate distance to the straight segment between STOP_A and STOP_B.

    This uses a local planar projection, suitable for this short prototype
    route. It does not represent the actual road geometry.
    """
    (lat_a, lon_a) = STOP_COORDINATES["STOP_A"]
    (lat_b, lon_b) = STOP_COORDINATES["STOP_B"]

    reference_lat = math.radians((lat_a + lat_b) / 2)
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = (
        111_320.0 * math.cos(reference_lat)
    )

    ax = lon_a * meters_per_degree_lon
    ay = lat_a * meters_per_degree_lat
    bx = lon_b * meters_per_degree_lon
    by = lat_b * meters_per_degree_lat
    px = longitude * meters_per_degree_lon
    py = latitude * meters_per_degree_lat

    abx = bx - ax
    aby = by - ay
    length_squared = abx * abx + aby * aby

    if length_squared == 0:
        return haversine_meters(latitude, longitude, lat_a, lon_a)

    projection = ((px - ax) * abx + (py - ay) * aby) / length_squared
    projection = max(0.0, min(1.0, projection))

    closest_x = ax + projection * abx
    closest_y = ay + projection * aby

    return math.hypot(px - closest_x, py - closest_y)


def distance_to_stop_m(
    latitude: float,
    longitude: float,
    stop_id: str,
) -> float:
    """Calculate straight-line distance from a GPS point to a stop."""
    normalized_stop_id = stop_id.upper()
    if normalized_stop_id not in STOP_COORDINATES:
        raise ValueError(f"Unknown stop: {stop_id}")

    stop_lat, stop_lon = STOP_COORDINATES[normalized_stop_id]
    return haversine_meters(
        latitude, longitude, stop_lat, stop_lon
    )


def route_progress_fraction(latitude: float, longitude: float) -> float:
    """Return projected progress from STOP_A (0) to STOP_B (1).

    Values are clamped to the segment endpoints.
    """
    (lat_a, lon_a) = STOP_COORDINATES["STOP_A"]
    (lat_b, lon_b) = STOP_COORDINATES["STOP_B"]

    reference_lat = math.radians((lat_a + lat_b) / 2)
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = (
        111_320.0 * math.cos(reference_lat)
    )

    ax = lon_a * meters_per_degree_lon
    ay = lat_a * meters_per_degree_lat
    bx = lon_b * meters_per_degree_lon
    by = lat_b * meters_per_degree_lat
    px = longitude * meters_per_degree_lon
    py = latitude * meters_per_degree_lat

    abx = bx - ax
    aby = by - ay
    length_squared = abx * abx + aby * aby

    if length_squared == 0:
        return 0.0

    fraction = ((px - ax) * abx + (py - ay) * aby) / length_squared
    return max(0.0, min(1.0, fraction))
