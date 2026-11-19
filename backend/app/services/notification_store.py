
"""Firebase-backed persistent notification cooldown storage."""

import hashlib
from datetime import datetime, timedelta, timezone

from app.core.firebase import get_database

COOLDOWN_SECONDS = 15 * 60


def _cooldown_key(student_id: str, bus_id: str, stop_id: str) -> str:
    """Create a stable key without exposing IDs in the Firebase path."""
    raw_key = f"{student_id}|{bus_id}|{stop_id}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def notification_is_due(
    student_id: str,
    bus_id: str,
    stop_id: str,
    now: datetime | None = None,
) -> bool:
    """Check whether the cooldown has elapsed without modifying state."""
    current = now or datetime.now(timezone.utc)
    key = _cooldown_key(student_id, bus_id, stop_id)

    record = (
        get_database()
        .child("notification_cooldowns")
        .child(key)
        .get()
    )

    if not isinstance(record, dict):
        return True

    last_sent_raw = record.get("last_sent_at")
    if not isinstance(last_sent_raw, str):
        return True

    try:
        last_sent = datetime.fromisoformat(
            last_sent_raw.replace("Z", "+00:00")
        )
        if last_sent.tzinfo is None:
            last_sent = last_sent.replace(tzinfo=timezone.utc)
    except ValueError:
        return True

    elapsed = (current - last_sent.astimezone(timezone.utc)).total_seconds()
    return elapsed >= COOLDOWN_SECONDS


def record_notification_sent(
    student_id: str,
    bus_id: str,
    stop_id: str,
    now: datetime | None = None,
) -> None:
    """Record a successfully sent notification for future cooldown checks."""
    current = now or datetime.now(timezone.utc)
    key = _cooldown_key(student_id, bus_id, stop_id)

    (
        get_database()
        .child("notification_cooldowns")
        .child(key)
        .set({
            "last_sent_at": current.astimezone(timezone.utc).isoformat(),
            "student_id": student_id,
            "bus_id": bus_id,
            "stop_id": stop_id,
        })
    )
