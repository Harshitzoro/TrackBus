
from datetime import datetime, timedelta, timezone

from app.services import notification_store as store


class FakeRef:
    def __init__(self, db, path=()):
        self.db = db
        self.path = path

    def child(self, key):
        return FakeRef(self.db, self.path + (key,))

    def get(self):
        value = self.db
        for key in self.path:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value

    def set(self, value):
        target = self.db
        for key in self.path[:-1]:
            target = target.setdefault(key, {})
        target[self.path[-1]] = value


def setup_fake_database(monkeypatch):
    fake_data = {}
    monkeypatch.setattr(
        store,
        "get_database",
        lambda: FakeRef(fake_data),
    )
    return fake_data


def test_no_record_means_notification_is_due(monkeypatch):
    setup_fake_database(monkeypatch)

    assert store.notification_is_due(
        "student-1", "BUS_001", "STOP_01"
    )


def test_cooldown_blocks_notification_within_15_minutes(monkeypatch):
    data = setup_fake_database(monkeypatch)
    now = datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)

    store.record_notification_sent(
        "student-1", "BUS_001", "STOP_01", now
    )

    assert not store.notification_is_due(
        "student-1", "BUS_001", "STOP_01",
        now + timedelta(minutes=10),
    )

    assert store.notification_is_due(
        "student-1", "BUS_001", "STOP_01",
        now + timedelta(minutes=15),
    )


def test_cooldown_is_separate_per_stop(monkeypatch):
    setup_fake_database(monkeypatch)
    now = datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)

    store.record_notification_sent(
        "student-1", "BUS_001", "STOP_01", now
    )

    assert store.notification_is_due(
        "student-1", "BUS_001", "STOP_02", now
    )


def test_record_survives_new_database_reference(monkeypatch):
    data = setup_fake_database(monkeypatch)
    now = datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)

    store.record_notification_sent(
        "student-1", "BUS_001", "STOP_01", now
    )

    # A new reference sees the same backing database state.
    monkeypatch.setattr(
        store, "get_database", lambda: FakeRef(data)
    )

    assert not store.notification_is_due(
        "student-1", "BUS_001", "STOP_01",
        now + timedelta(minutes=5),
    )
