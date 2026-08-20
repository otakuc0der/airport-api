from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from rest_framework.exceptions import ValidationError

from airport.models import Flight
from airport.tests.validation.test_flight_validators import (
    BaseFlightScheduleTestCase,
)
from airport.utils.validators import (
    validate_ticket_flight,
    validate_ticket_rows_and_seats_in_row,
    validate_tickets_flights,
)


class TicketSeatValidationTests(BaseFlightScheduleTestCase):
    ROW_ERROR_MSG = {
        "row": [
            "Row must be between 1 and 20.",
        ],
    }

    SEAT_ERROR_MSG = {
        "seat": [
            "Seat must be between 1 and 6.",
        ],
    }

    def test_validate_ticket_seat_allows_valid_row_and_seat(
        self,
    ) -> None:
        validate_ticket_rows_and_seats_in_row(
            flight=self.existing_flight,
            row=10,
            seat=3,
            error_to_raise=ValidationError,
        )

    def test_validate_ticket_seat_allows_first_row_and_first_seat(
        self,
    ) -> None:
        validate_ticket_rows_and_seats_in_row(
            flight=self.existing_flight,
            row=1,
            seat=1,
            error_to_raise=ValidationError,
        )

    def test_validate_ticket_seat_allows_last_row_and_last_seat(
        self,
    ) -> None:
        validate_ticket_rows_and_seats_in_row(
            flight=self.existing_flight,
            row=20,
            seat=6,
            error_to_raise=ValidationError,
        )

    def test_validate_ticket_seat_rejects_row_zero(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_ticket_rows_and_seats_in_row(
                flight=self.existing_flight,
                row=0,
                seat=1,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ROW_ERROR_MSG,
        )

    def test_validate_ticket_seat_rejects_row_above_airplane_rows(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_ticket_rows_and_seats_in_row(
                flight=self.existing_flight,
                row=21,
                seat=1,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ROW_ERROR_MSG,
        )

    def test_validate_ticket_seat_rejects_seat_zero(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_ticket_rows_and_seats_in_row(
                flight=self.existing_flight,
                row=1,
                seat=0,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.SEAT_ERROR_MSG,
        )

    def test_validate_ticket_seat_rejects_seat_above_seats_in_row(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_ticket_rows_and_seats_in_row(
                flight=self.existing_flight,
                row=1,
                seat=7,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.SEAT_ERROR_MSG,
        )

    def test_validate_ticket_seat_ignores_missing_flight(
        self,
    ) -> None:
        validate_ticket_rows_and_seats_in_row(
            flight=None,
            row=1,
            seat=1,
            error_to_raise=ValidationError,
        )

    def test_validate_ticket_seat_ignores_missing_row(
        self,
    ) -> None:
        validate_ticket_rows_and_seats_in_row(
            flight=self.existing_flight,
            row=None,
            seat=1,
            error_to_raise=ValidationError,
        )

    def test_validate_ticket_seat_ignores_missing_seat(
        self,
    ) -> None:
        validate_ticket_rows_and_seats_in_row(
            flight=self.existing_flight,
            row=1,
            seat=None,
            error_to_raise=ValidationError,
        )


class TicketFlightValidationTests(BaseFlightScheduleTestCase):
    NOW = datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ERROR_CANCELLED_MSG = {
        "flight": [
            "Tickets cannot be purchased for a cancelled flight.",
        ],
    }

    ERROR_DEPARTED_MSG = {
        "flight": [
            "Tickets cannot be purchased after departure.",
        ],
    }

    def make_flight(
        self,
        *,
        departure_time: datetime,
        status: str = Flight.Status.SCHEDULED,
    ) -> Flight:
        return Flight(
            airplane=self.airplane_1,
            route=self.route,
            departure_time=departure_time,
            arrival_time=departure_time + timedelta(hours=2),
            status=status,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_ticket_flight_allows_future_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW + timedelta(hours=1),
        )

        validate_ticket_flight(
            flight=flight,
            error_to_raise=ValidationError,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_ticket_flight_allows_future_delayed_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW + timedelta(hours=1),
            status=Flight.Status.DELAYED,
        )

        validate_ticket_flight(
            flight=flight,
            error_to_raise=ValidationError,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_ticket_flight_rejects_cancelled_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW + timedelta(hours=1),
            status=Flight.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError) as context:
            validate_ticket_flight(
                flight=flight,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_CANCELLED_MSG,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_ticket_flight_rejects_departed_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW - timedelta(hours=1),
        )

        with self.assertRaises(ValidationError) as context:
            validate_ticket_flight(
                flight=flight,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_DEPARTED_MSG,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_ticket_flight_rejects_flight_departing_now(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW,
        )

        with self.assertRaises(ValidationError) as context:
            validate_ticket_flight(
                flight=flight,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_DEPARTED_MSG,
        )

    def test_validate_ticket_flight_ignores_none(
        self,
    ) -> None:
        validate_ticket_flight(
            flight=None,
            error_to_raise=ValidationError,
        )


class TicketsFlightsValidationTests(
    BaseFlightScheduleTestCase,
):
    ERROR_MSG = [
        "All tickets in an order must belong to the same flight.",
    ]

    def test_validate_tickets_flights_allows_single_ticket(
        self,
    ) -> None:
        tickets = [
            {
                "flight": self.existing_flight,
            },
        ]

        validate_tickets_flights(
            tickets=tickets,
            error_to_raise=ValidationError,
        )

    def test_validate_tickets_flights_allows_multiple_tickets_for_same_flight(
        self,
    ) -> None:
        tickets = [
            {
                "flight": self.existing_flight,
            },
            {
                "flight": self.existing_flight,
            },
        ]

        validate_tickets_flights(
            tickets=tickets,
            error_to_raise=ValidationError,
        )

    def test_validate_tickets_flights_rejects_tickets_for_different_flights(
        self,
    ) -> None:
        tickets = [
            {
                "flight": self.existing_flight,
            },
            {
                "flight": self.cancelled_flight,
            },
        ]

        with self.assertRaises(ValidationError) as context:
            validate_tickets_flights(
                tickets=tickets,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )
