from datetime import datetime
from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from airport.admin_filters import (
    AirplaneFilter,
    AirplaneTypeFilter,
    FlightDestinationCityFilter,
    FlightDestinationCountryFilter,
    FlightSourceCityFilter,
    FlightSourceCountryFilter,
    RouteDestinationCityFilter,
    RouteDestinationCountryFilter,
    RouteSourceCityFilter,
    RouteSourceCountryFilter,
    TicketDestinationCityFilter,
    TicketDestinationCountryFilter,
    TicketSourceCityFilter,
    TicketSourceCountryFilter,
)
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


@admin.register(Crew)
class CrewAdmin(ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "photo",
    ]
    search_fields = [
        "first_name",
        "last_name",
    ]


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = [
        "name",
    ]
    search_fields = [
        "name",
    ]


@admin.register(City)
class CityAdmin(ModelAdmin):
    list_select_related = [
        "country",
    ]
    list_display = [
        "name",
        "get_country_name",
    ]
    list_filter = [
        "country",
    ]
    search_fields = [
        "name",
        "country__name",
    ]

    @admin.display(
        ordering="country__name",
        description="Country",
    )
    def get_country_name(
        self,
        obj: City,
    ) -> str:
        return obj.country.name


@admin.register(Airport)
class AirportAdmin(ModelAdmin):
    list_select_related = [
        "closest_big_city__country",
    ]
    list_display = [
        "name",
        "get_closest_big_city",
        "get_country",
        "image",
    ]
    list_filter = [
        "closest_big_city__country",
    ]
    search_fields = [
        "name",
        "closest_big_city__name",
        "closest_big_city__country__name",
    ]

    def formfield_for_foreignkey(
        self,
        db_field: models.Field,
        request: HttpRequest,
        **kwargs: Any,
    ) -> forms.Field | None:
        if db_field.name == "closest_big_city":
            kwargs["queryset"] = (
                City.objects
                .select_related("country")
                .order_by(
                    "country__name",
                    "name",
                )
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    @admin.display(
        ordering="closest_big_city__name",
        description="Closest big city",
    )
    def get_closest_big_city(
        self,
        obj: Airport,
    ) -> str:
        return obj.closest_big_city.name

    @admin.display(
        ordering="closest_big_city__country__name",
        description="Country",
    )
    def get_country(
        self,
        obj: Airport,
    ) -> str:
        return obj.closest_big_city.country.name


@admin.register(AirplaneType)
class AirplaneTypeAdmin(ModelAdmin):
    list_display = [
        "name",
    ]
    search_fields = [
        "name",
    ]


@admin.register(Airplane)
class AirplaneAdmin(ModelAdmin):
    list_select_related = [
        "airplane_type",
    ]
    list_display = [
        "name",
        "get_airplane_type",
        "rows",
        "seats_in_row",
        "capacity",
        "image",
    ]
    list_filter = [
        "airplane_type",
    ]
    search_fields = [
        "name",
        "airplane_type__name",
    ]

    @admin.display(
        ordering="airplane_type__name",
        description="Airplane type",
    )
    def get_airplane_type(
        self,
        obj: Airplane,
    ) -> str:
        return obj.airplane_type.name


@admin.register(Route)
class RouteAdmin(ModelAdmin):
    list_display = [
        "get_source_destination",
        "get_source",
        "get_destination",
        "distance",
    ]
    list_filter = [
        RouteSourceCountryFilter,
        RouteDestinationCountryFilter,
        RouteSourceCityFilter,
        RouteDestinationCityFilter,
    ]
    search_fields = [
        "source__name",
        "destination__name",
        "source__closest_big_city__name",
        "destination__closest_big_city__name",
        "source__closest_big_city__country__name",
        "destination__closest_big_city__country__name",
    ]

    def formfield_for_foreignkey(
        self,
        db_field: models.Field,
        request: HttpRequest,
        **kwargs: Any,
    ) -> forms.Field | None:
        if db_field.name in {
            "source",
            "destination",
        }:
            kwargs["queryset"] = (
                Airport.objects
                .select_related(
                    "closest_big_city__country",
                )
                .order_by("name")
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def get_queryset(
        self,
        request: HttpRequest,
    ) -> QuerySet[Route]:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "source__closest_big_city__country",
                "destination__closest_big_city__country",
            )
        )

    @admin.display(
        ordering="source__name",
        description="Source airport",
    )
    def get_source(
        self,
        obj: Route,
    ) -> str:
        return obj.source.name

    @admin.display(
        ordering="destination__name",
        description="Destination airport",
    )
    def get_destination(
        self,
        obj: Route,
    ) -> str:
        return obj.destination.name

    @admin.display(
        ordering="source__closest_big_city__name",
        description="Source - Destination",
    )
    def get_source_destination(
        self,
        obj: Route,
    ) -> str:
        return (
            f"{obj.source.closest_big_city.name} ➝ "
            f"{obj.destination.closest_big_city.name}"
        )


class FlightAdminForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = "__all__"

    def clean_status(self) -> str:
        flight_status = self.cleaned_data["status"]

        if flight_status == Flight.Status.CANCELLED:
            raise ValidationError(
                (
                    "Flight cannot be cancelled by changing "
                    "its status directly."
                )
            )

        return flight_status


@admin.register(Flight)
class FlightAdmin(ModelAdmin):
    form = FlightAdminForm

    list_display = [
        "get_route",
        "get_airplane",
        "departure_time",
        "arrival_time",
        "flight_duration",
        "status",
        "get_current_state",
    ]

    list_filter = [
        "status",
        FlightSourceCountryFilter,
        FlightDestinationCountryFilter,
        FlightSourceCityFilter,
        FlightDestinationCityFilter,
        AirplaneTypeFilter,
        AirplaneFilter,
        "departure_time",
        "arrival_time",
    ]

    search_fields = [
        "route__source__name",
        "route__destination__name",
        "route__source__closest_big_city__name",
        "route__destination__closest_big_city__name",
        "route__source__closest_big_city__country__name",
        "route__destination__closest_big_city__country__name",
        "airplane__name",
        "airplane__airplane_type__name",
    ]

    filter_horizontal = [
        "crew",
    ]

    ordering = [
        "-departure_time",
    ]

    readonly_fields = [
        "get_current_state",
    ]

    def has_change_permission(
        self,
        request: HttpRequest,
        obj: Flight | None = None,
    ) -> bool:
        if (
            obj is not None
            and obj.status == Flight.Status.CANCELLED
        ):
            return False

        return super().has_change_permission(
            request,
            obj,
        )

    def formfield_for_foreignkey(
        self,
        db_field: models.Field,
        request: HttpRequest,
        **kwargs: Any,
    ) -> forms.Field | None:
        if db_field.name == "route":
            kwargs["queryset"] = (
                Route.objects
                .select_related(
                    "source__closest_big_city__country",
                    "destination__closest_big_city__country",
                )
            )

        elif db_field.name == "airplane":
            kwargs["queryset"] = (
                Airplane.objects
                .select_related(
                    "airplane_type",
                )
                .order_by("name")
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def get_queryset(
        self,
        request: HttpRequest,
    ) -> QuerySet[Flight]:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "route__source__closest_big_city__country",
                "route__destination__closest_big_city__country",
                "airplane__airplane_type",
            )
        )

    @admin.display(
        ordering="route__source__closest_big_city__name",
        description="Route",
    )
    def get_route(
        self,
        obj: Flight,
    ) -> str:
        source = obj.route.source.closest_big_city
        destination = obj.route.destination.closest_big_city

        return (
            f"{source.name} ({source.country.name}) ➝ "
            f"{destination.name} "
            f"({destination.country.name})"
        )

    @admin.display(
        ordering="airplane__name",
        description="Airplane",
    )
    def get_airplane(
        self,
        obj: Flight,
    ) -> str:
        airplane = obj.airplane

        return (
            f"{airplane.name} | "
            f"{airplane.airplane_type.name} | "
            f"{airplane.capacity} seats"
        )

    @admin.display(
        description="Current state",
    )
    def get_current_state(
        self,
        obj: Flight,
    ) -> str:
        return obj.flight_state


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1
    min_num = 1
    validate_min = True

    fields = [
        "flight",
        "row",
        "seat",
        "status",
    ]

    readonly_fields = [
        "status",
    ]

    autocomplete_fields = [
        "flight",
    ]

    def get_queryset(
        self,
        request: HttpRequest,
    ) -> QuerySet[Ticket]:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "flight__airplane__airplane_type",
                "flight__route__source__closest_big_city__country",
                "flight__route__destination__closest_big_city__country",
            )
        )

    def formfield_for_foreignkey(
        self,
        db_field: models.Field,
        request: HttpRequest,
        **kwargs: Any,
    ) -> forms.Field | None:
        if db_field.name == "flight":
            kwargs["queryset"] = (
                Flight.objects
                .select_related(
                    "airplane__airplane_type",
                    "route__source__closest_big_city__country",
                    "route__destination__closest_big_city__country",
                )
                .order_by("-departure_time")
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = [
        "get_ticket_route",
        "departure_time",
        "arrival_time",
        "row",
        "seat",
        "status",
        "get_user",
    ]

    list_filter = [
        "status",
        TicketSourceCountryFilter,
        TicketDestinationCountryFilter,
        TicketSourceCityFilter,
        TicketDestinationCityFilter,
        "flight__departure_time",
        "order__created_at",
    ]

    search_fields = [
        "order__user__email",
        "flight__airplane__name",
        "flight__route__source__name",
        "flight__route__destination__name",
        "flight__route__source__closest_big_city__name",
        "flight__route__destination__closest_big_city__name",
    ]

    ordering = [
        "-flight__departure_time",
    ]

    autocomplete_fields = [
        "flight",
        "order",
    ]

    readonly_fields = [
        "status",
    ]

    def formfield_for_foreignkey(
        self,
        db_field: models.Field,
        request: HttpRequest,
        **kwargs: Any,
    ) -> forms.Field | None:
        if db_field.name == "flight":
            kwargs["queryset"] = (
                Flight.objects
                .select_related(
                    "route__source__closest_big_city__country",
                    "route__destination__closest_big_city__country",
                    "airplane__airplane_type",
                )
                .order_by("-departure_time")
            )

        elif db_field.name == "order":
            kwargs["queryset"] = (
                Order.objects
                .select_related("user")
                .order_by("-created_at")
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def get_queryset(
        self,
        request: HttpRequest,
    ) -> QuerySet[Ticket]:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "flight__airplane__airplane_type",
                "flight__route__source__closest_big_city__country",
                "flight__route__destination__closest_big_city__country",
                "order__user",
            )
        )

    @admin.display(
        ordering="flight__route__source__closest_big_city__name",
        description="Route",
    )
    def get_ticket_route(
        self,
        obj: Ticket,
    ) -> str:
        source = obj.flight.route.source.closest_big_city
        destination = (
            obj.flight.route.destination.closest_big_city
        )

        return (
            f"{source.name} ({source.country.name}) → "
            f"{destination.name} "
            f"({destination.country.name})"
        )

    @admin.display(
        ordering="flight__departure_time",
        description="Departure",
    )
    def departure_time(
        self,
        obj: Ticket,
    ) -> datetime:
        return obj.flight.departure_time

    @admin.display(
        ordering="flight__arrival_time",
        description="Arrival",
    )
    def arrival_time(
        self,
        obj: Ticket,
    ) -> datetime:
        return obj.flight.arrival_time

    @admin.display(
        ordering="order__user__email",
        description="User",
    )
    def get_user(
        self,
        obj: Ticket,
    ) -> str:
        return obj.order.user.email

    def has_add_permission(
        self,
        request: HttpRequest,
    ) -> bool:
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    inlines = [
        TicketInline,
    ]

    list_display = [
        "user",
        "created_at",
        "status",
        "tickets_count",
    ]

    list_filter = [
        "status",
        "created_at",
    ]

    search_fields = [
        "user__email",
    ]

    ordering = [
        "-created_at",
    ]

    readonly_fields = [
        "status",
        "created_at",
    ]

    def get_queryset(
        self,
        request: HttpRequest,
    ) -> QuerySet[Order]:
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            .annotate(
                tickets_total=Count("tickets"),
            )
        )

    @admin.display(
        ordering="tickets_total",
        description="Tickets total",
    )
    def tickets_count(
        self,
        obj: Order,
    ) -> int:
        return getattr(
            obj,
            "tickets_total",
            0,
        )
