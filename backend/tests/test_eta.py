import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.eta import ETAResponse
from app.services import eta_service

client = TestClient(app)

def test_eta_can_represent_unavailable_estimate() -> None:
    result = ETAResponse(
        bus_id="BUS-001",
        stop_id="STOP-001",
        status="unavailable",
    )

    assert result.eta_seconds is None
    assert result.distance_m is None


def test_distance_between_identical_coordinates_is_zero() -> None:
    distance = eta_service.distance_between_m(
        26.9124, 75.7873, 26.9124, 75.7873
    )

    assert distance == pytest.approx(0.0)


def test_eta_returns_unavailable_without_bus_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeReference:
        def child(self, _key: str) -> "FakeReference":
            return self

        def get(self) -> None:
            return None

    monkeypatch.setattr(
        eta_service,
        "get_database",
        lambda: FakeReference(),
    )

    result = eta_service.estimate_arrival("BUS_SIM_001", "STOP_B")

    assert result.status == "unavailable"
    assert result.eta_seconds is None


def test_eta_calculates_for_bus_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    latitude, longitude = eta_service.coordinates_at_distance(25.0)

    class FakeReference:
        def child(self, _key: str) -> "FakeReference":
            return self

        def get(self) -> dict[str, float]:
            return {
                "latitude": latitude,
                "longitude": longitude,
            }

    monkeypatch.setattr(
        eta_service,
        "get_database",
        lambda: FakeReference(),
    )

    result = eta_service.estimate_arrival("BUS_SIM_001", "STOP_B")

    assert result.status == "available"
    assert result.distance_m == pytest.approx(25.0, abs=0.5)
    assert result.eta_seconds == pytest.approx(23, abs=1)


def test_eta_rejects_unknown_stop() -> None:
    with pytest.raises(ValueError, match="Unknown simulation stop"):
        eta_service.estimate_arrival("BUS_SIM_001", "STOP_UNKNOWN")


def test_eta_endpoint_returns_estimate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    latitude, longitude = eta_service.coordinates_at_distance(25.0)

    class FakeReference:
        def child(self, _key: str) -> "FakeReference":
            return self

        def get(self) -> dict[str, float]:
            return {
                "latitude": latitude,
                "longitude": longitude,
            }

    monkeypatch.setattr(
        eta_service,
        "get_database",
        lambda: FakeReference(),
    )

    response = client.get("/api/v1/eta/BUS_SIM_001/STOP_B")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert data["eta_seconds"] is not None
    assert data["distance_m"] == pytest.approx(25.0, abs=0.5)
