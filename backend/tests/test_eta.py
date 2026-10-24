
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.eta import ETAResponse
from app.services import eta_service
from app.services.route_config import STOP_COORDINATES

client = TestClient(app)


def fresh_location(
    latitude: float,
    longitude: float,
    speed_kmph: float = 18.0,
) -> dict[str, object]:
    return {
        "latitude": latitude,
        "longitude": longitude,
        "speed_kmph": speed_kmph,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def patch_location(monkeypatch, location) -> None:
    class FakeReference:
        def child(self, _key):
            return self

        def get(self):
            return location

    monkeypatch.setattr(
        eta_service,
        "get_database",
        lambda: FakeReference(),
    )


def test_eta_can_represent_unavailable_estimate():
    result = ETAResponse(
        bus_id="BUS_001",
        stop_id="STOP_A",
        status="unavailable",
    )

    assert result.eta_seconds is None
    assert result.distance_m is None


def test_real_stop_coordinates_are_configured():
    assert STOP_COORDINATES["STOP_A"] == (
        25.1386742,
        75.8260137,
    )
    assert STOP_COORDINATES["STOP_B"] == (
        25.1421876,
        75.8284360,
    )


def test_eta_returns_unavailable_without_bus_location(monkeypatch):
    patch_location(monkeypatch, None)

    result = eta_service.estimate_arrival("BUS_001", "STOP_A")

    assert result.status == "unavailable"
    assert result.eta_seconds is None


def test_eta_calculates_for_fresh_bus_location(monkeypatch):
    latitude, longitude = STOP_COORDINATES["STOP_A"]
    # Place the simulated bus near the middle of the straight route.
    lat_b, lon_b = STOP_COORDINATES["STOP_B"]
    latitude = (latitude + lat_b) / 2
    longitude = (longitude + lon_b) / 2

    patch_location(
        monkeypatch,
        fresh_location(latitude, longitude),
    )

    result = eta_service.estimate_arrival("BUS_001", "STOP_B")

    assert result.status == "available"
    assert result.distance_m is not None
    assert result.distance_m > 0
    assert result.eta_seconds is not None
    assert result.eta_seconds > 0


def test_eta_unavailable_when_speed_is_zero(monkeypatch):
    latitude, longitude = STOP_COORDINATES["STOP_A"]
    patch_location(
        monkeypatch,
        fresh_location(latitude, longitude, speed_kmph=0),
    )

    result = eta_service.estimate_arrival("BUS_001", "STOP_A")

    assert result.status == "unavailable"


def test_eta_unavailable_when_speed_is_missing(monkeypatch):
    latitude, longitude = STOP_COORDINATES["STOP_A"]
    location = fresh_location(latitude, longitude)
    location.pop("speed_kmph")
    patch_location(monkeypatch, location)

    result = eta_service.estimate_arrival("BUS_001", "STOP_A")

    assert result.status == "unavailable"


def test_eta_unavailable_when_location_is_stale(monkeypatch):
    latitude, longitude = STOP_COORDINATES["STOP_A"]
    location = fresh_location(latitude, longitude)
    location["timestamp"] = (
        datetime.now(timezone.utc) - timedelta(minutes=10)
    ).isoformat()
    patch_location(monkeypatch, location)

    result = eta_service.estimate_arrival("BUS_001", "STOP_A")

    assert result.status == "unavailable"


def test_eta_rejects_unknown_stop():
    with pytest.raises(ValueError, match="Unknown stop"):
        eta_service.estimate_arrival("BUS_001", "STOP_UNKNOWN")


def test_eta_endpoint_returns_estimate(monkeypatch):
    lat_a, lon_a = STOP_COORDINATES["STOP_A"]
    lat_b, lon_b = STOP_COORDINATES["STOP_B"]

    patch_location(
        monkeypatch,
        fresh_location(
            (lat_a + lat_b) / 2,
            (lon_a + lon_b) / 2,
        ),
    )

    response = client.get("/api/v1/eta/BUS_001/STOP_B")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert data["eta_seconds"] is not None
    assert data["distance_m"] > 0
def test_eta_to_stop_a_unavailable_after_bus_has_progressed(monkeypatch):
    lat_a, lon_a = STOP_COORDINATES["STOP_A"]
    lat_b, lon_b = STOP_COORDINATES["STOP_B"]

    # Simulate a bus 25% of the way from STOP_A to STOP_B.
    latitude = lat_a + 0.25 * (lat_b - lat_a)
    longitude = lon_a + 0.25 * (lon_b - lon_a)

    patch_location(
        monkeypatch,
        fresh_location(latitude, longitude),
    )

    result = eta_service.estimate_arrival("BUS_001", "STOP_A")

    assert result.status == "unavailable"
    assert result.eta_seconds is None


def test_eta_to_stop_b_available_mid_route(monkeypatch):
    lat_a, lon_a = STOP_COORDINATES["STOP_A"]
    lat_b, lon_b = STOP_COORDINATES["STOP_B"]

    patch_location(
        monkeypatch,
        fresh_location(
            (lat_a + lat_b) / 2,
            (lon_a + lon_b) / 2,
        ),
    )

    result = eta_service.estimate_arrival("BUS_001", "STOP_B")

    assert result.status == "available"
    assert result.eta_seconds is not None
    assert result.eta_seconds > 0