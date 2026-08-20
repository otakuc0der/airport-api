from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Crew,
    airplane_image_file_path,
    airport_image_file_path,
    crew_photo_file_path,
)


class CrewModelTests(TestCase):
    def setUp(self) -> None:
        self.crew = Crew.objects.create(
            first_name="John",
            last_name="Smith",
        )

    def test_full_name(self) -> None:
        self.assertEqual(
            self.crew.full_name,
            "John Smith",
        )

    def test_str(self) -> None:
        self.assertEqual(
            str(self.crew),
            "John Smith",
        )

    @patch("airport.models.generate_image_file_path")
    def test_crew_photo_file_path(
        self,
        mock_generate_image_file_path,
    ) -> None:
        mock_generate_image_file_path.return_value = (
            "uploads/crews/test.jpg"
        )

        result = crew_photo_file_path(
            self.crew,
            "photo.jpg",
        )

        mock_generate_image_file_path.assert_called_once_with(
            "John-Smith",
            "photo.jpg",
            "uploads/crews",
        )

        self.assertEqual(
            result,
            "uploads/crews/test.jpg",
        )


class CountryModelTests(TestCase):
    def test_str(self) -> None:
        country = Country.objects.create(
            name="Ukraine",
        )

        self.assertEqual(
            str(country),
            "Ukraine",
        )

    def test_country_name_is_unique(self) -> None:
        Country.objects.create(
            name="Ukraine",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Country.objects.create(
                    name="Ukraine",
                )


class CityModelTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.ukraine = Country.objects.create(
            name="Ukraine",
        )
        cls.poland = Country.objects.create(
            name="Poland",
        )

    def test_str(self) -> None:
        city = City.objects.create(
            name="Kyiv",
            country=self.ukraine,
        )

        self.assertEqual(
            str(city),
            "Kyiv (Ukraine)",
        )

    def test_city_name_country_pair_is_unique(
        self,
    ) -> None:
        City.objects.create(
            name="Kyiv",
            country=self.ukraine,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                City.objects.create(
                    name="Kyiv",
                    country=self.ukraine,
                )

    def test_same_city_name_allowed_for_different_country(
        self,
    ) -> None:
        City.objects.create(
            name="Springfield",
            country=self.ukraine,
        )

        city = City.objects.create(
            name="Springfield",
            country=self.poland,
        )

        self.assertEqual(
            city.name,
            "Springfield",
        )
        self.assertEqual(
            city.country,
            self.poland,
        )


class AirportModelTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.country = Country.objects.create(
            name="Ukraine",
        )
        cls.city = City.objects.create(
            name="Kyiv",
            country=cls.country,
        )
        cls.airport = Airport.objects.create(
            name="Boryspil International Airport",
            closest_big_city=cls.city,
        )

    def test_str(self) -> None:
        self.assertEqual(
            str(self.airport),
            (
                "Boryspil International Airport "
                "(closest city: Kyiv)"
            ),
        )

    def test_airport_name_is_unique(self) -> None:
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Airport.objects.create(
                    name=self.airport.name,
                    closest_big_city=self.city,
                )

    @patch("airport.models.generate_image_file_path")
    def test_airport_image_file_path(
        self,
        mock_generate_image_file_path,
    ) -> None:
        mock_generate_image_file_path.return_value = (
            "uploads/airports/test.jpg"
        )

        result = airport_image_file_path(
            self.airport,
            "airport.jpg",
        )

        mock_generate_image_file_path.assert_called_once_with(
            self.airport.name,
            "airport.jpg",
            "uploads/airports",
        )

        self.assertEqual(
            result,
            "uploads/airports/test.jpg",
        )


class AirplaneTypeModelTests(TestCase):
    def test_str(self) -> None:
        airplane_type = AirplaneType.objects.create(
            name="Boeing 737",
        )

        self.assertEqual(
            str(airplane_type),
            "Boeing 737",
        )

    def test_airplane_type_name_is_unique(
        self,
    ) -> None:
        AirplaneType.objects.create(
            name="Boeing 737",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AirplaneType.objects.create(
                    name="Boeing 737",
                )


class AirplaneModelTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.airplane_type = AirplaneType.objects.create(
            name="Boeing 737",
        )

        cls.airplane = Airplane.objects.create(
            name="UR-001",
            rows=20,
            seats_in_row=6,
            airplane_type=cls.airplane_type,
        )

    def test_capacity(self) -> None:
        self.assertEqual(
            self.airplane.capacity,
            120,
        )

    def test_str(self) -> None:
        self.assertEqual(
            str(self.airplane),
            (
                "UR-001 | Boeing 737"
                " (rows: 20, seats in row: 6)"
            ),
        )

    def test_airplane_name_is_unique(self) -> None:
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Airplane.objects.create(
                    name=self.airplane.name,
                    rows=20,
                    seats_in_row=6,
                    airplane_type=self.airplane_type,
                )

    def test_rows_must_be_at_least_one(self) -> None:
        airplane = Airplane(
            name="UR-002",
            rows=0,
            seats_in_row=6,
            airplane_type=self.airplane_type,
        )

        with self.assertRaises(ValidationError) as context:
            airplane.full_clean()

        self.assertIn(
            "rows",
            context.exception.message_dict,
        )

    def test_seats_in_row_must_be_at_least_one(
        self,
    ) -> None:
        airplane = Airplane(
            name="UR-002",
            rows=20,
            seats_in_row=0,
            airplane_type=self.airplane_type,
        )

        with self.assertRaises(ValidationError) as context:
            airplane.full_clean()

        self.assertIn(
            "seats_in_row",
            context.exception.message_dict,
        )

    @patch("airport.models.generate_image_file_path")
    def test_airplane_image_file_path(
        self,
        mock_generate_image_file_path,
    ) -> None:
        mock_generate_image_file_path.return_value = (
            "uploads/airplanes/test.jpg"
        )

        result = airplane_image_file_path(
            self.airplane,
            "airplane.jpg",
        )

        mock_generate_image_file_path.assert_called_once_with(
            self.airplane.name,
            "airplane.jpg",
            "uploads/airplanes",
        )

        self.assertEqual(
            result,
            "uploads/airplanes/test.jpg",
        )
