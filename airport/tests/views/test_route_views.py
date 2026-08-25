import uuid
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.filters import PopularRouteFilter
from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Flight,
    Order,
    Route,
    Ticket,
)
from airport.serializers import (
    RouteDetailSerializer,
    RouteListSerializer,
)


ROUTE_URL = reverse("airport:route-list")
POPULAR_ROUTE_URL = reverse("airport:route-popular")


def route_detail_url(route_id: uuid.UUID) -> str:
    return reverse(
        "airport:route-detail",
        args=[route_id],
    )


class BaseRouteApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.ukraine = Country.objects.create(
            name="Ukraine",
        )
        cls.poland = Country.objects.create(
            name="Poland",
        )

        cls.kyiv = City.objects.create(
            name="Kyiv",
            country=cls.ukraine,
        )
        cls.lviv = City.objects.create(
            name="Lviv",
            country=cls.ukraine,
        )
        cls.warsaw = City.objects.create(
            name="Warsaw",
            country=cls.poland,
        )

        cls.boryspil = Airport.objects.create(
            name="Boryspil International Airport",
            closest_big_city=cls.kyiv,
        )
        cls.lviv_airport = Airport.objects.create(
            name="Lviv International Airport",
            closest_big_city=cls.lviv,
        )
        cls.warsaw_airport = Airport.objects.create(
            name="Warsaw Chopin Airport",
            closest_big_city=cls.warsaw,
        )

        cls.route_1 = Route.objects.create(
            source=cls.boryspil,
            destination=cls.lviv_airport,
            distance=470,
        )
        cls.route_2 = Route.objects.create(
            source=cls.boryspil,
            destination=cls.warsaw_airport,
            distance=690,
        )
        cls.route_3 = Route.objects.create(
            source=cls.warsaw_airport,
            destination=cls.boryspil,
            distance=690,
        )

    def setUp(self) -> None:
        cache.clear()


