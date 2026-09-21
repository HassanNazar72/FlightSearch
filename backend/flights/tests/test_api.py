import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture(autouse=True)
def quick_deadline(settings):
    settings.PROVIDER_TIMEOUT_SECONDS = 0.5
    settings.MOCK_SLOW_SECONDS = 1.0


def test_search_returns_canonical_flights_and_meta(client, future_date):
    response = client.get("/api/search/", {"origin": "jfk", "destination": "LHR", "date": future_date})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == {"origin": "JFK", "destination": "LHR", "date": future_date.isoformat()}
    assert body["meta"]["providers_ok"] == 95
    assert body["meta"]["providers_failed"] == 5
    assert body["meta"]["cached"] is False

    flight = body["flights"][0]
    assert set(flight) == {
        "id", "provider_id", "airline", "flight_number", "origin", "destination",
        "departure_time", "arrival_time", "duration_minutes", "stops", "price_usd",
        "currency", "score", "tags",
    }  # fmt: skip
    for tag in ("cheapest", "fastest", "recommended"):
        assert sum(tag in f["tags"] for f in body["flights"]) == 1
    scores = [f["score"] for f in body["flights"]]
    assert scores == sorted(scores, reverse=True)


def test_repeat_search_is_cached(client, future_date):
    params = {"origin": "JFK", "destination": "LHR", "date": future_date}
    client.get("/api/search/", params)
    assert client.get("/api/search/", params).json()["meta"]["cached"] is True


@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"origin": "XXX"}, "origin"),
        ({"date": "2020-01-01"}, "date"),
        ({"date": "not-a-date"}, "date"),
        ({"date": None}, "date"),
        ({"destination": "JFK"}, "non_field_errors"),
    ],
)
def test_invalid_params_return_400(client, future_date, overrides, field):
    params = {"origin": "JFK", "destination": "LHR", "date": future_date, **overrides}
    params = {k: v for k, v in params.items() if v is not None}

    response = client.get("/api/search/", params)

    assert response.status_code == 400
    assert field in response.json()


def test_airports_and_health(client):
    assert any(a["code"] == "JFK" for a in client.get("/api/airports/").json())
    assert client.get("/api/health/").json() == {"status": "ok"}
