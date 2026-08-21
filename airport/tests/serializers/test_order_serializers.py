from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from airport.models import Flight, Order, Ticket
from airport.serializers import (
    MAX_TICKETS_PER_ORDER,
    OrderCancelSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderSerializer,
)
from airport.tests.base import BaseFlightScheduleTestCase


class OrderSerializerTests(BaseFlightScheduleTestCase):
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

        cls.user = get_user_model().objects.create_user(
            email="someone@example.com",
            password="testpass123",
        )

    def make_ticket_data(
        self,
        *,
        flight: Flight | None = None,
        row: int = 1,
        seat: int = 1,
    ) -> dict[str, object]:
        if flight is None:
            flight = self.existing_flight

        return {
            "flight": flight.pk,
            "row": row,
            "seat": seat,
        }

    def make_order_data(
        self,
        *,
        tickets: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        if tickets is None:
            tickets = [
                self.make_ticket_data(),
            ]

        return {
            "tickets": tickets,
        }

    def make_existing_ticket(
        self,
        *,
        flight: Flight | None = None,
        row: int = 1,
        seat: int = 1,
        status: str = Ticket.Status.ACTIVE,
    ) -> Ticket:
        if flight is None:
            flight = self.existing_flight

        order = Order.objects.create(
            user=self.user,
        )

        return Ticket.objects.create(
            order=order,
            flight=flight,
            row=row,
            seat=seat,
            status=status,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_accepts_valid_data(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(),
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            len(serializer.validated_data["tickets"]),
            1,
        )

        ticket = serializer.validated_data["tickets"][0]

        self.assertEqual(
            ticket["flight"],
            self.existing_flight,
        )
        self.assertEqual(
            ticket["row"],
            1,
        )
        self.assertEqual(
            ticket["seat"],
            1,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_accepts_multiple_tickets_for_same_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        row=1,
                        seat=1,
                    ),
                    self.make_ticket_data(
                        row=1,
                        seat=2,
                    ),
                ],
            ),
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            len(serializer.validated_data["tickets"]),
            2,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_accepts_maximum_ticket_count(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        tickets = [
            self.make_ticket_data(
                row=1,
                seat=index + 1,
            )
            for index in range(MAX_TICKETS_PER_ORDER)
        ]

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=tickets,
            ),
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_rejects_more_than_maximum_ticket_count(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        tickets = []

        for index in range(MAX_TICKETS_PER_ORDER + 1):
            row = (
                index // self.airplane_1.seats_in_row
            ) + 1
            seat = (
                index % self.airplane_1.seats_in_row
            ) + 1

            tickets.append(
                self.make_ticket_data(
                    row=row,
                    seat=seat,
                )
            )

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=tickets,
            ),
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "tickets": [
                    (
                        f"An order cannot contain more "
                        f"than {MAX_TICKETS_PER_ORDER} tickets."
                    ),
                ],
            },
        )

    def test_order_serializer_rejects_empty_tickets(
        self,
    ) -> None:
        serializer = OrderSerializer(
            data={
                "tickets": [],
            },
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "tickets",
            serializer.errors,
        )

    def test_order_serializer_rejects_missing_tickets(
        self,
    ) -> None:
        serializer = OrderSerializer(
            data={},
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "tickets": [
                    "This field is required.",
                ],
            },
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_rejects_tickets_for_different_flights(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = datetime(
            2026,
            9,
            10,
            8,
            0,
            tzinfo=timezone.utc,
        )

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        flight=self.existing_flight,
                        row=1,
                        seat=1,
                    ),
                    self.make_ticket_data(
                        flight=self.cancelled_flight,
                        row=1,
                        seat=2,
                    ),
                ],
            ),
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "tickets": [
                    (
                        "All tickets in an order must belong "
                        "to the same flight."
                    ),
                ],
            },
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_rejects_cancelled_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        flight=self.cancelled_flight,
                    ),
                ],
            ),
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "tickets": {
                    "flight": [
                        (
                            "Tickets cannot be purchased "
                            "for a cancelled flight."
                        ),
                    ],
                },
            },
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_rejects_departed_flight(
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

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        flight=self.existing_flight,
                    ),
                ],
            ),
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "tickets": {
                    "flight": [
                        "Tickets cannot be purchased after departure.",
                    ],
                },
            },
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_rejects_flight_departing_now(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.EXISTING_DEPARTURE_TIME

        serializer = OrderSerializer(
            data=self.make_order_data(),
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "tickets",
            serializer.errors,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_rejects_duplicate_seat_in_request(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        row=1,
                        seat=1,
                    ),
                    self.make_ticket_data(
                        row=1,
                        seat=1,
                    ),
                ],
            ),
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "tickets": [
                    "Seat 1-1 is duplicated in this order.",
                ],
            },
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_allows_different_seats(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        row=1,
                        seat=1,
                    ),
                    self.make_ticket_data(
                        row=1,
                        seat=2,
                    ),
                ],
            ),
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_rejects_already_booked_active_seat(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.make_existing_ticket(
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        row=1,
                        seat=1,
                    ),
                ],
            ),
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "tickets": [
                    (
                        "Seat 1-1 is already booked "
                        "for this flight."
                    ),
                ],
            },
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_allows_seat_from_cancelled_ticket(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        self.make_existing_ticket(
            row=1,
            seat=1,
            status=Ticket.Status.CANCELLED,
        )

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        row=1,
                        seat=1,
                    ),
                ],
            ),
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_creates_order(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(),
        )

        serializer.is_valid(
            raise_exception=True,
        )

        order = serializer.save(
            user=self.user,
        )

        self.assertIsInstance(
            order,
            Order,
        )

        self.assertEqual(
            order.user,
            self.user,
        )

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

        self.assertTrue(
            Order.objects.filter(
                pk=order.pk,
            ).exists(),
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_creates_all_tickets(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(
                tickets=[
                    self.make_ticket_data(
                        row=1,
                        seat=1,
                    ),
                    self.make_ticket_data(
                        row=1,
                        seat=2,
                    ),
                ],
            ),
        )

        serializer.is_valid(
            raise_exception=True,
        )

        order = serializer.save(
            user=self.user,
        )

        self.assertEqual(
            order.tickets.count(),
            2,
        )

        self.assertTrue(
            order.tickets.filter(
                flight=self.existing_flight,
                row=1,
                seat=1,
            ).exists(),
        )

        self.assertTrue(
            order.tickets.filter(
                flight=self.existing_flight,
                row=1,
                seat=2,
            ).exists(),
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_creates_tickets_with_active_status(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(),
        )

        serializer.is_valid(
            raise_exception=True,
        )

        order = serializer.save(
            user=self.user,
        )

        ticket = order.tickets.get()

        self.assertEqual(
            ticket.status,
            Ticket.Status.ACTIVE,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_status_is_read_only(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        data = self.make_order_data()
        data["status"] = Order.Status.CANCELLED

        serializer = OrderSerializer(
            data=data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "status",
            serializer.validated_data,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_id_is_read_only(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        data = self.make_order_data()
        data["id"] = "11111111-1111-1111-1111-111111111111"

        serializer = OrderSerializer(
            data=data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "id",
            serializer.validated_data,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_order_serializer_created_at_is_read_only(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        data = self.make_order_data()
        data["created_at"] = self.NOW

        serializer = OrderSerializer(
            data=data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "created_at",
            serializer.validated_data,
        )

    @patch("airport.utils.validators.timezone.now")
    @patch(
        "airport.serializers.Ticket.objects.create",
        side_effect=IntegrityError,
    )
    def test_order_serializer_converts_integrity_error_to_validation_error(
        self,
        mock_ticket_create: MagicMock,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        serializer = OrderSerializer(
            data=self.make_order_data(),
        )

        serializer.is_valid(
            raise_exception=True,
        )

        with self.assertRaises(ValidationError) as context:
            serializer.save(
                user=self.user,
            )

        self.assertEqual(
            context.exception.detail,
            {
                "tickets": [
                    (
                        "One or more selected seats are no longer "
                        "available. Please choose different seats."
                    ),
                ],
            },
        )

        mock_ticket_create.assert_called_once()

    @patch("airport.utils.validators.timezone.now")
    @patch(
        "airport.serializers.Ticket.objects.create",
        side_effect=IntegrityError,
    )
    def test_order_serializer_rolls_back_order_when_ticket_creation_fails(
        self,
        mock_ticket_create: MagicMock,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        initial_orders_count = Order.objects.count()

        serializer = OrderSerializer(
            data=self.make_order_data(),
        )

        serializer.is_valid(
            raise_exception=True,
        )

        with self.assertRaises(ValidationError):
            serializer.save(
                user=self.user,
            )

        self.assertEqual(
            Order.objects.count(),
            initial_orders_count,
        )


class OrderListSerializerTests(
    BaseFlightScheduleTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(
            email="someone@example.com",
            password="testpass123",
        )

        cls.order = Order.objects.create(
            user=cls.user,
        )

    def setUp(self) -> None:
        self.order.tickets_count = 2

    def test_order_list_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = OrderListSerializer(
            self.order,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "tickets_count",
                "status",
                "created_at",
            },
        )

    def test_order_list_serializer_returns_order_id(
        self,
    ) -> None:
        serializer = OrderListSerializer(
            self.order,
        )

        self.assertEqual(
            serializer.data["id"],
            str(self.order.pk),
        )

    def test_order_list_serializer_returns_tickets_count(
        self,
    ) -> None:
        serializer = OrderListSerializer(
            self.order,
        )

        self.assertEqual(
            serializer.data["tickets_count"],
            2,
        )

    def test_order_list_serializer_returns_status(
        self,
    ) -> None:
        serializer = OrderListSerializer(
            self.order,
        )

        self.assertEqual(
            serializer.data["status"],
            Order.Status.CONFIRMED,
        )

    def test_order_list_serializer_returns_created_at(
        self,
    ) -> None:
        serializer = OrderListSerializer(
            self.order,
        )

        self.assertIn(
            "created_at",
            serializer.data,
        )

        self.assertIsNotNone(
            serializer.data["created_at"],
        )

    def test_order_list_serializer_returns_cancelled_status(
        self,
    ) -> None:
        self.order.status = Order.Status.CANCELLED

        serializer = OrderListSerializer(
            self.order,
        )

        self.assertEqual(
            serializer.data["status"],
            Order.Status.CANCELLED,
        )


class OrderDetailSerializerTests(
    BaseFlightScheduleTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(
            email="someone@example.com",
            password="testpass123",
        )

        cls.order = Order.objects.create(
            user=cls.user,
        )

        cls.ticket_1 = Ticket.objects.create(
            order=cls.order,
            flight=cls.existing_flight,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        cls.ticket_2 = Ticket.objects.create(
            order=cls.order,
            flight=cls.existing_flight,
            row=1,
            seat=2,
            status=Ticket.Status.ACTIVE,
        )

    def setUp(self) -> None:
        self.existing_flight.available_seats = (
            self.airplane_1.capacity - 2
        )

        tickets = list(
            self.order.tickets.select_related(
                "flight__airplane__airplane_type",
                "flight__route__source__closest_big_city__country",
                "flight__route__destination__closest_big_city__country",
            ).prefetch_related(
                "flight__crew",
            )
        )

        for ticket in tickets:
            ticket.flight.available_seats = (
                self.airplane_1.capacity - 2
            )

        self.order._prefetched_objects_cache = {
            "tickets": tickets,
        }

    def test_order_detail_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = OrderDetailSerializer(
            self.order,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "tickets",
                "status",
                "created_at",
            },
        )

    def test_order_detail_serializer_returns_order_id(
        self,
    ) -> None:
        serializer = OrderDetailSerializer(
            self.order,
        )

        self.assertEqual(
            serializer.data["id"],
            str(self.order.pk),
        )

    def test_order_detail_serializer_returns_status(
        self,
    ) -> None:
        serializer = OrderDetailSerializer(
            self.order,
        )

        self.assertEqual(
            serializer.data["status"],
            Order.Status.CONFIRMED,
        )

    def test_order_detail_serializer_returns_all_tickets(
        self,
    ) -> None:
        serializer = OrderDetailSerializer(
            self.order,
        )

        self.assertEqual(
            len(serializer.data["tickets"]),
            2,
        )

    def test_order_detail_serializer_returns_ticket_data(
        self,
    ) -> None:
        serializer = OrderDetailSerializer(
            self.order,
        )

        tickets = serializer.data["tickets"]

        ticket_data = next(
            ticket
            for ticket in tickets
            if ticket["id"] == str(self.ticket_1.pk)
        )

        self.assertEqual(
            ticket_data["row"],
            1,
        )
        self.assertEqual(
            ticket_data["seat"],
            1,
        )
        self.assertEqual(
            ticket_data["status"],
            Ticket.Status.ACTIVE,
        )

    def test_order_detail_serializer_returns_all_ticket_data(
        self,
    ) -> None:
        serializer = OrderDetailSerializer(
            self.order,
        )

        tickets = serializer.data["tickets"]

        seats = {
            (
                ticket["row"],
                ticket["seat"],
                ticket["status"],
            )
            for ticket in tickets
        }

        self.assertEqual(
            seats,
            {
                (
                    1,
                    1,
                    Ticket.Status.ACTIVE,
                ),
                (
                    1,
                    2,
                    Ticket.Status.ACTIVE,
                ),
            },
        )

    def test_order_detail_serializer_returns_nested_flight(
        self,
    ) -> None:
        serializer = OrderDetailSerializer(
            self.order,
        )

        flight_data = (
            serializer.data["tickets"][0]["flight"]
        )

        self.assertEqual(
            flight_data["id"],
            str(self.existing_flight.pk),
        )
        self.assertEqual(
            flight_data["source"],
            self.kyiv.name,
        )
        self.assertEqual(
            flight_data["destination"],
            self.lviv.name,
        )
        self.assertEqual(
            flight_data["airplane"],
            self.airplane_1.name,
        )
        self.assertEqual(
            flight_data["airplane_type"],
            self.airplane_type.name,
        )
        self.assertEqual(
            flight_data["crew"],
            [
                self.crew_1.full_name,
            ],
        )
        self.assertEqual(
            flight_data["available_seats"],
            self.airplane_1.capacity - 2,
        )

    def test_order_detail_serializer_returns_created_at(
        self,
    ) -> None:
        serializer = OrderDetailSerializer(
            self.order,
        )

        self.assertIsNotNone(
            serializer.data["created_at"],
        )

    def test_order_detail_serializer_returns_empty_tickets_for_empty_order(
        self,
    ) -> None:
        order = Order.objects.create(
            user=self.user,
        )

        serializer = OrderDetailSerializer(
            order,
        )

        self.assertEqual(
            serializer.data["tickets"],
            [],
        )


class OrderCancelSerializerTests(
    BaseFlightScheduleTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(
            email="someone@example.com",
            password="testpass123",
        )

        cls.cancelled_order = Order.objects.create(
            user=cls.user,
            status=Order.Status.CANCELLED,
        )

    def test_order_cancel_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = OrderCancelSerializer(
            self.cancelled_order,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "status",
            },
        )

    def test_order_cancel_serializer_returns_order_id(
        self,
    ) -> None:
        serializer = OrderCancelSerializer(
            self.cancelled_order,
        )

        self.assertEqual(
            serializer.data["id"],
            str(self.cancelled_order.pk),
        )

    def test_order_cancel_serializer_returns_cancelled_status(
        self,
    ) -> None:
        serializer = OrderCancelSerializer(
            self.cancelled_order,
        )

        self.assertEqual(
            serializer.data["status"],
            Order.Status.CANCELLED,
        )

    def test_order_cancel_serializer_fields_are_read_only(
        self,
    ) -> None:
        serializer = OrderCancelSerializer(
            data={
                "id": self.cancelled_order.pk,
                "status": Order.Status.CONFIRMED,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data,
            {},
        )
