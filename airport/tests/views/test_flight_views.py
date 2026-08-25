import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.filters import FlightFilter
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


FLIGHT_URL = reverse("airport:flight-list")


def flight_detail_url(flight_id: uuid.UUID) -> str:
    return reverse(
        "airport:flight-detail",
        args=[flight_id],
    )


def flight_cancel_url(flight_id: uuid.UUID) -> str:
    return reverse(
        "airport:flight-cancel",
        args=[flight_id],
    )


class BaseFlightApiTestCase(TestCase):
    FLIGHT_1_DEPARTURE = datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )
    FLIGHT_1_ARRIVAL = datetime(
        2026,
        9,
        10,
        12,
        0,
        tzinfo=timezone.utc,
    )

    FLIGHT_2_DEPARTURE = datetime(
        2026,
        9,
        11,
        14,
        0,
        tzinfo=timezone.utc,
    )
    FLIGHT_2_ARRIVAL = datetime(
        2026,
        9,
        11,
        16,
        0,
        tzinfo=timezone.utc,
    )

    FLIGHT_3_DEPARTURE = datetime(
        2026,
        9,
        12,
        18,
        0,
        tzinfo=timezone.utc,
    )
    FLIGHT_3_ARRIVAL = datetime(
        2026,
        9,
        12,
        20,
        0,
        tzinfo=timezone.utc,
    )

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

        cls.airplane_type = AirplaneType.objects.create(
            name="Boeing 737",
        )

        cls.airplane_1 = Airplane.objects.create(
            name="UR-001",
            rows=2,
            seats_in_row=2,
            airplane_type=cls.airplane_type,
        )
        cls.airplane_2 = Airplane.objects.create(
            name="UR-002",
            rows=2,
            seats_in_row=2,
            airplane_type=cls.airplane_type,
        )
        cls.airplane_3 = Airplane.objects.create(
            name="UR-003",
            rows=2,
            seats_in_row=2,
            airplane_type=cls.airplane_type,
        )

        cls.crew_1 = Crew.objects.create(
            first_name="John",
            last_name="Smith",
        )
        cls.crew_2 = Crew.objects.create(
            first_name="Anna",
            last_name="Brown",
        )
        cls.crew_3 = Crew.objects.create(
            first_name="Michael",
            last_name="White",
        )

        cls.flight_1 = Flight.objects.create(
            route=cls.route_1,
            airplane=cls.airplane_1,
            departure_time=cls.FLIGHT_1_DEPARTURE,
            arrival_time=cls.FLIGHT_1_ARRIVAL,
        )
        cls.flight_1.crew.add(cls.crew_1)

        cls.flight_2 = Flight.objects.create(
            route=cls.route_2,
            airplane=cls.airplane_2,
            departure_time=cls.FLIGHT_2_DEPARTURE,
            arrival_time=cls.FLIGHT_2_ARRIVAL,
        )
        cls.flight_2.crew.add(cls.crew_2)

        cls.flight_3 = Flight.objects.create(
            route=cls.route_3,
            airplane=cls.airplane_3,
            departure_time=cls.FLIGHT_3_DEPARTURE,
            arrival_time=cls.FLIGHT_3_ARRIVAL,
        )
        cls.flight_3.crew.add(
            cls.crew_1,
            cls.crew_3,
        )

        cls.user = get_user_model().objects.create_user(
            email="tickets@example.com",
            password="testpass123",
        )

        cls.order_1 = Order.objects.create(
            user=cls.user,
        )

        cls.active_ticket_flight_1 = Ticket.objects.create(
            order=cls.order_1,
            flight=cls.flight_1,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        cls.cancelled_ticket_flight_1 = Ticket.objects.create(
            order=cls.order_1,
            flight=cls.flight_1,
            row=1,
            seat=2,
            status=Ticket.Status.CANCELLED,
        )

        cls.order_2 = Order.objects.create(
            user=cls.user,
        )
        cls.order_3 = Order.objects.create(
            user=cls.user,
        )

        Ticket.objects.create(
            order=cls.order_2,
            flight=cls.flight_2,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )
        Ticket.objects.create(
            order=cls.order_2,
            flight=cls.flight_2,
            row=1,
            seat=2,
            status=Ticket.Status.ACTIVE,
        )
        Ticket.objects.create(
            order=cls.order_2,
            flight=cls.flight_2,
            row=2,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )
        Ticket.objects.create(
            order=cls.order_3,
            flight=cls.flight_2,
            row=2,
            seat=2,
            status=Ticket.Status.ACTIVE,
        )

    def setUp(self) -> None:
        cache.clear()

    def assert_response_ids(
        self,
        response,
        expected_ids: set[str],
    ) -> None:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            {
                item["id"]
                for item in response.data["results"]
            },
            expected_ids,
        )


