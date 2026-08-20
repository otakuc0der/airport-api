import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from django.contrib.auth import get_user_model

from airport.models import (
    Crew,
    Flight,
    Order,
    Ticket,
)
from airport.serializers import (
    FlightCancelSerializer,
    FlightDetailSerializer,
    FlightListSerializer,
    FlightSerializer,
)
from airport.tests.validation.test_flight_validators import (
    BaseFlightScheduleTestCase,
)


class FlightSerializerTests(BaseFlightScheduleTestCase):
    NEW_DEPARTURE_TIME = datetime(
        2026,
        9,
        11,
        10,
        0,
        tzinfo=timezone.utc,
    )
    NEW_ARRIVAL_TIME = datetime(
        2026,
        9,
        11,
        12,
        0,
        tzinfo=timezone.utc,
    )

    ARRIVAL_TIME_ERROR_MSG = {
        "arrival_time": [
            "Arrival time must be later than departure time.",
        ],
    }

    EMPTY_CREW_ERROR_MSG = {
        "crew": [
            "A flight must have at least one crew member.",
        ],
    }

    AIRPLANE_SCHEDULE_ERROR_MSG = {
        "airplane": [
            (
                "This airplane is unavailable during the selected "
                "time or the required 30-minute interval "
                "between flights."
            ),
        ],
    }

    AIRPLANE_CHANGE_ERROR_MSG = {
        "airplane": [
            (
                "The airplane cannot be changed because "
                "active tickets already exist for this flight."
            ),
        ],
    }

    CANCELLED_STATUS_ERROR_MSG = {
        "status": [
            "Use the flight cancel endpoint to cancel a flight.",
        ],
    }

    CANCELLED_FLIGHT_MODIFICATION_ERROR_MSG = {
        "status": [
            "A cancelled flight cannot be modified.",
        ],
    }

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.crew_3 = Crew.objects.create(
            first_name="Michael",
            last_name="White",
        )

        cls.user = get_user_model().objects.create_user(
            email="someone@example.com",
            password="testpass123",
        )

    def make_valid_data(self) -> dict[str, Any]:
        return {
            "route": self.route.pk,
            "airplane": self.airplane_2.pk,
            "departure_time": self.NEW_DEPARTURE_TIME,
            "arrival_time": self.NEW_ARRIVAL_TIME,
            "status": Flight.Status.SCHEDULED,
            "crew": [
                self.crew_3.pk,
            ],
        }

    def make_ticket(
        self,
        *,
        flight: Flight,
        status: str = Ticket.Status.ACTIVE,
        row: int = 1,
        seat: int = 1,
    ) -> Ticket:
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

    def test_flight_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = FlightSerializer(
            data=self.make_valid_data(),
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["route"],
            self.route,
        )
        self.assertEqual(
            serializer.validated_data["airplane"],
            self.airplane_2,
        )
        self.assertEqual(
            serializer.validated_data["departure_time"],
            self.NEW_DEPARTURE_TIME,
        )
        self.assertEqual(
            serializer.validated_data["arrival_time"],
            self.NEW_ARRIVAL_TIME,
        )
        self.assertEqual(
            serializer.validated_data["status"],
            Flight.Status.SCHEDULED,
        )
        self.assertEqual(
            serializer.validated_data["crew"],
            [self.crew_3],
        )

    def test_flight_serializer_creates_flight(
        self,
    ) -> None:
        serializer = FlightSerializer(
            data=self.make_valid_data(),
        )

        serializer.is_valid(
            raise_exception=True,
        )

        flight = serializer.save()

        self.assertEqual(
            flight.route,
            self.route,
        )
        self.assertEqual(
            flight.airplane,
            self.airplane_2,
        )
        self.assertEqual(
            flight.departure_time,
            self.NEW_DEPARTURE_TIME,
        )
        self.assertEqual(
            flight.arrival_time,
            self.NEW_ARRIVAL_TIME,
        )
        self.assertEqual(
            flight.status,
            Flight.Status.SCHEDULED,
        )
        self.assertEqual(
            list(flight.crew.all()),
            [self.crew_3],
        )
        self.assertTrue(
            Flight.objects.filter(pk=flight.pk).exists(),
        )

    def test_flight_serializer_rejects_missing_route_on_create(
        self,
    ) -> None:
        data = self.make_valid_data()
        data.pop("route")

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "route": [
                    "This field is required.",
                ],
            },
        )

    def test_flight_serializer_rejects_missing_airplane_on_create(
        self,
    ) -> None:
        data = self.make_valid_data()
        data.pop("airplane")

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "airplane": [
                    "This field is required.",
                ],
            },
        )

    def test_flight_serializer_rejects_missing_departure_time_on_create(
        self,
    ) -> None:
        data = self.make_valid_data()
        data.pop("departure_time")

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "departure_time": [
                    "This field is required.",
                ],
            },
        )

    def test_flight_serializer_rejects_missing_arrival_time_on_create(
        self,
    ) -> None:
        data = self.make_valid_data()
        data.pop("arrival_time")

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "arrival_time": [
                    "This field is required.",
                ],
            },
        )

    def test_flight_serializer_rejects_missing_crew_on_create(
        self,
    ) -> None:
        data = self.make_valid_data()
        data.pop("crew")

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "crew": [
                    "This field is required.",
                ],
            },
        )

    def test_flight_serializer_rejects_invalid_route_id(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["route"] = uuid.uuid4()

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "route",
            serializer.errors,
        )
        self.assertIn(
            "does not exist",
            str(serializer.errors["route"][0]),
        )

    def test_flight_serializer_rejects_invalid_airplane_id(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["airplane"] = uuid.uuid4()

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "airplane",
            serializer.errors,
        )
        self.assertIn(
            "does not exist",
            str(serializer.errors["airplane"][0]),
        )

    def test_flight_serializer_rejects_invalid_crew_id(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["crew"] = [
            uuid.uuid4(),
        ]

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "crew",
            serializer.errors,
        )
        self.assertIn(
            "does not exist",
            str(serializer.errors["crew"][0]),
        )

    def test_flight_serializer_rejects_arrival_before_departure(
        self,
    ) -> None:
        data = self.make_valid_data()

        data["arrival_time"] = (
            self.NEW_DEPARTURE_TIME
            - timedelta(hours=1)
        )

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.ARRIVAL_TIME_ERROR_MSG,
        )

    def test_flight_serializer_rejects_arrival_equal_to_departure(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["arrival_time"] = self.NEW_DEPARTURE_TIME

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.ARRIVAL_TIME_ERROR_MSG,
        )

    def test_flight_serializer_rejects_empty_crew(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["crew"] = []

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.EMPTY_CREW_ERROR_MSG,
        )

    def test_flight_serializer_allows_available_crew(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["crew"] = [
            self.crew_3.pk,
        ]

        serializer = FlightSerializer(
            data=data,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_flight_serializer_rejects_busy_crew(
        self,
    ) -> None:
        data = self.make_valid_data()

        data["airplane"] = self.airplane_2.pk
        data["crew"] = [
            self.crew_1.pk,
        ]
        data["departure_time"] = datetime(
            2026,
            9,
            10,
            11,
            0,
            tzinfo=timezone.utc,
        )
        data["arrival_time"] = datetime(
            2026,
            9,
            10,
            13,
            0,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "crew": [
                    (
                        "The following crew members are unavailable "
                        "for this flight and its required 30-minute "
                        f"buffer: {self.crew_1.full_name}."
                    ),
                ],
            },
        )

    def test_flight_serializer_rejects_crew_inside_schedule_buffer(
        self,
    ) -> None:
        data = self.make_valid_data()

        data["airplane"] = self.airplane_2.pk
        data["crew"] = [
            self.crew_1.pk,
        ]
        data["departure_time"] = datetime(
            2026,
            9,
            10,
            12,
            15,
            tzinfo=timezone.utc,
        )
        data["arrival_time"] = datetime(
            2026,
            9,
            10,
            13,
            15,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "crew",
            serializer.errors,
        )

    def test_flight_serializer_allows_crew_exactly_after_schedule_buffer(
        self,
    ) -> None:
        data = self.make_valid_data()

        data["airplane"] = self.airplane_2.pk
        data["crew"] = [
            self.crew_1.pk,
        ]
        data["departure_time"] = datetime(
            2026,
            9,
            10,
            12,
            30,
            tzinfo=timezone.utc,
        )
        data["arrival_time"] = datetime(
            2026,
            9,
            10,
            13,
            30,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            data=data,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_flight_serializer_allows_available_airplane(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["airplane"] = self.airplane_2.pk

        serializer = FlightSerializer(
            data=data,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_flight_serializer_rejects_busy_airplane(
        self,
    ) -> None:
        data = self.make_valid_data()

        data["airplane"] = self.airplane_1.pk
        data["crew"] = [
            self.crew_3.pk,
        ]
        data["departure_time"] = datetime(
            2026,
            9,
            10,
            11,
            0,
            tzinfo=timezone.utc,
        )
        data["arrival_time"] = datetime(
            2026,
            9,
            10,
            13,
            0,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.AIRPLANE_SCHEDULE_ERROR_MSG,
        )

    def test_flight_serializer_rejects_airplane_inside_schedule_buffer(
        self,
    ) -> None:
        data = self.make_valid_data()

        data["airplane"] = self.airplane_1.pk
        data["crew"] = [
            self.crew_3.pk,
        ]
        data["departure_time"] = datetime(
            2026,
            9,
            10,
            12,
            15,
            tzinfo=timezone.utc,
        )
        data["arrival_time"] = datetime(
            2026,
            9,
            10,
            13,
            15,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "airplane",
            serializer.errors,
        )

    def test_flight_serializer_allows_airplane_exactly_after_schedule_buffer(
        self,
    ) -> None:
        data = self.make_valid_data()

        data["airplane"] = self.airplane_1.pk
        data["crew"] = [
            self.crew_3.pk,
        ]
        data["departure_time"] = datetime(
            2026,
            9,
            10,
            12,
            30,
            tzinfo=timezone.utc,
        )
        data["arrival_time"] = datetime(
            2026,
            9,
            10,
            13,
            30,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            data=data,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_flight_serializer_allows_scheduled_status(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["status"] = Flight.Status.SCHEDULED

        serializer = FlightSerializer(
            data=data,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_flight_serializer_allows_delayed_status(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["status"] = Flight.Status.DELAYED

        serializer = FlightSerializer(
            data=data,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_flight_serializer_rejects_cancelled_status(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["status"] = Flight.Status.CANCELLED

        serializer = FlightSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.CANCELLED_STATUS_ERROR_MSG,
        )

    def test_flight_serializer_partial_update_uses_existing_departure_time(
        self,
    ) -> None:
        new_arrival_time = datetime(
            2026,
            9,
            10,
            12,
            15,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "arrival_time": new_arrival_time,
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        flight = serializer.save()

        self.assertEqual(
            flight.departure_time,
            self.EXISTING_DEPARTURE_TIME,
        )
        self.assertEqual(
            flight.arrival_time,
            new_arrival_time,
        )

    def test_flight_serializer_partial_update_uses_existing_arrival_time(
        self,
    ) -> None:
        new_departure_time = datetime(
            2026,
            9,
            10,
            9,
            45,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "departure_time": new_departure_time,
            },
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        flight = serializer.save()

        self.assertEqual(
            flight.departure_time,
            new_departure_time,
        )
        self.assertEqual(
            flight.arrival_time,
            self.EXISTING_ARRIVAL_TIME,
        )

    def test_flight_serializer_allows_partial_update_without_status(
        self,
    ) -> None:
        original_status = self.existing_flight.status

        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "arrival_time": datetime(
                    2026,
                    9,
                    10,
                    12,
                    15,
                    tzinfo=timezone.utc,
                ),
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        flight = serializer.save()

        self.assertEqual(
            flight.status,
            original_status,
        )

    def test_flight_serializer_allows_partial_update_without_crew(
        self,
    ) -> None:
        original_crew = list(
            self.existing_flight.crew.all(),
        )

        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "arrival_time": datetime(
                    2026,
                    9,
                    10,
                    12,
                    15,
                    tzinfo=timezone.utc,
                ),
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        flight = serializer.save()

        self.assertEqual(
            list(flight.crew.all()),
            original_crew,
        )

    def test_flight_serializer_allows_partial_update_without_airplane(
        self,
    ) -> None:
        original_airplane = self.existing_flight.airplane

        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "arrival_time": datetime(
                    2026,
                    9,
                    10,
                    12,
                    15,
                    tzinfo=timezone.utc,
                ),
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        flight = serializer.save()

        self.assertEqual(
            flight.airplane,
            original_airplane,
        )

    def test_flight_serializer_rejects_partial_update_with_empty_crew(
        self,
    ) -> None:
        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "crew": [],
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.EMPTY_CREW_ERROR_MSG,
        )

    def test_flight_serializer_rejects_partial_update_causing_invalid_times(
        self,
    ) -> None:
        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "arrival_time": datetime(
                    2026,
                    9,
                    10,
                    9,
                    0,
                    tzinfo=timezone.utc,
                ),
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.ARRIVAL_TIME_ERROR_MSG,
        )

    def test_flight_serializer_does_not_change_fields_not_provided_on_partial_update(
        self,
    ) -> None:
        original_route = self.existing_flight.route
        original_airplane = self.existing_flight.airplane
        original_departure_time = self.existing_flight.departure_time
        original_status = self.existing_flight.status
        original_crew = list(
            self.existing_flight.crew.all(),
        )

        new_arrival_time = datetime(
            2026,
            9,
            10,
            12,
            15,
            tzinfo=timezone.utc,
        )

        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "arrival_time": new_arrival_time,
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        flight = serializer.save()

        self.assertEqual(
            flight.route,
            original_route,
        )
        self.assertEqual(
            flight.airplane,
            original_airplane,
        )
        self.assertEqual(
            flight.departure_time,
            original_departure_time,
        )
        self.assertEqual(
            flight.arrival_time,
            new_arrival_time,
        )
        self.assertEqual(
            flight.status,
            original_status,
        )
        self.assertEqual(
            list(flight.crew.all()),
            original_crew,
        )

    def test_flight_serializer_allows_airplane_change_without_active_tickets(
        self,
    ) -> None:
        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "airplane": self.airplane_2.pk,
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        flight = serializer.save()

        self.assertEqual(
            flight.airplane,
            self.airplane_2,
        )

    def test_flight_serializer_rejects_airplane_change_with_active_tickets(
        self,
    ) -> None:
        self.make_ticket(
            flight=self.existing_flight,
            status=Ticket.Status.ACTIVE,
        )

        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "airplane": self.airplane_2.pk,
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.AIRPLANE_CHANGE_ERROR_MSG,
        )

    def test_flight_serializer_allows_airplane_change_with_only_cancelled_tickets(
        self,
    ) -> None:
        self.make_ticket(
            flight=self.existing_flight,
            status=Ticket.Status.CANCELLED,
        )

        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "airplane": self.airplane_2.pk,
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        flight = serializer.save()

        self.assertEqual(
            flight.airplane,
            self.airplane_2,
        )

    def test_flight_serializer_rejects_modification_of_cancelled_flight(
        self,
    ) -> None:
        serializer = FlightSerializer(
            self.cancelled_flight,
            data={
                "arrival_time": (
                    self.CANCELLED_ARRIVAL_TIME
                    + timedelta(hours=1)
                ),
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.CANCELLED_FLIGHT_MODIFICATION_ERROR_MSG,
        )

    def test_flight_serializer_rejects_cancelled_status_on_partial_update(
        self,
    ) -> None:
        serializer = FlightSerializer(
            self.existing_flight,
            data={
                "status": Flight.Status.CANCELLED,
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.CANCELLED_STATUS_ERROR_MSG,
        )


class FlightListSerializerTests(
    BaseFlightScheduleTestCase,
):
    def setUp(self) -> None:
        self.existing_flight.available_seats = (
            self.existing_flight.airplane.capacity
        )
        self.existing_flight.active_tickets = []

    def test_flight_list_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "source",
                "destination",
                "airplane",
                "airplane_type",
                "crew",
                "departure_time",
                "arrival_time",
                "status",
                "current_state",
                "flight_duration",
                "available_seats",
            },
        )

    def test_flight_list_serializer_returns_correct_id(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["id"],
            str(self.existing_flight.pk),
        )

    def test_flight_list_serializer_returns_source_city_name(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["source"],
            self.kyiv.name,
        )

    def test_flight_list_serializer_returns_destination_city_name(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["destination"],
            self.lviv.name,
        )

    def test_flight_list_serializer_returns_airplane_name(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["airplane"],
            self.airplane_1.name,
        )

    def test_flight_list_serializer_returns_airplane_type_name(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["airplane_type"],
            self.airplane_type.name,
        )

    def test_flight_list_serializer_returns_crew_full_names(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["crew"],
            [
                self.crew_1.full_name,
            ],
        )

    def test_flight_list_serializer_returns_flight_status(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["status"],
            Flight.Status.SCHEDULED,
        )

    def test_flight_list_serializer_returns_current_state(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["current_state"],
            self.existing_flight.flight_state,
        )

    def test_flight_list_serializer_returns_flight_duration(
        self,
    ) -> None:
        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["flight_duration"],
            "02:00:00",
        )

    def test_flight_list_serializer_returns_available_seats(
        self,
    ) -> None:
        self.existing_flight.available_seats = 115

        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["available_seats"],
            115,
        )

    def test_flight_list_serializer_returns_zero_available_seats(
        self,
    ) -> None:
        self.existing_flight.available_seats = 0

        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["available_seats"],
            0,
        )

    def test_flight_list_serializer_returns_delayed_status(
        self,
    ) -> None:
        self.existing_flight.status = Flight.Status.DELAYED

        serializer = FlightListSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["status"],
            Flight.Status.DELAYED,
        )


class FlightDetailSerializerTests(
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

        cls.active_ticket_1 = Ticket.objects.create(
            order=cls.order,
            flight=cls.existing_flight,
            row=1,
            seat=1,
            status=Ticket.Status.ACTIVE,
        )

        cls.active_ticket_2 = Ticket.objects.create(
            order=cls.order,
            flight=cls.existing_flight,
            row=1,
            seat=2,
            status=Ticket.Status.ACTIVE,
        )

        cls.cancelled_ticket = Ticket.objects.create(
            order=cls.order,
            flight=cls.existing_flight,
            row=1,
            seat=3,
            status=Ticket.Status.CANCELLED,
        )

    def setUp(self) -> None:
        self.existing_flight.active_tickets = [
            self.active_ticket_1,
            self.active_ticket_2,
        ]

    def test_flight_detail_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "route",
                "airplane",
                "departure_time",
                "arrival_time",
                "status",
                "current_state",
                "flight_duration",
                "crew",
                "taken_seats",
            },
        )

    def test_flight_detail_serializer_returns_correct_id(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["id"],
            str(self.existing_flight.pk),
        )

    def test_flight_detail_serializer_returns_nested_route(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        route_data = serializer.data["route"]

        self.assertEqual(
            route_data["id"],
            str(self.route.pk),
        )
        self.assertEqual(
            route_data["distance"],
            self.route.distance,
        )

    def test_flight_detail_serializer_returns_nested_source_airport(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        source = serializer.data["route"]["source"]

        self.assertEqual(
            source["id"],
            str(self.source_airport.pk),
        )
        self.assertEqual(
            source["name"],
            self.source_airport.name,
        )

    def test_flight_detail_serializer_returns_nested_destination_airport(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        destination = serializer.data["route"]["destination"]

        self.assertEqual(
            destination["id"],
            str(self.destination_airport.pk),
        )
        self.assertEqual(
            destination["name"],
            self.destination_airport.name,
        )

    def test_flight_detail_serializer_returns_nested_source_city(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        city = (
            serializer.data["route"]
            ["source"]
            ["closest_big_city"]
        )

        self.assertEqual(
            city["id"],
            str(self.kyiv.pk),
        )
        self.assertEqual(
            city["name"],
            self.kyiv.name,
        )

    def test_flight_detail_serializer_returns_nested_destination_city(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        city = (
            serializer.data["route"]
            ["destination"]
            ["closest_big_city"]
        )

        self.assertEqual(
            city["id"],
            str(self.lviv.pk),
        )
        self.assertEqual(
            city["name"],
            self.lviv.name,
        )

    def test_flight_detail_serializer_returns_nested_country(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        source_country = (
            serializer.data["route"]
            ["source"]
            ["closest_big_city"]
            ["country"]
        )

        destination_country = (
            serializer.data["route"]
            ["destination"]
            ["closest_big_city"]
            ["country"]
        )

        self.assertEqual(
            source_country["id"],
            str(self.country.pk),
        )
        self.assertEqual(
            source_country["name"],
            self.country.name,
        )

        self.assertEqual(
            destination_country["id"],
            str(self.country.pk),
        )
        self.assertEqual(
            destination_country["name"],
            self.country.name,
        )

    def test_flight_detail_serializer_returns_nested_airplane(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        airplane = serializer.data["airplane"]

        self.assertEqual(
            airplane["id"],
            str(self.airplane_1.pk),
        )
        self.assertEqual(
            airplane["name"],
            self.airplane_1.name,
        )
        self.assertEqual(
            airplane["rows"],
            self.airplane_1.rows,
        )
        self.assertEqual(
            airplane["seats_in_row"],
            self.airplane_1.seats_in_row,
        )
        self.assertEqual(
            airplane["capacity"],
            self.airplane_1.capacity,
        )

    def test_flight_detail_serializer_returns_nested_airplane_type(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        airplane_type = (
            serializer.data["airplane"]["airplane_type"]
        )

        self.assertEqual(
            airplane_type["id"],
            str(self.airplane_type.pk),
        )
        self.assertEqual(
            airplane_type["name"],
            self.airplane_type.name,
        )

    def test_flight_detail_serializer_returns_crew(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["crew"],
            [
                {
                    "id": str(self.crew_1.pk),
                    "first_name": self.crew_1.first_name,
                    "last_name": self.crew_1.last_name,
                },
            ],
        )

    def test_flight_detail_serializer_returns_flight_duration(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["flight_duration"],
            "02:00:00",
        )

    def test_flight_detail_serializer_returns_status(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["status"],
            Flight.Status.SCHEDULED,
        )

    def test_flight_detail_serializer_returns_current_state(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["current_state"],
            self.existing_flight.flight_state,
        )

    def test_flight_detail_serializer_returns_active_taken_seats(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["taken_seats"],
            [
                {
                    "row": 1,
                    "seat": 1,
                },
                {
                    "row": 1,
                    "seat": 2,
                },
            ],
        )

    def test_flight_detail_serializer_does_not_return_cancelled_ticket_seat(
        self,
    ) -> None:
        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertNotIn(
            {
                "row": self.cancelled_ticket.row,
                "seat": self.cancelled_ticket.seat,
            },
            serializer.data["taken_seats"],
        )

    def test_flight_detail_serializer_returns_empty_taken_seats_when_no_active_tickets(
        self,
    ) -> None:
        self.existing_flight.active_tickets = []

        serializer = FlightDetailSerializer(
            self.existing_flight,
        )

        self.assertEqual(
            serializer.data["taken_seats"],
            [],
        )


class FlightCancelSerializerTests(
    BaseFlightScheduleTestCase,
):
    def test_flight_cancel_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = FlightCancelSerializer(
            self.cancelled_flight,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "status",
            },
        )

    def test_flight_cancel_serializer_returns_flight_id(
        self,
    ) -> None:
        serializer = FlightCancelSerializer(
            self.cancelled_flight,
        )

        self.assertEqual(
            serializer.data["id"],
            str(self.cancelled_flight.pk),
        )

    def test_flight_cancel_serializer_returns_cancelled_status(
        self,
    ) -> None:
        serializer = FlightCancelSerializer(
            self.cancelled_flight,
        )

        self.assertEqual(
            serializer.data["status"],
            Flight.Status.CANCELLED,
        )

    def test_flight_cancel_serializer_fields_are_read_only(
        self,
    ) -> None:
        serializer = FlightCancelSerializer(
            data={
                "id": self.existing_flight.pk,
                "status": Flight.Status.SCHEDULED,
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
