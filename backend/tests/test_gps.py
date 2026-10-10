from unittest.mock import patch
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.gps import GPSUpdate


client = TestClient(app)


# --------------------------------------------------
# GPS Schema Tests
# --------------------------------------------------

def test_gps_update_accepts_valid_coordinates() -> None:
    update = GPSUpdate(
        bus_id="BUS-001",
        latitude=12.9,
        longitude=77.5,
        timestamp=datetime.now(timezone.utc),
    )

    assert update.bus_id == "BUS-001"
    assert update.latitude == 12.9
    assert update.longitude == 77.5


def test_gps_update_rejects_out_of_range_coordinates() -> None:
    with pytest.raises(ValidationError):
        GPSUpdate(
            bus_id="BUS-001",
            latitude=91,
            longitude=77.5,
            timestamp=datetime.now(timezone.utc),
        )


def test_gps_update_rejects_invalid_longitude() -> None:
    with pytest.raises(ValidationError):
        GPSUpdate(
            bus_id="BUS-001",
            latitude=12.9,
            longitude=181,
            timestamp=datetime.now(timezone.utc),
        )


def test_gps_update_rejects_empty_bus_id() -> None:
    with pytest.raises(ValidationError):
        GPSUpdate(
            bus_id="",
            latitude=12.9,
            longitude=77.5,
            timestamp=datetime.now(timezone.utc),
        )


# --------------------------------------------------
# GPS API Endpoint Tests
# --------------------------------------------------

@patch("app.api.routes.gps.save_gps_update")
def test_gps_endpoint_accepts_valid_update(mock_save) -> None:
    mock_save.return_value = {
        "status": "saved",
        "bus_id": "BUS-001",
        "location": {
            "latitude": 26.9124,
            "longitude": 75.7873,
            "timestamp": "2026-10-10T12:00:00+00:00",
        },
    }

    response = client.post(
        "/api/v1/gps",
        json={
            "bus_id": "BUS-001",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "timestamp": "2026-10-10T12:00:00Z",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["bus_id"] == "BUS-001"
    assert data["location"]["latitude"] == 26.9124
    assert data["location"]["longitude"] == 75.7873
    mock_save.assert_called_once()


def test_gps_endpoint_rejects_invalid_latitude() -> None:
    response = client.post(
        "/api/v1/gps",
        json={
            "bus_id": "BUS-001",
            "latitude": 91,
            "longitude": 75.7873,
            "timestamp": "2026-10-10T12:00:00Z",
        },
    )

    assert response.status_code == 422


def test_gps_endpoint_rejects_invalid_longitude() -> None:
    response = client.post(
        "/api/v1/gps",
        json={
            "bus_id": "BUS-001",
            "latitude": 26.9124,
            "longitude": 181,
            "timestamp": "2026-10-10T12:00:00Z",
        },
    )

    assert response.status_code == 422


def test_gps_endpoint_rejects_missing_bus_id() -> None:
    response = client.post(
        "/api/v1/gps",
        json={
            "latitude": 26.9124,
            "longitude": 75.7873,
            "timestamp": "2026-10-10T12:00:00Z",
        },
    )

    assert response.status_code == 422
