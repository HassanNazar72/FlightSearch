from datetime import date, timedelta

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def fast_isolated_env(settings):
    """Every test starts with an empty cache and instant mock providers."""
    cache.clear()
    settings.MOCK_LATENCY_SCALE = 0
    yield
    cache.clear()


@pytest.fixture
def future_date() -> date:
    return date.today() + timedelta(days=30)
