from django.core.exceptions import ValidationError
from django.test import TestCase

from airport.models import (
    Airport,
    City,
    Country,
    Route,
)


class RouteModelTests(TestCase):
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

    def test_create_valid_route(self) -> None:
        route = Route.objects.create(
            source=self.source_airport,
            destination=self.destination_airport,
            distance=470,
        )

        self.assertEqual(
            route.source,
            self.source_airport,
        )
        self.assertEqual(
            route.destination,
            self.destination_airport,
        )
        self.assertEqual(
            route.distance,
            470,
        )

    def test_save_rejects_same_source_and_destination(
        self,
    ) -> None:
        route = Route(
            source=self.source_airport,
            destination=self.source_airport,
            distance=100,
        )

        with self.assertRaises(ValidationError) as context:
            route.save()

        self.assertEqual(
            context.exception.message_dict,
            {
                "destination": [
                    "Destination must differ from source.",
                ],
            },
        )

    def test_duplicate_route_is_rejected(
        self,
    ) -> None:
        Route.objects.create(
            source=self.source_airport,
            destination=self.destination_airport,
            distance=470,
        )

        duplicate = Route(
            source=self.source_airport,
            destination=self.destination_airport,
            distance=500,
        )

        with self.assertRaises(ValidationError):
            duplicate.save()

    def test_reverse_route_is_allowed(self) -> None:
        Route.objects.create(
            source=self.source_airport,
            destination=self.destination_airport,
            distance=470,
        )

        reverse_route = Route.objects.create(
            source=self.destination_airport,
            destination=self.source_airport,
            distance=470,
        )

        self.assertEqual(
            reverse_route.source,
            self.destination_airport,
        )
        self.assertEqual(
            reverse_route.destination,
            self.source_airport,
        )

    def test_str(self) -> None:
        route = Route.objects.create(
            source=self.source_airport,
            destination=self.destination_airport,
            distance=470,
        )

        self.assertEqual(
            str(route),
            (
                f"Source: {self.source_airport}; "
                f"Destination: {self.destination_airport}; "
                "Distance: 470"
            ),
        )
