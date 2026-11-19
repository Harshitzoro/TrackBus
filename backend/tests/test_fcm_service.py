
import pytest

from app.services import fcm_service


def test_send_builds_and_submits_fcm_message(monkeypatch):
    captured = {}

    def fake_send(message):
        captured["message"] = message
        return "mock-message-id"

    monkeypatch.setattr(fcm_service.messaging, "send", fake_send)

    result = fcm_service.send_bus_approaching_notification(
        token="fake-token-for-tests",
        bus_id="BUS_001",
        stop_id="STOP_02",
        eta_seconds=601,
    )

    assert result == "mock-message-id"
    message = captured["message"]
    assert message.token == "fake-token-for-tests"
    assert message.notification.title == "Your bus is approaching"
    assert message.data["event"] == "bus_approaching"
    assert message.data["eta_seconds"] == "601"


@pytest.mark.parametrize(
    "token,bus_id,stop_id,eta",
    [
        ("", "BUS_001", "STOP_02", 60),
        ("fake-token", "", "STOP_02", 60),
        ("fake-token", "BUS_001", "", 60),
        ("fake-token", "BUS_001", "STOP_02", -1),
    ],
)
def test_invalid_notification_arguments_are_rejected(
    token, bus_id, stop_id, eta
):
    with pytest.raises(ValueError):
        fcm_service.send_bus_approaching_notification(
            token, bus_id, stop_id, eta
        )
