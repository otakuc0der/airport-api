from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.exceptions import ValidationError

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
from airport.utils.validators import (
    get_conflicting_flights,
    validate_flight_airplane_change,
    validate_flight_airplane_schedule,
    validate_flight_cancellation,
    validate_flight_crew_presence,
    validate_flight_crew_schedule,
    validate_flight_departure_and_arrival_time,
    validate_flight_modification,
    validate_flight_status_change,
)


class FlightTimeValidationTests(SimpleTestCase):
    DEPARTURE_TIME = datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ERROR_MSG = {
        "arrival_time": [
            "Arrival time must be later than departure time.",
        ],
    }

    def test_validate_flight_times_allows_arrival_after_departure(
        self,
    ) -> None:
        validate_flight_departure_and_arrival_time(
            departure_time=self.DEPARTURE_TIME,
            arrival_time=self.DEPARTURE_TIME + timedelta(hours=2),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_times_rejects_arrival_before_departure(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_departure_and_arrival_time(
                departure_time=self.DEPARTURE_TIME,
                arrival_time=self.DEPARTURE_TIME - timedelta(hours=1),
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )

    def test_validate_flight_times_rejects_arrival_equal_to_departure(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_departure_and_arrival_time(
                departure_time=self.DEPARTURE_TIME,
                arrival_time=self.DEPARTURE_TIME,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )

    def test_validate_flight_times_ignores_missing_departure(
        self,
    ) -> None:
        validate_flight_departure_and_arrival_time(
            departure_time=None,
            arrival_time=self.DEPARTURE_TIME,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_times_ignores_missing_arrival(
        self,
    ) -> None:
        validate_flight_departure_and_arrival_time(
            departure_time=self.DEPARTURE_TIME,
            arrival_time=None,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_times_ignores_missing_both(
        self,
    ) -> None:
        validate_flight_departure_and_arrival_time(
            departure_time=None,
            arrival_time=None,
            error_to_raise=ValidationError,
        )


class FlightCrewPresenceValidationTests(SimpleTestCase):
    ERROR_MSG = {
        "crew": [
            "A flight must have at least one crew member.",
        ],
    }

    def test_validate_flight_crew_presence_allows_non_empty_crew(
        self,
    ) -> None:
        validate_flight_crew_presence(
            crew=[Crew()],
            error_to_raise=ValidationError,
        )

    def test_validate_flight_crew_presence_rejects_empty_crew(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_crew_presence(
                crew=[],
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )

    def test_validate_flight_crew_presence_rejects_none(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_crew_presence(
                crew=None,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )


class BaseFlightScheduleTestCase(TestCase):
    EXISTING_DEPARTURE_TIME = datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )
    EXISTING_ARRIVAL_TIME = datetime(
        2026,
        9,
        10,
        12,
        0,
        tzinfo=timezone.utc,
    )

    CANCELLED_DEPARTURE_TIME = datetime(
        2026,
        9,
        10,
        14,
        0,
        tzinfo=timezone.utc,
    )
    CANCELLED_ARRIVAL_TIME = datetime(
        2026,
        9,
        10,
        15,
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
            name="Boryspil",
            closest_big_city=cls.kyiv,
        )
        cls.destination_airport = Airport.objects.create(
            name="Lviv Airport",
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

        cls.crew_1 = Crew.objects.create(
            first_name="John",
            last_name="Smith",
        )
        cls.crew_2 = Crew.objects.create(
            first_name="Anna",
            last_name="Brown",
        )

        cls.existing_flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane_1,
            departure_time=cls.EXISTING_DEPARTURE_TIME,
            arrival_time=cls.EXISTING_ARRIVAL_TIME,
        )
        cls.existing_flight.crew.add(cls.crew_1)

        cls.cancelled_flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane_1,
            departure_time=cls.CANCELLED_DEPARTURE_TIME,
            arrival_time=cls.CANCELLED_ARRIVAL_TIME,
            status=Flight.Status.CANCELLED,
        )
        cls.cancelled_flight.crew.add(cls.crew_2)


class FlightScheduleValidationTests(BaseFlightScheduleTestCase):
    def test_get_conflicting_flights_finds_overlapping_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=datetime(
                2026,
                9,
                10,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                13,
                0,
                tzinfo=timezone.utc,
            ),
            airplane=self.airplane_1,
        )

        self.assertIn(
            self.existing_flight,
            result,
        )

    def test_get_conflicting_flights_finds_flight_inside_existing_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=datetime(
                2026,
                9,
                10,
                10,
                30,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            airplane=self.airplane_1,
        )

        self.assertIn(
            self.existing_flight,
            result,
        )

    def test_get_conflicting_flights_finds_flight_covering_existing_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=datetime(
                2026,
                9,
                10,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                13,
                0,
                tzinfo=timezone.utc,
            ),
            airplane=self.airplane_1,
        )

        self.assertIn(
            self.existing_flight,
            result,
        )

    def test_get_conflicting_flights_finds_conflict_inside_buffer_before_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=datetime(
                2026,
                9,
                10,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                9,
                45,
                tzinfo=timezone.utc,
            ),
            airplane=self.airplane_1,
        )

        self.assertIn(
            self.existing_flight,
            result,
        )

    def test_get_conflicting_flights_finds_conflict_inside_buffer_after_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=datetime(
                2026,
                9,
                10,
                12,
                15,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                13,
                0,
                tzinfo=timezone.utc,
            ),
            airplane=self.airplane_1,
        )

        self.assertIn(
            self.existing_flight,
            result,
        )

    def test_get_conflicting_flights_allows_exactly_30_minutes_before_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=datetime(
                2026,
                9,
                10,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                9,
                30,
                tzinfo=timezone.utc,
            ),
            airplane=self.airplane_1,
        )

        self.assertNotIn(
            self.existing_flight,
            result,
        )

    def test_get_conflicting_flights_allows_exactly_30_minutes_after_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=datetime(
                2026,
                9,
                10,
                12,
                30,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                13,
                30,
                tzinfo=timezone.utc,
            ),
            airplane=self.airplane_1,
        )

        self.assertNotIn(
            self.existing_flight,
            result,
        )

    def test_get_conflicting_flights_excludes_current_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=self.EXISTING_DEPARTURE_TIME,
            arrival_time=self.EXISTING_ARRIVAL_TIME,
            current_flight=self.existing_flight,
            airplane=self.airplane_1,
        )

        self.assertNotIn(
            self.existing_flight,
            result,
        )

    def test_get_conflicting_flights_ignores_cancelled_flight(
        self,
    ) -> None:
        result = get_conflicting_flights(
            departure_time=datetime(
                2026,
                9,
                10,
                14,
                15,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                14,
                45,
                tzinfo=timezone.utc,
            ),
            airplane=self.airplane_1,
        )

        self.assertNotIn(
            self.cancelled_flight,
            result,
        )


