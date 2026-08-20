from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

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


class TicketModelTests(TestCase):
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
            rows=20,
            seats_in_row=6,
            airplane_type=cls.airplane_type,
        )

        cls.flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane,
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
        )

        cls.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="password123",
        )

        cls.order = Order.objects.create(
            user=cls.user,
        )

    def make_ticket(
        self,
        *,
        row: int = 1,
        seat: int = 1,
        status: str = Ticket.Status.ACTIVE,
    ) -> Ticket:
        return Ticket(
            order=self.order,
            flight=self.flight,
            row=row,
            seat=seat,
            status=status,
        )

    def test_default_status_is_active(self) -> None:
        ticket = Ticket(
            order=self.order,
            flight=self.flight,
            row=1,
            seat=1,
        )

        self.assertEqual(
            ticket.status,
            Ticket.Status.ACTIVE,
        )

    def test_save_valid_ticket(self) -> None:
        ticket = self.make_ticket()

        ticket.save()

        self.assertTrue(
            Ticket.objects.filter(
                pk=ticket.pk,
            ).exists(),
        )

    def test_save_rejects_row_zero(self) -> None:
        ticket = self.make_ticket(
            row=0,
        )

        with self.assertRaises(ValidationError) as context:
            ticket.save()

        self.assertEqual(
            context.exception.message_dict,
            {
                "row": [
                    "Row must be between 1 and 20.",
                ],
            },
        )

    def test_save_rejects_row_above_airplane_rows(
        self,
    ) -> None:
        ticket = self.make_ticket(
            row=21,
        )

        with self.assertRaises(ValidationError) as context:
            ticket.save()

        self.assertEqual(
            context.exception.message_dict,
            {
                "row": [
                    "Row must be between 1 and 20.",
                ],
            },
        )

    def test_save_rejects_seat_zero(self) -> None:
        ticket = self.make_ticket(
            seat=0,
        )

        with self.assertRaises(ValidationError) as context:
            ticket.save()

        self.assertEqual(
            context.exception.message_dict,
            {
                "seat": [
                    "Seat must be between 1 and 6.",
                ],
            },
        )

    def test_save_rejects_seat_above_seats_in_row(
        self,
    ) -> None:
        ticket = self.make_ticket(
            seat=7,
        )

        with self.assertRaises(ValidationError) as context:
            ticket.save()

        self.assertEqual(
            context.exception.message_dict,
            {
                "seat": [
                    "Seat must be between 1 and 6.",
                ],
            },
        )

    def test_save_allows_first_row_and_first_seat(
        self,
    ) -> None:
        ticket = self.make_ticket(
            row=1,
            seat=1,
        )

        ticket.save()

        self.assertEqual(
            ticket.row,
            1,
        )
        self.assertEqual(
            ticket.seat,
            1,
        )

    def test_save_allows_last_row_and_last_seat(
        self,
    ) -> None:
        ticket = self.make_ticket(
            row=self.airplane.rows,
            seat=self.airplane.seats_in_row,
        )

        ticket.save()

        self.assertEqual(
            ticket.row,
            20,
        )
        self.assertEqual(
            ticket.seat,
            6,
        )

    def test_duplicate_active_seat_is_rejected(
        self,
    ) -> None:
        first_ticket = self.make_ticket(
            row=1,
            seat=1,
        )
        first_ticket.save()

        duplicate_ticket = self.make_ticket(
            row=1,
            seat=1,
        )

        with self.assertRaises(ValidationError):
            duplicate_ticket.save()

    def test_cancelled_ticket_does_not_block_active_seat(
        self,
    ) -> None:
        cancelled_ticket = self.make_ticket(
            row=1,
            seat=1,
            status=Ticket.Status.CANCELLED,
        )
        cancelled_ticket.save()

        active_ticket = self.make_ticket(
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )
        active_ticket.save()

        self.assertEqual(
            Ticket.objects.filter(
                flight=self.flight,
                row=1,
                seat=1,
            ).count(),
            2,
        )

    def test_active_ticket_does_not_block_cancelled_ticket(
        self,
    ) -> None:
        active_ticket = self.make_ticket(
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )
        active_ticket.save()

        cancelled_ticket = self.make_ticket(
            row=1,
            seat=1,
            status=Ticket.Status.CANCELLED,
        )
        cancelled_ticket.save()

        self.assertEqual(
            Ticket.objects.filter(
                flight=self.flight,
                row=1,
                seat=1,
            ).count(),
            2,
        )

    def test_multiple_cancelled_tickets_can_use_same_seat(
        self,
    ) -> None:
        first_ticket = self.make_ticket(
            row=1,
            seat=1,
            status=Ticket.Status.CANCELLED,
        )
        first_ticket.save()

        second_ticket = self.make_ticket(
            row=1,
            seat=1,
            status=Ticket.Status.CANCELLED,
        )
        second_ticket.save()

        self.assertEqual(
            Ticket.objects.filter(
                flight=self.flight,
                row=1,
                seat=1,
                status=Ticket.Status.CANCELLED,
            ).count(),
            2,
        )

    def test_str(self) -> None:
        ticket = self.make_ticket(
            row=3,
            seat=4,
        )

        self.assertEqual(
            str(ticket),
            (
                f"Ticket for flight: |{self.flight}| "
                "(row: 3, seat: 4)"
            ),
        )
