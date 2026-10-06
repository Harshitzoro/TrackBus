from app.utils.distance import haversine_meters


def test_distance_between_identical_coordinates_is_zero() -> None:
    assert haversine_meters(12.9, 77.5, 12.9, 77.5) == 0