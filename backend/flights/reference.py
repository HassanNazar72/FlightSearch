"""Static reference data: airports, airlines and currency rates.

Shared by the mock providers (to synthesise realistic flights) and by the
adapters (to resolve codes and time zones while normalising).
"""
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


@dataclass(frozen=True)
class Airport:
    code: str
    city: str
    lat: float
    lon: float
    tz: str


@dataclass(frozen=True)
class Airline:
    code: str
    name: str


def _airports(*rows: tuple) -> dict[str, Airport]:
    return {r[0]: Airport(*r) for r in rows}


AIRPORTS: dict[str, Airport] = _airports(
    ("JFK", "New York", 40.6413, -73.7781, "America/New_York"),
    ("LAX", "Los Angeles", 33.9416, -118.4085, "America/Los_Angeles"),
    ("ORD", "Chicago", 41.9742, -87.9073, "America/Chicago"),
    ("SFO", "San Francisco", 37.6213, -122.3790, "America/Los_Angeles"),
    ("MIA", "Miami", 25.7959, -80.2870, "America/New_York"),
    ("BOS", "Boston", 42.3656, -71.0096, "America/New_York"),
    ("ATL", "Atlanta", 33.6407, -84.4277, "America/New_York"),
    ("DFW", "Dallas", 32.8998, -97.0403, "America/Chicago"),
    ("SEA", "Seattle", 47.4502, -122.3088, "America/Los_Angeles"),
    ("YYZ", "Toronto", 43.6777, -79.6248, "America/Toronto"),
    ("MEX", "Mexico City", 19.4361, -99.0719, "America/Mexico_City"),
    ("GRU", "Sao Paulo", -23.4356, -46.4731, "America/Sao_Paulo"),
    ("LHR", "London", 51.4700, -0.4543, "Europe/London"),
    ("CDG", "Paris", 49.0097, 2.5479, "Europe/Paris"),
    ("FRA", "Frankfurt", 50.0379, 8.5622, "Europe/Berlin"),
    ("AMS", "Amsterdam", 52.3105, 4.7683, "Europe/Amsterdam"),
    ("MAD", "Madrid", 40.4983, -3.5676, "Europe/Madrid"),
    ("FCO", "Rome", 41.8003, 12.2389, "Europe/Rome"),
    ("ZRH", "Zurich", 47.4647, 8.5492, "Europe/Zurich"),
    ("IST", "Istanbul", 41.2753, 28.7519, "Europe/Istanbul"),
    ("DXB", "Dubai", 25.2532, 55.3657, "Asia/Dubai"),
    ("DOH", "Doha", 25.2731, 51.6081, "Asia/Qatar"),
    ("DEL", "Delhi", 28.5562, 77.1000, "Asia/Kolkata"),
    ("BOM", "Mumbai", 19.0896, 72.8656, "Asia/Kolkata"),
    ("LHE", "Lahore", 31.5216, 74.4036, "Asia/Karachi"),
    ("ISB", "Islamabad", 33.5605, 72.8495, "Asia/Karachi"),
    ("KHI", "Karachi", 24.9065, 67.1608, "Asia/Karachi"),
    ("SIN", "Singapore", 1.3644, 103.9915, "Asia/Singapore"),
    ("HKG", "Hong Kong", 22.3080, 113.9185, "Asia/Hong_Kong"),
    ("HND", "Tokyo", 35.5494, 139.7798, "Asia/Tokyo"),
    ("ICN", "Seoul", 37.4602, 126.4407, "Asia/Seoul"),
    ("SYD", "Sydney", -33.9399, 151.1753, "Australia/Sydney"),
    ("JNB", "Johannesburg", -26.1392, 28.2460, "Africa/Johannesburg"),
    ("CAI", "Cairo", 30.1219, 31.4056, "Africa/Cairo"),
)

# Airports the mock generator uses for connections.
HUBS = ("AMS", "FRA", "DXB", "IST", "DOH", "CDG", "LHR", "ATL", "ORD")

AIRLINES: tuple[Airline, ...] = (
    Airline("BA", "British Airways"),
    Airline("AA", "American Airlines"),
    Airline("DL", "Delta Air Lines"),
    Airline("UA", "United Airlines"),
    Airline("AF", "Air France"),
    Airline("LH", "Lufthansa"),
    Airline("KL", "KLM"),
    Airline("VS", "Virgin Atlantic"),
    Airline("EK", "Emirates"),
    Airline("QR", "Qatar Airways"),
    Airline("TK", "Turkish Airlines"),
    Airline("SQ", "Singapore Airlines"),
    Airline("AC", "Air Canada"),
    Airline("IB", "Iberia"),
)
AIRLINES_BY_CODE = {a.code: a for a in AIRLINES}
AIRLINES_BY_NAME = {a.name.lower(): a for a in AIRLINES}

# Fixed demo rates (units of USD per 1 unit of currency). A real system would
# refresh these from an FX API and record the rate used for each quote.
USD_PER_UNIT: dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.27,
    "CAD": 0.73,
    "AED": 0.272,
    "INR": 0.012,
}
CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP"}
SYMBOL_BY_CURRENCY = {v: k for k, v in CURRENCY_SYMBOLS.items()}


def to_usd(amount: float, currency: str) -> float:
    return round(amount * USD_PER_UNIT[currency], 2)


def from_usd(amount_usd: float, currency: str) -> float:
    return round(amount_usd / USD_PER_UNIT[currency], 2)


def distance_km(a: Airport, b: Airport) -> float:
    """Great-circle (haversine) distance."""
    lat1, lon1, lat2, lon2 = map(radians, (a.lat, a.lon, b.lat, b.lon))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))
