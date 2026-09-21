"""Round-trip tests: generate itineraries -> render in a provider's schema -> parse
with its adapter -> compare with the original. If a renderer and its adapter
ever disagree, one of these fails."""
from datetime import timezone

import pytest

from flights.adapters import get_adapter, registered_schemas
from flights.domain import SearchQuery
from flights.providers import get_providers
from flights.providers.itineraries import generate_itineraries
from flights.providers.payloads import RENDERERS

ROUTES = [("JFK", "LHR"), ("LHR", "SIN"), ("JFK", "MIA"), ("SYD", "LHR"), ("LHE", "DXB")]


def all_cases():
    for schema, (_, currencies) in RENDERERS.items():
        for currency in currencies:
            for origin, dest in ROUTES:
                yield pytest.param(schema, currency, origin, dest, id=f"{schema}-{currency}-{origin}{dest}")


@pytest.mark.parametrize("schema,currency,origin,dest", list(all_cases()))
def test_adapter_round_trip(schema, currency, origin, dest, future_date):
    query = SearchQuery(origin, dest, future_date)
    itineraries = generate_itineraries("provider_test", 1.0, query)
    renderer, _ = RENDERERS[schema]

    flights = get_adapter(schema).parse(renderer(itineraries, currency), "provider_test")

    assert len(flights) == len(itineraries)
    for flight, it in zip(flights, itineraries, strict=True):
        assert flight.airline == it.first.airline.name
        assert flight.flight_number == it.flight_code
        assert (flight.origin, flight.destination) == (origin, dest)
        assert flight.stops == it.stops
        assert flight.departure_time == it.first.departure
        assert flight.arrival_time == it.last.arrival
        elapsed = it.last.arrival.astimezone(timezone.utc) - it.first.departure.astimezone(timezone.utc)
        assert flight.duration_minutes == round(elapsed.total_seconds() / 60)
        assert abs(flight.price_usd - it.price_usd) <= 0.02
        assert flight.currency == currency


def test_canonical_output_has_local_times_with_offsets(future_date):
    query = SearchQuery("JFK", "LHR", future_date)
    it = generate_itineraries("provider_test", 1.0, query)[0]
    # columnar provider sends UTC; the adapter must return airport-local times
    flight = get_adapter("columnar").parse(RENDERERS["columnar"][0]([it], "USD"), "provider_test")[0]
    assert flight.departure_time.tzname() in {"EDT", "EST"}
    assert flight.arrival_time.tzname() in {"BST", "GMT"}


def test_malformed_offer_is_skipped_not_fatal():
    good = {
        "flightNo": "BA117", "carrier": "British Airways", "from": "JFK", "to": "LHR",
        "departs": "2026-10-01T18:30:00-04:00", "arrives": "2026-10-02T06:35:00+01:00",
        "fare": 500.0, "currency": "USD", "stops": 0,
    }  # fmt: skip
    broken = {**good, "fare": -5}
    missing_key = {k: v for k, v in good.items() if k != "carrier"}

    flights = get_adapter("fare_iso").parse({"results": [good, broken, missing_key]}, "provider_x")

    assert [f.flight_number for f in flights] == ["BA117"]


def test_every_provider_schema_has_an_adapter():
    assert {p.schema for p in get_providers()} <= set(registered_schemas())


def test_unknown_schema_raises():
    with pytest.raises(LookupError):
        get_adapter("does_not_exist")


def test_there_are_100_providers_with_diverse_schemas():
    providers = get_providers()
    assert len(providers) == 100
    assert len({p.id for p in providers}) == 100
    assert len({p.schema for p in providers}) == 7
    assert len({p.currency for p in providers}) > 3
