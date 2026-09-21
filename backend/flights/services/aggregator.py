"""Core of the platform: fan out to every provider, normalise, rank, cache."""
import logging
import time
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import replace

from django.conf import settings
from django.core.cache import cache

from flights.adapters import get_adapter
from flights.domain import Flight, ProviderFailure, SearchQuery, SearchResult
from flights.providers import get_providers
from flights.services.ranking import rank_and_tag

logger = logging.getLogger(__name__)


def search_flights(query: SearchQuery, providers=None) -> SearchResult:
    """Return ranked flights for a query, served from cache when possible."""
    started = time.perf_counter()

    cached = cache.get(query.cache_key)
    if cached is not None:
        return replace(cached, cached=True, took_ms=_elapsed_ms(started))

    providers = providers if providers is not None else get_providers()
    flights, failures = fetch_all(query, providers, settings.PROVIDER_TIMEOUT_SECONDS)
    result = SearchResult(
        flights=rank_and_tag(flights, settings.RANKING_WEIGHTS),
        providers_total=len(providers),
        failures=failures,
    )

    # A partial result (some providers down) gets a short TTL so we retry soon.
    ttl = settings.SEARCH_CACHE_TTL_PARTIAL if failures else settings.SEARCH_CACHE_TTL
    cache.set(query.cache_key, result, ttl)

    return replace(result, took_ms=_elapsed_ms(started))


def fetch_all(query: SearchQuery, providers, timeout: float) -> tuple[list[Flight], list[ProviderFailure]]:
    """Query all providers concurrently under one overall deadline.

    Failures are isolated: an exception or a timeout in one provider is recorded
    and everyone else's results are still returned.
    """
    executor = ThreadPoolExecutor(max_workers=len(providers), thread_name_prefix="provider")
    futures = {executor.submit(_query_provider, p, query): p for p in providers}
    done, not_done = wait(futures, timeout=timeout)

    flights: list[Flight] = []
    failures: list[ProviderFailure] = []
    for future in done:
        provider = futures[future]
        try:
            flights.extend(future.result())
        except Exception as exc:  # noqa: BLE001 - any provider failure must be isolated
            logger.warning("%s failed: %s", provider.id, exc)
            failures.append(ProviderFailure(provider.id, f"error: {exc}"))
    for future in not_done:
        future.cancel()
        logger.warning("%s timed out after %.1fs", futures[future].id, timeout)
        failures.append(ProviderFailure(futures[future].id, "timeout"))

    # wait=False: don't block on stragglers (threads can't be killed; they finish in the background).
    executor.shutdown(wait=False, cancel_futures=True)
    failures.sort(key=lambda f: f.provider_id)
    return flights, failures


def _query_provider(provider, query: SearchQuery) -> list[Flight]:
    raw = provider.fetch(query)
    return get_adapter(provider.schema).parse(raw, provider.id)


def _elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)
