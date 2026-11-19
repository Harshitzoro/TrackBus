
"""ETA notification trigger logic with a 15-minute cooldown."""

from time import monotonic
from typing import Any

ETA_THRESHOLD_SECONDS = 15 * 60
NOTIFICATION_COOLDOWN_SECONDS = 15 * 60

# Prototype-only in-memory cooldown store.
# A persistent store is needed for multiple workers or restarts.
_last_sent_at: dict[tuple[str, str, str], float] = {}


def evaluate_eta_notification(
    student_id: str,
    bus_id: str,
    stop_id: str,
    eta_seconds: int | None,
    now: float | None = None,
) -> dict[str, Any] | None:
    """Return an alert event when due, otherwise return None."""

    if not student_id.strip() or not bus_id.strip() or not stop_id.strip():
        raise ValueError("Student, bus, and stop IDs are required")

    if eta_seconds is None or eta_seconds < 0:
        return None

    if eta_seconds > ETA_THRESHOLD_SECONDS:
        return None

    current_time = monotonic() if now is None else now
    key = (student_id, bus_id, stop_id)
    last_sent = _last_sent_at.get(key)

    if last_sent is not None:
        elapsed = current_time - last_sent
        if elapsed < NOTIFICATION_COOLDOWN_SECONDS:
            return None

    _last_sent_at[key] = current_time

    return {
        "student_id": student_id,
        "bus_id": bus_id,
        "stop_id": stop_id,
        "eta_seconds": eta_seconds,
        "event": "bus_approaching",
    }


def clear_notification_state() -> None:
    """Reset prototype cooldown state, primarily for tests."""
    _last_sent_at.clear()
