from django.db.models import Count, F, QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from airport.filters import (
    AirplaneFilter,
    AirportFilter,
    CityFilter,
    CrewFilter,
    FlightFilter,
    RouteFilter,
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
)
from airport.serializers import (
    AirplaneDetailSerializer,
    AirplaneListSerializer,
    AirplaneSerializer,
    AirplaneTypeSerializer,
    AirplaneUploadImageSerializer,
    AirportDetailSerializer,
    AirportListSerializer,
    AirportSerializer,
    AirportUploadImageSerializer,
    CityDetailSerializer,
    CityListSerializer,
    CitySerializer,
    CountrySerializer,
    CrewDetailSerializer,
    CrewListSerializer,
    CrewSerializer,
    CrewUploadPhotoSerializer,
    FlightDetailSerializer,
    FlightListSerializer,
    FlightSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderSerializer,
    RouteDetailSerializer,
    RouteListSerializer,
    RouteSerializer,
)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.select_related("country")
    filterset_class = CityFilter

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return CityListSerializer
        if self.action == "retrieve":
            return CityDetailSerializer
        return CitySerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.select_related(
        "closest_big_city__country"
    )
    filterset_class = AirportFilter

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return AirportListSerializer
        if self.action == "retrieve":
            return AirportDetailSerializer
        if self.action == "upload_airport_image":
            return AirportUploadImageSerializer
        return AirportSerializer

    @action(
        methods=["post"],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path="upload-image",
    )
    def upload_airport_image(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:
        airport = self.get_object()
        serializer = self.get_serializer(
            airport,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    filterset_class = AirplaneFilter

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer
        if self.action == "upload_airplane_image":
            return AirplaneUploadImageSerializer
        return AirplaneSerializer

    @action(
        methods=["post"],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path="upload-image",
    )
    def upload_airplane_image(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:
        airplane = self.get_object()
        serializer = self.get_serializer(
            airplane,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    filterset_class = CrewFilter

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return CrewListSerializer
        if self.action == "retrieve":
            return CrewDetailSerializer
        if self.action == "upload_photo":
            return CrewUploadPhotoSerializer
        return CrewSerializer

    @action(
        methods=["post"],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path="upload-photo",
    )
    def upload_photo(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:
        crew_member = self.get_object()
        serializer = self.get_serializer(
            crew_member,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related(
        "source__closest_big_city__country",
        "destination__closest_big_city__country"
    )
    filterset_class = RouteFilter

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = (
        Flight
        .objects
        .select_related(
            "route__source__closest_big_city__country",
            "route__destination__closest_big_city__country",
            "airplane__airplane_type"
        )
        .prefetch_related("crew")
        .annotate(
            available_seats=(
                F("airplane__rows") * F("airplane__seats_in_row")
                - Count("tickets", distinct=True)
            )
        )
    )
    filterset_class = FlightFilter

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Order]:
        queryset = (
            Order.objects
            .select_related("user")
            .prefetch_related(
                "tickets__flight__route__source__closest_big_city__country",
                "tickets__flight__route__destination__closest_big_city__country",
                "tickets__flight__airplane__airplane_type",
                "tickets__flight__crew",
            )
            .annotate(
                tickets_count=Count("tickets"),
            )
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return OrderListSerializer

        if self.action == "retrieve":
            return OrderDetailSerializer

        return OrderSerializer

    def perform_create(
        self,
        serializer: BaseSerializer,
    ) -> None:
        serializer.save(user=self.request.user)
