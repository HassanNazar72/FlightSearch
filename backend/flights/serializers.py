from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from flights.reference import AIRPORTS

MAX_DAYS_AHEAD = 330


class SearchParamsSerializer(serializers.Serializer):
    """Validates ?origin=&destination=&date= and normalises the airport codes."""

    origin = serializers.CharField(min_length=3, max_length=3)
    destination = serializers.CharField(min_length=3, max_length=3)
    date = serializers.DateField()

    def _airport(self, value: str) -> str:
        code = value.upper()
        if code not in AIRPORTS:
            raise serializers.ValidationError(f"Unknown airport '{value}'. See /api/airports/.")
        return code

    def validate_origin(self, value):
        return self._airport(value)

    def validate_destination(self, value):
        return self._airport(value)

    def validate_date(self, value):
        today = timezone.now().date()
        if value < today:
            raise serializers.ValidationError("Date is in the past.")
        if value > today + timedelta(days=MAX_DAYS_AHEAD):
            raise serializers.ValidationError(f"Date is more than {MAX_DAYS_AHEAD} days ahead.")
        return value

    def validate(self, attrs):
        if attrs["origin"] == attrs["destination"]:
            raise serializers.ValidationError("Origin and destination must differ.")
        return attrs


class FlightSerializer(serializers.Serializer):
    """Canonical flight schema. Times are ISO-8601 in the airport's local time (with UTC offset)."""

    id = serializers.CharField()
    provider_id = serializers.CharField()
    airline = serializers.CharField()
    flight_number = serializers.CharField()
    origin = serializers.CharField()
    destination = serializers.CharField()
    departure_time = serializers.SerializerMethodField()
    arrival_time = serializers.SerializerMethodField()
    duration_minutes = serializers.IntegerField()
    stops = serializers.IntegerField()
    price_usd = serializers.FloatField()
    currency = serializers.CharField()
    score = serializers.FloatField()
    tags = serializers.ListField(child=serializers.CharField())

    # DRF's DateTimeField would convert to UTC and drop the local offset, so format by hand.
    def get_departure_time(self, obj) -> str:
        return obj.departure_time.isoformat(timespec="minutes")

    def get_arrival_time(self, obj) -> str:
        return obj.arrival_time.isoformat(timespec="minutes")


class AirportSerializer(serializers.Serializer):
    code = serializers.CharField()
    city = serializers.CharField()
