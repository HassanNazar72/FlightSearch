"""Round-trip tests: generate itineraries -> render in a provider's schema -> parse
with its adapter -> compare with the original. If a renderer and its adapter
ever disagree, one of these fails."""
from datetime import date, timezone

import pytest

from flights.adapters import get_adapter, registered_schemas
from flights.domain import SearchQuery
from flights.providers import get_providers
from flights.providers.itineraries import generate_itineraries
from flights.providers.payloads import RENDERERS

ROUTES = [("JFK", "LHR"), ("LHR", "SIN"), ("JFK", "MIA"), ("SYD", "LHR"), ("LHE", "DXB")]
# An ordinary day plus the days daylight-saving time starts in Europe and ends in the US.
DATES = [date(2026, 10, 15), date(2026, 3, 29), date(2026, 11, 1)]


@pytest.mark.parametrize("day", DATES, ids=str)
@pytest.mark.parametrize("origin,dest", ROUTES, ids=lambda r: r)
@pytest.mark.parametrize("schema", list(RENDERERS))
def test_adapter_round_trip(schema, origin, dest, day):
    itineraries = generate_itineraries("provider_test", 1.0, SearchQuery(origin, dest, day))

    flights = get_adapter(schema).parse(RENDERERS[schema](itineraries), "provider_test")

    assert len(flights) == len(itineraries)
    for flight, it in zip(flights, itineraries, strict=True):
        assert flight.airline == it.airline.name
        assert flight.flight_number == it.flight_code
        assert (flight.origin, flight.destination) == (origin, dest)
        assert flight.stops == it.stops
        assert flight.departure_time == it.departure
        assert flight.arrival_time == it.arrival
        elapsed = it.arrival.astimezone(timezone.utc) - it.departure.astimezone(timezone.utc)
        assert flight.duration_minutes == round(elapsed.total_seconds() / 60)
        assert flight.price_usd == pytest.approx(it.price_usd, abs=0.01)
        assert flight.currency == "USD"


def test_canonical_output_has_local_times_with_offsets():
    it = generate_itineraries("provider_test", 1.0, SearchQuery("JFK", "LHR", date(2026, 10, 15)))[0]
    # the columnar provider sends UTC; the adapter must return airport-local times
    flight = get_adapter("columnar").parse(RENDERERS["columnar"]([it]), "provider_test")[0]
    assert flight.departure_time.tzname() in {"EDT", "EST"}
    assert flight.arrival_time.tzname() in {"BST", "GMT"}


GOOD_OFFER = {
    "flightNo": "BA117", "carrier": "British Airways", "from": "JFK", "to": "LHR",
    "departs": "2026-10-01T18:30:00-04:00", "arrives": "2026-10-02T06:35:00+01:00",
    "fare": 500.0, "currency": "USD", "stops": 0,
}  # fmt: skip


def test_malformed_offer_is_skipped_not_fatal():
    broken = {**GOOD_OFFER, "fare": -5}
    missing_key = {k: v for k, v in GOOD_OFFER.items() if k != "carrier"}

    flights = get_adapter("fare_iso").parse({"results": [GOOD_OFFER, broken, missing_key]}, "provider_x")

    assert [f.flight_number for f in flights] == ["BA117"]


def test_non_usd_offer_is_rejected():
    euro_offer = {**GOOD_OFFER, "currency": "EUR"}
    assert get_adapter("fare_iso").parse({"results": [euro_offer]}, "provider_x") == []


def test_every_provider_schema_has_an_adapter():
    assert {p.schema for p in get_providers()} <= set(registered_schemas())


def test_unknown_schema_raises():
    with pytest.raises(LookupError):
        get_adapter("does_not_exist")


def test_there_are_100_providers_with_diverse_schemas():
    providers = get_providers()
    assert len(providers) == 100
    assert len({p.id for p in providers}) == 100
    assert len({p.schema for p in providers}) == 6
