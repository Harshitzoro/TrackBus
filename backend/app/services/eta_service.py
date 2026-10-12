import math
from app.core.firebase import get_database
from app.schemas.eta import ETAResponse
# Temporary 100-metre simulation route.
# These coordinates must match scripts/simulate_route.py.
START_LAT = 26.9124
START_LON = 75.7873

ROUTE_LENGTH_M = 100.0
WALKING_SPEED_KMH = 4.0

STOP_DISTANCES_M = {
    "STOP_A": 0.0,
    "STOP_B": 50.0,
    "STOP_C": 100.0,
}


def coordinates_at_distance(
    distance_m: float,
) -> tuple[float, float]:
    """Return coordinates along the simulated eastward route."""
    distance_m = max(0.0, min(distance_m, ROUTE_LENGTH_M))

    meters_per_degree_lon = (
        111320.0 * math.cos(math.radians(START_LAT))
    )

    latitude = START_LAT
    longitude = START_LON + distance_m / meters_per_degree_lon

    return latitude, longitude


def distance_between_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate the great-circle distance between two coordinates."""
    earth_radius_m = 6_371_000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )

    a = min(1.0, max(0.0, a))
    return 2 * earth_radius_m * math.asin(math.sqrt(a))


def estimate_arrival(
    bus_id: str,
    stop_id: str,
) -> ETAResponse:
    """Estimate arrival time on the temporary simulation route."""
    normalized_stop_id = stop_id.upper()

    if normalized_stop_id not in STOP_DISTANCES_M:
        raise ValueError(f"Unknown simulation stop: {stop_id}")

    try:
        location = (
            get_database()
            .child("buses")
            .child(bus_id)
            .child("location")
            .get()
        )
    except Exception as exc:
        raise RuntimeError("Could not read bus location from Firebase") from exc

    if not isinstance(location, dict):
        return ETAResponse(
            bus_id=bus_id,
            stop_id=normalized_stop_id,
            status="unavailable",
        )

    try:
        latitude = float(location["latitude"])
        longitude = float(location["longitude"])
    except (KeyError, TypeError, ValueError):
        return ETAResponse(
            bus_id=bus_id,
            stop_id=normalized_stop_id,
            status="unavailable",
        )

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        return ETAResponse(
            bus_id=bus_id,
            stop_id=normalized_stop_id,
            status="unavailable",
        )

    stop_lat, stop_lon = coordinates_at_distance(
        STOP_DISTANCES_M[normalized_stop_id]
    )

    distance_m = distance_between_m(
        latitude,
        longitude,
        stop_lat,
        stop_lon,
    )

    speed_mps = WALKING_SPEED_KMH / 3.6
    eta_seconds = round(distance_m / speed_mps)

    return ETAResponse(
        bus_id=bus_id,
        stop_id=normalized_stop_id,
        eta_seconds=eta_seconds,
        distance_m=round(distance_m, 2),
        status="available",
    )
