from django.db.models import QuerySet
from django_filters import rest_framework as filters

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Crew,
    Flight,
    Route,
)


class CityFilter(filters.FilterSet):
    country = filters.ModelChoiceFilter(
        field_name="country",
        queryset=Country.objects.all(),
        error_messages={
            "invalid_choice": (
                "Country with ID '%(value)s' was not found."
            ),
        },
    )
    country_name = filters.CharFilter(
        field_name="country__name",
        lookup_expr="icontains",
        error_messages={
            "required": "Country name is required.",
        },
    )
    name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains"
    )

    class Meta:
        model = City
        fields = []


class AirportFilter(filters.FilterSet):
    city = filters.ModelChoiceFilter(
        field_name="closest_big_city",
        queryset=City.objects.select_related("country"),
        error_messages={
            "invalid_choice": (
                "City with ID '%(value)s' was not found."
            ),
        },
        label="City id",
    )
    city_name = filters.CharFilter(
        field_name="closest_big_city__name",
        lookup_expr="icontains",
        label="City name",
    )
    country = filters.ModelChoiceFilter(
        field_name="closest_big_city__country",
        queryset=Country.objects.all(),
        error_messages={
            "invalid_choice": (
                "Country with ID '%(value)s' was not found."
            ),
        },
        label="Country id",
    )
    country_name = filters.CharFilter(
        field_name="closest_big_city__country__name",
        lookup_expr="icontains",
        error_messages={
            "required": "Country name is required.",
        },
        label="Country name",
    )
    name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label="Airport name",
    )

    class Meta:
        model = Airport
        fields = []


class AirplaneFilter(filters.FilterSet):
    airplane_type = filters.ModelChoiceFilter(
        queryset=AirplaneType.objects.all(),
        error_messages={
            "invalid_choice": (
                "Airplane type with ID '%(value)s' was not found."
            ),
        },
        label="Airplane type id"
    )
    airplane_type_name = filters.CharFilter(
        field_name="airplane_type__name",
        lookup_expr="icontains",
        label="Airplane type name"
    )
    name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label="Airplane name"
    )

    class Meta:
        model = Airplane
        fields = []


class CrewFilter(filters.FilterSet):
    first_name = filters.CharFilter(
        field_name="first_name",
        lookup_expr="icontains",
        label="Crew first name"
    )
    last_name = filters.CharFilter(
        field_name="last_name",
        lookup_expr="icontains",
        label="Crew last name"
    )
    flight = filters.ModelChoiceFilter(
        queryset=(
            Flight
            .objects
            .select_related(
                "route__source__closest_big_city__country",
                "route__destination__closest_big_city__country",
                "airplane__airplane_type"
            )
        ),
        field_name="flights",
        distinct=True,
        label="Flight id"
    )

    class Meta:
        model = Crew
        fields = []


class RouteFilter(filters.FilterSet):
    source = filters.ModelChoiceFilter(
        queryset=Airport.objects.select_related(
            "closest_big_city__country"
        ),
        error_messages={
            "invalid_choice": (
                "Source with ID '%(value)s' was not found."
            ),
        },
        label="Source id"
    )
    destination = filters.ModelChoiceFilter(
        queryset=Airport.objects.select_related(
            "closest_big_city__country"
        ),
        error_messages={
            "invalid_choice": (
                "Destination with ID '%(value)s' was not found."
            ),
        },
        label="Destination id"
    )
    source_city = filters.CharFilter(
        field_name="source__closest_big_city__name",
        lookup_expr="icontains",
        label="Source city name"
    )
    destination_city = filters.CharFilter(
        field_name="destination__closest_big_city__name",
        lookup_expr="icontains",
        label="Destination city name"
    )
    source_country = filters.CharFilter(
        field_name="source__closest_big_city__country__name",
        lookup_expr="icontains",
        label="Source country name"
    )
    destination_country = filters.CharFilter(
        field_name="destination__closest_big_city__country__name",
        lookup_expr="icontains",
        label="Destination country name"
    )

    class Meta:
        model = Route
        fields = []


