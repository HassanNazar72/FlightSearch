from datetime import datetime, timezone

from flights.domain import Flight
from flights.services.ranking import rank_and_tag

WEIGHTS = {"price": 0.6, "duration": 0.4}
NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def flight(id, price, minutes):
    return Flight(id, "p", "Air", "AA1", "JFK", "LHR", NOW, NOW, minutes, 0, price, "USD")


def by_tag(flights, tag):
    return [f for f in flights if tag in f.tags]


def test_tags_pick_cheapest_fastest_and_recommended():
    cheap = flight("cheap", 300, 700)
    fast = flight("fast", 900, 400)
    balanced = flight("balanced", 400, 450)

    ranked = rank_and_tag([cheap, fast, balanced], WEIGHTS)

    assert by_tag(ranked, "cheapest") == [cheap]
    assert by_tag(ranked, "fastest") == [fast]
    assert by_tag(ranked, "recommended") == [balanced]
    assert ranked[0] is balanced  # best score first


def test_score_is_between_0_and_100_and_uses_weights():
    cheap, fast = flight("cheap", 300, 700), flight("fast", 900, 400)

    price_heavy = rank_and_tag([cheap, fast], {"price": 0.9, "duration": 0.1})
    assert price_heavy[0] is cheap

    duration_heavy = rank_and_tag([cheap, fast], {"price": 0.1, "duration": 0.9})
    assert duration_heavy[0] is fast
    assert all(0 <= f.score <= 100 for f in duration_heavy)


def test_one_flight_gets_all_tags():
    only = flight("only", 500, 500)
    ranked = rank_and_tag([only], WEIGHTS)
    assert set(ranked[0].tags) == {"cheapest", "fastest", "recommended"}
    assert ranked[0].score == 100


def test_ties_are_broken_by_the_other_criterion():
    a = flight("a", 300, 600)
    b = flight("b", 300, 500)  # same price, faster
    ranked = rank_and_tag([a, b], WEIGHTS)
    assert by_tag(ranked, "cheapest") == [b]


def test_empty_input():
    assert rank_and_tag([], WEIGHTS) == []
