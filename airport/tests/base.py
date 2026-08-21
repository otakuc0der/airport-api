from datetime import datetime, timezone

from django.test import TestCase

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Crew,
    Flight,
    Route,
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
