import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from flights.domain import Flight
from flights.reference import AIRLINES_BY_CODE, AIRLINES_BY_NAME, AIRPORTS, to_usd

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Translates one provider schema into canonical Flight objects.

    Subclasses implement two small hooks:
      * extract_items(raw): dig the list of offers out of the response envelope
      * to_flight(item, provider_id): map ONE offer to a Flight

    parse() is the template method: a malformed offer is skipped and logged,
    it does not throw away the rest of that provider's results.
    """

    @abstractmethod
    def extract_items(self, raw: Any) -> list[Any]: ...

    @abstractmethod
    def to_flight(self, item: Any, provider_id: str) -> Flight: ...

    def parse(self, raw: Any, provider_id: str) -> list[Flight]:
        flights = []
        for item in self.extract_items(raw):
            try:
                flights.append(self.to_flight(item, provider_id))
            except (KeyError, ValueError, TypeError, IndexError) as exc:
                logger.warning("%s: skipped malformed offer (%r)", provider_id, exc)
        return flights


def airline_name(code_or_name: str) -> str:
    """Resolve an IATA code ('BA') or a name ('British Airways') to the display name."""
    key = str(code_or_name).strip()
    airline = AIRLINES_BY_CODE.get(key.upper()) or AIRLINES_BY_NAME.get(key.lower())
    return airline.name if airline else key


def local_tz(airport_code: str) -> ZoneInfo:
    return ZoneInfo(AIRPORTS[airport_code].tz)  # KeyError for unknown airports -> offer skipped


def build_flight(
    *,
    provider_id: str,
    airline: str,
    flight_number: str,
    origin: str,
    destination: str,
    departure: datetime,
    arrival: datetime,
    stops: int,
    price: float,
    currency: str,
) -> Flight:
    """Single place where canonical invariants are enforced, so every adapter
    produces identical output regardless of how the provider shaped its data."""
    if departure.tzinfo is None or arrival.tzinfo is None:
        raise ValueError("naive datetime")
    # Measure elapsed time in UTC; subtracting two datetimes that share a ZoneInfo
    # uses wall-clock time, which is wrong across a DST change.
    duration = arrival.astimezone(timezone.utc) - departure.astimezone(timezone.utc)
    if duration <= timedelta(0):
        raise ValueError("arrival before departure")
    if price <= 0:
        raise ValueError("non-positive price")

    origin, destination = origin.upper(), destination.upper()
    departure = departure.astimezone(local_tz(origin))
    arrival = arrival.astimezone(local_tz(destination))
    flight_number = str(flight_number).replace(" ", "").upper()
    digest = hashlib.blake2s(
        f"{provider_id}|{flight_number}|{departure.isoformat()}".encode(), digest_size=5
    ).hexdigest()

    return Flight(
        id=f"{provider_id}-{digest}",
        provider_id=provider_id,
        airline=airline_name(airline),
        flight_number=flight_number,
        origin=origin,
        destination=destination,
        departure_time=departure,
        arrival_time=arrival,
        duration_minutes=round(duration.total_seconds() / 60),
        stops=int(stops),
        price_usd=to_usd(float(price), currency),
        currency=currency,
    )
