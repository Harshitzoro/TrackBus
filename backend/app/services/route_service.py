
"""Route geometry and progress helpers for TrackBus."""

import math

from app.services.route_config import ROUTE_START, ROUTE_STOPS
from app.utils.distance import haversine_meters


def _route_points():
    """Return the configured start and ordered stops as coordinate pairs."""
    points = [
        (ROUTE_START["latitude"], ROUTE_START["longitude"]),
    ]
    points.extend(
        (stop["latitude"], stop["longitude"])
        for stop in ROUTE_STOPS
    )
    return points


def _segment_lengths(points):
    """Calculate straight-line distances between consecutive route points."""
    return [
        haversine_meters(lat1, lon1, lat2, lon2)
        for (lat1, lon1), (lat2, lon2)
        in zip(points, points[1:])
    ]


def route_cumulative_distances_m():
    """Distance from the route start to each configured stop."""
    points = _route_points()
    cumulative = [0.0]

    for length in _segment_lengths(points):
        cumulative.append(cumulative[-1] + length)

    return cumulative


def total_route_distance_m() -> float:
    """Return the configured route's approximate total distance."""
    return route_cumulative_distances_m()[-1]


def _project_to_segment(latitude, longitude, start, end):
    """Project a point onto one short segment in a local metre-based plane."""
    lat1, lon1 = start
    lat2, lon2 = end
    reference_lat = math.radians((lat1 + lat2) / 2)
    scale_x = 111_320.0 * math.cos(reference_lat)
    scale_y = 111_320.0

    ax, ay = lon1 * scale_x, lat1 * scale_y
    bx, by = lon2 * scale_x, lat2 * scale_y
    px, py = longitude * scale_x, latitude * scale_y

    dx, dy = bx - ax, by - ay
    length_squared = dx * dx + dy * dy

    if length_squared == 0:
        return 0.0, haversine_meters(
            latitude, longitude, lat1, lon1
        )

    fraction = ((px - ax) * dx + (py - ay) * dy) / length_squared
    fraction = max(0.0, min(1.0, fraction))

    nearest_x = ax + fraction * dx
    nearest_y = ay + fraction * dy

    distance = math.hypot(px - nearest_x, py - nearest_y)
    return fraction, distance


def route_position(latitude: float, longitude: float) -> dict:
    """Find the nearest route segment and estimate progress along the route."""
    points = _route_points()
    lengths = _segment_lengths(points)
    cumulative = route_cumulative_distances_m()

    best = None

    for index, (start, end) in enumerate(zip(points, points[1:])):
        fraction, cross_track_m = _project_to_segment(
            latitude, longitude, start, end
        )
        along_m = cumulative[index] + fraction * lengths[index]

        if best is None or cross_track_m < best["cross_track_m"]:
            best = {
                "segment_index": index,
                "segment_fraction": fraction,
                "along_route_m": along_m,
                "cross_track_m": cross_track_m,
                "total_route_m": cumulative[-1],
            }

    if best is None:
        raise ValueError("Route has no segments")

    return best


def distance_to_route_m(latitude: float, longitude: float) -> float:
    """Return distance from a GPS point to the nearest configured segment."""
    return route_position(latitude, longitude)["cross_track_m"]


def distance_to_stop_m(
    latitude: float,
    longitude: float,
    stop_id: str,
) -> float:
    """Calculate straight-line distance from a GPS point to a named stop."""
    normalized = stop_id.upper()

    for stop in ROUTE_STOPS:
        if stop["stop_id"].upper() == normalized:
            return haversine_meters(
                latitude,
                longitude,
                stop["latitude"],
                stop["longitude"],
            )

    raise ValueError(f"Unknown stop: {stop_id}")


def route_progress_fraction(latitude: float, longitude: float) -> float:
    """Return estimated progress from 0.0 to 1.0 along the configured route."""
    position = route_position(latitude, longitude)
    total = position["total_route_m"]

    if total <= 0:
        return 0.0

    return position["along_route_m"] / total


def upcoming_stops(latitude: float, longitude: float) -> list[dict]:
    """Return stops whose configured route distance is ahead of the bus."""
    position = route_position(latitude, longitude)
    cumulative = route_cumulative_distances_m()

    # The first cumulative position is the route start; stops follow it.
    result = []

    for index, stop in enumerate(ROUTE_STOPS, start=1):
        stop_along_m = cumulative[index]

        if stop_along_m > position["along_route_m"]:
            result.append({
                **stop,
                "distance_remaining_m": round(
                    stop_along_m - position["along_route_m"], 2
                ),
            })

    return result
