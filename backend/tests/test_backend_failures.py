from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.routes import bus as bus_routes
from app.api.routes import eta as eta_routes
from app.api.routes import notifications as notifications_routes
from app.core import auth
from app.core.config import settings
from app.core.firebase import get_database
from app.main import app
from app.schemas.gps import GPSUpdate
from app.services import (
    deviation_service,
    eta_service,
    fcm_service,
    notification_store,
)
from app.workers import notification_worker as worker


class FakeRef:
    def __init__(self, value):
        self.value = value

    def child(self, key):
        if not isinstance(self.value, dict):
            return FakeRef(None)
        return FakeRef(self.value.get(key))

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        return value


@pytest.fixture
def client():
    return TestClient(app)


# Firebase and database failures

def test_get_database_requires_database_url(monkeypatch):
    monkeypatch.setattr(settings, "firebase_database_url", "")
    monkeypatch.setattr(settings, "firebase_credentials_path", "/tmp/not_used.json")

    with pytest.raises(RuntimeError, match="FIREBASE_DATABASE_URL"):
        get_database()


def test_get_database_fails_for_missing_credentials_file(monkeypatch):
    monkeypatch.setattr(settings, "firebase_database_url", "https://example.firebaseio.com")
    monkeypatch.setattr(settings, "firebase_credentials_path", "/tmp/does-not-exist.json")

    with pytest.raises(RuntimeError, match="Firebase secret path diagnostic"):
        get_database()


def test_get_current_student_raises_when_profile_missing(monkeypatch):
    fake_db = FakeRef({"users": {"uid-1": None}})
    monkeypatch.setattr(auth, "get_database", lambda: fake_db)

    with pytest.raises(HTTPException, match="User profile or bus assignment is not configured") as exc:
        auth.get_current_student({"uid": "uid-1"})

    assert exc.value.status_code == 403


def test_get_current_student_raises_on_database_read_failure(monkeypatch):
    class ExplodingRef:
        def child(self, key):
            raise RuntimeError("db read failure")

    monkeypatch.setattr(auth, "get_database", lambda: ExplodingRef())

    with pytest.raises(HTTPException, match="Unable to retrieve user profile") as exc:
        auth.get_current_student({"uid": "uid-1"})

    assert exc.value.status_code == 503


def test_bus_listing_returns_empty_list_when_bus_record_missing(monkeypatch):
    fake_db = FakeRef({"buses": {"BUS_001": None}})
    monkeypatch.setattr(bus_routes, "get_database", lambda: fake_db)

    result = bus_routes.list_buses({"bus_id": "BUS_001"})

    assert result == {"buses": []}


# Authentication and authorization failures

def test_get_current_user_requires_authorization_header():
    with pytest.raises(HTTPException, match="Authentication required") as exc:
        auth.get_current_user(None)

    assert exc.value.status_code == 401


@pytest.mark.parametrize(
    "error_cls",
    [auth.auth.ExpiredIdTokenError, auth.auth.RevokedIdTokenError],
)
def test_get_current_user_rejects_expired_or_revoked_firebase_tokens(monkeypatch, error_cls):
    monkeypatch.setattr(auth, "get_database", lambda: object())

    def fake_verify(token, check_revoked):
        if error_cls is auth.auth.RevokedIdTokenError:
            raise error_cls("expired or revoked token")
        raise error_cls("expired or revoked token", ValueError("cause"))

    monkeypatch.setattr(auth.auth, "verify_id_token", fake_verify)

    with pytest.raises(HTTPException, match="Invalid or expired authentication token") as exc:
        auth.get_current_user(type("Creds", (), {"credentials": "bad-token"})())

    assert exc.value.status_code == 401


def test_get_current_student_rejects_non_student_profiles(monkeypatch):
    fake_db = FakeRef({"users": {"uid-1": {"role": "Admin", "bus_id": "BUS_001"}}})
    monkeypatch.setattr(auth, "get_database", lambda: fake_db)

    with pytest.raises(HTTPException, match="Student access required") as exc:
        auth.get_current_student({"uid": "uid-1"})

    assert exc.value.status_code == 403


