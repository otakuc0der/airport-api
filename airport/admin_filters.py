from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from airport.models import (
    Airplane,
    AirplaneType,
    City,
    Country,
)


class BaseRelatedFilter(admin.SimpleListFilter):
    field: str = ""

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet,
    ) -> QuerySet:
        if value := self.value():
            return queryset.filter(**{f"{self.field}_id": value})

        return queryset


# City filters
class BaseCityFilter(BaseRelatedFilter):
    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,
    ) -> list[tuple[str, str]]:
        cache_name = "_airport_city_filter_lookups"

        if not hasattr(request, cache_name):
            lookups = [
                (
                    str(city.pk),
                    f"{city.name} ({city.country.name})",
                )
                for city in (
                    City.objects.select_related("country").order_by(
                        "country__name", "name"
                    )
                )
            ]

            setattr(request, cache_name, lookups)

        return getattr(request, cache_name)


class SourceCityFilter(BaseCityFilter):
    title = "source city"
    parameter_name = "source_city"


class DestinationCityFilter(BaseCityFilter):
    title = "destination city"
    parameter_name = "destination_city"


class RouteSourceCityFilter(SourceCityFilter):
    field = "source__closest_big_city"


class RouteDestinationCityFilter(DestinationCityFilter):
    field = "destination__closest_big_city"


class FlightSourceCityFilter(SourceCityFilter):
    field = "route__source__closest_big_city"


class FlightDestinationCityFilter(DestinationCityFilter):
    field = "route__destination__closest_big_city"


class TicketSourceCityFilter(SourceCityFilter):
    field = "flight__route__source__closest_big_city"


class TicketDestinationCityFilter(DestinationCityFilter):
    field = "flight__route__destination__closest_big_city"


# Country filters
class BaseCountryFilter(BaseRelatedFilter):
    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,
    ) -> list[tuple[str, str]]:
        cache_name = "_airport_country_filter_lookups"

        if not hasattr(request, cache_name):
            lookups = [
                (
                    str(country.pk),
                    country.name,
                )
                for country in Country.objects.order_by("name")
            ]

            setattr(request, cache_name, lookups)

        return getattr(request, cache_name)


class SourceCountryFilter(BaseCountryFilter):
    title = "source country"
    parameter_name = "source_country"


class DestinationCountryFilter(BaseCountryFilter):
    title = "destination country"
    parameter_name = "destination_country"


class RouteSourceCountryFilter(SourceCountryFilter):
    field = "source__closest_big_city__country"


class RouteDestinationCountryFilter(DestinationCountryFilter):
    field = "destination__closest_big_city__country"


class FlightSourceCountryFilter(SourceCountryFilter):
    field = "route__source__closest_big_city__country"


class FlightDestinationCountryFilter(DestinationCountryFilter):
    field = "route__destination__closest_big_city__country"


class TicketSourceCountryFilter(SourceCountryFilter):
    field = "flight__route__source__closest_big_city__country"


class TicketDestinationCountryFilter(DestinationCountryFilter):
    field = "flight__route__destination__closest_big_city__country"


# Airplane filters
class AirplaneTypeFilter(admin.SimpleListFilter):
    title = "airplane type"
    parameter_name = "airplane_type"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,
    ) -> list[tuple[str, str]]:
        return [
            (
                str(airplane_type.pk),
                airplane_type.name,
            )
            for airplane_type in (AirplaneType.objects.order_by("name"))
        ]

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet,
    ) -> QuerySet:
        if value := self.value():
            return queryset.filter(airplane__airplane_type_id=value)

        return queryset


class AirplaneFilter(admin.SimpleListFilter):
    title = "airplane"
    parameter_name = "airplane"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,
    ) -> list[tuple[str, str]]:
        return [
            (
                str(airplane.pk),
                airplane.name,
            )
            for airplane in Airplane.objects.order_by("name")
        ]

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet,
    ) -> QuerySet:
        if value := self.value():
            return queryset.filter(airplane_id=value)

        return queryset
