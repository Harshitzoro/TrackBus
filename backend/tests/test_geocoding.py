from collections import OrderedDict

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_student
from app.main import app
from app.services import geocoding_service
from app.services.geocoding_service import (
    GeocodingError,
    GeocodingResult,
    GeocodingTimeoutError,
    reverse_geocode,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


@pytest.fixture(autouse=True)
def reset_geocoding_state(monkeypatch):
    monkeypatch.setattr(geocoding_service, "_cache", OrderedDict())
    monkeypatch.setattr(geocoding_service, "_last_request_at", None)


@pytest.fixture
def authenticated_client():
    previous_override = app.dependency_overrides.get(get_current_student)
    app.dependency_overrides[get_current_student] = lambda: {
        "uid": "student-1",
        "role": "Student",
        "bus_id": "BUS_001",
    }

    try:
        with TestClient(app) as client:
            yield client
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_current_student, None)
        else:
            app.dependency_overrides[get_current_student] = previous_override


def mock_successful_lookup(monkeypatch, address="Alnia, Rajasthan, India"):
    requests = []

    def fake_get(url, **kwargs):
        requests.append((url, kwargs))
        return FakeResponse({"display_name": address})

    monkeypatch.setattr(geocoding_service.httpx, "get", fake_get)
    return requests


def test_reverse_geocode_returns_address_and_uses_nominatim(monkeypatch):
    monkeypatch.setenv(
        geocoding_service.USER_AGENT_ENV,
        "TrackBus-test/1.0 (tests@example.invalid)",
    )
    requests = mock_successful_lookup(monkeypatch)

    result = reverse_geocode(25.011938, 75.914605)

    assert result == GeocodingResult(
        address="Alnia, Rajasthan, India",
        source="nominatim",
    )
    url, options = requests[0]
    assert url == geocoding_service.NOMINATIM_REVERSE_URL
    assert options["params"] == {
        "lat": 25.011938,
        "lon": 75.914605,
        "format": "jsonv2",
    }
    assert options["headers"]["User-Agent"] == (
        "TrackBus-test/1.0 (tests@example.invalid)"
    )
    assert options["timeout"] == geocoding_service.REQUEST_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(90.1, 0), (-90.1, 0)],
)
def test_reverse_geocode_rejects_invalid_latitude(
    latitude,
    longitude,
):
    with pytest.raises(ValueError, match="Latitude"):
        reverse_geocode(latitude, longitude)


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(0, 180.1), (0, -180.1)],
)
def test_reverse_geocode_rejects_invalid_longitude(
    latitude,
    longitude,
):
    with pytest.raises(ValueError, match="Longitude"):
        reverse_geocode(latitude, longitude)


def test_reverse_geocode_returns_none_when_address_is_missing(monkeypatch):
    monkeypatch.setattr(
        geocoding_service.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse({"place_id": 123}),
    )

    assert reverse_geocode(25.011938, 75.914605) is None


def test_reverse_geocode_raises_timeout_error(monkeypatch):
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("private timeout details")

    monkeypatch.setattr(geocoding_service.httpx, "get", timeout)

    with pytest.raises(GeocodingTimeoutError) as exc_info:
        reverse_geocode(25.011938, 75.914605)

    assert "private timeout details" not in str(exc_info.value)


def test_reverse_geocode_handles_http_error(monkeypatch):
    def fail_with_http_error(*args, **kwargs):
        request = httpx.Request("GET", geocoding_service.NOMINATIM_REVERSE_URL)
        response = httpx.Response(503, request=request)
        raise httpx.HTTPStatusError(
            "private provider details",
            request=request,
            response=response,
        )

    monkeypatch.setattr(geocoding_service.httpx, "get", fail_with_http_error)

    with pytest.raises(GeocodingError) as exc_info:
        reverse_geocode(25.011938, 75.914605)

    assert "private provider details" not in str(exc_info.value)