def test_require_assigned_bus_rejects_other_student_bus():
    with pytest.raises(HTTPException, match="not authorized") as exc:
        auth.require_assigned_bus("BUS_002", {"bus_id": "BUS_001"})

    assert exc.value.status_code == 403


# GPS and schema validation failures

def test_gps_schema_rejects_missing_timestamp():
    with pytest.raises(ValidationError):
        GPSUpdate(
            bus_id="BUS_001",
            latitude=12.34,
            longitude=56.78,
        )


def test_gps_schema_rejects_out_of_range_coordinates():
    with pytest.raises(ValidationError):
        GPSUpdate(
            bus_id="BUS_001",
            latitude=91,
            longitude=0,
            timestamp=datetime.now(timezone.utc),
        )


def test_gps_api_rejects_invalid_payload_types(client):
    response = client.post(
        "/api/v1/gps",
        json={
            "bus_id": 123,
            "latitude": "not-a-number",
            "longitude": 77.0,
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 422


# ETA service failures

def test_eta_unknown_stop_raises_value_error():
    with pytest.raises(ValueError, match="Unknown stop"):
        eta_service.estimate_arrival("BUS_001", "STOP_NOPE")


def test_eta_service_returns_unavailable_when_location_data_missing(monkeypatch):
    fake_db = FakeRef({"buses": {"BUS_001": {"location": {"latitude": "bad"}}}})
    monkeypatch.setattr(eta_service, "get_database", lambda: fake_db)

    result = eta_service.estimate_arrival("BUS_001", "STOP_01")

    assert result.status == "unavailable"


def test_eta_service_returns_unavailable_when_speed_is_zero(monkeypatch):
    location = {
        "latitude": 12.0,
        "longitude": 77.0,
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "speed_kmph": 0,
    }
    fake_db = FakeRef({"buses": {"BUS_001": {"location": location}}})
    monkeypatch.setattr(eta_service, "get_database", lambda: fake_db)

    result = eta_service.estimate_arrival("BUS_001", "STOP_01")

    assert result.status == "unavailable"


def test_eta_service_returns_unavailable_for_stale_location(monkeypatch):
    stale_timestamp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    fake_db = FakeRef({
        "buses": {
            "BUS_001": {
                "location": {
                    "latitude": 30.0,
                    "longitude": 76.0,
                    "timestamp": stale_timestamp,
                    "speed_kmph": 10,
                }
            }
        }
    })
    monkeypatch.setattr(eta_service, "get_database", lambda: fake_db)

    result = eta_service.estimate_arrival("BUS_001", "STOP_01")

    assert result.status == "unavailable"


def test_eta_api_returns_safe_error_for_database_failure(monkeypatch):
    app.dependency_overrides[auth.require_assigned_bus] = lambda bus_id: {"bus_id": "BUS_001", "uid": "uid-1", "role": "Student"}
    try:
        monkeypatch.setattr(
            eta_routes,
            "estimate_arrival",
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("db failure")),
        )
        response = TestClient(app).get("/api/v1/eta/BUS_001/STOP_01")
        assert response.status_code == 503
        assert response.json()["detail"] == "Unable to retrieve bus location"
    finally:
        app.dependency_overrides.clear()


# Route deviation failures

def test_route_deviation_returns_unavailable_for_invalid_location(monkeypatch):
    fake_db = FakeRef({"buses": {"BUS_001": {"location": {"latitude": "bad", "longitude": 76.0, "timestamp": "2024-01-01T00:00:00Z"}}}})
    monkeypatch.setattr(deviation_service, "get_database", lambda: fake_db)

    result = deviation_service.check_route_deviation("BUS_001")

    assert result["status"] == "unavailable"
    assert result["reason"] == "invalid_location"


def test_route_deviation_raises_on_database_failure(monkeypatch):
    class ExplodingRef:
        def child(self, key):
            raise RuntimeError("db read failure")

    monkeypatch.setattr(deviation_service, "get_database", lambda: ExplodingRef())

    with pytest.raises(RuntimeError, match="Could not read bus location from Firebase"):
        deviation_service.check_route_deviation("BUS_001")


# Notification registration failures

def test_notification_registration_rejects_missing_bus_record(monkeypatch):
    student = {"uid": "student-1", "bus_id": "BUS_001"}
    fake_db = FakeRef({
        "users": {"student-1": {"bus_id": "BUS_001", "stop_id": "STOP_01"}},
        "buses": {"BUS_001": None},
    })
    monkeypatch.setattr(notifications_routes, "get_database", lambda: fake_db)

    request = notifications_routes.NotificationRegistrationRequest(fcm_token="12345678901234567890")
    with pytest.raises(HTTPException, match="Assigned bus not found") as exc:
        notifications_routes.register_notification_device(request, student)

    assert exc.value.status_code == 400


def test_notification_registration_rejects_missing_route_record(monkeypatch):
    student = {"uid": "student-1", "bus_id": "BUS_001"}
    fake_db = FakeRef({
        "users": {"student-1": {"bus_id": "BUS_001", "stop_id": "STOP_01"}},
        "buses": {"BUS_001": {"routeId": "route-1"}},
        "routes": {"route-1": {"stops": {}}},
    })
    monkeypatch.setattr(notifications_routes, "get_database", lambda: fake_db)

    request = notifications_routes.NotificationRegistrationRequest(fcm_token="12345678901234567890")
    with pytest.raises(HTTPException, match="Assigned pickup stop is not on the bus route") as exc:
        notifications_routes.register_notification_device(request, student)

    assert exc.value.status_code == 400


def test_notification_registration_write_failure_raises_503(monkeypatch):
    class TokenNode:
        def child(self, key):
            return self

        def set(self, value):
            raise RuntimeError("write failed")

    class UserRecordNode:
        def child(self, key):
            if key == "fcm_tokens":
                return TokenNode()
            return self

        def get(self):
            return {"bus_id": "BUS_001", "stop_id": "STOP_01"}

    class UserCollectionNode:
        def child(self, key):
            return UserRecordNode()

    class BusRecordNode:
        def get(self):
            return {"routeId": "route-1"}

    class BusCollectionNode:
        def child(self, key):
            return BusRecordNode()

    class StopNode:
        def get(self):
            return {"stop_id": "STOP_01"}

    class StopCollectionNode:
        def child(self, key):
            return StopNode()

    class RouteNode:
        def child(self, key):
            if key == "stops":
                return StopCollectionNode()
            return self

        def get(self):
            return {"routeId": "route-1"}

    class RouteCollectionNode:
        def child(self, key):
            return RouteNode()

    class FakeDatabase:
        def child(self, key):
            if key == "users":
                return UserCollectionNode()
            if key == "buses":
                return BusCollectionNode()
            if key == "routes":
                return RouteCollectionNode()
            return self

    student = {"uid": "student-1", "bus_id": "BUS_001"}
    database = FakeDatabase()
    monkeypatch.setattr(notifications_routes, "get_database", lambda: database)

    request = notifications_routes.NotificationRegistrationRequest(fcm_token="12345678901234567890")
    with pytest.raises(HTTPException, match="Unable to register notification device") as exc:
        notifications_routes.register_notification_device(request, student)

    assert exc.value.status_code == 503


# Notification service, store, and FCM failures

def test_notification_store_treats_malformed_cooldown_as_due(monkeypatch):
    fake_db = FakeRef({
        "notification_cooldowns": {
            "abc": {"last_sent_at": "not-a-real-timestamp"}
        }
    })
    monkeypatch.setattr(notification_store, "get_database", lambda: fake_db)

    assert notification_store.notification_is_due("student-1", "BUS_001", "STOP_01") is True


def test_notification_store_raises_on_database_read_failure(monkeypatch):
    class ExplodingRef:
        def child(self, key):
            raise RuntimeError("cooldown read failure")

    monkeypatch.setattr(notification_store, "get_database", lambda: ExplodingRef())

    with pytest.raises(RuntimeError, match="cooldown read failure"):
        notification_store.notification_is_due("student-1", "BUS_001", "STOP_01")


def test_record_notification_sent_raises_on_database_write_failure(monkeypatch):
    class ExplodingRef:
        def child(self, key):
            raise RuntimeError("cooldown write failure")

    monkeypatch.setattr(notification_store, "get_database", lambda: ExplodingRef())

    with pytest.raises(RuntimeError, match="cooldown write failure"):
        notification_store.record_notification_sent("student-1", "BUS_001", "STOP_01")


def test_fcm_service_raises_when_external_send_fails(monkeypatch):
    def fake_send(message):
        raise RuntimeError("FCM backend unavailable")

    monkeypatch.setattr(fcm_service.messaging, "send", fake_send)

    with pytest.raises(RuntimeError, match="FCM backend unavailable"):
        fcm_service.send_bus_approaching_notification(
            token="abc1234567890",
            bus_id="BUS_001",
            stop_id="STOP_01",
            eta_seconds=600,
        )


# Notification worker resilience

def test_worker_handles_malformed_student_profiles_and_continues(monkeypatch, caplog):
    caplog.set_level("INFO", logger="app.workers.notification_worker")
    users = {
        "student-bad": {
            "role": "student",
            "bus_id": "BUS_001",
            "stop_id": "STOP_01",
            "fcm_tokens": {"token-1": {"token": "first-fake-token"}},
        },
        "student-good": {
            "role": "student",
            "bus_id": "BUS_002",
            "stop_id": "STOP_02",
            "fcm_tokens": {"token-2": {"token": "second-fake-token"}},
        },
    }

    def fake_eta(bus_id, stop_id):
        if bus_id == "BUS_001":
            raise RuntimeError("ETA evaluation failure")
        return type("ETA", (), {"status": "available", "eta_seconds": 600})()

    monkeypatch.setattr(worker, "get_database", lambda: FakeRef({"users": users}))
    monkeypatch.setenv("TRACKBUS_NOTIFICATIONS_DRY_RUN", "true")
    monkeypatch.setattr(worker, "estimate_arrival", fake_eta)
    monkeypatch.setattr(worker, "notification_is_due", lambda *args, **kwargs: True)

    worker.check_student_notifications()

    assert "Failed to evaluate notification for one student profile" in caplog.text
    assert "DRY RUN: notification eligible" in caplog.text
    assert "bus=BUS_002" in caplog.text


def test_worker_dry_run_never_sends_notifications(monkeypatch):
    profile = {
        "role": "Student",
        "bus_id": "BUS_001",
        "stop_id": "STOP_02",
        "fcm_tokens": {"token-1": {"token": "fake-fcm-token"}},
    }
    fake_db = FakeRef({"users": {"student-1": profile}})
    monkeypatch.setattr(worker, "get_database", lambda: fake_db)
    monkeypatch.setenv("TRACKBUS_NOTIFICATIONS_DRY_RUN", "true")
    monkeypatch.setattr(worker, "estimate_arrival", lambda *_args, **_kwargs: type("ETA", (), {"status": "available", "eta_seconds": 600})())
    monkeypatch.setattr(worker, "notification_is_due", lambda *_args, **_kwargs: True)

    sent = []
    recorded = []
    monkeypatch.setattr(worker, "send_bus_approaching_notification", lambda **kwargs: sent.append(kwargs) or "id-123")
    monkeypatch.setattr(worker, "record_notification_sent", lambda *args: recorded.append(args))

    worker.check_student_notifications()

    assert sent == []
    assert recorded == []


def test_bus_api_returns_503_for_database_read_failure(monkeypatch):
    app.dependency_overrides[auth.get_current_student] = lambda: {"uid": "uid-1", "role": "Student", "bus_id": "BUS_001"}
    try:
        class ExplodingRef:
            def child(self, key):
                raise RuntimeError("firebase unavailable")

        monkeypatch.setattr(bus_routes, "get_database", lambda: ExplodingRef())
        response = TestClient(app).get("/api/v1/buses")

        assert response.status_code == 503
        assert response.json()["detail"] == "Unable to retrieve buses from Firebase"
    finally:
        app.dependency_overrides.clear()
