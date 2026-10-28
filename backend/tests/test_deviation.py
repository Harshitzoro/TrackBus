
from datetime import datetime, timedelta, timezone

import pytest

from app.services import deviation_service
from app.services.route_config import ROUTE_START, ROUTE_STOPS
from app.services.route_service import (
    distance_to_route_m,
    distance_to_stop_m,
    route_progress_fraction,
)


def _fresh_location(latitude: float, longitude: float) -> dict:
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


def test_distance_between_identical_coordinates_is_zero():
    from app.utils.distance import haversine_meters

    assert haversine_meters(12.9, 77.5, 12.9, 77.5) == 0


def test_route_start_is_at_start_of_route():
    latitude = ROUTE_START["latitude"]
    longitude = ROUTE_START["longitude"]

    assert distance_to_route_m(latitude, longitude) == pytest.approx(0)
    assert route_progress_fraction(latitude, longitude) == pytest.approx(0)


def test_final_stop_is_at_end_of_route():
    final_stop = ROUTE_STOPS[-1]
    latitude = final_stop["latitude"]
    longitude = final_stop["longitude"]

    assert distance_to_route_m(latitude, longitude) == pytest.approx(0)
    assert route_progress_fraction(latitude, longitude) == pytest.approx(1)
    assert distance_to_stop_m(
        latitude, longitude, final_stop["stop_id"]
    ) == pytest.approx(0)


def test_all_configured_stops_have_unique_ids():
    ids = [stop["stop_id"] for stop in ROUTE_STOPS]
    assert len(ids) == 16
    assert len(ids) == len(set(ids))


def test_point_far_from_route_has_large_cross_track_distance():
    latitude = ROUTE_START["latitude"] + 0.01
    longitude = ROUTE_START["longitude"]

    assert distance_to_route_m(latitude, longitude) > 100


def test_unknown_stop_is_rejected():
    with pytest.raises(ValueError, match="Unknown stop"):
        distance_to_stop_m(25.138, 75.827, "STOP_UNKNOWN")


def test_deviation_reports_on_route_at_start(monkeypatch):
    _patch_firebase_location(
        monkeypatch,
        _fresh_location(
            ROUTE_START["latitude"],
            ROUTE_START["longitude"],
        ),
    )

    result = deviation_service.check_route_deviation("BUS_001")

    assert result["status"] == "on_route"
    assert result["distance_from_route_m"] == pytest.approx(0)


def test_deviation_reports_deviated_for_far_position(monkeypatch):
    _patch_firebase_location(
        monkeypatch,
        _fresh_location(
            ROUTE_START["latitude"] + 0.01,
            ROUTE_START["longitude"],
        ),
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
    location = _fresh_location(
        ROUTE_START["latitude"],
        ROUTE_START["longitude"],
    )
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

    _patch_firebase_location(
        monkeypatch,
        _fresh_location(
            ROUTE_START["latitude"],
            ROUTE_START["longitude"],
        ),
    )

    from app.core.auth import get_current_student

    app.dependency_overrides[get_current_student] = lambda: {
        "uid": "test-student-uid",
        "role": "Student",
        "bus_id": "BUS_001",
    }

    try:
        client = TestClient(app)
        response = client.get("/api/v1/deviation/BUS_001")
    finally:
        app.dependency_overrides.pop(get_current_student, None)

    assert response.status_code == 200
    assert response.json()["status"] == "on_route"
