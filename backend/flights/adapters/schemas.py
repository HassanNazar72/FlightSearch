"""One adapter per provider schema family.

Every family names its fields differently (fare / ticket_price / amount / ...),
encodes time differently (ISO, split date+time+tz, epoch, UTC, basic-ISO) and
prices differently (float, cents, a "$480.00" string) and stops differently
(number, layover count, boolean).
Importing this module registers all adapters.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from flights.adapters.base import BaseAdapter, build_flight, local_tz
from flights.adapters.registry import register
from flights.domain import Flight


@register("fare_iso")
class FareIsoAdapter(BaseAdapter):
    """{"status": "ok", "results": [{"flightNo", "carrier", "from", "to", "departs", "arrives", "fare", "currency", "stops"}]}
    ISO-8601 timestamps with UTC offset, float price."""

    def extract_items(self, raw: Any) -> list[Any]:
        return raw["results"]

    def to_flight(self, item: Any, provider_id: str) -> Flight:
        return build_flight(
            provider_id=provider_id,
            airline=item["carrier"],
            flight_number=item["flightNo"],
            origin=item["from"],
            destination=item["to"],
            departure=datetime.fromisoformat(item["departs"]),
            arrival=datetime.fromisoformat(item["arrives"]),
            stops=item["stops"],
            price=item["fare"],
            currency=item["currency"],
        )


@register("ticket_price_nested")
class TicketPriceNestedAdapter(BaseAdapter):
    """{"data": {"itineraries": [{"ticket_price": {"total", "cur"}, "airline": {"code"},
    "origin": {"airport"}, "depart": {"date", "time", "tz"}, "connections"}]}}
    Everything nested; date, time and time zone are separate fields."""

    def extract_items(self, raw: Any) -> list[Any]:
        return raw["data"]["itineraries"]

    @staticmethod
    def _moment(part: dict) -> datetime:
        naive = datetime.strptime(f'{part["date"]} {part["time"]}', "%Y-%m-%d %H:%M")
        return naive.replace(tzinfo=ZoneInfo(part["tz"]))

    def to_flight(self, item: Any, provider_id: str) -> Flight:
        code = item["airline"]["code"]
        return build_flight(
            provider_id=provider_id,
            airline=code,
            flight_number=f'{code}{item["flight"]}',
            origin=item["origin"]["airport"],
            destination=item["destination"]["airport"],
            departure=self._moment(item["depart"]),
            arrival=self._moment(item["arrive"]),
            stops=item["connections"],
            price=item["ticket_price"]["total"],
            currency=item["ticket_price"]["cur"],
        )


@register("amount_epoch")
class AmountEpochAdapter(BaseAdapter):
    """[{"amount": 52340, "ccy", "carrier_code", "number", "src", "dst", "dep_epoch", "arr_epoch", "layover_count"}]
    Bare list, price in minor units (cents), Unix-epoch times."""

    def extract_items(self, raw: Any) -> list[Any]:
        return raw

    def to_flight(self, item: Any, provider_id: str) -> Flight:
        code = item["carrier_code"]
        return build_flight(
            provider_id=provider_id,
            airline=code,
            flight_number=f'{code}{item["number"]}',
            origin=item["src"],
            destination=item["dst"],
            departure=datetime.fromtimestamp(item["dep_epoch"], tz=timezone.utc),
            arrival=datetime.fromtimestamp(item["arr_epoch"], tz=timezone.utc),
            stops=item["layover_count"],
            price=item["amount"] / 100,
            currency=item["ccy"],
        )


_PRICE_RE = re.compile(r"^\s*\$\s*([\d,]+(?:\.\d+)?)\s*$")


@register("offers_duration")
class OffersDurationAdapter(BaseAdapter):
    """{"offers": [{"airlineName", "flightCode": "BA 117", "origin_iata", "dest_iata",
    "departureLocal": "2026-10-01 18:30", "durationMinutes", "totalPrice": "$480.00", "numStops"}]}
    No arrival time (derived from duration), price is a formatted string."""

    def extract_items(self, raw: Any) -> list[Any]:
        return raw["offers"]

    def to_flight(self, item: Any, provider_id: str) -> Flight:
        match = _PRICE_RE.match(item["totalPrice"])
        if not match:
            raise ValueError(f'unparseable price {item["totalPrice"]!r}')
        amount = match.group(1)

        origin = item["origin_iata"]
        departure = datetime.strptime(item["departureLocal"], "%Y-%m-%d %H:%M").replace(
            tzinfo=local_tz(origin)
        )
        arrival = departure.astimezone(timezone.utc) + timedelta(minutes=item["durationMinutes"])
        return build_flight(
            provider_id=provider_id,
            airline=item["airlineName"],
            flight_number=item["flightCode"],
            origin=origin,
            destination=item["dest_iata"],
            departure=departure,
            arrival=arrival,
            stops=item["numStops"],
            price=float(amount.replace(",", "")),
        )


_DURATION_RE = re.compile(r"^(\d+)h(\d+)m$")


@register("compact_trips")
class CompactTripsAdapter(BaseAdapter):
    """{"trips": [{"airline_iata", "flt", "o", "d", "dep": "20261001T1830-0400", "dur": "7h05m",
    "price_minor", "cur", "nonstop"}]}
    Terse keys, basic-format ISO date, "7h05m" duration, boolean instead of a stop count."""

    def extract_items(self, raw: Any) -> list[Any]:
        return raw["trips"]

    def to_flight(self, item: Any, provider_id: str) -> Flight:
        match = _DURATION_RE.match(item["dur"])
        if not match:
            raise ValueError(f'unparseable duration {item["dur"]!r}')
        hours, minutes = map(int, match.groups())
        departure = datetime.strptime(item["dep"], "%Y%m%dT%H%M%z")
        return build_flight(
            provider_id=provider_id,
            airline=item["airline_iata"],
            flight_number=item["flt"],
            origin=item["o"],
            destination=item["d"],
            departure=departure,
            arrival=departure + timedelta(hours=hours, minutes=minutes),
            stops=0 if item["nonstop"] else 1,
            price=item["price_minor"] / 100,
            currency=item["cur"],
        )


@register("columnar")
class ColumnarAdapter(BaseAdapter):
    """{"columns": ["flight", "from", ...], "rows": [["BA117", "JFK", ...], ...]}
    Column-oriented table (like a CSV): rows are positional, times are UTC ('Z')."""

    def extract_items(self, raw: Any) -> list[Any]:
        columns = raw["columns"]
        return [dict(zip(columns, row, strict=True)) for row in raw["rows"]]

    def to_flight(self, item: Any, provider_id: str) -> Flight:
        return build_flight(
            provider_id=provider_id,
            airline=item["flight"][:2],
            flight_number=item["flight"],
            origin=item["from"],
            destination=item["to"],
            departure=datetime.fromisoformat(item["depart_utc"]),
            arrival=datetime.fromisoformat(item["arrive_utc"]),
            stops=item["stops"],
            price=item["price"],
            currency=item["cur"],
        )
