from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone as django_timezone

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Flight,
    Route,
)


class FlightModelTests(TestCase):
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

    def make_flight(
        self,
        *,
        departure_time: datetime | None = None,
        arrival_time: datetime | None = None,
        status: str = Flight.Status.SCHEDULED,
    ) -> Flight:
        if departure_time is None:
            departure_time = self.NOW + timedelta(hours=2)

        if arrival_time is None:
            arrival_time = departure_time + timedelta(hours=2)

        return Flight(
            route=self.route,
            airplane=self.airplane,
            departure_time=departure_time,
            arrival_time=arrival_time,
            status=status,
        )

    def test_default_status_is_scheduled(self) -> None:
        flight = self.make_flight()

        self.assertEqual(
            flight.status,
            Flight.Status.SCHEDULED,
        )

    def test_flight_duration(self) -> None:
        departure = self.NOW
        arrival = self.NOW + timedelta(
            hours=3,
            minutes=30,
        )

        flight = self.make_flight(
            departure_time=departure,
            arrival_time=arrival,
        )

        self.assertEqual(
            flight.flight_duration,
            timedelta(
                hours=3,
                minutes=30,
            ),
        )

    def test_save_valid_flight(self) -> None:
        flight = self.make_flight()

        flight.save()

        self.assertTrue(
            Flight.objects.filter(
                pk=flight.pk,
            ).exists(),
        )

    def test_save_rejects_arrival_before_departure(
        self,
    ) -> None:
        flight = self.make_flight(
            departure_time=self.NOW,
            arrival_time=self.NOW - timedelta(hours=1),
        )

        with self.assertRaises(ValidationError) as context:
            flight.save()

        self.assertEqual(
            context.exception.message_dict,
            {
                "arrival_time": [
                    (
                        "Arrival time must be later "
                        "than departure time."
                    ),
                ],
            },
        )

    def test_save_rejects_arrival_equal_to_departure(
        self,
    ) -> None:
        flight = self.make_flight(
            departure_time=self.NOW,
            arrival_time=self.NOW,
        )

        with self.assertRaises(ValidationError):
            flight.save()

    @patch("airport.models.timezone.now")
    def test_flight_state_returns_cancelled(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            status=Flight.Status.CANCELLED,
        )

        self.assertEqual(
            flight.flight_state,
            "cancelled",
        )

    @patch("airport.models.timezone.now")
    def test_flight_state_returns_scheduled_before_departure(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW + timedelta(hours=1),
            status=Flight.Status.SCHEDULED,
        )

        self.assertEqual(
            flight.flight_state,
            Flight.Status.SCHEDULED,
        )

    @patch("airport.models.timezone.now")
    def test_flight_state_returns_delayed_before_departure(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW + timedelta(hours=1),
            status=Flight.Status.DELAYED,
        )

        self.assertEqual(
            flight.flight_state,
            Flight.Status.DELAYED,
        )

    @patch("airport.models.timezone.now")
    def test_flight_state_returns_departed_during_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW - timedelta(hours=1),
            arrival_time=self.NOW + timedelta(hours=1),
        )

        self.assertEqual(
            flight.flight_state,
            "departed",
        )

    @patch("airport.models.timezone.now")
    def test_flight_state_returns_departed_exactly_at_departure(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW,
            arrival_time=self.NOW + timedelta(hours=2),
        )

        self.assertEqual(
            flight.flight_state,
            "departed",
        )

    @patch("airport.models.timezone.now")
    def test_flight_state_returns_arrived_after_arrival(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW - timedelta(hours=3),
            arrival_time=self.NOW - timedelta(hours=1),
        )

        self.assertEqual(
            flight.flight_state,
            "arrived",
        )

    @patch("airport.models.timezone.now")
    def test_flight_state_returns_arrived_exactly_at_arrival(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        flight = self.make_flight(
            departure_time=self.NOW - timedelta(hours=2),
            arrival_time=self.NOW,
        )

        self.assertEqual(
            flight.flight_state,
            "arrived",
        )

    def test_str(self) -> None:
        flight = self.make_flight(
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

        departure_time = django_timezone.localtime(
            flight.departure_time,
        ).strftime("%Y-%m-%d %H:%M")

        arrival_time = django_timezone.localtime(
            flight.arrival_time,
        ).strftime("%Y-%m-%d %H:%M")

        self.assertEqual(
            str(flight),
            (
                "Flight 'Kyiv (Ukraine) - Lviv (Ukraine)' "
                f"(departure time: {departure_time}; "
                f"arrival time: {arrival_time})"
            ),
        )
