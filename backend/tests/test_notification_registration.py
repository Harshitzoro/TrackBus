
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import notifications
from app.core.auth import get_current_student
from app.core.firebase import get_database


client = TestClient(app)


class FakeRef:
    def __init__(self, data, writes=None):
        self.data = data
        self.writes = writes if writes is not None else []
        self.path = []

    def child(self, key):
        ref = FakeRef(self.data, self.writes)
        ref.path = self.path + [key]
        return ref

    def get(self):
        path = self.path
        value = self.data
        for key in path:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return value

    def set(self, value):
        self.writes.append((self.path, value))


def setup_function():
    app.dependency_overrides[get_current_student] = lambda: {
        "uid": "test-student",
        "role": "Student",
        "bus_id": "BUS_001",
    }


def teardown_function():
    app.dependency_overrides.clear()


def test_register_valid_student_token(monkeypatch):
    data = {
        "users": {
            "test-student": {
                "role": "Student",
                "bus_id": "BUS_001",
                "stop_id": "STOP_02",
            }
        },
        "buses": {"BUS_001": {"routeId": "ROUTE_001"}},
        "routes": {
            "ROUTE_001": {
                "stops": {"STOP_02": {"name": "Dadabari"}}
            }
        },
    }
    fake_db = FakeRef(data)
    monkeypatch.setattr(notifications, "get_database", lambda: fake_db)

    response = client.post(
        "/api/v1/notifications/register",
        json={"fcm_token": "x" * 40},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "registered"
    assert len(fake_db.writes) == 1
    assert fake_db.writes[0][0][:2] == ["users", "test-student"]


def test_register_rejects_missing_stop(monkeypatch):
    data = {
        "users": {
            "test-student": {
                "role": "Student",
                "bus_id": "BUS_001",
            }
        }
    }
    monkeypatch.setattr(
        notifications, "get_database", lambda: FakeRef(data)
    )

    response = client.post(
        "/api/v1/notifications/register",
        json={"fcm_token": "x" * 40},
    )

    assert response.status_code == 400
    assert "pickup stop" in response.json()["detail"]


def test_register_rejects_stop_not_on_route(monkeypatch):
    data = {
        "users": {
            "test-student": {
                "role": "Student",
                "bus_id": "BUS_001",
                "stop_id": "STOP_99",
            }
        },
        "buses": {"BUS_001": {"routeId": "ROUTE_001"}},
        "routes": {"ROUTE_001": {"stops": {}}},
    }
    monkeypatch.setattr(
        notifications, "get_database", lambda: FakeRef(data)
    )

    response = client.post(
        "/api/v1/notifications/register",
        json={"fcm_token": "x" * 40},
    )

    assert response.status_code == 400
    assert "not on the bus route" in response.json()["detail"]
    assert not FakeRef(data).writes