class FlightFilter(filters.FilterSet):
    source = filters.ModelChoiceFilter(
        field_name="route__source",
        queryset=Airport.objects.select_related(
            "closest_big_city__country"
        ),
        error_messages={
            "invalid_choice": (
                "Route source with ID '%(value)s' was not found."
            ),
        },
        label="Route source airport ID",
    )

    destination = filters.ModelChoiceFilter(
        field_name="route__destination",
        queryset=Airport.objects.select_related(
            "closest_big_city__country"
        ),
        error_messages={
            "invalid_choice": (
                "Route destination with ID '%(value)s' was not found."
            ),
        },
        label="Route destination airport ID",
    )

    source_city = filters.CharFilter(
        field_name="route__source__closest_big_city__name",
        lookup_expr="icontains",
        label="Route source city",
    )

    destination_city = filters.CharFilter(
        field_name="route__destination__closest_big_city__name",
        lookup_expr="icontains",
        label="Route destination city",
    )

    departure_time = filters.DateTimeFilter(
        field_name="departure_time",
        input_formats=["%Y-%m-%d %H:%M"],
        label="Exact departure time",
    )

    departure_time_range = filters.IsoDateTimeFromToRangeFilter(
        field_name="departure_time",
        label="Departure time range",
    )

    arrival_time = filters.DateTimeFilter(
        field_name="arrival_time",
        input_formats=["%Y-%m-%d %H:%M"],
        label="Exact arrival time",
    )

    arrival_time_range = filters.IsoDateTimeFromToRangeFilter(
        field_name="arrival_time",
        label="Arrival time range",
    )

    airplane = filters.ModelChoiceFilter(
        queryset=Airplane.objects.select_related(
            "airplane_type"
        ),
        error_messages={
            "invalid_choice": (
                "Airplane with ID '%(value)s' was not found."
            ),
        },
        label="Airplane ID",
    )

    airplane_name = filters.CharFilter(
        field_name="airplane__name",
        lookup_expr="icontains",
        label="Airplane name",
    )

    crew = filters.ModelMultipleChoiceFilter(
        field_name="crew",
        queryset=Crew.objects.all(),
        label="Crew member IDs",
    )

    crew_last_names = filters.CharFilter(
        method="filter_crew_last_names",
        label="Crew last names (any)",
    )

    crew_all_last_names = filters.CharFilter(
        method="filter_crew_all_last_names",
        label="Crew last names (all)",
    )

    has_available_seats = filters.BooleanFilter(
        method="filter_has_available_seats",
        label="Has available seats",
    )

    def filter_has_available_seats(
        self,
        queryset: QuerySet,
        name: str,
        value: bool | None,
    ) -> QuerySet:
        if value is None:
            return queryset

        if value:
            return queryset.filter(available_seats__gt=0)

        return queryset.filter(available_seats=0)

    def filter_crew_last_names(
        self,
        queryset: QuerySet,
        name: str,
        value: str,
    ) -> QuerySet:
        last_names = [
            last_name.strip()
            for last_name in value.split(",")
            if last_name.strip()
        ]

        return queryset.filter(
            crew__last_name__in=last_names
        ).distinct()

    def filter_crew_all_last_names(
        self,
        queryset: QuerySet,
        name: str,
        value: str,
    ) -> QuerySet:
        last_names = [
            last_name.strip()
            for last_name in value.split(",")
            if last_name.strip()
        ]

        for last_name in last_names:
            queryset = queryset.filter(
                crew__last_name__iexact=last_name
            )

        return queryset.distinct()

    class Meta:
        model = Flight
        fields = []


class PopularRouteFilter(filters.FilterSet):
    limit = filters.NumberFilter(
        method="limit_popular_routes",
        label="Limit top popular routes",
        min_value=1,
    )

    def limit_popular_routes(
        self,
        queryset: QuerySet,
        name: str,
        value: int | None,
    ) -> QuerySet:
        if value is not None:
            return queryset[:value]

        return queryset