def test_reverse_geocode_handles_malformed_json(monkeypatch):
    class MalformedJsonResponse(FakeResponse):
        def json(self):
            raise ValueError("private parser details")

    monkeypatch.setattr(
        geocoding_service.httpx,
        "get",
        lambda *args, **kwargs: MalformedJsonResponse(None),
    )

    with pytest.raises(GeocodingError) as exc_info:
        reverse_geocode(25.011938, 75.914605)

    assert "private parser details" not in str(exc_info.value)


def test_reverse_geocode_cache_hit_skips_second_http_request(monkeypatch):
    requests = mock_successful_lookup(monkeypatch)

    first = reverse_geocode(25.011938, 75.914605)
    second = reverse_geocode(25.011938, 75.914605)

    assert first == second
    assert len(requests) == 1


def test_nearby_coordinates_share_cache_entry(monkeypatch):
    requests = mock_successful_lookup(monkeypatch)

    first = reverse_geocode(25.011938, 75.914605)
    second = reverse_geocode(25.011939, 75.914606)

    assert first == second
    assert len(requests) == 1


def test_reverse_geocode_limits_requests_to_one_per_second(monkeypatch):
    clock = [10.0]
    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr(geocoding_service, "monotonic", lambda: clock[0])
    monkeypatch.setattr(geocoding_service, "sleep", fake_sleep)
    mock_successful_lookup(monkeypatch)

    reverse_geocode(25.011938, 75.914605)
    reverse_geocode(25.111938, 75.914605)

    assert sleeps == [pytest.approx(1.0)]


def test_reverse_geocoding_requires_authentication(monkeypatch):
    requests = mock_successful_lookup(monkeypatch)

    response = TestClient(app).get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 25.011938, "longitude": 75.914605},
    )

    assert response.status_code == 401
    assert requests == []


@pytest.mark.parametrize(
    ("params", "expected_status"),
    [
        ({"latitude": 90.1, "longitude": 0}, 422),
        ({"latitude": 0, "longitude": -180.1}, 422),
        ({"latitude": 25.0}, 422),
        ({"longitude": 75.0}, 422),
        ({}, 422),
        ({"latitude": "not-a-number", "longitude": 75.0}, 422),
    ],
)
def test_reverse_geocoding_validates_query_parameters(
    authenticated_client,
    monkeypatch,
    params,
    expected_status,
):
    requests = mock_successful_lookup(monkeypatch)

    response = authenticated_client.get(
        "/api/v1/geocoding/reverse",
        params=params,
    )

    assert response.status_code == expected_status
    assert requests == []


def test_authenticated_reverse_geocoding_returns_expected_response(
    authenticated_client,
    monkeypatch,
):
    mock_successful_lookup(monkeypatch)

    response = authenticated_client.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 25.011938, "longitude": 75.914605},
    )

    assert response.status_code == 200
    assert response.json() == {
        "address": "Alnia, Rajasthan, India",
        "source": "nominatim",
        "latitude": 25.011938,
        "longitude": 75.914605,
    }


def test_reverse_geocoding_returns_not_found_without_address(
    authenticated_client,
    monkeypatch,
):
    monkeypatch.setattr(
        geocoding_service.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse({}),
    )

    response = authenticated_client.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 25.011938, "longitude": 75.914605},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "No address found for these coordinates"


@pytest.mark.parametrize(
    ("exception", "expected_status", "expected_detail"),
    [
        (
            httpx.ReadTimeout("secret provider diagnostic"),
            504,
            "Address lookup timed out",
        ),
        (
            httpx.ConnectError("secret provider diagnostic"),
            502,
            "Address lookup is temporarily unavailable",
        ),
    ],
)
def test_reverse_geocoding_provider_failure_is_safe(
    authenticated_client,
    monkeypatch,
    exception,
    expected_status,
    expected_detail,
):
    def fail(*args, **kwargs):
        raise exception

    monkeypatch.setattr(geocoding_service.httpx, "get", fail)

    response = authenticated_client.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 25.011938, "longitude": 75.914605},
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert "secret provider diagnostic" not in response.text
