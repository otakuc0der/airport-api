from typing import Any
from uuid import UUID

from django.db import transaction
from rest_framework import serializers

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Crew,
    Flight,
    Order,
    Route,
    Ticket,
)
from airport.utils.validators import (
    validate_flight_departure_and_arrival_time,
    validate_route_source_destination,
    validate_ticket_rows_and_seats_in_row,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name", "country"]


class CityListSerializer(CitySerializer):
    country = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


class CityDetailSerializer(CitySerializer):
    country = CountrySerializer(read_only=True)


class AirportSerializer(serializers.ModelSerializer):
    closest_big_city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.select_related("country"),
    )

    class Meta:
        model = Airport
        fields = ["id", "name", "closest_big_city", "image"]


class AirportListSerializer(AirportSerializer):
    closest_big_city = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )


class AirportDetailSerializer(AirportSerializer):
    closest_big_city = CityDetailSerializer(read_only=True)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Airplane
        fields = [
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "image",
            "capacity",
        ]


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = [
            "id",
            "first_name",
            "last_name",
            "photo",
        ]


class CrewListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = [
            "id",
            "full_name",
            "photo",
        ]


class RouteSerializer(serializers.ModelSerializer):
    source = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.select_related("closest_big_city"),
    )
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.select_related("closest_big_city"),
    )

    class Meta:
        model = Route
        fields = [
            "id",
            "source",
            "destination",
            "distance",
        ]

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        source = attrs.get("source")
        destination = attrs.get("destination")

        if self.instance is not None:
            source = attrs.get(
                "source",
                self.instance.source,
            )
            destination = attrs.get(
                "destination",
                self.instance.destination,
            )

        validate_route_source_destination(
            source,
            destination,
            serializers.ValidationError,
        )

        return attrs


class RouteListSerializer(RouteSerializer):
    source_city = serializers.CharField(
        read_only=True, source="source.closest_big_city.name"
    )
    destination_city = serializers.CharField(
        read_only=True, source="destination.closest_big_city.name"
    )
    source_airport = serializers.CharField(read_only=True, source="source.name")
    destination_airport = serializers.CharField(
        read_only=True, source="destination.name"
    )

    class Meta(RouteSerializer.Meta):
        fields = [
            "id",
            "source_city",
            "destination_city",
            "source_airport",
            "destination_airport",
            "distance",
        ]


class RouteDetailSerializer(RouteSerializer):
    source = AirportDetailSerializer(read_only=True)
    destination = AirportDetailSerializer(read_only=True)


class FlightSerializer(serializers.ModelSerializer):
    route = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.select_related(
            "source__closest_big_city", "destination__closest_big_city"
        ),
    )
    airplane = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.select_related("airplane_type"),
    )
    crew = serializers.PrimaryKeyRelatedField(
        queryset=Crew.objects.all(),
        many=True,
    )

    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
        ]

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        departure_time = attrs.get("departure_time")
        arrival_time = attrs.get("arrival_time")

        if self.instance is not None:
            departure_time = attrs.get(
                "departure_time",
                self.instance.departure_time,
            )
            arrival_time = attrs.get(
                "arrival_time",
                self.instance.arrival_time,
            )

        validate_flight_departure_and_arrival_time(
            departure_time,
            arrival_time,
            serializers.ValidationError,
        )

        return attrs


class FlightListSerializer(FlightSerializer):
    source = serializers.CharField(
        read_only=True, source="route.source.closest_big_city.name"
    )
    destination = serializers.CharField(
        read_only=True, source="route.destination.closest_big_city.name"
    )
    airplane = serializers.SlugRelatedField(read_only=True, slug_field="name")
    airplane_type = serializers.CharField(
        read_only=True, source="airplane.airplane_type.name"
    )
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    flight_duration = serializers.DurationField(read_only=True)

    class Meta(FlightSerializer.Meta):
        fields = [
            "id",
            "source",
            "destination",
            "airplane",
            "airplane_type",
            "crew",
            "departure_time",
            "arrival_time",
            "flight_duration",
        ]


class FlightDetailSerializer(FlightSerializer):
    route = RouteDetailSerializer(read_only=True)
    airplane = AirplaneDetailSerializer(read_only=True)
    flight_duration = serializers.DurationField(read_only=True)
    crew = CrewSerializer(many=True, read_only=True)

    class Meta(FlightSerializer.Meta):
        fields = [
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "flight_duration",
            "crew",
        ]


class TicketSerializer(serializers.ModelSerializer):
    flight = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.select_related(
            "route__source__closest_big_city__country",
            "route__destination__closest_big_city__country",
            "airplane__airplane_type",
        ),
    )

    class Meta:
        model = Ticket
        fields = [
            "id",
            "row",
            "seat",
            "flight",
        ]

    def validate(
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        flight = attrs.get(
            "flight",
            getattr(self.instance, "flight", None),
        )
        row = attrs.get(
            "row",
            getattr(self.instance, "row", None),
        )
        seat = attrs.get(
            "seat",
            getattr(self.instance, "seat", None),
        )

        validate_ticket_rows_and_seats_in_row(
            flight,
            row,
            seat,
            serializers.ValidationError,
        )

        return attrs


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        allow_empty=False,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "tickets",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_tickets(
        self,
        tickets: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        requested_seats: set[tuple[UUID, int, int]] = set()

        for ticket in tickets:
            flight = ticket["flight"]
            row = ticket["row"]
            seat = ticket["seat"]

            seat_key = (
                flight.pk,
                row,
                seat,
            )

            if seat_key in requested_seats:
                raise serializers.ValidationError(
                    (
                        f"Seat {row}-{seat} is duplicated "
                        "in this order."
                    )
                )

            if Ticket.objects.filter(
                flight=flight,
                row=row,
                seat=seat,
            ).exists():
                raise serializers.ValidationError(
                    (
                        f"Seat {row}-{seat} is already booked "
                        "for this flight."
                    )
                )

            requested_seats.add(seat_key)

        return tickets

    def create(
        self,
        validated_data: dict[str, Any],
    ) -> Order:
        tickets_data = validated_data.pop("tickets")

        with transaction.atomic():
            order = Order.objects.create(**validated_data)

            for ticket_data in tickets_data:
                Ticket.objects.create(
                    order=order,
                    **ticket_data,
                )

        return order


class OrderListSerializer(OrderSerializer):
    tickets_count = serializers.IntegerField(read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = [
            "id",
            "tickets_count",
            "created_at",
        ]


class OrderDetailSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = [
            "id",
            "tickets",
            "created_at",
        ]
