from django.db import transaction
from django.db.models import (
    Count,
    F,
    Prefetch,
    Q,
    QuerySet,
    Value,
)
from django.db.models.functions import Concat
from django.utils import timezone

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny,
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
    PopularRouteFilter,
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
    Ticket,
)
from airport.schema.responses import (
    BAD_REQUEST_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    NO_CONTENT_RESPONSE,
    PROTECTED_OBJECT_RESPONSE,
    TOO_MANY_REQUESTS_RESPONSE,
    UNAUTHORIZED_RESPONSE,
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
    AirportStatisticsSerializer,
    AirportUploadImageSerializer,
    CityDetailSerializer,
    CityListSerializer,
    CitySerializer,
    CountrySerializer,
    CrewDetailSerializer,
    CrewListSerializer,
    CrewSerializer,
    CrewUploadPhotoSerializer,
    FlightCancelSerializer,
    FlightDetailSerializer,
    FlightListSerializer,
    FlightSerializer,
    OrderCancelSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderSerializer,
    RouteDetailSerializer,
    RouteListSerializer,
    RoutePopularSerializer,
    RouteSerializer,
)
from airport.utils.validators import (
    validate_flight_cancellation,
    validate_order_cancellation,
)


@extend_schema_view(
    list=extend_schema(
        summary="List countries",
        description=(
            "Return a paginated list of all countries."
        ),
        responses={
            200: CountrySerializer(many=True),
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Countries"],
    ),
    retrieve=extend_schema(
        summary="Retrieve country",
        description=(
            "Return information about a country identified by its ID."
        ),
        responses={
            200: CountrySerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Countries"],
    ),
    create=extend_schema(
        summary="Create country",
        description=(
            "Create a new country. "
            "This operation is available only to administrators."
        ),
        responses={
            201: CountrySerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Countries"],
    ),
    update=extend_schema(
        summary="Update country",
        description=(
            "Replace the data of an existing country. "
            "This operation is available only to administrators."
        ),
        responses={
            200: CountrySerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Countries"],
    ),
    partial_update=extend_schema(
        summary="Partially update country",
        description=(
            "Update one or more fields of an existing country. "
            "This operation is available only to administrators."
        ),
        responses={
            200: CountrySerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Countries"],
    ),
    destroy=extend_schema(
        summary="Delete country",
        description=(
            "Delete a country identified by its ID. "
            "A country cannot be deleted while it is referenced "
            "by protected related objects."
        ),
        responses={
            204: NO_CONTENT_RESPONSE,
            400: PROTECTED_OBJECT_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Countries"],
    ),
)
class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


@extend_schema_view(
    list=extend_schema(
        summary="List cities",
        description=(
            "Return a paginated list of cities. "
            "The results can be filtered by country, country name, "
            "or city name."
        ),
        parameters=[
            OpenApiParameter(
                name="country",
                description="Filter cities by country ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="country_name",
                description=(
                    "Filter cities by a partial, case-insensitive "
                    "country name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="name",
                description=(
                    "Filter cities by a partial, case-insensitive "
                    "city name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={
            200: CityListSerializer(many=True),
            400: BAD_REQUEST_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Cities"],
    ),
    retrieve=extend_schema(
        summary="Retrieve city",
        description=(
            "Return detailed information about a city identified by "
            "its ID, including its country."
        ),
        responses={
            200: CityDetailSerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Cities"],
    ),
    create=extend_schema(
        summary="Create city",
        description=(
            "Create a new city and assign it to an existing country. "
            "This operation is available only to administrators."
        ),
        responses={
            201: CitySerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Cities"],
    ),
    update=extend_schema(
        summary="Update city",
        description=(
            "Replace the data of an existing city. "
            "This operation is available only to administrators."
        ),
        responses={
            200: CitySerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Cities"],
    ),
    partial_update=extend_schema(
        summary="Partially update city",
        description=(
            "Update one or more fields of an existing city. "
            "This operation is available only to administrators."
        ),
        responses={
            200: CitySerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Cities"],
    ),
    destroy=extend_schema(
        summary="Delete city",
        description=(
            "Delete a city identified by its ID. "
            "A city cannot be deleted while it is referenced by "
            "protected related objects."
        ),
        responses={
            204: NO_CONTENT_RESPONSE,
            400: PROTECTED_OBJECT_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Cities"],
    ),
)
class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.select_related("country")
    filterset_class = CityFilter

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return CityListSerializer
        if self.action == "retrieve":
            return CityDetailSerializer
        return CitySerializer


@extend_schema_view(
    list=extend_schema(
        summary="List airports",
        description=(
            "Return a paginated list of airports. "
            "The results can be filtered by city, country, "
            "or airport name."
        ),
        parameters=[
            OpenApiParameter(
                name="city",
                description="Filter airports by city ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="city_name",
                description=(
                    "Filter airports by a partial, case-insensitive "
                    "city name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="country",
                description="Filter airports by country ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="country_name",
                description=(
                    "Filter airports by a partial, case-insensitive "
                    "country name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="name",
                description=(
                    "Filter airports by a partial, case-insensitive "
                    "airport name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={
            200: AirportListSerializer(many=True),
            400: BAD_REQUEST_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airports"],
    ),
    retrieve=extend_schema(
        summary="Retrieve airport",
        description=(
            "Return detailed information about an airport identified "
            "by its ID, including its closest big city, country, "
            "and uploaded image."
        ),
        responses={
            200: AirportDetailSerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airports"],
    ),
    create=extend_schema(
        summary="Create airport",
        description=(
            "Create a new airport and assign its closest big city. "
            "The image is uploaded separately through the image upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            201: AirportSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airports"],
    ),
    update=extend_schema(
        summary="Update airport",
        description=(
            "Replace the data of an existing airport. "
            "The image is managed separately through the image upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            200: AirportSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airports"],
    ),
    partial_update=extend_schema(
        summary="Partially update airport",
        description=(
            "Update one or more fields of an existing airport. "
            "The image is managed separately through the image upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            200: AirportSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airports"],
    ),
    destroy=extend_schema(
        summary="Delete airport",
        description=(
            "Delete an airport identified by its ID. "
            "An airport cannot be deleted while it is referenced by "
            "protected related objects. This operation is available "
            "only to administrators."
        ),
        responses={
            204: NO_CONTENT_RESPONSE,
            400: PROTECTED_OBJECT_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airports"],
    ),
    upload_airport_image=extend_schema(
        summary="Upload airport image",
        description=(
            "Upload or replace the image of an existing airport. "
            "This operation is available only to administrators."
        ),
        request=AirportUploadImageSerializer,
        responses={
            200: AirportUploadImageSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airports"],
    ),
    airport_statistics=extend_schema(
        summary="Retrieve airport statistics",
        description=(
            "Return operational statistics for an airport identified by "
            "its ID. The response includes the number of departing and "
            "arriving routes, upcoming departures and arrivals, and ticket "
            "statistics for flights departing from the airport. Cancelled "
            "flights are excluded from upcoming flight counts."
        ),
        responses={
            200: AirportStatisticsSerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airports"],
    ),
)
class AirportViewSet(viewsets.ModelViewSet):
    filterset_class = AirportFilter

    def get_queryset(self) -> QuerySet[Airport]:
        queryset = Airport.objects.select_related(
            "closest_big_city__country"
        )

        if self.action == "airport_statistics":
            now = timezone.now()

            queryset = queryset.annotate(
                departing_routes_count=Count(
                    "source_routes",
                    distinct=True,
                ),
                arriving_routes_count=Count(
                    "destination_routes",
                    distinct=True,
                ),
                upcoming_departures_count=Count(
                    "source_routes__flights",
                    filter=~Q(
                        source_routes__flights__status=Flight.Status.CANCELLED,
                    ) & Q(
                        source_routes__flights__departure_time__gt=now,
                    ),
                    distinct=True,
                ),
                upcoming_arrivals_count=Count(
                    "destination_routes__flights",
                    filter=~Q(
                        destination_routes__flights__status=Flight.Status.CANCELLED,
                    ) & Q(
                        destination_routes__flights__arrival_time__gt=now,
                    ),
                    distinct=True,
                ),
                active_tickets_count=Count(
                    "source_routes__flights__tickets",
                    filter=Q(
                        source_routes__flights__tickets__status=Ticket.Status.ACTIVE
                    ),
                    distinct=True,
                ),
                cancelled_tickets_count=Count(
                    "source_routes__flights__tickets",
                    filter=Q(
                        source_routes__flights__tickets__status=Ticket.Status.CANCELLED
                    ),
                    distinct=True,
                )
            ).annotate(
                total_upcoming_flights=(
                    F("upcoming_departures_count")
                    + F("upcoming_arrivals_count")
                ),
                total_tickets_count=(
                    F("active_tickets_count")
                    + F("cancelled_tickets_count")
                )
            )

        return queryset

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return AirportListSerializer
        if self.action == "retrieve":
            return AirportDetailSerializer
        if self.action == "upload_airport_image":
            return AirportUploadImageSerializer
        if self.action == "airport_statistics":
            return AirportStatisticsSerializer
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

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[AllowAny],
        url_path="statistics",
        url_name="statistics"
    )
    def airport_statistics(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:
        airport = self.get_object()
        serializer = self.get_serializer(airport)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        summary="List airplane types",
        description=(
            "Return a paginated list of all airplane types."
        ),
        responses={
            200: AirplaneTypeSerializer(many=True),
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplane Types"],
    ),
    retrieve=extend_schema(
        summary="Retrieve airplane type",
        description=(
            "Return information about an airplane type identified "
            "by its ID."
        ),
        responses={
            200: AirplaneTypeSerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplane Types"],
    ),
    create=extend_schema(
        summary="Create airplane type",
        description=(
            "Create a new airplane type. "
            "This operation is available only to administrators."
        ),
        responses={
            201: AirplaneTypeSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplane Types"],
    ),
    update=extend_schema(
        summary="Update airplane type",
        description=(
            "Replace the data of an existing airplane type. "
            "This operation is available only to administrators."
        ),
        responses={
            200: AirplaneTypeSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplane Types"],
    ),
    partial_update=extend_schema(
        summary="Partially update airplane type",
        description=(
            "Update one or more fields of an existing airplane type. "
            "This operation is available only to administrators."
        ),
        responses={
            200: AirplaneTypeSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplane Types"],
    ),
    destroy=extend_schema(
        summary="Delete airplane type",
        description=(
            "Delete an airplane type identified by its ID. "
            "An airplane type cannot be deleted while it is referenced "
            "by protected related objects."
        ),
        responses={
            204: NO_CONTENT_RESPONSE,
            400: PROTECTED_OBJECT_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplane Types"],
    ),
)
class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List airplanes",
        description=(
            "Return a paginated list of airplanes. "
            "The results can be filtered by airplane type or name."
        ),
        parameters=[
            OpenApiParameter(
                name="airplane_type",
                description="Filter airplanes by airplane type ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="airplane_type_name",
                description=(
                    "Filter airplanes by a partial, case-insensitive "
                    "airplane type name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="name",
                description=(
                    "Filter airplanes by a partial, case-insensitive "
                    "airplane name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={
            200: AirplaneListSerializer(many=True),
            400: BAD_REQUEST_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplanes"],
    ),
    retrieve=extend_schema(
        summary="Retrieve airplane",
        description=(
            "Return detailed information about an airplane identified "
            "by its ID, including its airplane type and capacity."
        ),
        responses={
            200: AirplaneDetailSerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplanes"],
    ),
    create=extend_schema(
        summary="Create airplane",
        description=(
            "Create a new airplane and assign its airplane type. "
            "The image is uploaded separately through the image upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            201: AirplaneSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplanes"],
    ),
    update=extend_schema(
        summary="Update airplane",
        description=(
            "Replace the data of an existing airplane. "
            "The image is managed separately through the image upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            200: AirplaneSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplanes"],
    ),
    partial_update=extend_schema(
        summary="Partially update airplane",
        description=(
            "Update one or more fields of an existing airplane. "
            "The image is managed separately through the image upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            200: AirplaneSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplanes"],
    ),
    destroy=extend_schema(
        summary="Delete airplane",
        description=(
            "Delete an airplane identified by its ID. "
            "An airplane cannot be deleted while it is referenced by "
            "protected related objects."
        ),
        responses={
            204: NO_CONTENT_RESPONSE,
            400: PROTECTED_OBJECT_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplanes"],
    ),
    upload_airplane_image=extend_schema(
        summary="Upload airplane image",
        description=(
            "Upload or replace the image of an existing airplane. "
            "This operation is available only to administrators."
        ),
        request=AirplaneUploadImageSerializer,
        responses={
            200: AirplaneUploadImageSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Airplanes"],
    ),
)
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


@extend_schema_view(
    list=extend_schema(
        summary="List crew members",
        description=(
            "Return a paginated list of crew members. "
            "The results can be filtered by first name, last name, "
            "or flight."
        ),
        parameters=[
            OpenApiParameter(
                name="first_name",
                description=(
                    "Filter crew members by a partial, "
                    "case-insensitive first name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="last_name",
                description=(
                    "Filter crew members by a partial, "
                    "case-insensitive last name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="flight",
                description="Filter crew members by flight ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
        ],
        responses={
            200: CrewListSerializer(many=True),
            400: BAD_REQUEST_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Crew"],
    ),
    retrieve=extend_schema(
        summary="Retrieve crew member",
        description=(
            "Return detailed information about a crew member identified "
            "by their ID."
        ),
        responses={
            200: CrewDetailSerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Crew"],
    ),
    create=extend_schema(
        summary="Create crew member",
        description=(
            "Create a new crew member. "
            "The photo is uploaded separately through the photo upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            201: CrewSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Crew"],
    ),
    update=extend_schema(
        summary="Update crew member",
        description=(
            "Replace the data of an existing crew member. "
            "The photo is managed separately through the photo upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            200: CrewSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Crew"],
    ),
    partial_update=extend_schema(
        summary="Partially update crew member",
        description=(
            "Update one or more fields of an existing crew member. "
            "The photo is managed separately through the photo upload "
            "endpoint. This operation is available only to administrators."
        ),
        responses={
            200: CrewSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Crew"],
    ),
    destroy=extend_schema(
        summary="Delete crew member",
        description=(
            "Delete a crew member identified by their ID. "
            "This operation is available only to administrators."
        ),
        responses={
            204: NO_CONTENT_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Crew"],
    ),
    upload_photo=extend_schema(
        summary="Upload crew member photo",
        description=(
            "Upload or replace the photo of an existing crew member. "
            "This operation is available only to administrators."
        ),
        request=CrewUploadPhotoSerializer,
        responses={
            200: CrewUploadPhotoSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Crew"],
    ),
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


@extend_schema_view(
    list=extend_schema(
        summary="List routes",
        description=(
            "Return a paginated list of routes. "
            "The results can be filtered by source and destination "
            "airports, cities, or countries."
        ),
        parameters=[
            OpenApiParameter(
                name="source",
                description="Filter routes by source airport ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="destination",
                description="Filter routes by destination airport ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="source_city",
                description=(
                    "Filter routes by a partial, case-insensitive "
                    "source city name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="destination_city",
                description=(
                    "Filter routes by a partial, case-insensitive "
                    "destination city name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="source_country",
                description=(
                    "Filter routes by a partial, case-insensitive "
                    "source country name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="destination_country",
                description=(
                    "Filter routes by a partial, case-insensitive "
                    "destination country name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={
            200: RouteListSerializer(many=True),
            400: BAD_REQUEST_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Routes"],
    ),
    retrieve=extend_schema(
        summary="Retrieve route",
        description=(
            "Return detailed information about a route identified by "
            "its ID, including source and destination airports, cities, "
            "and countries."
        ),
        responses={
            200: RouteDetailSerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Routes"],
    ),
    create=extend_schema(
        summary="Create route",
        description=(
            "Create a new route between two different airports. "
            "The same source and destination combination cannot be "
            "created more than once. "
            "This operation is available only to administrators."
        ),
        responses={
            201: RouteSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Routes"],
    ),
    update=extend_schema(
        summary="Update route",
        description=(
            "Replace the data of an existing route. "
            "The source and destination airports must be different and "
            "the resulting route must remain unique. "
            "This operation is available only to administrators."
        ),
        responses={
            200: RouteSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Routes"],
    ),
    partial_update=extend_schema(
        summary="Partially update route",
        description=(
            "Update one or more fields of an existing route. "
            "The source and destination airports must remain different "
            "and the resulting route must remain unique. "
            "This operation is available only to administrators."
        ),
        responses={
            200: RouteSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Routes"],
    ),
    destroy=extend_schema(
        summary="Delete route",
        description=(
            "Delete a route identified by its ID. "
            "A route cannot be deleted while it is referenced by "
            "protected related objects."
        ),
        responses={
            204: NO_CONTENT_RESPONSE,
            400: PROTECTED_OBJECT_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Routes"],
    ),
    popular_routes=extend_schema(
        summary="List popular routes",
        description=(
            "Return routes ordered by popularity. Popularity is based "
            "primarily on the number of active tickets and secondarily "
            "on the number of non-cancelled flights. Cancelled tickets "
            "and cancelled flights are excluded from the statistics."
        ),
        parameters=[
            OpenApiParameter(
                name="limit",
                description=(
                    "Limit the response to the specified number of "
                    "most popular routes."
                ),
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
        responses={
            200: RoutePopularSerializer(many=True),
            400: BAD_REQUEST_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Routes"],
    ),
)
class RouteViewSet(viewsets.ModelViewSet):
    filterset_class = RouteFilter

    def filter_queryset(
        self,
        queryset: QuerySet[Route],
    ) -> QuerySet[Route]:
        if self.action == "popular_routes":
            self.filterset_class = PopularRouteFilter

        return super().filter_queryset(queryset)

    def get_queryset(self) -> QuerySet[Route]:
        queryset = Route.objects.select_related(
            "source__closest_big_city__country",
            "destination__closest_big_city__country"
        ).order_by("id")

        if self.action == "popular_routes":
            queryset = queryset.annotate(
                route_name=Concat(
                    F("source__closest_big_city__name"),
                    Value(" → "),
                    F("destination__closest_big_city__name")
                ),
                route_airports_names=Concat(
                    F("source__name"),
                    Value(" → "),
                    F("destination__name")
                ),
                flights_count=Count(
                    "flights",
                    filter=~Q(flights__status=Flight.Status.CANCELLED),
                    distinct=True,
                ),
                tickets_count=Count(
                    "flights__tickets",
                    filter=(
                        Q(flights__tickets__status=Ticket.Status.ACTIVE)
                        & ~Q(flights__status=Flight.Status.CANCELLED)
                    ),
                    distinct=True,
                ),
            ).order_by(
                "-tickets_count",
                "-flights_count"
            )

        return queryset

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer
        if self.action == "popular_routes":
            return RoutePopularSerializer
        return RouteSerializer

    @action(
        detail=False,
        methods=["get"],
        url_name="popular",
        url_path="popular",
        permission_classes=[AllowAny],
    )
    def popular_routes(
        self,
        request: Request,
    ) -> Response:
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        summary="List flights",
        description=(
            "Return a paginated list of flights. "
            "The results can be filtered by source and destination "
            "airports, source and destination cities, departure and "
            "arrival times, airplane, crew members, and seat availability."
        ),
        parameters=[
            OpenApiParameter(
                name="source",
                description="Filter flights by source airport ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="destination",
                description="Filter flights by destination airport ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="source_city",
                description=(
                    "Filter flights by a partial, case-insensitive "
                    "source city name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="destination_city",
                description=(
                    "Filter flights by a partial, case-insensitive "
                    "destination city name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="departure_time",
                description=(
                    "Filter flights by exact departure time. "
                    "Expected format: YYYY-MM-DD HH:MM."
                ),
                required=False,
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="departure_time_range_after",
                description=(
                    "Filter flights with departure time greater than "
                    "or equal to the specified datetime."
                ),
                required=False,
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="departure_time_range_before",
                description=(
                    "Filter flights with departure time less than "
                    "or equal to the specified datetime."
                ),
                required=False,
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="arrival_time",
                description=(
                    "Filter flights by exact arrival time. "
                    "Expected format: YYYY-MM-DD HH:MM."
                ),
                required=False,
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="arrival_time_range_after",
                description=(
                    "Filter flights with arrival time greater than "
                    "or equal to the specified datetime."
                ),
                required=False,
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="arrival_time_range_before",
                description=(
                    "Filter flights with arrival time less than "
                    "or equal to the specified datetime."
                ),
                required=False,
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="airplane",
                description="Filter flights by airplane ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="airplane_name",
                description=(
                    "Filter flights by a partial, case-insensitive "
                    "airplane name."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="crew",
                description=(
                    "Filter flights by one or more crew member IDs."
                ),
                required=False,
                type=OpenApiTypes.UUID,
                many=True,
            ),
            OpenApiParameter(
                name="crew_last_names",
                description=(
                    "Filter flights that contain any crew member whose "
                    "last name is included in the comma-separated list."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="crew_all_last_names",
                description=(
                    "Filter flights that contain crew members matching "
                    "all last names in the comma-separated list."
                ),
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="has_available_seats",
                description=(
                    "Filter flights by seat availability. "
                    "Use true to return flights with available seats "
                    "and false to return fully booked flights."
                ),
                required=False,
                type=OpenApiTypes.BOOL,
            ),
        ],
        responses={
            200: FlightListSerializer(many=True),
            400: BAD_REQUEST_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Flights"],
    ),

    retrieve=extend_schema(
        summary="Retrieve flight",
        description=(
            "Return detailed information about a flight identified by "
            "its ID, including route information, airplane details, "
            "assigned crew members, flight duration, and currently "
            "occupied seats. Only active tickets are included in the "
            "occupied seat information."
        ),
        responses={
            200: FlightDetailSerializer,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Flights"],
    ),

    create=extend_schema(
        summary="Create flight",
        description=(
            "Create a new flight with a route, airplane, departure and "
            "arrival times, and assigned crew members. The arrival time "
            "must be later than the departure time and at least one crew "
            "member must be assigned. The selected airplane and all crew "
            "members must be available for the entire flight interval. "
            "Schedule validation also requires a 30-minute buffer before "
            "and after flights to prevent overlapping assignments. "
            "A flight cannot be created directly with cancelled status; "
            "the dedicated cancellation endpoint must be used to cancel "
            "a flight. This operation is available only to administrators."
        ),
        request=FlightSerializer,
        responses={
            201: FlightSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Flights"],
    ),

    update=extend_schema(
        summary="Update flight",
        description=(
            "Replace the data of an existing flight. A cancelled flight "
            "cannot be modified. The arrival time must remain later than "
            "the departure time and at least one crew member must remain "
            "assigned. The selected airplane and crew members must not "
            "conflict with other flights and must respect the required "
            "30-minute buffer between flights. The airplane cannot be "
            "changed if active tickets already exist for the flight. "
            "The flight cannot be cancelled by changing its status "
            "directly; use the dedicated cancellation endpoint instead. "
            "This operation is available only to administrators."
        ),
        request=FlightSerializer,
        responses={
            200: FlightSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Flights"],
    ),

    partial_update=extend_schema(
        summary="Partially update flight",
        description=(
            "Update one or more fields of an existing flight. Fields "
            "omitted from the request keep their current values. A "
            "cancelled flight cannot be modified. The resulting flight "
            "must have valid departure and arrival times, at least one "
            "crew member, and no airplane or crew schedule conflicts. "
            "The required 30-minute buffer between flights must remain "
            "satisfied. The airplane cannot be changed if active tickets "
            "already exist for the flight. The flight cannot be cancelled "
            "by changing its status directly; use the dedicated "
            "cancellation endpoint instead. This operation is available "
            "only to administrators."
        ),
        request=FlightSerializer,
        responses={
            200: FlightSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Flights"],
    ),

    destroy=extend_schema(
        summary="Delete flight",
        description=(
            "Delete a flight identified by its ID. "
            "A flight cannot be deleted while it is referenced by "
            "protected related objects. This operation is available "
            "only to administrators."
        ),
        responses={
            204: NO_CONTENT_RESPONSE,
            400: PROTECTED_OBJECT_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Flights"],
    ),

    cancel_flight=extend_schema(
        summary="Cancel flight",
        description=(
            "Cancel an existing flight. A flight that has already been "
            "cancelled or has already departed cannot be cancelled. "
            "The flight status is changed to cancelled and all active "
            "tickets associated with the flight are also cancelled. "
            "Confirmed orders containing tickets for the cancelled flight "
            "are changed to cancelled status. This operation is available "
            "only to administrators."
        ),
        request=None,
        responses={
            200: FlightCancelSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            403: FORBIDDEN_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Flights"],
    ),
)
class FlightViewSet(viewsets.ModelViewSet):
    filterset_class = FlightFilter

    def get_queryset(self) -> QuerySet[Flight]:
        queryset = (
            Flight.objects
            .select_related(
                "route__source__closest_big_city__country",
                "route__destination__closest_big_city__country",
                "airplane__airplane_type",
            )
            .prefetch_related("crew")
            .annotate(
                available_seats=(
                    F("airplane__rows")
                    * F("airplane__seats_in_row")
                    - Count(
                        "tickets",
                        filter=Q(tickets__status=Ticket.Status.ACTIVE,),
                        distinct=True,
                    )
                ),
            )
            .order_by("-departure_time", "id")
        )

        if self.action == "retrieve":
            queryset = (
                queryset.prefetch_related(
                    Prefetch(
                        "tickets",
                        queryset=Ticket.objects.filter(
                            status=Ticket.Status.ACTIVE
                        ),
                        to_attr="active_tickets",
                    )
                )
            )

        return queryset

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer
        if self.action == "cancel_flight":
            return FlightCancelSerializer
        return FlightSerializer

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminUser],
        url_name="cancel",
        url_path="cancel"
    )
    def cancel_flight(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:
        flight = self.get_object()

        validate_flight_cancellation(
            flight,
            ValidationError
        )

        with transaction.atomic():
            flight.status = Flight.Status.CANCELLED
            flight.save(update_fields=["status"])

            Ticket.objects.filter(
                flight=flight,
                status=Ticket.Status.ACTIVE,
            ).update(
                status=Ticket.Status.CANCELLED,
            )

            Order.objects.filter(
                tickets__flight=flight,
                status=Order.Status.CONFIRMED,
            ).update(
                status=Order.Status.CANCELLED,
            )

        serializer = self.get_serializer(flight)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        summary="List orders",
        description=(
            "Return a paginated list of orders available to the current "
            "authenticated user. Regular users can view only their own "
            "orders, while staff users can view all orders. Each list "
            "item includes the number of tickets in the order."
        ),
        responses={
            200: OrderListSerializer(many=True),
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Orders"],
    ),

    retrieve=extend_schema(
        summary="Retrieve order",
        description=(
            "Return detailed information about an order identified by "
            "its ID, including its status, tickets, and related flight "
            "information. Regular users can retrieve only their own "
            "orders, while staff users can retrieve any order."
        ),
        responses={
            200: OrderDetailSerializer,
            401: UNAUTHORIZED_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Orders"],
    ),

    create=extend_schema(
        summary="Create order",
        description=(
            "Create a new order for the authenticated user. The user is "
            "assigned automatically and cannot be provided in the request. "
            "The order must contain at least one ticket and cannot exceed "
            "the configured maximum number of tickets. All tickets in the "
            "same order must belong to the same flight. Requested row and "
            "seat numbers must exist on the airplane assigned to the flight. "
            "The same seat cannot be duplicated within the request and an "
            "already active booked seat cannot be purchased again. Tickets "
            "cannot be purchased for a cancelled flight or after the flight "
            "has departed. The order and all nested tickets are created "
            "atomically."
        ),
        request=OrderSerializer,
        responses={
            201: OrderSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Orders"],
    ),

    cancel_order=extend_schema(
        summary="Cancel order",
        description=(
            "Cancel an order available to the authenticated user. "
            "An order that is already cancelled cannot be cancelled again. "
            "The order cannot be cancelled if it contains an active ticket "
            "for a non-cancelled flight that has already departed. "
            "When cancellation succeeds, all tickets belonging to the order "
            "are changed to cancelled status and the order itself is changed "
            "to cancelled status. Regular users can cancel only their own "
            "orders, while staff users can cancel any order."
        ),
        request=None,
        responses={
            200: OrderCancelSerializer,
            400: BAD_REQUEST_RESPONSE,
            401: UNAUTHORIZED_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            429: TOO_MANY_REQUESTS_RESPONSE,
        },
        tags=["Orders"],
    ),
)
class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Order]:
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

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
                tickets_count=Count(
                    "tickets"
                ),
            )
            .order_by("-created_at", "id")
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return OrderListSerializer

        if self.action == "retrieve":
            return OrderDetailSerializer

        if self.action == "cancel_order":
            return OrderCancelSerializer

        return OrderSerializer

    def perform_create(
        self,
        serializer: BaseSerializer,
    ) -> None:
        serializer.save(user=self.request.user)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="cancel",
        url_name="cancel",
    )
    def cancel_order(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:
        order = self.get_object()

        validate_order_cancellation(
            order,
            ValidationError,
        )

        with transaction.atomic():
            order.tickets.all().update(
                status=Ticket.Status.CANCELLED
            )

            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status"])

        serializer = self.get_serializer(order)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
