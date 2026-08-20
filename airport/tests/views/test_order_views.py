import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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
from airport.views import OrderViewSet


ORDER_URL = reverse("airport:order-list")


def order_detail_url(order_id: uuid.UUID) -> str:
    return reverse(
        "airport:order-detail",
        args=[order_id],
    )


def order_cancel_url(order_id: uuid.UUID) -> str:
    return reverse(
        "airport:order-cancel",
        args=[order_id],
    )


class BaseOrderApiTestCase(TestCase):
    NOW = datetime(
        2026,
        9,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    FUTURE_DEPARTURE = datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    FUTURE_ARRIVAL = datetime(
        2026,
        9,
        10,
        12,
        0,
        tzinfo=timezone.utc,
    )

    @classmethod
    def setUpTestData(cls) -> None:
        cls.country = Country.objects.create(
            name="Ukraine",
        )

        cls.kyiv = City.objects.create(
            name="Kyiv",
            country=cls.country,
        )
        cls.lviv = City.objects.create(
            name="Lviv",
            country=cls.country,
        )

        cls.source_airport = Airport.objects.create(
            name="Boryspil International Airport",
            closest_big_city=cls.kyiv,
        )
        cls.destination_airport = Airport.objects.create(
            name="Lviv International Airport",
            closest_big_city=cls.lviv,
        )

        cls.route = Route.objects.create(
            source=cls.source_airport,
            destination=cls.destination_airport,
            distance=470,
        )

        cls.airplane_type = AirplaneType.objects.create(
            name="Boeing 737",
        )

        cls.airplane = Airplane.objects.create(
            name="UR-001",
            rows=3,
            seats_in_row=4,
            airplane_type=cls.airplane_type,
        )

        cls.crew = Crew.objects.create(
            first_name="John",
            last_name="Smith",
        )

        cls.flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane,
            departure_time=cls.FUTURE_DEPARTURE,
            arrival_time=cls.FUTURE_ARRIVAL,
        )
        cls.flight.crew.add(cls.crew)

        cls.cancelled_flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane,
            departure_time=datetime(
                2026,
                9,
                20,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                20,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            status=Flight.Status.CANCELLED,
        )
        cls.cancelled_flight.crew.add(cls.crew)

        cls.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )

        cls.other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="testpass123",
        )

        cls.user_order = Order.objects.create(
            user=cls.user,
        )

        cls.user_ticket_active = Ticket.objects.create(
            order=cls.user_order,
            flight=cls.flight,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        cls.user_ticket_cancelled = Ticket.objects.create(
            order=cls.user_order,
            flight=cls.flight,
            row=1,
            seat=2,
            status=Ticket.Status.CANCELLED,
        )

        cls.second_user_order = Order.objects.create(
            user=cls.user,
        )

        cls.second_user_ticket = Ticket.objects.create(
            order=cls.second_user_order,
            flight=cls.flight,
            row=1,
            seat=3,
            status=Ticket.Status.ACTIVE,
        )

        cls.other_user_order = Order.objects.create(
            user=cls.other_user,
        )

        cls.other_user_ticket = Ticket.objects.create(
            order=cls.other_user_order,
            flight=cls.flight,
            row=1,
            seat=4,
            status=Ticket.Status.ACTIVE,
        )

    def setUp(self) -> None:
        cache.clear()

    def make_order_payload(
        self,
        *,
        flight: Flight | None = None,
        row: int = 2,
        seat: int = 1,
    ) -> dict[str, object]:
        if flight is None:
            flight = self.flight

        return {
            "tickets": [
                {
                    "flight": flight.pk,
                    "row": row,
                    "seat": seat,
                },
            ],
        }


class UnauthenticatedOrderApiTests(
    BaseOrderApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_list_orders_requires_authentication(
        self,
    ) -> None:
        response = self.client.get(
            path=ORDER_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_retrieve_order_requires_authentication(
        self,
    ) -> None:
        response = self.client.get(
            path=order_detail_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_create_order_requires_authentication(
        self,
    ) -> None:
        response = self.client.post(
            path=ORDER_URL,
            data=self.make_order_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_cancel_order_requires_authentication(
        self,
    ) -> None:
        response = self.client.post(
            path=order_cancel_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class AuthenticatedOrderApiTests(
    BaseOrderApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()

        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user,
        )

    def test_list_returns_only_authenticated_users_orders(
        self,
    ) -> None:
        response = self.client.get(
            path=ORDER_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.user_order.pk),
                str(self.second_user_order.pk),
            },
        )

        self.assertNotIn(
            str(self.other_user_order.pk),
            returned_ids,
        )

    def test_list_returns_correct_order_count(
        self,
    ) -> None:
        response = self.client.get(
            path=ORDER_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

    def test_list_returns_tickets_count(
        self,
    ) -> None:
        response = self.client.get(
            path=ORDER_URL,
        )

        order_data = next(
            item
            for item in response.data["results"]
            if item["id"] == str(self.user_order.pk)
        )

        self.assertEqual(
            order_data["tickets_count"],
            2,
        )

    def test_tickets_count_includes_cancelled_tickets(
        self,
    ) -> None:
        response = self.client.get(
            path=ORDER_URL,
        )

        order_data = next(
            item
            for item in response.data["results"]
            if item["id"] == str(self.user_order.pk)
        )

        self.assertEqual(
            order_data["tickets_count"],
            2,
        )

    def test_retrieve_own_order(
        self,
    ) -> None:
        response = self.client.get(
            path=order_detail_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            str(self.user_order.pk),
        )

        self.assertEqual(
            len(response.data["tickets"]),
            2,
        )

    def test_retrieve_order_returns_ticket_data(
        self,
    ) -> None:
        response = self.client.get(
            path=order_detail_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_seats = {
            (
                ticket["row"],
                ticket["seat"],
            )
            for ticket in response.data["tickets"]
        }

        self.assertEqual(
            returned_seats,
            {
                (1, 1),
                (1, 2),
            },
        )

    def test_retrieve_another_users_order_returns_not_found(
        self,
    ) -> None:
        response = self.client.get(
            path=order_detail_url(
                self.other_user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_retrieve_nonexistent_order_returns_not_found(
        self,
    ) -> None:
        response = self.client.get(
            path=order_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_create_order(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        initial_count = Order.objects.count()

        response = self.client.post(
            path=ORDER_URL,
            data=self.make_order_payload(
                row=2,
                seat=1,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Order.objects.count(),
            initial_count + 1,
        )

        order = Order.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            order.user,
            self.user,
        )

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_create_order_creates_tickets(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=ORDER_URL,
            data=self.make_order_payload(
                row=2,
                seat=1,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            order.tickets.count(),
            1,
        )

        ticket = order.tickets.get()

        self.assertEqual(
            ticket.flight,
            self.flight,
        )
        self.assertEqual(
            ticket.row,
            2,
        )
        self.assertEqual(
            ticket.seat,
            1,
        )
        self.assertEqual(
            ticket.status,
            Ticket.Status.ACTIVE,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_create_order_assigns_authenticated_user(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        payload = self.make_order_payload(
            row=2,
            seat=1,
        )

        payload["user"] = self.other_user.pk

        response = self.client.post(
            path=ORDER_URL,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            order.user,
            self.user,
        )

        self.assertNotEqual(
            order.user,
            self.other_user,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_create_order_rejects_already_booked_active_seat(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=ORDER_URL,
            data=self.make_order_payload(
                row=1,
                seat=1,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "tickets",
            response.data,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_create_order_allows_seat_from_cancelled_ticket(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=ORDER_URL,
            data=self.make_order_payload(
                row=1,
                seat=2,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            pk=response.data["id"],
        )

        self.assertTrue(
            order.tickets.filter(
                flight=self.flight,
                row=1,
                seat=2,
                status=Ticket.Status.ACTIVE,
            ).exists(),
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_create_order_rejects_cancelled_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=ORDER_URL,
            data=self.make_order_payload(
                flight=self.cancelled_flight,
                row=2,
                seat=1,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "tickets",
            response.data,
        )

    def test_update_order_not_allowed(
        self,
    ) -> None:
        response = self.client.put(
            path=order_detail_url(
                self.user_order.pk,
            ),
            data={
                "status": Order.Status.CANCELLED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_partial_update_order_not_allowed(
        self,
    ) -> None:
        response = self.client.patch(
            path=order_detail_url(
                self.user_order.pk,
            ),
            data={
                "status": Order.Status.CANCELLED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_delete_order_not_allowed(
        self,
    ) -> None:
        order_id = self.user_order.pk

        response = self.client.delete(
            path=order_detail_url(
                order_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        self.assertTrue(
            Order.objects.filter(
                pk=order_id,
            ).exists(),
        )


class OrderCancellationApiTests(
    BaseOrderApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()

        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_user_can_cancel_own_future_order(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=order_cancel_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user_order.refresh_from_db()

        self.assertEqual(
            self.user_order.status,
            Order.Status.CANCELLED,
        )

        self.assertEqual(
            response.data["id"],
            str(self.user_order.pk),
        )

        self.assertEqual(
            response.data["status"],
            Order.Status.CANCELLED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_order_cancels_all_tickets(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=order_cancel_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            self.user_order.tickets.filter(
                status=Ticket.Status.ACTIVE,
            ).exists(),
        )

        self.assertEqual(
            self.user_order.tickets.filter(
                status=Ticket.Status.CANCELLED,
            ).count(),
            2,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_order_does_not_change_flight_status(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        original_status = self.flight.status

        response = self.client.post(
            path=order_cancel_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.flight.refresh_from_db()

        self.assertEqual(
            self.flight.status,
            original_status,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_order_does_not_affect_other_orders(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=order_cancel_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.second_user_order.refresh_from_db()
        self.other_user_order.refresh_from_db()

        self.assertEqual(
            self.second_user_order.status,
            Order.Status.CONFIRMED,
        )

        self.assertEqual(
            self.other_user_order.status,
            Order.Status.CONFIRMED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_order_rejects_already_cancelled_order(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.user_order.status = Order.Status.CANCELLED
        self.user_order.save(
            update_fields=[
                "status",
            ],
        )

        response = self.client.post(
            path=order_cancel_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data,
            {
                "detail": [
                    "Order is already cancelled.",
                ],
            },
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_order_rejects_order_after_flight_departure(
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

        response = self.client.post(
            path=order_cancel_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.user_order.refresh_from_db()
        self.user_ticket_active.refresh_from_db()

        self.assertEqual(
            self.user_order.status,
            Order.Status.CONFIRMED,
        )

        self.assertEqual(
            self.user_ticket_active.status,
            Ticket.Status.ACTIVE,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_order_rejects_order_at_flight_departure_time(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.FUTURE_DEPARTURE

        response = self.client.post(
            path=order_cancel_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_user_cannot_cancel_another_users_order(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=order_cancel_url(
                self.other_user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.other_user_order.refresh_from_db()

        self.assertEqual(
            self.other_user_order.status,
            Order.Status.CONFIRMED,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_cancel_nonexistent_order_returns_not_found(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=order_cancel_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class AdminOrderApiTests(
    BaseOrderApiTestCase,
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

    def test_admin_list_returns_all_orders(
        self,
    ) -> None:
        response = self.client.get(
            path=ORDER_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.user_order.pk),
                str(self.second_user_order.pk),
                str(self.other_user_order.pk),
            },
        )

    def test_admin_can_retrieve_another_users_order(
        self,
    ) -> None:
        response = self.client.get(
            path=order_detail_url(
                self.other_user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            str(self.other_user_order.pk),
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_admin_can_create_order(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=ORDER_URL,
            data=self.make_order_payload(
                row=2,
                seat=1,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            order.user,
            self.admin,
        )

    @patch(
        "airport.utils.validators.timezone.now"
    )
    def test_admin_can_cancel_another_users_order(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        response = self.client.post(
            path=order_cancel_url(
                self.other_user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.other_user_order.refresh_from_db()
        self.other_user_ticket.refresh_from_db()

        self.assertEqual(
            self.other_user_order.status,
            Order.Status.CANCELLED,
        )

        self.assertEqual(
            self.other_user_ticket.status,
            Ticket.Status.CANCELLED,
        )

    def test_admin_retrieve_nonexistent_order_returns_not_found(
        self,
    ) -> None:
        response = self.client.get(
            path=order_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_admin_update_order_not_allowed(
        self,
    ) -> None:
        response = self.client.put(
            path=order_detail_url(
                self.user_order.pk,
            ),
            data={},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_admin_partial_update_order_not_allowed(
        self,
    ) -> None:
        response = self.client.patch(
            path=order_detail_url(
                self.user_order.pk,
            ),
            data={},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_admin_delete_order_not_allowed(
        self,
    ) -> None:
        response = self.client.delete(
            path=order_detail_url(
                self.user_order.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class OrderViewSetQuerysetTests(TestCase):
    def test_get_queryset_returns_none_queryset_for_swagger_fake_view(
        self,
    ) -> None:
        view = OrderViewSet()
        view.swagger_fake_view = True

        queryset = view.get_queryset()

        self.assertFalse(
            queryset.exists(),
        )

        self.assertEqual(
            queryset.model,
            Order,
        )
