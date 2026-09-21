"""Renderers: turn generated itineraries into each provider family's raw payload.

These are the mock 'provider APIs'. Each returns a different shape on purpose;
flights.adapters holds the matching parsers. Keys of RENDERERS are the schema
names that adapters register under. All prices are USD.
"""
from datetime import timezone
from typing import Callable

from flights.providers.itineraries import Itinerary

Renderer = Callable[[list[Itinerary]], object]


def render_fare_iso(itineraries):
    return {
        "status": "ok",
        "results": [
            {
                "flightNo": it.flight_code,
                "carrier": it.airline.name,
                "from": it.origin,
                "to": it.destination,
                "departs": it.departure.isoformat(),
                "arrives": it.arrival.isoformat(),
                "fare": it.price_usd,
                "currency": "USD",
                "stops": it.stops,
            }
            for it in itineraries
        ],
    }


def render_ticket_price_nested(itineraries):
    def moment(dt):
        return {"date": dt.strftime("%Y-%m-%d"), "time": dt.strftime("%H:%M"), "tz": str(dt.tzinfo)}

    return {
        "data": {
            "itineraries": [
                {
                    "ticket_price": {"total": it.price_usd, "cur": "USD"},
                    "airline": {"code": it.airline.code, "name": it.airline.name},
                    "flight": it.number,
                    "origin": {"airport": it.origin},
                    "destination": {"airport": it.destination},
                    "depart": moment(it.departure),
                    "arrive": moment(it.arrival),
                    "connections": it.stops,
                }
                for it in itineraries
            ]
        }
    }


def render_amount_epoch(itineraries):
    return [
        {
            "offer_id": f"{it.flight_code}-{int(it.departure.timestamp())}",
            "amount": round(it.price_usd * 100),
            "ccy": "USD",
            "carrier_code": it.airline.code,
            "number": it.number,
            "src": it.origin,
            "dst": it.destination,
            "dep_epoch": int(it.departure.timestamp()),
            "arr_epoch": int(it.arrival.timestamp()),
            "layover_count": it.stops,
        }
        for it in itineraries
    ]


def render_offers_duration(itineraries):
    return {
        "offers": [
            {
                "airlineName": it.airline.name,
                "flightCode": f"{it.airline.code} {it.number}",
                "origin_iata": it.origin,
                "dest_iata": it.destination,
                "departureLocal": it.departure.strftime("%Y-%m-%d %H:%M"),
                "durationMinutes": it.duration_minutes,
                "totalPrice": f"${it.price_usd:,.2f}",
                "numStops": it.stops,
            }
            for it in itineraries
        ]
    }


def render_compact_trips(itineraries):
    def duration(it):
        hours, minutes = divmod(it.duration_minutes, 60)
        return f"{hours}h{minutes:02d}m"

    return {
        "trips": [
            {
                "airline_iata": it.airline.code,
                "flt": it.flight_code,
                "o": it.origin,
                "d": it.destination,
                "dep": it.departure.strftime("%Y%m%dT%H%M%z"),
                "dur": duration(it),
                "price_minor": round(it.price_usd * 100),
                "cur": "USD",
                "nonstop": it.stops == 0,
            }
            for it in itineraries
        ]
    }


def render_columnar(itineraries):
    def utc(dt):
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "columns": ["flight", "from", "to", "depart_utc", "arrive_utc", "price", "cur", "stops"],
        "rows": [
            [it.flight_code, it.origin, it.destination, utc(it.departure), utc(it.arrival), it.price_usd, "USD", it.stops]
            for it in itineraries
        ],
    }


RENDERERS: dict[str, Renderer] = {
    "fare_iso": render_fare_iso,
    "ticket_price_nested": render_ticket_price_nested,
    "amount_epoch": render_amount_epoch,
    "offers_duration": render_offers_duration,
    "compact_trips": render_compact_trips,
    "columnar": render_columnar,
}
