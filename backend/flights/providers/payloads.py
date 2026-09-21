"""Renderers: turn generated itineraries into each provider family's raw payload.

These are the mock 'provider APIs'. Each returns a different shape on purpose;
flights.adapters holds the matching parsers. Keys of RENDERERS are the schema
names that adapters register under.
"""
from datetime import timezone
from typing import Callable

from flights.providers.itineraries import Itinerary
from flights.reference import SYMBOL_BY_CURRENCY, from_usd

Renderer = Callable[[list[Itinerary], str], object]  # (itineraries, currency) -> raw payload


def _duration_minutes(it: Itinerary) -> int:
    delta = it.last.arrival.astimezone(timezone.utc) - it.first.departure.astimezone(timezone.utc)
    return round(delta.total_seconds() / 60)


def render_fare_iso(itineraries, currency):
    return {
        "status": "ok",
        "results": [
            {
                "flightNo": it.flight_code,
                "carrier": it.first.airline.name,
                "from": it.first.origin,
                "to": it.last.destination,
                "departs": it.first.departure.isoformat(),
                "arrives": it.last.arrival.isoformat(),
                "fare": from_usd(it.price_usd, currency),
                "currency": currency,
                "stops": it.stops,
            }
            for it in itineraries
        ],
    }


def render_ticket_price_nested(itineraries, currency):
    def moment(dt):
        return {"date": dt.strftime("%Y-%m-%d"), "time": dt.strftime("%H:%M"), "tz": str(dt.tzinfo)}

    return {
        "data": {
            "itineraries": [
                {
                    "ticket_price": {"total": from_usd(it.price_usd, currency), "cur": currency},
                    "airline": {"code": it.first.airline.code, "name": it.first.airline.name},
                    "flight": it.first.number,
                    "origin": {"airport": it.first.origin},
                    "destination": {"airport": it.last.destination},
                    "depart": moment(it.first.departure),
                    "arrive": moment(it.last.arrival),
                    "connections": it.stops,
                }
                for it in itineraries
            ]
        }
    }


def render_amount_epoch(itineraries, currency):
    return [
        {
            "offer_id": f"{it.flight_code}-{int(it.first.departure.timestamp())}",
            "amount": round(from_usd(it.price_usd, currency) * 100),
            "ccy": currency,
            "carrier_code": it.first.airline.code,
            "number": it.first.number,
            "src": it.first.origin,
            "dst": it.last.destination,
            "dep_epoch": int(it.first.departure.timestamp()),
            "arr_epoch": int(it.last.arrival.timestamp()),
            "layovers": [
                {"airport": leg.destination, "minutes": _layover_minutes(it, i)}
                for i, leg in enumerate(it.legs[:-1])
            ],
        }
        for it in itineraries
    ]


def _layover_minutes(it: Itinerary, index: int) -> int:
    gap = it.legs[index + 1].departure - it.legs[index].arrival
    return round(gap.total_seconds() / 60)


def render_offers_duration(itineraries, currency):
    symbol = SYMBOL_BY_CURRENCY[currency]
    return {
        "offers": [
            {
                "airlineName": it.first.airline.name,
                "flightCode": f"{it.first.airline.code} {it.first.number}",
                "origin_iata": it.first.origin,
                "dest_iata": it.last.destination,
                "departureLocal": it.first.departure.strftime("%Y-%m-%d %H:%M"),
                "durationMinutes": _duration_minutes(it),
                "totalPrice": f"{symbol}{from_usd(it.price_usd, currency):,.2f}",
                "numStops": it.stops,
            }
            for it in itineraries
        ]
    }


def render_segments_pricing(itineraries, currency):
    def point(iata, dt):
        return {"iata": iata, "time": dt.strftime("%Y-%m-%dT%H:%M:%S")}

    flights = []
    for it in itineraries:
        total = from_usd(it.price_usd, currency)
        taxes = round(total * 0.18, 2)
        flights.append(
            {
                "segments": [
                    {
                        "carrier": leg.airline.code,
                        "flight_number": str(leg.number),
                        "from": point(leg.origin, leg.departure),
                        "to": point(leg.destination, leg.arrival),
                    }
                    for leg in it.legs
                ],
                "pricing": {"base": round(total - taxes, 2), "taxes": taxes, "currency": currency},
            }
        )
    return {"flights": flights}


def render_compact_trips(itineraries, currency):
    def duration(it):
        hours, minutes = divmod(_duration_minutes(it), 60)
        return f"{hours}h{minutes:02d}m"

    return {
        "trips": [
            {
                "airline_iata": it.first.airline.code,
                "flt": it.flight_code,
                "o": it.first.origin,
                "d": it.last.destination,
                "dep": it.first.departure.strftime("%Y%m%dT%H%M%z"),
                "dur": duration(it),
                "price_minor": round(from_usd(it.price_usd, currency) * 100),
                "cur": currency,
                "nonstop": it.stops == 0,
            }
            for it in itineraries
        ]
    }


def render_columnar(itineraries, currency):
    def utc(dt):
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "columns": ["flight", "from", "to", "depart_utc", "arrive_utc", "price", "cur", "stops"],
        "rows": [
            [
                it.flight_code,
                it.first.origin,
                it.last.destination,
                utc(it.first.departure),
                utc(it.last.arrival),
                from_usd(it.price_usd, currency),
                currency,
                it.stops,
            ]
            for it in itineraries
        ],
    }


# schema name -> (renderer, currencies this family can quote in)
# The "offers_duration" family prints a currency symbol, so it is limited to unambiguous ones.
RENDERERS: dict[str, tuple[Renderer, tuple[str, ...]]] = {
    "fare_iso": (render_fare_iso, ("USD", "EUR", "GBP", "CAD")),
    "ticket_price_nested": (render_ticket_price_nested, ("USD", "EUR", "GBP", "AED")),
    "amount_epoch": (render_amount_epoch, ("USD", "EUR", "INR", "AED")),
    "offers_duration": (render_offers_duration, ("USD", "EUR", "GBP")),
    "segments_pricing": (render_segments_pricing, ("USD", "EUR", "GBP", "CAD")),
    "compact_trips": (render_compact_trips, ("USD", "EUR", "GBP", "INR")),
    "columnar": (render_columnar, ("USD", "EUR", "GBP", "AED")),
}
