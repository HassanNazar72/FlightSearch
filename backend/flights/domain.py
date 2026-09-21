"""Canonical types shared by every layer (adapters, aggregator, API)."""
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class SearchQuery:
    origin: str
    destination: str
    date: date

    @property
    def cache_key(self) -> str:
        return f"search:{self.origin}:{self.destination}:{self.date.isoformat()}"


@dataclass
class Flight:
    """The one schema the rest of the system understands.

    departure_time / arrival_time are timezone-aware datetimes in the local time
    of the origin / destination airport.
    """

    id: str
    provider_id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    stops: int
    price_usd: float
    currency: str  # always "USD" in this prototype
    # Filled in by the ranking step, not by adapters.
    score: float = 0.0
    tags: list[str] = field(default_factory=list)


class ProviderError(Exception):
    """A provider failed (HTTP 5xx, malformed payload, ...)."""


@dataclass(frozen=True)
class ProviderFailure:
    provider_id: str
    reason: str


@dataclass
class SearchResult:
    flights: list[Flight]
    providers_total: int
    failures: list[ProviderFailure]
    cached: bool = False
    took_ms: int = 0

    @property
    def providers_ok(self) -> int:
        return self.providers_total - len(self.failures)