class UnauthenticatedFlightApiTests(
    BaseFlightApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_list_flights(self) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            3,
        )

    def test_list_flights_ordered_by_departure_time_descending(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            [
                item["id"]
                for item in response.data["results"]
            ],
            [
                str(self.flight_3.pk),
                str(self.flight_2.pk),
                str(self.flight_1.pk),
            ],
        )

    def test_list_flights_returns_available_seats_count(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        flight_1_data = next(
            item
            for item in response.data["results"]
            if item["id"] == str(self.flight_1.pk)
        )
        flight_2_data = next(
            item
            for item in response.data["results"]
            if item["id"] == str(self.flight_2.pk)
        )

        self.assertEqual(
            flight_1_data["available_seats"],
            3,
        )
        self.assertEqual(
            flight_2_data["available_seats"],
            0,
        )

    def test_cancelled_ticket_does_not_reduce_available_seats(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        flight_data = next(
            item
            for item in response.data["results"]
            if item["id"] == str(self.flight_1.pk)
        )

        self.assertEqual(
            flight_data["available_seats"],
            3,
        )

    def test_retrieve_flight(self) -> None:
        response = self.client.get(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["id"],
            str(self.flight_1.pk),
        )

    def test_retrieve_flight_returns_only_active_taken_seats(
        self,
    ) -> None:
        response = self.client.get(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["taken_seats"],
            [
                {
                    "row": 1,
                    "seat": 1,
                },
            ],
        )
        self.assertNotIn(
            {
                "row": 1,
                "seat": 2,
            },
            response.data["taken_seats"],
        )

    def test_retrieve_nonexistent_flight(
        self,
    ) -> None:
        response = self.client.get(
            path=flight_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_filter_flights_by_source(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "source": self.boryspil.pk,
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_1.pk),
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_destination(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "destination": self.boryspil.pk,
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_3.pk),
            },
        )

    def test_filter_flights_by_source_city(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "source_city": "ky",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_1.pk),
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_destination_city(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "destination_city": "lviv",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_1.pk),
            },
        )

    def test_filter_flights_by_source_city_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "source_city": "KYIV",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_1.pk),
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_exact_departure_time(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "departure_time": "2026-09-10 10:00",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_1.pk),
            },
        )

    def test_filter_flights_by_departure_time_range(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "departure_time_range_after": (
                    "2026-09-10T00:00:00Z"
                ),
                "departure_time_range_before": (
                    "2026-09-11T23:59:59Z"
                ),
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_1.pk),
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_exact_arrival_time(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "arrival_time": "2026-09-10 12:00",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_1.pk),
            },
        )

    def test_filter_flights_by_arrival_time_range(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "arrival_time_range_after": (
                    "2026-09-11T00:00:00Z"
                ),
                "arrival_time_range_before": (
                    "2026-09-12T23:59:59Z"
                ),
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_2.pk),
                str(self.flight_3.pk),
            },
        )

    def test_filter_flights_by_airplane(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "airplane": self.airplane_2.pk,
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_airplane_name(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "airplane_name": "002",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_crew(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "crew": [
                    self.crew_2.pk,
                ],
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_multiple_crew_members_matches_any(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "crew": [
                    self.crew_2.pk,
                    self.crew_3.pk,
                ],
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_2.pk),
                str(self.flight_3.pk),
            },
        )

    def test_filter_flights_by_crew_last_names_matches_any(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "crew_last_names": "Brown, White",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_2.pk),
                str(self.flight_3.pk),
            },
        )

    def test_filter_flights_by_all_crew_last_names(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "crew_all_last_names": "Smith, White",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_3.pk),
            },
        )

    def test_filter_flights_with_available_seats(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "has_available_seats": "true",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_1.pk),
                str(self.flight_3.pk),
            },
        )

    def test_filter_flights_without_available_seats(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "has_available_seats": "false",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_multiple_filters(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "source": self.boryspil.pk,
                "airplane_name": "002",
            },
        )

        self.assert_response_ids(
            response,
            {
                str(self.flight_2.pk),
            },
        )

    def test_filter_flights_by_nonexistent_source_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
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

    def test_filter_flights_by_nonexistent_destination_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
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

    def test_filter_flights_by_nonexistent_airplane_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "airplane": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "airplane",
            response.data,
        )

    def test_filter_flights_by_nonexistent_crew_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "crew": [
                    uuid.uuid4(),
                ],
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "crew",
            response.data,
        )

    def test_filter_flights_by_invalid_departure_time_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "departure_time": "not-a-date",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "departure_time",
            response.data,
        )

    def test_filter_flights_by_invalid_arrival_time_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
            data={
                "arrival_time": "not-a-date",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "arrival_time",
            response.data,
        )

    def test_create_flight_unauthorized(
        self,
    ) -> None:
        response = self.client.post(
            path=FLIGHT_URL,
            data={
                "route": self.route_1.pk,
                "airplane": self.airplane_1.pk,
                "departure_time": "2026-09-20T10:00:00Z",
                "arrival_time": "2026-09-20T12:00:00Z",
                "status": Flight.Status.SCHEDULED,
                "crew": [
                    self.crew_2.pk,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_update_flight_unauthorized(
        self,
    ) -> None:
        response = self.client.put(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
            data={
                "route": self.route_1.pk,
                "airplane": self.airplane_1.pk,
                "departure_time": "2026-09-10T10:00:00Z",
                "arrival_time": "2026-09-10T12:00:00Z",
                "status": Flight.Status.SCHEDULED,
                "crew": [
                    self.crew_1.pk,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_partial_update_flight_unauthorized(
        self,
    ) -> None:
        response = self.client.patch(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
            data={
                "route": self.route_2.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_delete_flight_unauthorized(
        self,
    ) -> None:
        response = self.client.delete(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_cancel_flight_unauthorized(
        self,
    ) -> None:
        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class AuthenticatedFlightApiTests(
    BaseFlightApiTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.regular_user = get_user_model().objects.create_user(
            email="regular@example.com",
            password="testpass123",
        )

    def setUp(self) -> None:
        super().setUp()

        self.client = APIClient()
        self.client.force_authenticate(
            user=self.regular_user,
        )

    def test_list_flights(self) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_retrieve_flight(self) -> None:
        response = self.client.get(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_create_flight_forbidden(
        self,
    ) -> None:
        response = self.client.post(
            path=FLIGHT_URL,
            data={
                "route": self.route_1.pk,
                "airplane": self.airplane_1.pk,
                "departure_time": "2026-09-20T10:00:00Z",
                "arrival_time": "2026-09-20T12:00:00Z",
                "crew": [
                    self.crew_2.pk,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_update_flight_forbidden(
        self,
    ) -> None:
        response = self.client.put(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
            data={
                "route": self.route_1.pk,
                "airplane": self.airplane_1.pk,
                "departure_time": "2026-09-10T10:00:00Z",
                "arrival_time": "2026-09-10T12:00:00Z",
                "status": Flight.Status.SCHEDULED,
                "crew": [
                    self.crew_1.pk,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_partial_update_flight_forbidden(
        self,
    ) -> None:
        response = self.client.patch(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
            data={
                "route": self.route_2.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_flight_forbidden(
        self,
    ) -> None:
        response = self.client.delete(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_cancel_flight_forbidden(
        self,
    ) -> None:
        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class AdminFlightApiTests(
    BaseFlightApiTestCase,
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

    def valid_payload(self) -> dict[str, object]:
        return {
            "route": self.route_1.pk,
            "airplane": self.airplane_3.pk,
            "departure_time": "2026-09-20T10:00:00Z",
            "arrival_time": "2026-09-20T12:00:00Z",
            "status": Flight.Status.SCHEDULED,
            "crew": [
                self.crew_2.pk,
            ],
        }

    def test_list_flights(self) -> None:
        response = self.client.get(
            path=FLIGHT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_retrieve_flight(self) -> None:
        response = self.client.get(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_create_flight(
        self,
    ) -> None:
        response = self.client.post(
            path=FLIGHT_URL,
            data=self.valid_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        flight = Flight.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            flight.route,
            self.route_1,
        )
        self.assertEqual(
            flight.airplane,
            self.airplane_3,
        )
        self.assertEqual(
            list(flight.crew.all()),
            [
                self.crew_2,
            ],
        )

    def test_create_flight_rejects_invalid_times(
        self,
    ) -> None:
        payload = self.valid_payload()
        payload["arrival_time"] = "2026-09-20T09:00:00Z"

        response = self.client.post(
            path=FLIGHT_URL,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "arrival_time",
            response.data,
        )

    def test_create_flight_rejects_empty_crew(
        self,
    ) -> None:
        payload = self.valid_payload()
        payload["crew"] = []

        response = self.client.post(
            path=FLIGHT_URL,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "crew",
            response.data,
        )

    def test_create_flight_rejects_busy_crew(
        self,
    ) -> None:
        payload = self.valid_payload()
        payload["airplane"] = self.airplane_3.pk
        payload["crew"] = [
            self.crew_1.pk,
        ]
        payload["departure_time"] = "2026-09-10T11:00:00Z"
        payload["arrival_time"] = "2026-09-10T13:00:00Z"

        response = self.client.post(
            path=FLIGHT_URL,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "crew",
            response.data,
        )

    def test_create_flight_rejects_busy_airplane(
        self,
    ) -> None:
        payload = self.valid_payload()
        payload["airplane"] = self.airplane_1.pk
        payload["crew"] = [
            self.crew_2.pk,
        ]
        payload["departure_time"] = "2026-09-10T11:00:00Z"
        payload["arrival_time"] = "2026-09-10T13:00:00Z"

        response = self.client.post(
            path=FLIGHT_URL,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "airplane",
            response.data,
        )

    def test_create_flight_rejects_cancelled_status(
        self,
    ) -> None:
        payload = self.valid_payload()
        payload["status"] = Flight.Status.CANCELLED

        response = self.client.post(
            path=FLIGHT_URL,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "status",
            response.data,
        )

    def test_update_flight(
        self,
    ) -> None:
        payload = {
            "route": self.route_2.pk,
            "airplane": self.airplane_3.pk,
            "departure_time": "2026-09-20T14:00:00Z",
            "arrival_time": "2026-09-20T16:00:00Z",
            "status": Flight.Status.DELAYED,
            "crew": [
                self.crew_2.pk,
            ],
        }

        response = self.client.put(
            path=flight_detail_url(
                self.flight_3.pk,
            ),
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.flight_3.refresh_from_db()

        self.assertEqual(
            self.flight_3.route,
            self.route_2,
        )
        self.assertEqual(
            self.flight_3.airplane,
            self.airplane_3,
        )
        self.assertEqual(
            self.flight_3.status,
            Flight.Status.DELAYED,
        )
        self.assertEqual(
            list(self.flight_3.crew.all()),
            [
                self.crew_2,
            ],
        )

    def test_partial_update_flight(
        self,
    ) -> None:
        original_airplane = self.flight_3.airplane
        original_departure = self.flight_3.departure_time

        response = self.client.patch(
            path=flight_detail_url(
                self.flight_3.pk,
            ),
            data={
                "route": self.route_2.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.flight_3.refresh_from_db()

        self.assertEqual(
            self.flight_3.route,
            self.route_2,
        )
        self.assertEqual(
            self.flight_3.airplane,
            original_airplane,
        )
        self.assertEqual(
            self.flight_3.departure_time,
            original_departure,
        )

    def test_partial_update_rejects_airplane_change_with_active_tickets(
        self,
    ) -> None:
        response = self.client.patch(
            path=flight_detail_url(
                self.flight_1.pk,
            ),
            data={
                "airplane": self.airplane_3.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "airplane",
            response.data,
        )

    def test_partial_update_rejects_cancel_status(
        self,
    ) -> None:
        response = self.client.patch(
            path=flight_detail_url(
                self.flight_3.pk,
            ),
            data={
                "status": Flight.Status.CANCELLED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "status",
            response.data,
        )

    def test_delete_flight(
        self,
    ) -> None:
        flight = Flight.objects.create(
            route=self.route_1,
            airplane=self.airplane_3,
            departure_time=datetime(
                2026,
                10,
                1,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                10,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )
        flight.crew.add(
            self.crew_2,
        )

        flight_id = flight.pk

        response = self.client.delete(
            path=flight_detail_url(
                flight_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            Flight.objects.filter(
                pk=flight_id,
            ).exists(),
        )

    def test_retrieve_nonexistent_flight(
        self,
    ) -> None:
        response = self.client.get(
            path=flight_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_nonexistent_flight(
        self,
    ) -> None:
        response = self.client.put(
            path=flight_detail_url(
                uuid.uuid4(),
            ),
            data=self.valid_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_partial_update_nonexistent_flight(
        self,
    ) -> None:
        response = self.client.patch(
            path=flight_detail_url(
                uuid.uuid4(),
            ),
            data={
                "route": self.route_2.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_nonexistent_flight(
        self,
    ) -> None:
        response = self.client.delete(
            path=flight_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class FlightCancellationApiTests(
    BaseFlightApiTestCase,
):
    NOW = datetime(
        2026,
        9,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.admin = get_user_model().objects.create_user(
            email="cancel-admin@example.com",
            password="testpass123",
            is_staff=True,
        )

        cls.regular_user = get_user_model().objects.create_user(
            email="cancel-user@example.com",
            password="testpass123",
        )

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_cancel_flight_requires_authentication(
        self,
    ) -> None:
        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_regular_user_cannot_cancel_flight(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.regular_user,
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_admin_can_cancel_future_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.flight_1.refresh_from_db()

        self.assertEqual(
            self.flight_1.status,
            Flight.Status.CANCELLED,
        )
        self.assertEqual(
            response.data["id"],
            str(self.flight_1.pk),
        )
        self.assertEqual(
            response.data["status"],
            Flight.Status.CANCELLED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_flight_cancels_active_tickets(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.active_ticket_flight_1.refresh_from_db()

        self.assertEqual(
            self.active_ticket_flight_1.status,
            Ticket.Status.CANCELLED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_flight_keeps_cancelled_tickets_cancelled(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.cancelled_ticket_flight_1.refresh_from_db()

        self.assertEqual(
            self.cancelled_ticket_flight_1.status,
            Ticket.Status.CANCELLED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_flight_cancels_related_confirmed_order(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.client.force_authenticate(
            user=self.admin,
        )

        self.assertEqual(
            self.order_1.status,
            Order.Status.CONFIRMED,
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.order_1.refresh_from_db()

        self.assertEqual(
            self.order_1.status,
            Order.Status.CANCELLED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_flight_does_not_cancel_unrelated_orders(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.order_2.refresh_from_db()
        self.order_3.refresh_from_db()

        self.assertEqual(
            self.order_2.status,
            Order.Status.CONFIRMED,
        )
        self.assertEqual(
            self.order_3.status,
            Order.Status.CONFIRMED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_flight_rejects_already_cancelled_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.client.force_authenticate(
            user=self.admin,
        )

        self.flight_3.status = Flight.Status.CANCELLED
        self.flight_3.save(
            update_fields=[
                "status",
            ],
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_3.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.data,
            {
                "status": [
                    "Flight is already cancelled.",
                ],
            },
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_flight_rejects_departed_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = datetime(
            2026,
            9,
            10,
            13,
            0,
            tzinfo=timezone.utc,
        )

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.flight_1.refresh_from_db()

        self.assertEqual(
            self.flight_1.status,
            Flight.Status.SCHEDULED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_flight_rejects_flight_departing_now(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.FLIGHT_1_DEPARTURE

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=flight_cancel_url(
                self.flight_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.flight_1.refresh_from_db()

        self.assertEqual(
            self.flight_1.status,
            Flight.Status.SCHEDULED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_nonexistent_flight_returns_not_found(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=flight_cancel_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class FlightFilterTests(SimpleTestCase):
    def test_filter_has_available_seats_returns_queryset_when_value_is_none(
        self,
    ) -> None:
        queryset = MagicMock()

        filterset = FlightFilter()

        result = filterset.filter_has_available_seats(
            queryset=queryset,
            name="has_available_seats",
            value=None,
        )

        self.assertIs(
            result,
            queryset,
        )
