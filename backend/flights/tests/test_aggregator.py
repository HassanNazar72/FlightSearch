import time
from dataclasses import dataclass

from flights.domain import ProviderError, SearchQuery
from flights.providers import get_providers
from flights.services.aggregator import search_flights

OFFER = {
    "flightNo": "BA117", "carrier": "British Airways", "from": "JFK", "to": "LHR",
    "departs": "2026-10-01T18:30:00-04:00", "arrives": "2026-10-02T06:35:00+01:00",
    "fare": 500.0, "currency": "USD", "stops": 0,
}  # fmt: skip


@dataclass
class FakeProvider:
    id: str
    behaviour: str = "ok"  # ok | error | hang | garbage
    schema: str = "fare_iso"
    calls: int = 0

    def fetch(self, query):
        self.calls += 1
        if self.behaviour == "error":
            raise ProviderError("HTTP 500")
        if self.behaviour == "hang":
            time.sleep(1.0)
        if self.behaviour == "garbage":
            return {"unexpected": "shape"}
        return {"results": [{**OFFER, "flightNo": f"BA{self.id[-3:]}"}]}


def query(future_date):
    return SearchQuery("JFK", "LHR", future_date)


def test_failing_and_hanging_providers_do_not_break_the_search(settings, future_date):
    settings.PROVIDER_TIMEOUT_SECONDS = 0.3
    providers = [
        FakeProvider("p001"), FakeProvider("p002"), FakeProvider("p003"),
        FakeProvider("p004", "error"), FakeProvider("p005", "hang"), FakeProvider("p006", "garbage"),
    ]  # fmt: skip

    started = time.perf_counter()
    result = search_flights(query(future_date), providers)

    assert time.perf_counter() - started < 0.9  # did not wait for the 1s hang
    assert len(result.flights) == 3
    assert result.providers_total == 6
    assert result.providers_ok == 3
    reasons = {f.provider_id: f.reason for f in result.failures}
    assert reasons["p004"].startswith("error")
    assert reasons["p005"] == "timeout"
    assert "p006" in reasons  # payload with the wrong shape counts as a failure


def test_second_identical_search_is_served_from_cache(future_date):
    provider = FakeProvider("p001")

    first = search_flights(query(future_date), [provider])
    second = search_flights(query(future_date), [provider])

    assert provider.calls == 1
    assert (first.cached, second.cached) == (False, True)
    assert [f.id for f in second.flights] == [f.id for f in first.flights]


def test_different_query_is_not_a_cache_hit(future_date):
    provider = FakeProvider("p001")
    search_flights(SearchQuery("JFK", "LHR", future_date), [provider])
    search_flights(SearchQuery("JFK", "CDG", future_date), [provider])
    assert provider.calls == 2


def test_real_registry_returns_95_of_100(settings, future_date):
    settings.PROVIDER_TIMEOUT_SECONDS = 0.5
    settings.MOCK_SLOW_SECONDS = 1.0

    result = search_flights(query(future_date), get_providers())

    assert result.providers_total == 100
    assert result.providers_ok == 95
    assert len(result.failures) == 5
    assert len(result.flights) > 100
