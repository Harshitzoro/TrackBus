
import pytest

from app.services.notification_service import (
    clear_notification_state,
    evaluate_eta_notification,
)


@pytest.fixture(autouse=True)
def reset_notification_state():
    clear_notification_state()


def test_notification_triggers_at_threshold():
    result = evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_01", 900, now=1000
    )

    assert result is not None
    assert result["event"] == "bus_approaching"


def test_notification_does_not_trigger_above_threshold():
    result = evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_01", 901, now=1000
    )

    assert result is None


@pytest.mark.parametrize("eta", [None, -1])
def test_notification_ignores_unavailable_or_invalid_eta(eta):
    assert evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_01", eta, now=1000
    ) is None


def test_duplicate_notification_is_suppressed_for_15_minutes():
    first = evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_01", 600, now=1000
    )
    second = evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_01", 500, now=1500
    )

    assert first is not None
    assert second is None


def test_notification_can_trigger_after_cooldown():
    evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_01", 600, now=1000
    )

    result = evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_01", 500, now=1900
    )

    assert result is not None


def test_cooldown_is_separate_for_each_stop():
    evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_01", 600, now=1000
    )

    result = evaluate_eta_notification(
        "student-1", "BUS_001", "STOP_02", 600, now=1001
    )

    assert result is not None


def test_empty_identifiers_are_rejected():
    with pytest.raises(ValueError):
        evaluate_eta_notification(
            "", "BUS_001", "STOP_01", 600, now=1000
        )
