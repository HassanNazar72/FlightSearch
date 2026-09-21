"""Generates the 'ground truth' flights a mock provider would sell.

The renderers (payloads.py) then serialise the same itineraries into each
provider's own schema. Output is deterministic per (provider, route, date), so
results are reproducible and cacheable.
"""
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flights.domain import SearchQuery
from flights.reference import AIRLINES, AIRPORTS, HUBS, Airline, distance_km


@dataclass(frozen=True)
class Leg:
    airline: Airline
    number: int
    origin: str
    destination: str
    departure: datetime  # tz-aware, airport-local
    arrival: datetime


@dataclass(frozen=True)
class Itinerary:
    legs: tuple[Leg, ...]
    price_usd: float

    @property
    def first(self) -> Leg:
        return self.legs[0]

    @property
    def last(self) -> Leg:
        return self.legs[-1]

    @property
    def stops(self) -> int:
        return len(self.legs) - 1

    @property
    def flight_code(self) -> str:
        return f"{self.first.airline.code}{self.first.number}"


CRUISE_KMH = 830
LONGEST_NONSTOP_KM = 9500


def generate_itineraries(provider_id: str, markup: float, query: SearchQuery) -> list[Itinerary]:
    rng = random.Random(f"{provider_id}|{query.origin}|{query.destination}|{query.date}")
    origin, dest = AIRPORTS[query.origin], AIRPORTS[query.destination]
    km = distance_km(origin, dest)

    itineraries, used_numbers = [], set()
    for _ in range(rng.randint(2, 4)):
        airline = rng.choice(AIRLINES)
        number = rng.randint(100, 999)
        if (airline.code, number) in used_numbers:
            continue
        used_numbers.add((airline.code, number))

        stops = 1 if km > LONGEST_NONSTOP_KM or rng.random() > 0.65 else 0
        departure = datetime(
            query.date.year, query.date.month, query.date.day,
            rng.randint(5, 22), rng.randrange(0, 60, 5),
            tzinfo=ZoneInfo(origin.tz),
        )  # fmt: skip
        wind_and_routing = rng.uniform(0.94, 1.08)  # so two flights on one route rarely take identical time
        air_minutes = round(km / CRUISE_KMH * 60 * wind_and_routing * (1.1 if stops else 1.0)) + 30

        if stops:
            hub = rng.choice([h for h in HUBS if h not in (query.origin, query.destination)])
            layover = rng.randint(75, 200)
            first_minutes = air_minutes // 2
            legs = _two_legs(airline, number, query, hub, departure, first_minutes,
                             layover, air_minutes - first_minutes, rng)  # fmt: skip
        else:
            legs = (_leg(airline, number, query.origin, query.destination, departure, air_minutes),)

        price = (45 + km * 0.085) * rng.uniform(0.75, 1.45) * markup * (0.82 if stops else 1.0)
        itineraries.append(Itinerary(legs=legs, price_usd=round(price, 2)))
    return itineraries


def _leg(airline, number, origin, destination, departure, minutes) -> Leg:
    # Add the flight time in UTC: datetime + timedelta on a ZoneInfo datetime is
    # wall-clock arithmetic and would be off by an hour across a DST change.
    arrival_utc = departure.astimezone(timezone.utc) + timedelta(minutes=minutes)
    arrival = arrival_utc.astimezone(ZoneInfo(AIRPORTS[destination].tz))
    return Leg(airline, number, origin, destination, departure, arrival)


def _two_legs(airline, number, query, hub, departure, first_minutes, layover, second_minutes, rng):
    first = _leg(airline, number, query.origin, hub, departure, first_minutes)
    second_departure = first.arrival + timedelta(minutes=layover)
    second = _leg(airline, rng.randint(100, 999), hub, query.destination, second_departure, second_minutes)
    return (first, second)