class UnauthenticatedRouteApiTests(
    BaseRouteApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_list_routes(self) -> None:
        response = self.client.get(
            path=ROUTE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        routes = (
            Route.objects
            .select_related(
                "source__closest_big_city__country",
                "destination__closest_big_city__country",
            )
            .order_by("id")
        )

        serializer = RouteListSerializer(
            routes,
            many=True,
        )

        self.assertEqual(
            response.data["count"],
            3,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_route(self) -> None:
        response = self.client.get(
            path=route_detail_url(
                self.route_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = RouteDetailSerializer(
            self.route_1,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_retrieve_nonexistent_route(
        self,
    ) -> None:
        response = self.client.get(
            path=route_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_filter_routes_by_source(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "source": self.boryspil.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            route["id"]
            for route in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.route_1.pk),
                str(self.route_2.pk),
            },
        )

    def test_filter_routes_by_destination(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "destination": self.boryspil.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.route_3.pk),
        )

    def test_filter_routes_by_source_city(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "source_city": "ky",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            route["id"]
            for route in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.route_1.pk),
                str(self.route_2.pk),
            },
        )

    def test_filter_routes_by_destination_city(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "destination_city": "lviv",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.route_1.pk),
        )

    def test_filter_routes_by_source_country(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "source_country": "ukr",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            route["id"]
            for route in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.route_1.pk),
                str(self.route_2.pk),
            },
        )

    def test_filter_routes_by_destination_country(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "destination_country": "pol",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.route_2.pk),
        )

    def test_filter_routes_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "source_city": "KYIV",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            2,
        )

    def test_filter_routes_by_multiple_filters(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "source_country": "Ukraine",
                "destination_city": "Warsaw",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.route_2.pk),
        )

    def test_filter_routes_by_nonexistent_source_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "source": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "source",
            response.data,
        )

    def test_filter_routes_by_nonexistent_destination_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "destination": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "destination",
            response.data,
        )

    def test_filter_routes_returns_empty_results_when_not_found(
        self,
    ) -> None:
        response = self.client.get(
            path=ROUTE_URL,
            data={
                "source_city": "Berlin",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            0,
        )
        self.assertEqual(
            response.data["results"],
            [],
        )

    def test_create_route_unauthorized(
        self,
    ) -> None:
        response = self.client.post(
            path=ROUTE_URL,
            data={
                "source": self.lviv_airport.pk,
                "destination": self.warsaw_airport.pk,
                "distance": 800,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_update_route_unauthorized(
        self,
    ) -> None:
        response = self.client.put(
            path=route_detail_url(
                self.route_1.pk,
            ),
            data={
                "source": self.boryspil.pk,
                "destination": self.lviv_airport.pk,
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_partial_update_route_unauthorized(
        self,
    ) -> None:
        response = self.client.patch(
            path=route_detail_url(
                self.route_1.pk,
            ),
            data={
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_delete_route_unauthorized(
        self,
    ) -> None:
        response = self.client.delete(
            path=route_detail_url(
                self.route_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class AuthenticatedRouteApiTests(
    BaseRouteApiTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )

    def setUp(self) -> None:
        super().setUp()

        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user,
        )

    def test_list_routes(self) -> None:
        response = self.client.get(
            path=ROUTE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        routes = (
            Route.objects
            .select_related(
                "source__closest_big_city__country",
                "destination__closest_big_city__country",
            )
            .order_by("id")
        )

        serializer = RouteListSerializer(
            routes,
            many=True,
        )

        self.assertEqual(
            response.data["count"],
            3,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_route(self) -> None:
        response = self.client.get(
            path=route_detail_url(
                self.route_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_create_route_forbidden(
        self,
    ) -> None:
        response = self.client.post(
            path=ROUTE_URL,
            data={
                "source": self.lviv_airport.pk,
                "destination": self.warsaw_airport.pk,
                "distance": 800,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_update_route_forbidden(
        self,
    ) -> None:
        response = self.client.put(
            path=route_detail_url(
                self.route_1.pk,
            ),
            data={
                "source": self.boryspil.pk,
                "destination": self.lviv_airport.pk,
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_partial_update_route_forbidden(
        self,
    ) -> None:
        response = self.client.patch(
            path=route_detail_url(
                self.route_1.pk,
            ),
            data={
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_route_forbidden(
        self,
    ) -> None:
        response = self.client.delete(
            path=route_detail_url(
                self.route_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class AdminRouteApiTests(
    BaseRouteApiTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
        )

    def setUp(self) -> None:
        super().setUp()

        self.client = APIClient()
        self.client.force_authenticate(
            user=self.admin,
        )

    def test_create_route(
        self,
    ) -> None:
        payload = {
            "source": self.lviv_airport.pk,
            "destination": self.warsaw_airport.pk,
            "distance": 800,
        }

        response = self.client.post(
            path=ROUTE_URL,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        route = Route.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            route.source,
            self.lviv_airport,
        )
        self.assertEqual(
            route.destination,
            self.warsaw_airport,
        )
        self.assertEqual(
            route.distance,
            800,
        )

    def test_create_route_rejects_same_source_and_destination(
        self,
    ) -> None:
        response = self.client.post(
            path=ROUTE_URL,
            data={
                "source": self.boryspil.pk,
                "destination": self.boryspil.pk,
                "distance": 100,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data,
            {
                "destination": [
                    "Destination must differ from source.",
                ],
            },
        )

    def test_create_route_rejects_duplicate_route(
        self,
    ) -> None:
        response = self.client.post(
            path=ROUTE_URL,
            data={
                "source": self.route_1.source.pk,
                "destination": self.route_1.destination.pk,
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_route_with_invalid_source(
        self,
    ) -> None:
        response = self.client.post(
            path=ROUTE_URL,
            data={
                "source": uuid.uuid4(),
                "destination": self.lviv_airport.pk,
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "source",
            response.data,
        )

    def test_create_route_with_invalid_destination(
        self,
    ) -> None:
        response = self.client.post(
            path=ROUTE_URL,
            data={
                "source": self.boryspil.pk,
                "destination": uuid.uuid4(),
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "destination",
            response.data,
        )

    def test_create_route_without_source(
        self,
    ) -> None:
        response = self.client.post(
            path=ROUTE_URL,
            data={
                "destination": self.lviv_airport.pk,
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "source",
            response.data,
        )

    def test_create_route_without_destination(
        self,
    ) -> None:
        response = self.client.post(
            path=ROUTE_URL,
            data={
                "source": self.boryspil.pk,
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "destination",
            response.data,
        )

    def test_update_route(
        self,
    ) -> None:
        response = self.client.put(
            path=route_detail_url(
                self.route_1.pk,
            ),
            data={
                "source": self.lviv_airport.pk,
                "destination": self.warsaw_airport.pk,
                "distance": 900,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.route_1.refresh_from_db()

        self.assertEqual(
            self.route_1.source,
            self.lviv_airport,
        )
        self.assertEqual(
            self.route_1.destination,
            self.warsaw_airport,
        )
        self.assertEqual(
            self.route_1.distance,
            900,
        )

    def test_partial_update_route(
        self,
    ) -> None:
        original_source = self.route_1.source
        original_destination = self.route_1.destination

        response = self.client.patch(
            path=route_detail_url(
                self.route_1.pk,
            ),
            data={
                "distance": 550,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.route_1.refresh_from_db()

        self.assertEqual(
            self.route_1.distance,
            550,
        )
        self.assertEqual(
            self.route_1.source,
            original_source,
        )
        self.assertEqual(
            self.route_1.destination,
            original_destination,
        )

    def test_partial_update_route_rejects_same_source_destination(
        self,
    ) -> None:
        response = self.client.patch(
            path=route_detail_url(
                self.route_1.pk,
            ),
            data={
                "destination": self.route_1.source.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data,
            {
                "destination": [
                    "Destination must differ from source.",
                ],
            },
        )

    def test_delete_route(
        self,
    ) -> None:
        route = Route.objects.create(
            source=self.lviv_airport,
            destination=self.boryspil,
            distance=470,
        )

        route_id = route.pk

        response = self.client.delete(
            path=route_detail_url(
                route_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Route.objects.filter(
                pk=route_id,
            ).exists(),
        )

    def test_retrieve_nonexistent_route(
        self,
    ) -> None:
        response = self.client.get(
            path=route_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_nonexistent_route(
        self,
    ) -> None:
        response = self.client.put(
            path=route_detail_url(
                uuid.uuid4(),
            ),
            data={
                "source": self.boryspil.pk,
                "destination": self.lviv_airport.pk,
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_partial_update_nonexistent_route(
        self,
    ) -> None:
        response = self.client.patch(
            path=route_detail_url(
                uuid.uuid4(),
            ),
            data={
                "distance": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_nonexistent_route(
        self,
    ) -> None:
        response = self.client.delete(
            path=route_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class PopularRouteApiTests(
    BaseRouteApiTestCase,
):
    NOW = datetime(
        2026,
        9,
        10,
        8,
        0,
        tzinfo=timezone.utc,
    )

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.airplane_type = AirplaneType.objects.create(
            name="Boeing 737",
        )

        cls.airplane_1 = Airplane.objects.create(
            name="UR-001",
            rows=20,
            seats_in_row=6,
            airplane_type=cls.airplane_type,
        )

        cls.airplane_2 = Airplane.objects.create(
            name="UR-002",
            rows=20,
            seats_in_row=6,
            airplane_type=cls.airplane_type,
        )

        cls.airplane_3 = Airplane.objects.create(
            name="UR-003",
            rows=20,
            seats_in_row=6,
            airplane_type=cls.airplane_type,
        )

        cls.flight_route_1_a = Flight.objects.create(
            route=cls.route_1,
            airplane=cls.airplane_1,
            departure_time=cls.NOW + timedelta(hours=2),
            arrival_time=cls.NOW + timedelta(hours=3),
        )

        cls.flight_route_1_b = Flight.objects.create(
            route=cls.route_1,
            airplane=cls.airplane_2,
            departure_time=cls.NOW + timedelta(hours=5),
            arrival_time=cls.NOW + timedelta(hours=6),
        )

        cls.flight_route_2 = Flight.objects.create(
            route=cls.route_2,
            airplane=cls.airplane_3,
            departure_time=cls.NOW + timedelta(hours=8),
            arrival_time=cls.NOW + timedelta(hours=9),
        )

        cls.cancelled_flight_route_3 = Flight.objects.create(
            route=cls.route_3,
            airplane=cls.airplane_1,
            departure_time=cls.NOW + timedelta(hours=11),
            arrival_time=cls.NOW + timedelta(hours=12),
            status=Flight.Status.CANCELLED,
        )

        cls.user = get_user_model().objects.create_user(
            email="popular@example.com",
            password="testpass123",
        )

        cls.order_1 = Order.objects.create(
            user=cls.user,
        )

        cls.order_2 = Order.objects.create(
            user=cls.user,
        )

        Ticket.objects.create(
            order=cls.order_1,
            flight=cls.flight_route_1_a,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        Ticket.objects.create(
            order=cls.order_1,
            flight=cls.flight_route_1_a,
            row=1,
            seat=2,
            status=Ticket.Status.ACTIVE,
        )

        Ticket.objects.create(
            order=cls.order_2,
            flight=cls.flight_route_1_b,
            row=1,
            seat=3,
            status=Ticket.Status.ACTIVE,
        )

        Ticket.objects.create(
            order=cls.order_2,
            flight=cls.flight_route_2,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        Ticket.objects.create(
            order=cls.order_2,
            flight=cls.flight_route_2,
            row=1,
            seat=2,
            status=Ticket.Status.CANCELLED,
        )

        Ticket.objects.create(
            order=cls.order_2,
            flight=cls.cancelled_flight_route_3,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_popular_routes_available_for_unauthenticated_user(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_popular_routes_without_limit_returns_all_routes(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            3,
        )

    def test_popular_routes_returns_expected_fields(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            set(response.data[0].keys()),
            {
                "route_id",
                "route_cities",
                "route_airports",
                "flights_count",
                "tickets_count",
            },
        )

    def test_popular_routes_returns_route_names(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        route_data = next(
            item
            for item in response.data
            if item["route_id"] == str(self.route_1.pk)
        )

        self.assertEqual(
            route_data["route_cities"],
            "Kyiv → Lviv",
        )

        self.assertEqual(
            route_data["route_airports"],
            (
                "Boryspil International Airport "
                "→ Lviv International Airport"
            ),
        )

    def test_popular_routes_counts_non_cancelled_flights(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        route_1_data = next(
            item
            for item in response.data
            if item["route_id"] == str(self.route_1.pk)
        )

        route_3_data = next(
            item
            for item in response.data
            if item["route_id"] == str(self.route_3.pk)
        )

        self.assertEqual(
            route_1_data["flights_count"],
            2,
        )

        self.assertEqual(
            route_3_data["flights_count"],
            0,
        )

    def test_popular_routes_counts_only_active_tickets(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        route_1_data = next(
            item
            for item in response.data
            if item["route_id"] == str(self.route_1.pk)
        )

        route_2_data = next(
            item
            for item in response.data
            if item["route_id"] == str(self.route_2.pk)
        )

        self.assertEqual(
            route_1_data["tickets_count"],
            3,
        )

        self.assertEqual(
            route_2_data["tickets_count"],
            1,
        )

    def test_popular_routes_ignores_cancelled_tickets(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        route_2_data = next(
            item
            for item in response.data
            if item["route_id"] == str(self.route_2.pk)
        )

        self.assertEqual(
            route_2_data["tickets_count"],
            1,
        )

    def test_popular_routes_ignores_tickets_from_cancelled_flights(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        route_3_data = next(
            item
            for item in response.data
            if item["route_id"] == str(self.route_3.pk)
        )

        self.assertEqual(
            route_3_data["tickets_count"],
            0,
        )

    def test_popular_routes_are_ordered_by_ticket_count(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data[0]["route_id"],
            str(self.route_1.pk),
        )

        self.assertEqual(
            response.data[0]["tickets_count"],
            3,
        )

        self.assertEqual(
            response.data[1]["route_id"],
            str(self.route_2.pk),
        )

        self.assertEqual(
            response.data[1]["tickets_count"],
            1,
        )

        self.assertEqual(
            response.data[2]["route_id"],
            str(self.route_3.pk),
        )

        self.assertEqual(
            response.data[2]["tickets_count"],
            0,
        )

    def test_popular_routes_uses_flights_count_when_ticket_counts_are_equal(
        self,
    ) -> None:
        extra_flight_1 = Flight.objects.create(
            route=self.route_2,
            airplane=self.airplane_1,
            departure_time=(
                self.NOW
                + timedelta(days=2)
            ),
            arrival_time=(
                self.NOW
                + timedelta(
                    days=2,
                    hours=1,
                )
            ),
        )

        extra_flight_2 = Flight.objects.create(
            route=self.route_2,
            airplane=self.airplane_2,
            departure_time=(
                self.NOW
                + timedelta(days=3)
            ),
            arrival_time=(
                self.NOW
                + timedelta(
                    days=3,
                    hours=1,
                )
            ),
        )

        Ticket.objects.create(
            order=self.order_1,
            flight=extra_flight_1,
            row=2,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        Ticket.objects.create(
            order=self.order_1,
            flight=extra_flight_2,
            row=2,
            seat=2,
            status=Ticket.Status.ACTIVE,
        )

        response = self.client.get(
            path=POPULAR_ROUTE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data[0]["route_id"],
            str(self.route_2.pk),
        )

        self.assertEqual(
            response.data[0]["tickets_count"],
            3,
        )

        self.assertEqual(
            response.data[0]["flights_count"],
            3,
        )

        self.assertEqual(
            response.data[1]["route_id"],
            str(self.route_1.pk),
        )

        self.assertEqual(
            response.data[1]["tickets_count"],
            3,
        )

        self.assertEqual(
            response.data[1]["flights_count"],
            2,
        )

    def test_popular_routes_limit_filter(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
            data={
                "limit": 2,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

    def test_popular_routes_limit_one_returns_top_route(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
            data={
                "limit": 1,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["route_id"],
            str(self.route_1.pk),
        )

    def test_popular_routes_rejects_zero_limit(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
            data={
                "limit": 0,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "limit",
            response.data,
        )

    def test_popular_routes_rejects_negative_limit(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
            data={
                "limit": -1,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "limit",
            response.data,
        )

    def test_popular_routes_rejects_non_numeric_limit(
        self,
    ) -> None:
        response = self.client.get(
            path=POPULAR_ROUTE_URL,
            data={
                "limit": "abc",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "limit",
            response.data,
        )


class PopularRouteFilterTests(TestCase):
    def test_limit_popular_routes_returns_queryset_when_value_is_none(
        self,
    ) -> None:
        queryset = Route.objects.none()

        filterset = PopularRouteFilter(
            queryset=queryset,
        )

        result = filterset.limit_popular_routes(
            queryset=queryset,
            name="limit",
            value=None,
        )

        self.assertIs(
            result,
            queryset,
        )
