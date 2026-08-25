import uuid

from airport.models import Ticket
from airport.serializers import TicketSerializer
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
