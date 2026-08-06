from django.urls import include, path
from rest_framework.routers import DefaultRouter

from airport.views import (
    AirplaneTypeViewSet,
    AirplaneViewSet,
    AirportViewSet,
    CityViewSet,
    CountryViewSet,
    CrewViewSet,
    FlightViewSet,
    OrderViewSet,
    RouteViewSet,
)

app_name = "airport"

router = DefaultRouter()
router.register("countries", CountryViewSet, basename="country")
router.register("cities", CityViewSet, basename="city")
router.register("airports", AirportViewSet, basename="airport")
router.register("airplane-types", AirplaneTypeViewSet, basename="airplane-type")
router.register("airplanes", AirplaneViewSet, basename="airplane")
router.register("crew", CrewViewSet, basename="crew")
router.register("routes", RouteViewSet, basename="route")
router.register("flights", FlightViewSet, basename="flight")
router.register("orders", OrderViewSet, basename="order")


urlpatterns = [
    path("", include(router.urls)),
]
