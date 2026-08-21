import uuid

from airport.models import Flight, Ticket
from airport.serializers import TicketListSerializer, TicketSerializer
from airport.tests.base import BaseFlightScheduleTestCase


class TicketSerializerTests(BaseFlightScheduleTestCase):
    VALID_ROW = 10
    VALID_SEAT = 3

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

    def make_valid_data(self) -> dict[str, object]:
        return {
            "flight": self.existing_flight.pk,
            "row": self.VALID_ROW,
            "seat": self.VALID_SEAT,
        }

    def test_ticket_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = TicketSerializer(
            data=self.make_valid_data(),
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["flight"],
            self.existing_flight,
        )
        self.assertEqual(
            serializer.validated_data["row"],
            self.VALID_ROW,
        )
        self.assertEqual(
            serializer.validated_data["seat"],
            self.VALID_SEAT,
        )

    def test_ticket_serializer_accepts_first_row_and_first_seat(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["row"] = 1
        data["seat"] = 1

        serializer = TicketSerializer(
            data=data,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_ticket_serializer_accepts_last_row_and_last_seat(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["row"] = self.airplane_1.rows
        data["seat"] = self.airplane_1.seats_in_row

        serializer = TicketSerializer(
            data=data,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_ticket_serializer_rejects_row_zero(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["row"] = 0

        serializer = TicketSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.ROW_ERROR_MSG,
        )

    def test_ticket_serializer_rejects_row_above_airplane_rows(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["row"] = self.airplane_1.rows + 1

        serializer = TicketSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.ROW_ERROR_MSG,
        )

    def test_ticket_serializer_rejects_seat_zero(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["seat"] = 0

        serializer = TicketSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.SEAT_ERROR_MSG,
        )

    def test_ticket_serializer_rejects_seat_above_seats_in_row(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["seat"] = self.airplane_1.seats_in_row + 1

        serializer = TicketSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            self.SEAT_ERROR_MSG,
        )

    def test_ticket_serializer_rejects_missing_flight(
        self,
    ) -> None:
        data = self.make_valid_data()
        data.pop("flight")

        serializer = TicketSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "flight": [
                    "This field is required.",
                ],
            },
        )

    def test_ticket_serializer_rejects_missing_row(
        self,
    ) -> None:
        data = self.make_valid_data()
        data.pop("row")

        serializer = TicketSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "row": [
                    "This field is required.",
                ],
            },
        )

    def test_ticket_serializer_rejects_missing_seat(
        self,
    ) -> None:
        data = self.make_valid_data()
        data.pop("seat")

        serializer = TicketSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "seat": [
                    "This field is required.",
                ],
            },
        )

    def test_ticket_serializer_rejects_invalid_flight_id(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["flight"] = uuid.uuid4()

        serializer = TicketSerializer(
            data=data,
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "flight",
            serializer.errors,
        )
        self.assertIn(
            "does not exist",
            str(serializer.errors["flight"][0]),
        )

    def test_ticket_serializer_status_is_read_only(
        self,
    ) -> None:
        data = self.make_valid_data()
        data["status"] = Ticket.Status.CANCELLED

        serializer = TicketSerializer(
            data=data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "status",
            serializer.validated_data,
        )

    def test_ticket_serializer_id_is_read_only(
        self,
    ) -> None:
        fake_id = uuid.uuid4()

        data = self.make_valid_data()
        data["id"] = fake_id

        serializer = TicketSerializer(
            data=data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "id",
            serializer.validated_data,
        )


class TicketListSerializerTests(
    BaseFlightScheduleTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.ticket = Ticket(
            id=uuid.uuid4(),
            flight=cls.existing_flight,
            row=2,
            seat=4,
            status=Ticket.Status.ACTIVE,
        )

    def setUp(self) -> None:
        self.existing_flight.available_seats = (
            self.airplane_1.capacity - 1
        )

    def test_ticket_list_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = TicketListSerializer(
            self.ticket,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "row",
                "seat",
                "flight",
                "status",
            },
        )

    def test_ticket_list_serializer_returns_ticket_id(
        self,
    ) -> None:
        serializer = TicketListSerializer(
            self.ticket,
        )

        self.assertEqual(
            serializer.data["id"],
            str(self.ticket.pk),
        )

    def test_ticket_list_serializer_returns_row_and_seat(
        self,
    ) -> None:
        serializer = TicketListSerializer(
            self.ticket,
        )

        self.assertEqual(
            serializer.data["row"],
            2,
        )
        self.assertEqual(
            serializer.data["seat"],
            4,
        )

    def test_ticket_list_serializer_returns_status(
        self,
    ) -> None:
        serializer = TicketListSerializer(
            self.ticket,
        )

        self.assertEqual(
            serializer.data["status"],
            Ticket.Status.ACTIVE,
        )

    def test_ticket_list_serializer_returns_nested_flight(
        self,
    ) -> None:
        serializer = TicketListSerializer(
            self.ticket,
        )

        flight_data = serializer.data["flight"]

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
            flight_data["status"],
            Flight.Status.SCHEDULED,
        )

        self.assertEqual(
            flight_data["current_state"],
            self.existing_flight.flight_state,
        )

        self.assertEqual(
            flight_data["flight_duration"],
            "02:00:00",
        )

        self.assertEqual(
            flight_data["available_seats"],
            self.airplane_1.capacity - 1,
        )

        self.assertIn(
            "departure_time",
            flight_data,
        )
        self.assertIn(
            "arrival_time",
            flight_data,
        )

    def test_ticket_list_serializer_returns_cancelled_status(
        self,
    ) -> None:
        self.ticket.status = Ticket.Status.CANCELLED

        serializer = TicketListSerializer(
            self.ticket,
        )

        self.assertEqual(
            serializer.data["status"],
            Ticket.Status.CANCELLED,
        )