class FlightCrewScheduleValidationTests(
    BaseFlightScheduleTestCase,
):
    ERROR_MSG_TEMPLATE = (
        "The following crew members are unavailable for this flight "
        "and its required 30-minute buffer: {}."
    )

    def test_validate_flight_crew_schedule_allows_available_crew(
        self,
    ) -> None:
        validate_flight_crew_schedule(
            crew=[self.crew_2],
            current_flight=None,
            departure_time=datetime(
                2026,
                9,
                10,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                13,
                0,
                tzinfo=timezone.utc,
            ),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_crew_schedule_rejects_busy_crew(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_crew_schedule(
                crew=[self.crew_1],
                current_flight=None,
                departure_time=datetime(
                    2026,
                    9,
                    10,
                    11,
                    0,
                    tzinfo=timezone.utc,
                ),
                arrival_time=datetime(
                    2026,
                    9,
                    10,
                    13,
                    0,
                    tzinfo=timezone.utc,
                ),
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            {
                "crew": [
                    self.ERROR_MSG_TEMPLATE.format(
                        self.crew_1.full_name,
                    ),
                ],
            },
        )

    def test_validate_flight_crew_schedule_rejects_crew_inside_buffer_before_flight(
        self,
    ) -> None:
        with self.assertRaises(ValidationError):
            validate_flight_crew_schedule(
                crew=[self.crew_1],
                current_flight=None,
                departure_time=datetime(
                    2026,
                    9,
                    10,
                    8,
                    0,
                    tzinfo=timezone.utc,
                ),
                arrival_time=datetime(
                    2026,
                    9,
                    10,
                    9,
                    45,
                    tzinfo=timezone.utc,
                ),
                error_to_raise=ValidationError,
            )

    def test_validate_flight_crew_schedule_rejects_crew_inside_buffer_after_flight(
        self,
    ) -> None:
        with self.assertRaises(ValidationError):
            validate_flight_crew_schedule(
                crew=[self.crew_1],
                current_flight=None,
                departure_time=datetime(
                    2026,
                    9,
                    10,
                    12,
                    15,
                    tzinfo=timezone.utc,
                ),
                arrival_time=datetime(
                    2026,
                    9,
                    10,
                    13,
                    0,
                    tzinfo=timezone.utc,
                ),
                error_to_raise=ValidationError,
            )

    def test_validate_flight_crew_schedule_allows_crew_after_full_buffer(
        self,
    ) -> None:
        validate_flight_crew_schedule(
            crew=[self.crew_1],
            current_flight=None,
            departure_time=datetime(
                2026,
                9,
                10,
                12,
                30,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                13,
                30,
                tzinfo=timezone.utc,
            ),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_crew_schedule_excludes_current_flight_on_update(
        self,
    ) -> None:
        validate_flight_crew_schedule(
            crew=[self.crew_1],
            current_flight=self.existing_flight,
            departure_time=self.EXISTING_DEPARTURE_TIME,
            arrival_time=self.EXISTING_ARRIVAL_TIME,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_crew_schedule_ignores_cancelled_flights(
        self,
    ) -> None:
        validate_flight_crew_schedule(
            crew=[self.crew_2],
            current_flight=None,
            departure_time=datetime(
                2026,
                9,
                10,
                14,
                15,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                14,
                45,
                tzinfo=timezone.utc,
            ),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_crew_schedule_reports_only_conflicting_crew_members(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_crew_schedule(
                crew=[
                    self.crew_1,
                    self.crew_2,
                ],
                current_flight=None,
                departure_time=datetime(
                    2026,
                    9,
                    10,
                    10,
                    30,
                    tzinfo=timezone.utc,
                ),
                arrival_time=datetime(
                    2026,
                    9,
                    10,
                    11,
                    0,
                    tzinfo=timezone.utc,
                ),
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            {
                "crew": [
                    self.ERROR_MSG_TEMPLATE.format(
                        self.crew_1.full_name,
                    ),
                ],
            },
        )

    def test_validate_flight_crew_schedule_ignores_missing_crew(
        self,
    ) -> None:
        validate_flight_crew_schedule(
            crew=None,
            current_flight=None,
            departure_time=self.EXISTING_DEPARTURE_TIME,
            arrival_time=self.EXISTING_ARRIVAL_TIME,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_crew_schedule_ignores_missing_departure(
        self,
    ) -> None:
        validate_flight_crew_schedule(
            crew=[self.crew_1],
            current_flight=None,
            departure_time=None,
            arrival_time=self.EXISTING_ARRIVAL_TIME,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_crew_schedule_ignores_missing_arrival(
        self,
    ) -> None:
        validate_flight_crew_schedule(
            crew=[self.crew_1],
            current_flight=None,
            departure_time=self.EXISTING_DEPARTURE_TIME,
            arrival_time=None,
            error_to_raise=ValidationError,
        )


class FlightAirplaneScheduleValidationTests(
    BaseFlightScheduleTestCase,
):
    ERROR_MSG = {
        "airplane": [
            (
                "This airplane is unavailable during the selected "
                "time or the required 30-minute interval "
                "between flights."
            ),
        ],
    }

    def test_validate_flight_airplane_schedule_allows_available_airplane(
        self,
    ) -> None:
        validate_flight_airplane_schedule(
            airplane=self.airplane_2,
            current_flight=None,
            departure_time=self.EXISTING_DEPARTURE_TIME,
            arrival_time=self.EXISTING_ARRIVAL_TIME,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_schedule_rejects_busy_airplane(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_airplane_schedule(
                airplane=self.airplane_1,
                current_flight=None,
                departure_time=datetime(
                    2026,
                    9,
                    10,
                    11,
                    0,
                    tzinfo=timezone.utc,
                ),
                arrival_time=datetime(
                    2026,
                    9,
                    10,
                    13,
                    0,
                    tzinfo=timezone.utc,
                ),
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )

    def test_validate_flight_airplane_schedule_rejects_airplane_inside_buffer_before_flight(
        self,
    ) -> None:
        with self.assertRaises(ValidationError):
            validate_flight_airplane_schedule(
                airplane=self.airplane_1,
                current_flight=None,
                departure_time=datetime(
                    2026,
                    9,
                    10,
                    8,
                    0,
                    tzinfo=timezone.utc,
                ),
                arrival_time=datetime(
                    2026,
                    9,
                    10,
                    9,
                    45,
                    tzinfo=timezone.utc,
                ),
                error_to_raise=ValidationError,
            )

    def test_validate_flight_airplane_schedule_rejects_airplane_inside_buffer_after_flight(
        self,
    ) -> None:
        with self.assertRaises(ValidationError):
            validate_flight_airplane_schedule(
                airplane=self.airplane_1,
                current_flight=None,
                departure_time=datetime(
                    2026,
                    9,
                    10,
                    12,
                    15,
                    tzinfo=timezone.utc,
                ),
                arrival_time=datetime(
                    2026,
                    9,
                    10,
                    13,
                    0,
                    tzinfo=timezone.utc,
                ),
                error_to_raise=ValidationError,
            )

    def test_validate_flight_airplane_schedule_allows_airplane_after_full_buffer(
        self,
    ) -> None:
        validate_flight_airplane_schedule(
            airplane=self.airplane_1,
            current_flight=None,
            departure_time=datetime(
                2026,
                9,
                10,
                12,
                30,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                13,
                30,
                tzinfo=timezone.utc,
            ),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_schedule_excludes_current_flight_on_update(
        self,
    ) -> None:
        validate_flight_airplane_schedule(
            airplane=self.airplane_1,
            current_flight=self.existing_flight,
            departure_time=self.EXISTING_DEPARTURE_TIME,
            arrival_time=self.EXISTING_ARRIVAL_TIME,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_schedule_ignores_cancelled_flights(
        self,
    ) -> None:
        validate_flight_airplane_schedule(
            airplane=self.airplane_1,
            current_flight=None,
            departure_time=datetime(
                2026,
                9,
                10,
                14,
                15,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                14,
                45,
                tzinfo=timezone.utc,
            ),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_schedule_ignores_missing_airplane(
        self,
    ) -> None:
        validate_flight_airplane_schedule(
            airplane=None,
            current_flight=None,
            departure_time=self.EXISTING_DEPARTURE_TIME,
            arrival_time=self.EXISTING_ARRIVAL_TIME,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_schedule_ignores_missing_departure(
        self,
    ) -> None:
        validate_flight_airplane_schedule(
            airplane=self.airplane_1,
            current_flight=None,
            departure_time=None,
            arrival_time=self.EXISTING_ARRIVAL_TIME,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_schedule_ignores_missing_arrival(
        self,
    ) -> None:
        validate_flight_airplane_schedule(
            airplane=self.airplane_1,
            current_flight=None,
            departure_time=self.EXISTING_DEPARTURE_TIME,
            arrival_time=None,
            error_to_raise=ValidationError,
        )


class FlightStateValidationTests(BaseFlightScheduleTestCase):
    NOW = datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    MODIFICATION_ERROR_MSG = {
        "status": [
            "A cancelled flight cannot be modified.",
        ],
    }

    ALREADY_CANCELLED_ERROR_MSG = {
        "status": [
            "Flight is already cancelled.",
        ],
    }

    DEPARTED_ERROR_MSG = {
        "status": [
            "A flight cannot be cancelled after departure.",
        ],
    }

    def make_flight(
        self,
        *,
        departure_time: datetime,
        status: str = Flight.Status.SCHEDULED,
    ) -> Flight:
        return Flight(
            route=self.route,
            airplane=self.airplane_1,
            departure_time=departure_time,
            arrival_time=departure_time + timedelta(hours=2),
            status=status,
        )

    def test_validate_flight_modification_allows_scheduled_flight(
        self,
    ) -> None:
        validate_flight_modification(
            flight=self.make_flight(
                departure_time=self.NOW + timedelta(hours=1),
            ),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_modification_allows_delayed_flight(
        self,
    ) -> None:
        validate_flight_modification(
            flight=self.make_flight(
                departure_time=self.NOW + timedelta(hours=1),
                status=Flight.Status.DELAYED,
            ),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_modification_rejects_cancelled_flight(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_modification(
                flight=self.make_flight(
                    departure_time=self.NOW + timedelta(hours=1),
                    status=Flight.Status.CANCELLED,
                ),
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.MODIFICATION_ERROR_MSG,
        )

    def test_validate_flight_modification_ignores_none(
        self,
    ) -> None:
        validate_flight_modification(
            flight=None,
            error_to_raise=ValidationError,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_flight_cancellation_allows_future_scheduled_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        validate_flight_cancellation(
            flight=self.make_flight(
                departure_time=self.NOW + timedelta(hours=1),
            ),
            error_to_raise=ValidationError,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_flight_cancellation_allows_future_delayed_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        validate_flight_cancellation(
            flight=self.make_flight(
                departure_time=self.NOW + timedelta(hours=1),
                status=Flight.Status.DELAYED,
            ),
            error_to_raise=ValidationError,
        )

    def test_validate_flight_cancellation_rejects_already_cancelled_flight(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_cancellation(
                flight=self.make_flight(
                    departure_time=self.NOW + timedelta(hours=1),
                    status=Flight.Status.CANCELLED,
                ),
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ALREADY_CANCELLED_ERROR_MSG,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_flight_cancellation_rejects_departed_flight(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        with self.assertRaises(ValidationError) as context:
            validate_flight_cancellation(
                flight=self.make_flight(
                    departure_time=self.NOW - timedelta(hours=1),
                ),
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.DEPARTED_ERROR_MSG,
        )

    @patch("airport.utils.validators.timezone.now")
    def test_validate_flight_cancellation_rejects_flight_departing_now(
        self,
        mock_now: MagicMock,
    ) -> None:
        mock_now.return_value = self.NOW

        with self.assertRaises(ValidationError) as context:
            validate_flight_cancellation(
                flight=self.make_flight(
                    departure_time=self.NOW,
                ),
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.DEPARTED_ERROR_MSG,
        )


class FlightStatusChangeValidationTests(SimpleTestCase):
    ERROR_MSG = {
        "status": [
            "Use the flight cancel endpoint to cancel a flight.",
        ],
    }

    def test_validate_flight_status_change_allows_scheduled_status(
        self,
    ) -> None:
        validate_flight_status_change(
            status=Flight.Status.SCHEDULED,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_status_change_allows_delayed_status(
        self,
    ) -> None:
        validate_flight_status_change(
            status=Flight.Status.DELAYED,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_status_change_rejects_cancelled_status(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_flight_status_change(
                status=Flight.Status.CANCELLED,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )

    def test_validate_flight_status_change_ignores_none(
        self,
    ) -> None:
        validate_flight_status_change(
            status=None,
            error_to_raise=ValidationError,
        )


class FlightAirplaneChangeValidationTests(
    BaseFlightScheduleTestCase,
):
    ERROR_MSG = {
        "airplane": [
            (
                "The airplane cannot be changed because "
                "active tickets already exist for this flight."
            ),
        ],
    }

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(
            email="airplane-change@example.com",
            password="testpass123",
        )

    def make_ticket(
        self,
        *,
        status: str = Ticket.Status.ACTIVE,
    ) -> Ticket:
        order = Order.objects.create(
            user=self.user,
        )

        return Ticket.objects.create(
            order=order,
            flight=self.existing_flight,
            row=1,
            seat=1,
            status=status,
        )

    def test_validate_flight_airplane_change_allows_change_without_tickets(
        self,
    ) -> None:
        validate_flight_airplane_change(
            flight=self.existing_flight,
            new_airplane=self.airplane_2,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_change_allows_same_airplane(
        self,
    ) -> None:
        self.make_ticket()

        validate_flight_airplane_change(
            flight=self.existing_flight,
            new_airplane=self.airplane_1,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_change_rejects_change_with_active_ticket(
        self,
    ) -> None:
        self.make_ticket(
            status=Ticket.Status.ACTIVE,
        )

        with self.assertRaises(ValidationError) as context:
            validate_flight_airplane_change(
                flight=self.existing_flight,
                new_airplane=self.airplane_2,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )

    def test_validate_flight_airplane_change_allows_change_with_cancelled_ticket(
        self,
    ) -> None:
        self.make_ticket(
            status=Ticket.Status.CANCELLED,
        )

        validate_flight_airplane_change(
            flight=self.existing_flight,
            new_airplane=self.airplane_2,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_change_ignores_missing_flight(
        self,
    ) -> None:
        validate_flight_airplane_change(
            flight=None,
            new_airplane=self.airplane_2,
            error_to_raise=ValidationError,
        )

    def test_validate_flight_airplane_change_ignores_missing_new_airplane(
        self,
    ) -> None:
        validate_flight_airplane_change(
            flight=self.existing_flight,
            new_airplane=None,
            error_to_raise=ValidationError,
        )
