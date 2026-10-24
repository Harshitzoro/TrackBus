
import pytest

from app.services.route_config import STOP_COORDINATES
from app.services.route_service import (
    distance_to_route_m,
    distance_to_stop_m,
    route_progress_fraction,
)


def test_distance_between_identical_coordinates_is_zero():
    from app.utils.distance import haversine_meters

    assert haversine_meters(12.9, 77.5, 12.9, 77.5) == 0


def test_stop_a_is_at_start_of_route():
    latitude, longitude = STOP_COORDINATES["STOP_A"]

    assert distance_to_route_m(latitude, longitude) == pytest.approx(0)
    assert route_progress_fraction(latitude, longitude) == pytest.approx(0)
    assert distance_to_stop_m(latitude, longitude, "STOP_A") == pytest.approx(0)


def test_stop_b_is_at_end_of_route():
    latitude, longitude = STOP_COORDINATES["STOP_B"]

    assert distance_to_route_m(latitude, longitude) == pytest.approx(0)
    assert route_progress_fraction(latitude, longitude) == pytest.approx(1)
    assert distance_to_stop_m(latitude, longitude, "STOP_B") == pytest.approx(0)


def test_point_near_middle_has_middle_progress():
    lat_a, lon_a = STOP_COORDINATES["STOP_A"]
    lat_b, lon_b = STOP_COORDINATES["STOP_B"]

    latitude = (lat_a + lat_b) / 2
    longitude = (lon_a + lon_b) / 2

    assert route_progress_fraction(latitude, longitude) == pytest.approx(0.5)


def test_point_far_from_route_has_large_cross_track_distance():
    lat_a, lon_a = STOP_COORDINATES["STOP_A"]
    latitude = lat_a + 0.002
    longitude = lon_a

    assert distance_to_route_m(latitude, longitude) > 100


def test_unknown_stop_is_rejected():
    with pytest.raises(ValueError, match="Unknown stop"):
        distance_to_stop_m(25.138, 75.827, "STOP_UNKNOWN")

from datetime import datetime, timedelta, timezone

from app.services import deviation_service


def _fresh_location(
    latitude: float,
    longitude: float,
) -> dict:
    return {
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _patch_firebase_location(monkeypatch, location) -> None:
    class FakeReference:
        def child(self, _key):
            return self

        def get(self):
            return location

    monkeypatch.setattr(
        deviation_service,
        "get_database",
        lambda: FakeReference(),
    )


def test_deviation_reports_on_route_for_stop_a(monkeypatch):
    from app.services.route_config import STOP_COORDINATES

    latitude, longitude = STOP_COORDINATES["STOP_A"]
    _patch_firebase_location(
        monkeypatch,
        _fresh_location(latitude, longitude),
    )

    result = deviation_service.check_route_deviation("BUS_001")

    assert result["status"] == "on_route"
    assert result["distance_from_route_m"] == 0


def test_deviation_reports_deviated_for_far_position(monkeypatch):
    from app.services.route_config import STOP_COORDINATES

    latitude, longitude = STOP_COORDINATES["STOP_A"]
    _patch_firebase_location(
        monkeypatch,
        _fresh_location(latitude + 0.002, longitude),
    )

    result = deviation_service.check_route_deviation("BUS_001")

    assert result["status"] == "deviated"
    assert result["distance_from_route_m"] > result["threshold_m"]


def test_deviation_unavailable_when_location_missing(monkeypatch):
    _patch_firebase_location(monkeypatch, None)

    result = deviation_service.check_route_deviation("BUS_001")

    assert result["status"] == "unavailable"
    assert result["reason"] == "location_missing"


def test_deviation_unavailable_when_location_is_stale(monkeypatch):
    from app.services.route_config import STOP_COORDINATES

    latitude, longitude = STOP_COORDINATES["STOP_A"]
    location = _fresh_location(latitude, longitude)
    location["timestamp"] = (
        datetime.now(timezone.utc) - timedelta(minutes=10)
    ).isoformat()

    _patch_firebase_location(monkeypatch, location)

    result = deviation_service.check_route_deviation("BUS_001")

    assert result["status"] == "unavailable"
    assert result["reason"] == "stale_location"


def test_deviation_api_returns_status(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.route_config import STOP_COORDINATES

    latitude, longitude = STOP_COORDINATES["STOP_A"]
    _patch_firebase_location(
        monkeypatch,
        _fresh_location(latitude, longitude),
    )

    client = TestClient(app)
    response = client.get("/api/v1/deviation/BUS_001")

    assert response.status_code == 200
    assert response.json()["status"] == "on_route"
