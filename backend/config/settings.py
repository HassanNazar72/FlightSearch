"""Django settings. Everything environment-specific comes from env vars so the
same code runs locally and on Render."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name: str, default: str = "") -> list[str]:
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

_DEV_KEY = "dev-only-insecure-key"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", _DEV_KEY)
if not DEBUG and SECRET_KEY == _DEV_KEY:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY when DJANGO_DEBUG=0")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):  # injected automatically by Render
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

# No models, admin or sessions: the service is stateless, so no database is needed.
INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "flights",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DATABASES: dict = {}

TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- CORS: the React app is served from a different origin (Vercel) ----------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

# ---- Django REST Framework ----------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    # A cold search fans out to 100 providers, so cap how often one client can trigger it.
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": os.environ.get("SEARCH_RATE_LIMIT", "60/min")},
}

# ---- Cache: in-memory, per process (swap for Redis when running several workers) -
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "flight-search",
    }
}

# ---- Aggregator tuning --------------------------------------------------------
# Deadline for the whole provider fan-out; slower providers are dropped.
PROVIDER_TIMEOUT_SECONDS = float(os.environ.get("PROVIDER_TIMEOUT_SECONDS", "1.5"))
SEARCH_CACHE_TTL = int(os.environ.get("SEARCH_CACHE_TTL", "300"))
# Results missing some providers are cached briefly so the next search retries them.
SEARCH_CACHE_TTL_PARTIAL = int(os.environ.get("SEARCH_CACHE_TTL_PARTIAL", "60"))
# "Recommended" = weighted blend of normalised price and duration (weights sum to 1).
RANKING_WEIGHTS = {"price": 0.6, "duration": 0.4}

# ---- Mock providers -----------------------------------------------------------
MOCK_CHAOS_ENABLED = os.environ.get("MOCK_CHAOS_ENABLED", "1") == "1"  # 5 providers misbehave
MOCK_LATENCY_SCALE = float(os.environ.get("MOCK_LATENCY_SCALE", "1.0"))  # 0 = instant (tests)
MOCK_SLOW_SECONDS = float(os.environ.get("MOCK_SLOW_SECONDS", "3.0"))  # how long a "hung" provider stalls

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"flights": {"handlers": ["console"], "level": "INFO"}},
}
