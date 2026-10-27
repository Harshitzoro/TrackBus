
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.eta import ETAResponse
from app.services import eta_service
from app.services.route_config import ROUTE_START, ROUTE_STOPS

client = TestClient(app)


def fresh_location(
    latitude: float,
    longitude: float,
    speed_kmph: float | None = 18.0,
) -> dict:
    location = {
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if speed_kmph is not None:
        location["speed_kmph"] = speed_kmph
    return location


def patch_location(monkeypatch, location) -> None:
    class FakeReference:
        def child(self, _key):
            return self

        def get(self):
            return location

    monkeypatch.setattr(
        eta_service, "get_database", lambda: FakeReference()
    )


def test_eta_can_represent_unavailable_estimate():
    result = ETAResponse(
        bus_id="BUS_001",
        stop_id="STOP_01",
        status="unavailable",
    )
    assert result.eta_seconds is None
    assert result.distance_m is None


def test_complete_route_has_sixteen_unique_stops():
    assert ROUTE_START["stop_id"] == "CP_TOWER"
    assert len(ROUTE_STOPS) == 16
    assert ROUTE_STOPS[0]["stop_id"] == "STOP_01"
    assert ROUTE_STOPS[-1]["stop_id"] == "STOP_16"
    ids = [stop["stop_id"] for stop in ROUTE_STOPS]
    assert len(ids) == len(set(ids))


def test_eta_returns_unavailable_without_bus_location(monkeypatch):
    patch_location(monkeypatch, None)

    result = eta_service.estimate_arrival("BUS_001", "STOP_01")

    assert result.status == "unavailable"
    assert result.eta_seconds is None


def test_eta_calculates_for_fresh_bus_location(monkeypatch):
    patch_location(
        monkeypatch,
        fresh_location(
            ROUTE_START["latitude"],
            ROUTE_START["longitude"],
        ),
    )

    result = eta_service.estimate_arrival("BUS_001", "STOP_01")

    assert result.status == "available"
    assert result.distance_m is not None
    assert result.distance_m > 0
    assert result.eta_seconds is not None
    assert result.eta_seconds > 0


@pytest.mark.parametrize("speed", [0.0, None])
def test_eta_unavailable_when_speed_is_zero_or_missing(
    monkeypatch, speed
):
    patch_location(
        monkeypatch,
        fresh_location(
            ROUTE_START["latitude"],
            ROUTE_START["longitude"],
            speed,
        ),
    )

    result = eta_service.estimate_arrival("BUS_001", "STOP_01")

    assert result.status == "unavailable"
    assert result.eta_seconds is None


def test_eta_unavailable_when_location_is_stale(monkeypatch):
    location = fresh_location(
        ROUTE_START["latitude"],
        ROUTE_START["longitude"],
    )
    location["timestamp"] = (
        datetime.now(timezone.utc) - timedelta(minutes=10)
    ).isoformat()
    patch_location(monkeypatch, location)

    result = eta_service.estimate_arrival("BUS_001", "STOP_01")

    assert result.status == "unavailable"


def test_eta_rejects_unknown_stop():
    with pytest.raises(ValueError, match="Unknown stop"):
        eta_service.estimate_arrival("BUS_001", "STOP_UNKNOWN")


def test_eta_endpoint_returns_estimate(monkeypatch):
    patch_location(
        monkeypatch,
        fresh_location(
            ROUTE_START["latitude"],
            ROUTE_START["longitude"],
        ),
    )

    response = client.get("/api/v1/eta/BUS_001/STOP_01")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert data["eta_seconds"] is not None
    assert data["distance_m"] > 0


def test_eta_to_first_stop_unavailable_when_bus_has_passed_it(
    monkeypatch,
):
    last_stop = ROUTE_STOPS[-1]
    patch_location(
        monkeypatch,
        fresh_location(
            last_stop["latitude"],
            last_stop["longitude"],
        ),
    )

    result = eta_service.estimate_arrival("BUS_001", "STOP_01")

    assert result.status == "unavailable"


def test_route_eta_endpoint_returns_route_response(monkeypatch):
    patch_location(
        monkeypatch,
        fresh_location(
            ROUTE_START["latitude"],
            ROUTE_START["longitude"],
        ),
    )

    response = client.get("/api/v1/eta/BUS_001")

    assert response.status_code == 200
    data = response.json()
    assert data["bus_id"] == "BUS_001"
    assert data["status"] == "available"
    assert data["next_stop_id"] == "STOP_01"
    assert isinstance(data["upcoming_stops"], list)
