from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from airport.models import Flight, Order, Ticket
from airport.tests.base import BaseFlightScheduleTestCase
from airport.utils.validators import validate_order_cancellation


class OrderCancellationValidationTests(
    BaseFlightScheduleTestCase,
):
    NOW = datetime(
        2026,
        9,
        10,
        13,
        0,
        tzinfo=timezone.utc,
    )

    ALREADY_CANCELLED_ERROR_MSG = {
        "detail": [
            "Order is already cancelled.",
        ],
    }

    DEPARTED_FLIGHT_ERROR_MSG = {
        "detail": [
            "Order cannot be cancelled after flight departure.",
        ],
    }

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(
            email="order@example.com",
            password="testpass123",
        )

        cls.future_flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane_2,
            departure_time=datetime(
                2026,
                9,
                10,
                16,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                18,
                0,
                tzinfo=timezone.utc,
            ),
        )

        cls.cancelled_departed_flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane_2,
            departure_time=datetime(
                2026,
                9,
                10,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            status=Flight.Status.CANCELLED,
        )

    def make_order(
        self,
        *,
        status: str = Order.Status.CONFIRMED,
    ) -> Order:
        return Order.objects.create(
            user=self.user,
            status=status,
        )

    def make_ticket(
        self,
        *,
        order: Order,
        flight: Flight,
        status: str = Ticket.Status.ACTIVE,
        row: int = 1,
        seat: int = 1,
    ) -> Ticket:
        return Ticket.objects.create(
            order=order,
            flight=flight,
            status=status,
            row=row,
            seat=seat,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_order_cancellation_allows_order_before_flight_departure(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        order = self.make_order()

        self.make_ticket(
            order=order,
            flight=self.future_flight,
        )

        validate_order_cancellation(
            order=order,
            error_to_raise=ValidationError,
        )

    def test_validate_order_cancellation_rejects_already_cancelled_order(
        self,
    ) -> None:
        order = self.make_order(
            status=Order.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError) as context:
            validate_order_cancellation(
                order=order,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ALREADY_CANCELLED_ERROR_MSG,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_order_cancellation_rejects_order_after_flight_departure(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        order = self.make_order()

        self.make_ticket(
            order=order,
            flight=self.existing_flight,
        )

        with self.assertRaises(ValidationError) as context:
            validate_order_cancellation(
                order=order,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.DEPARTED_FLIGHT_ERROR_MSG,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_order_cancellation_rejects_flight_departing_now(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane_2,
            departure_time=self.NOW,
            arrival_time=datetime(
                2026,
                9,
                10,
                15,
                0,
                tzinfo=timezone.utc,
            ),
        )

        order = self.make_order()

        self.make_ticket(
            order=order,
            flight=flight,
        )

        with self.assertRaises(ValidationError) as context:
            validate_order_cancellation(
                order=order,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.DEPARTED_FLIGHT_ERROR_MSG,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_order_cancellation_ignores_cancelled_ticket(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        order = self.make_order()

        self.make_ticket(
            order=order,
            flight=self.existing_flight,
            status=Ticket.Status.CANCELLED,
        )

        validate_order_cancellation(
            order=order,
            error_to_raise=ValidationError,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_order_cancellation_ignores_cancelled_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        order = self.make_order()

        self.make_ticket(
            order=order,
            flight=self.cancelled_departed_flight,
        )

        validate_order_cancellation(
            order=order,
            error_to_raise=ValidationError,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_order_cancellation_allows_order_without_tickets(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        order = self.make_order()

        validate_order_cancellation(
            order=order,
            error_to_raise=ValidationError,
        )
