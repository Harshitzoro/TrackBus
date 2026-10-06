from app.schemas.eta import ETAResponse


def test_eta_can_represent_unavailable_estimate() -> None:
    result = ETAResponse(bus_id="BUS-001", stop_id="STOP-001", status="unavailable")

    assert result.eta_seconds is None