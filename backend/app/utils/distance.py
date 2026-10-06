from math import asin, cos, radians, sin, sqrt


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two coordinates in meters."""
    earth_radius_meters = 6_371_000
    latitude_delta = radians(lat2 - lat1)
    longitude_delta = radians(lon2 - lon1)
    value = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(longitude_delta / 2) ** 2
    )
    return 2 * earth_radius_meters * asin(sqrt(value))