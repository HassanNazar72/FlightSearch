"""Synthesises the 100 mock flight providers (provider_001 ... provider_100).

A provider is just a small object with `.id`, `.schema` and `.fetch(query)`.
`fetch` stands in for an HTTP call: it sleeps to simulate network latency and
returns the provider's own raw payload (or fails, for the 'chaos' providers).
"""
import random
import time
from dataclasses import dataclass
from functools import lru_cache

from django.conf import settings

from flights.domain import ProviderError, SearchQuery
from flights.providers.itineraries import generate_itineraries
from flights.providers.payloads import RENDERERS

PROVIDER_COUNT = 100

# Deterministic misbehaviour so the demo always shows graceful degradation:
# 3 providers return an error, 2 hang past the aggregator's deadline.
CHAOS: dict[int, str] = {13: "error", 37: "error", 58: "error", 72: "timeout", 91: "timeout"}


@dataclass(frozen=True)
class MockProvider:
    id: str
    schema: str
    currency: str
    markup: float  # each provider prices a bit differently
    latency: tuple[float, float]  # seconds, uniform range
    failure: str | None = None  # "error" | "timeout" | None

    def fetch(self, query: SearchQuery):
        """Pretend to call the provider's API and return its raw, provider-specific payload."""
        scale = settings.MOCK_LATENCY_SCALE
        if settings.MOCK_CHAOS_ENABLED and self.failure == "timeout":
            time.sleep(settings.MOCK_SLOW_SECONDS)
        else:
            time.sleep(random.uniform(*self.latency) * scale)
        if settings.MOCK_CHAOS_ENABLED and self.failure == "error":
            raise ProviderError("HTTP 503 Service Unavailable")

        renderer, _ = RENDERERS[self.schema]
        return renderer(generate_itineraries(self.id, self.markup, query), self.currency)


@lru_cache(maxsize=1)
def get_providers() -> tuple[MockProvider, ...]:
    schemas = list(RENDERERS)
    providers = []
    for n in range(1, PROVIDER_COUNT + 1):
        rng = random.Random(n)  # stable config across restarts
        schema = schemas[(n - 1) % len(schemas)]
        _, currencies = RENDERERS[schema]
        providers.append(
            MockProvider(
                id=f"provider_{n:03d}",
                schema=schema,
                currency=rng.choice(currencies),
                markup=round(rng.uniform(0.92, 1.15), 3),
                latency=(0.05, rng.choice([0.3, 0.6, 0.9])),
                failure=CHAOS.get(n),
            )
        )
    return tuple(providers)
