from rest_framework.response import Response
from rest_framework.views import APIView

from flights.domain import SearchQuery
from flights.reference import AIRPORTS
from flights.serializers import AirportSerializer, FlightSerializer, SearchParamsSerializer
from flights.services.aggregator import search_flights


class SearchView(APIView):
    """GET /api/search/?origin=JFK&destination=LHR&date=2026-10-01"""

    def get(self, request):
        params = SearchParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        query = SearchQuery(**params.validated_data)

        result = search_flights(query)

        return Response(
            {
                "query": {
                    "origin": query.origin,
                    "destination": query.destination,
                    "date": query.date.isoformat(),
                },
                "meta": {
                    "total_flights": len(result.flights),
                    "providers_total": result.providers_total,
                    "providers_ok": result.providers_ok,
                    "providers_failed": len(result.failures),
                    "failures": [{"provider_id": f.provider_id, "reason": f.reason} for f in result.failures],
                    "cached": result.cached,
                    "took_ms": result.took_ms,
                },
                "flights": FlightSerializer(result.flights, many=True).data,
            }
        )


class AirportsView(APIView):
    """GET /api/airports/ - the airports the mock providers cover."""

    def get(self, request):
        return Response(AirportSerializer(AIRPORTS.values(), many=True).data)


class HealthView(APIView):
    """GET /api/health/ - used by Render's health check and uptime pings."""

    throttle_classes: list = []

    def get(self, request):
        return Response({"status": "ok"})
