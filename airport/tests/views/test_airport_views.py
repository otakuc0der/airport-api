import os
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from PIL import Image

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import (
    Airport,
    City,
    Country,
    Flight,
    Order,
    Route,
    Ticket,
)
from airport.serializers import (
    AirportDetailSerializer,
    AirportListSerializer,
)


AIRPORT_URL = reverse("airport:airport-list")


def airport_detail_url(airport_id: uuid.UUID) -> str:
    return reverse(
        "airport:airport-detail",
        args=[airport_id],
    )


def airport_image_upload_url(airport_id: uuid.UUID) -> str:
    return reverse(
        "airport:airport-upload-airport-image",
        args=[airport_id],
    )


def airport_statistics_url(airport_id: uuid.UUID) -> str:
    return reverse(
        "airport:airport-statistics",
        args=[airport_id],
    )


class BaseAirportApiTestCase(TestCase):
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

    def setUp(self) -> None:
        cache.clear()


class UnauthenticatedAirportApiTests(
    BaseAirportApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_list_airports(self) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        airports = Airport.objects.select_related(
            "closest_big_city__country",
        )

        serializer = AirportListSerializer(
            airports,
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

    def test_retrieve_airport(self) -> None:
        url = airport_detail_url(
            self.boryspil.pk,
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = AirportDetailSerializer(
            self.boryspil,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_filter_airports_by_city(self) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "city": self.kyiv.pk,
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
            str(self.boryspil.pk),
        )

    def test_filter_airports_by_city_name(self) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "city_name": "ky",
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
            str(self.boryspil.pk),
        )

    def test_filter_airports_by_city_name_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "city_name": "KYIV",
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

    def test_filter_airports_by_country(self) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "country": self.ukraine.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            airport["id"]
            for airport in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.boryspil.pk),
                str(self.lviv_airport.pk),
            },
        )

    def test_filter_airports_by_country_name(self) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "country_name": "pol",
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
            str(self.warsaw_airport.pk),
        )

    def test_filter_airports_by_name(self) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "name": "Bory",
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
            str(self.boryspil.pk),
        )

    def test_filter_airports_by_multiple_filters(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "country": self.ukraine.pk,
                "city_name": "lviv",
                "name": "international",
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
            str(self.lviv_airport.pk),
        )

    def test_filter_airports_by_nonexistent_city_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "city": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "city",
            response.data,
        )

    def test_filter_airports_by_invalid_city_id_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "city": "invalid-id",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "city",
            response.data,
        )

    def test_filter_airports_by_nonexistent_country_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "country": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "country",
            response.data,
        )

    def test_filter_airports_returns_empty_results_when_not_found(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
            data={
                "name": "Nonexistent Airport",
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

    def test_create_airport_unauthorized(self) -> None:
        response = self.client.post(
            path=AIRPORT_URL,
            data={
                "name": "Odesa Airport",
                "closest_big_city": self.kyiv.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_update_airport_unauthorized(self) -> None:
        response = self.client.put(
            path=airport_detail_url(self.boryspil.pk),
            data={
                "name": "Updated Airport",
                "closest_big_city": self.kyiv.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_partial_update_airport_unauthorized(
        self,
    ) -> None:
        response = self.client.patch(
            path=airport_detail_url(self.boryspil.pk),
            data={
                "name": "Updated Airport",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_delete_airport_unauthorized(self) -> None:
        response = self.client.delete(
            path=airport_detail_url(self.boryspil.pk),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class AuthenticatedAirportApiTests(
    BaseAirportApiTestCase,
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

    def test_list_airports(self) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_retrieve_airport(self) -> None:
        response = self.client.get(
            path=airport_detail_url(self.boryspil.pk),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_create_airport_forbidden(self) -> None:
        response = self.client.post(
            path=AIRPORT_URL,
            data={
                "name": "Odesa Airport",
                "closest_big_city": self.kyiv.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_update_airport_forbidden(self) -> None:
        response = self.client.put(
            path=airport_detail_url(self.boryspil.pk),
            data={
                "name": "Updated Airport",
                "closest_big_city": self.kyiv.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_partial_update_airport_forbidden(
        self,
    ) -> None:
        response = self.client.patch(
            path=airport_detail_url(self.boryspil.pk),
            data={
                "name": "Updated Airport",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_airport_forbidden(self) -> None:
        response = self.client.delete(
            path=airport_detail_url(self.boryspil.pk),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class AdminAirportApiTests(
    BaseAirportApiTestCase,
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

    def test_create_airport(self) -> None:
        payload = {
            "name": "Odesa International Airport",
            "closest_big_city": self.kyiv.pk,
        }

        response = self.client.post(
            path=AIRPORT_URL,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        airport = Airport.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            airport.name,
            payload["name"],
        )
        self.assertEqual(
            airport.closest_big_city,
            self.kyiv,
        )

    def test_create_airport_with_duplicate_name(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPORT_URL,
            data={
                "name": self.boryspil.name,
                "closest_big_city": self.kyiv.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_airport_with_invalid_city(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPORT_URL,
            data={
                "name": "Odesa Airport",
                "closest_big_city": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "closest_big_city",
            response.data,
        )

    def test_create_airport_without_city(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPORT_URL,
            data={
                "name": "Odesa Airport",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_update_airport(self) -> None:
        response = self.client.put(
            path=airport_detail_url(self.boryspil.pk),
            data={
                "name": "Updated Airport",
                "closest_big_city": self.lviv.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.boryspil.refresh_from_db()

        self.assertEqual(
            self.boryspil.name,
            "Updated Airport",
        )
        self.assertEqual(
            self.boryspil.closest_big_city,
            self.lviv,
        )

    def test_partial_update_airport(self) -> None:
        response = self.client.patch(
            path=airport_detail_url(self.boryspil.pk),
            data={
                "name": "Updated Airport",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.boryspil.refresh_from_db()

        self.assertEqual(
            self.boryspil.name,
            "Updated Airport",
        )
        self.assertEqual(
            self.boryspil.closest_big_city,
            self.kyiv,
        )

    def test_delete_airport(self) -> None:
        airport = Airport.objects.create(
            name="Odesa Airport",
            closest_big_city=self.kyiv,
        )

        airport_id = airport.pk

        response = self.client.delete(
            path=airport_detail_url(airport_id),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Airport.objects.filter(
                pk=airport_id,
            ).exists(),
        )

    def test_retrieve_nonexistent_airport(self) -> None:
        response = self.client.get(
            path=airport_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_nonexistent_airport(self) -> None:
        response = self.client.put(
            path=airport_detail_url(
                uuid.uuid4(),
            ),
            data={
                "name": "Airport",
                "closest_big_city": self.kyiv.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_nonexistent_airport(self) -> None:
        response = self.client.delete(
            path=airport_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class AirportImageUploadTests(
    BaseAirportApiTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
        )

        cls.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def tearDown(self) -> None:
        self.boryspil.refresh_from_db()

        if self.boryspil.image:
            self.boryspil.image.delete(
                save=False,
            )

    def test_admin_can_upload_airport_image(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.admin,
        )

        url = airport_image_upload_url(
            self.boryspil.pk,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
        ) as image_file:
            image = Image.new(
                "RGB",
                (10, 10),
            )

            image.save(
                image_file,
                format="JPEG",
            )

            image_file.seek(0)

            response = self.client.post(
                path=url,
                data={
                    "image": image_file,
                },
                format="multipart",
            )

        self.boryspil.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "image",
            response.data,
        )

        self.assertTrue(
            bool(self.boryspil.image),
        )

        self.assertTrue(
            os.path.exists(
                self.boryspil.image.path,
            ),
        )

    def test_admin_cannot_upload_invalid_image(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=airport_image_upload_url(
                self.boryspil.pk,
            ),
            data={
                "image": "not-an-image",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_authenticated_user_cannot_upload_airport_image(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.user,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
        ) as image_file:
            image = Image.new(
                "RGB",
                (10, 10),
            )
            image.save(
                image_file,
                format="JPEG",
            )
            image_file.seek(0)

            response = self.client.post(
                path=airport_image_upload_url(
                    self.boryspil.pk,
                ),
                data={
                    "image": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unauthenticated_user_cannot_upload_airport_image(
        self,
    ) -> None:
        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
        ) as image_file:
            image = Image.new(
                "RGB",
                (10, 10),
            )
            image.save(
                image_file,
                format="JPEG",
            )
            image_file.seek(0)

            response = self.client.post(
                path=airport_image_upload_url(
                    self.boryspil.pk,
                ),
                data={
                    "image": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_upload_image_to_nonexistent_airport_returns_not_found(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.admin,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
        ) as image_file:
            image = Image.new(
                "RGB",
                (10, 10),
            )
            image.save(
                image_file,
                format="JPEG",
            )
            image_file.seek(0)

            response = self.client.post(
                path=airport_image_upload_url(
                    uuid.uuid4(),
                ),
                data={
                    "image": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_airport_list_contains_image_field(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPORT_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "image",
            response.data["results"][0],
        )

    def test_airport_detail_contains_image_field(
        self,
    ) -> None:
        response = self.client.get(
            path=airport_detail_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "image",
            response.data,
        )


class AirportStatisticsApiTests(
    BaseAirportApiTestCase,
):
    NOW = datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        from airport.models import (
            Airplane,
            AirplaneType,
        )

        cls.airplane_type = AirplaneType.objects.create(
            name="Boeing 737",
        )

        cls.airplane = Airplane.objects.create(
            name="UR-STAT",
            rows=20,
            seats_in_row=6,
            airplane_type=cls.airplane_type,
        )

        cls.route_from_boryspil = Route.objects.create(
            source=cls.boryspil,
            destination=cls.lviv_airport,
            distance=470,
        )

        cls.route_to_boryspil = Route.objects.create(
            source=cls.warsaw_airport,
            destination=cls.boryspil,
            distance=700,
        )

        cls.future_departure = Flight.objects.create(
            route=cls.route_from_boryspil,
            airplane=cls.airplane,
            departure_time=cls.NOW + timedelta(hours=2),
            arrival_time=cls.NOW + timedelta(hours=3),
        )

        cls.future_arrival = Flight.objects.create(
            route=cls.route_to_boryspil,
            airplane=cls.airplane,
            departure_time=cls.NOW + timedelta(hours=4),
            arrival_time=cls.NOW + timedelta(hours=5),
        )

        cls.cancelled_future_departure = Flight.objects.create(
            route=cls.route_from_boryspil,
            airplane=cls.airplane,
            departure_time=cls.NOW + timedelta(hours=6),
            arrival_time=cls.NOW + timedelta(hours=7),
            status=Flight.Status.CANCELLED,
        )

        cls.past_departure = Flight.objects.create(
            route=cls.route_from_boryspil,
            airplane=cls.airplane,
            departure_time=cls.NOW - timedelta(hours=3),
            arrival_time=cls.NOW - timedelta(hours=2),
        )

        cls.user = get_user_model().objects.create_user(
            email="someone@example.com",
            password="testpass123",
        )

        cls.order = Order.objects.create(
            user=cls.user,
        )

        cls.active_ticket = Ticket.objects.create(
            order=cls.order,
            flight=cls.future_departure,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        cls.cancelled_ticket = Ticket.objects.create(
            order=cls.order,
            flight=cls.future_departure,
            row=1,
            seat=2,
            status=Ticket.Status.CANCELLED,
        )

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    @patch("airport.views.timezone.now")
    def test_airport_statistics_is_available_for_unauthenticated_user(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    @patch("airport.views.timezone.now")
    def test_airport_statistics_returns_expected_fields(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            set(response.data.keys()),
            {
                "airport_id",
                "airport_name",
                "departing_routes_count",
                "arriving_routes_count",
                "upcoming_departures_count",
                "upcoming_arrivals_count",
                "total_upcoming_flights",
                "active_tickets_count",
                "cancelled_tickets_count",
                "total_tickets_count",
            },
        )

    @patch("airport.views.timezone.now")
    def test_airport_statistics_returns_route_counts(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            response.data["departing_routes_count"],
            1,
        )
        self.assertEqual(
            response.data["arriving_routes_count"],
            1,
        )

    @patch("airport.views.timezone.now")
    def test_airport_statistics_returns_upcoming_flight_counts(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            response.data["upcoming_departures_count"],
            1,
        )
        self.assertEqual(
            response.data["upcoming_arrivals_count"],
            1,
        )
        self.assertEqual(
            response.data["total_upcoming_flights"],
            2,
        )

    @patch("airport.views.timezone.now")
    def test_airport_statistics_ignores_cancelled_upcoming_flights(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            response.data["upcoming_departures_count"],
            1,
        )

    @patch("airport.views.timezone.now")
    def test_airport_statistics_ignores_past_flights(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            response.data["upcoming_departures_count"],
            1,
        )

    @patch("airport.views.timezone.now")
    def test_airport_statistics_returns_ticket_counts(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            response.data["active_tickets_count"],
            1,
        )
        self.assertEqual(
            response.data["cancelled_tickets_count"],
            1,
        )
        self.assertEqual(
            response.data["total_tickets_count"],
            2,
        )

    @patch("airport.views.timezone.now")
    def test_airport_statistics_returns_airport_identity(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                self.boryspil.pk,
            ),
        )

        self.assertEqual(
            response.data["airport_id"],
            str(self.boryspil.pk),
        )
        self.assertEqual(
            response.data["airport_name"],
            self.boryspil.name,
        )

    @patch("airport.views.timezone.now")
    def test_airport_statistics_returns_not_found_for_missing_airport(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.get(
            path=airport_statistics_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
