from django.contrib import admin
from django.contrib.admin import ModelAdmin

from airport.models import (
    Crew,
    Country,
    City,
    Airport,
    AirplaneType,
    Airplane,
)


@admin.register(Crew)
class CrewAdmin(ModelAdmin):
    list_display = ["first_name", "last_name"]
    search_fields = ["first_name", "last_name"]


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(City)
class CityAdmin(ModelAdmin):
    list_select_related = ["country"]
    list_display = ["name", "get_country_name"]
    list_filter = ["country__name"]
    search_fields = ["name", "country__name"]

    @admin.display(
        ordering="country__name",
        description="Country",
    )
    def get_country_name(self, obj: City) -> str:
        return obj.country.name


@admin.register(Airport)
class AirportAdmin(ModelAdmin):
    list_select_related = ["closest_big_city"]
    list_display = ["name", "get_closest_big_city_name"]
    list_filter = ["closest_big_city__name"]
    search_fields = ["name", "closest_big_city__name"]

    @admin.display(
        ordering="closest_big_city__name",
        description="Closest big city",
    )
    def get_closest_big_city_name(self, obj: Airport) -> str:
        return obj.closest_big_city.name


@admin.register(AirplaneType)
class AirplaneTypeAdmin(ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Airplane)
class AirplaneAdmin(ModelAdmin):
    list_select_related = ["airplane_type"]
    list_display = [
        "name",
        "rows",
        "seats_in_row",
        "capacity",
        "get_airplane_type_name",
    ]
    list_filter = ["airplane_type__name"]
    search_fields = ["name"]

    @admin.display(
        ordering="airplane_type__name",
        description="Airplane type",
    )
    def get_airplane_type_name(self, obj: Airplane) -> str:
        return obj.airplane_type.name
