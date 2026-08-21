from airport.admin import FlightAdminForm
from airport.models import Flight
from airport.tests.base import BaseFlightScheduleTestCase


class FlightAdminFormTests(
    BaseFlightScheduleTestCase,
):
    def get_form_data(
        self,
        *,
        status: str,
    ) -> dict:
        return {
            "route": self.existing_flight.route.pk,
            "airplane": self.existing_flight.airplane.pk,
            "departure_time": (
                self.existing_flight.departure_time
            ),
            "arrival_time": (
                self.existing_flight.arrival_time
            ),
            "status": status,
            "crew": [
                crew.pk
                for crew
                in self.existing_flight.crew.all()
            ],
        }

    def test_scheduled_status_is_valid(
        self,
    ) -> None:
        form = FlightAdminForm(
            data=self.get_form_data(
                status=Flight.Status.SCHEDULED,
            ),
            instance=self.existing_flight,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_scheduled_flight_can_be_changed_to_delayed(
        self,
    ) -> None:
        self.existing_flight.status = (
            Flight.Status.SCHEDULED
        )

        form = FlightAdminForm(
            data=self.get_form_data(
                status=Flight.Status.DELAYED,
            ),
            instance=self.existing_flight,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_delayed_flight_can_be_changed_to_scheduled(
        self,
    ) -> None:
        self.existing_flight.status = (
            Flight.Status.DELAYED
        )

        form = FlightAdminForm(
            data=self.get_form_data(
                status=Flight.Status.SCHEDULED,
            ),
            instance=self.existing_flight,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_cancelled_status_is_invalid(
        self,
    ) -> None:
        form = FlightAdminForm(
            data=self.get_form_data(
                status=Flight.Status.CANCELLED,
            ),
            instance=self.existing_flight,
        )

        self.assertFalse(
            form.is_valid(),
        )

        self.assertIn(
            "status",
            form.errors,
        )

    def test_cancelled_status_returns_expected_error(
        self,
    ) -> None:
        form = FlightAdminForm(
            data=self.get_form_data(
                status=Flight.Status.CANCELLED,
            ),
            instance=self.existing_flight,
        )

        form.is_valid()

        self.assertEqual(
            form.errors["status"],
            [
                (
                    "Flight cannot be cancelled by "
                    "changing its status directly."
                )
            ],
        )
