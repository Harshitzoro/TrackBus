
from types import SimpleNamespace

from app.workers import notification_worker as worker


class FakeRef:
    def __init__(self, data):
        self.data = data

    def child(self, key):
        return FakeRef(self.data.get(key) if isinstance(self.data, dict) else None)

    def get(self):
        return self.data


def student_profile(
    bus_id="BUS_001",
    stop_id="STOP_02",
    with_token=True,
):
    profile = {
        "role": "Student",
        "bus_id": bus_id,
        "stop_id": stop_id,
    }
    if with_token:
        profile["fcm_tokens"] = {
            "test-token-hash": {"token": "fake-fcm-token-for-tests"}
        }
    return profile


def setup_worker(monkeypatch, users, eta_seconds=600, status="available"):
    monkeypatch.setenv("TRACKBUS_NOTIFICATIONS_DRY_RUN", "true")
    monkeypatch.setattr(
        worker,
        "get_database",
        lambda: FakeRef({"users": users}),
    )
    monkeypatch.setattr(
        worker,
        "estimate_arrival",
        lambda bus_id, stop_id: SimpleNamespace(
            status=status,
            eta_seconds=eta_seconds,
        ),
    )
    monkeypatch.setattr(worker, "notification_is_due", lambda *args: True)

def enable_live_delivery(monkeypatch):
    monkeypatch.setenv("TRACKBUS_NOTIFICATIONS_DRY_RUN", "false")

def test_worker_logs_eligible_notification_in_dry_run(monkeypatch, caplog):
    caplog.set_level("INFO", logger="app.workers.notification_worker")
    setup_worker(
        monkeypatch,
        {"student-1": student_profile()},
        eta_seconds=600,
    )

    worker.check_student_notifications()

    assert "DRY RUN: notification eligible" in caplog.text
    assert "stop=STOP_02" in caplog.text


def test_worker_ignores_eta_above_15_minutes(monkeypatch, caplog):
    setup_worker(
        monkeypatch,
        {"student-1": student_profile()},
        eta_seconds=901,
    )

    worker.check_student_notifications()

    assert "notification eligible" not in caplog.text


def test_worker_ignores_unavailable_eta(monkeypatch, caplog):
    setup_worker(
        monkeypatch,
        {"student-1": student_profile()},
        eta_seconds=None,
        status="unavailable",
    )

    worker.check_student_notifications()

    assert "notification eligible" not in caplog.text


def test_worker_skips_student_without_token(monkeypatch, caplog):
    setup_worker(
        monkeypatch,
        {"student-1": student_profile(with_token=False)},
    )

    worker.check_student_notifications()

    assert "notification eligible" not in caplog.text


def test_worker_continues_after_one_student_fails(monkeypatch, caplog):
    caplog.set_level("INFO", logger="app.workers.notification_worker")
    users = {
        "student-bad": student_profile(),
        "student-good": student_profile(stop_id="STOP_03"),
    }
    setup_worker(monkeypatch, users)

    def fake_eta(bus_id, stop_id):
        if stop_id == "STOP_02":
            raise RuntimeError("simulated ETA failure")
        return SimpleNamespace(status="available", eta_seconds=600)

    monkeypatch.setattr(worker, "estimate_arrival", fake_eta)

    worker.check_student_notifications()

    assert "Failed to evaluate notification for one student profile" in caplog.text
    assert "stop=STOP_03" in caplog.text

def test_worker_sends_notification_and_records_cooldown(monkeypatch):
    setup_worker(monkeypatch, {"student-1": student_profile()})
    enable_live_delivery(monkeypatch)

    sent = []
    recorded = []

    monkeypatch.setattr(
        worker,
        "send_bus_approaching_notification",
        lambda **kwargs: sent.append(kwargs) or "mock-message-id",
    )
    monkeypatch.setattr(
        worker,
        "record_notification_sent",
        lambda *args: recorded.append(args),
    )

    worker.check_student_notifications()

    assert len(sent) == 1
    assert sent[0]["token"] == "fake-fcm-token-for-tests"
    assert sent[0]["bus_id"] == "BUS_001"
    assert sent[0]["stop_id"] == "STOP_02"
    assert sent[0]["eta_seconds"] == 600
    assert recorded == [("student-1", "BUS_001", "STOP_02")]


def test_worker_does_not_record_cooldown_when_delivery_fails(monkeypatch):
    setup_worker(monkeypatch, {"student-1": student_profile()})
    enable_live_delivery(monkeypatch)

    recorded = []

    def failed_send(**kwargs):
        raise RuntimeError("Simulated FCM failure")

    monkeypatch.setattr(worker, "send_bus_approaching_notification", failed_send)
    monkeypatch.setattr(
        worker,
        "record_notification_sent",
        lambda *args: recorded.append(args),
    )

    worker.check_student_notifications()

    assert recorded == []


def test_worker_continues_after_one_token_fails(monkeypatch):
    profile = student_profile()
    profile["fcm_tokens"] = {
        "token-1": {"token": "first-fake-token"},
        "token-2": {"token": "second-fake-token"},
    }

    setup_worker(monkeypatch, {"student-1": profile})
    enable_live_delivery(monkeypatch)

    attempted = []
    recorded = []

    def fake_send(**kwargs):
        attempted.append(kwargs["token"])
        if kwargs["token"] == "first-fake-token":
            raise RuntimeError("Simulated first-token failure")
        return "mock-message-id"

    monkeypatch.setattr(worker, "send_bus_approaching_notification", fake_send)
    monkeypatch.setattr(
        worker,
        "record_notification_sent",
        lambda *args: recorded.append(args),
    )

    worker.check_student_notifications()

    assert attempted == ["first-fake-token", "second-fake-token"]
    assert recorded == [("student-1", "BUS_001", "STOP_02")]


def test_worker_does_not_record_cooldown_when_all_tokens_fail(monkeypatch):
    setup_worker(monkeypatch, {"student-1": student_profile()})
    enable_live_delivery(monkeypatch)

    recorded = []

    def failed_send(**kwargs):
        raise RuntimeError("Simulated FCM failure")

    monkeypatch.setattr(worker, "send_bus_approaching_notification", failed_send)
    monkeypatch.setattr(
        worker,
        "record_notification_sent",
        lambda *args: recorded.append(args),
    )

    worker.check_student_notifications()

    assert recorded == []


def test_worker_dry_run_never_sends_or_records(monkeypatch):
    setup_worker(monkeypatch, {"student-1": student_profile()})

    sent = []
    recorded = []

    monkeypatch.setattr(
        worker,
        "send_bus_approaching_notification",
        lambda **kwargs: sent.append(kwargs),
    )
    monkeypatch.setattr(
        worker,
        "record_notification_sent",
        lambda *args: recorded.append(args),
    )

    worker.check_student_notifications()

    assert sent == []
    assert recorded == []
