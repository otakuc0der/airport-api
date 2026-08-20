import uuid
from types import SimpleNamespace

from django.test import TestCase

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Crew,
)
from airport.serializers import (
    AirplaneDetailSerializer,
    AirplaneListSerializer,
    AirplaneSerializer,
    AirplaneTypeSerializer,
    AirplaneUploadImageSerializer,
    AirportDetailSerializer,
    AirportListSerializer,
    AirportSerializer,
    AirportStatisticsSerializer,
    AirportUploadImageSerializer,
    CityDetailSerializer,
    CityListSerializer,
    CitySerializer,
    CountrySerializer,
    CrewDetailSerializer,
    CrewListSerializer,
    CrewSerializer,
    CrewUploadPhotoSerializer,
)


class BaseReferenceSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.ukraine = Country.objects.create(
            name="Ukraine",
        )
        cls.poland = Country.objects.create(
            name="Poland",
        )

        cls.kyiv = City.objects.create(
            name="Kyiv",
            country=cls.ukraine,
        )
        cls.warsaw = City.objects.create(
            name="Warsaw",
            country=cls.poland,
        )

        cls.boryspil = Airport.objects.create(
            name="Boryspil International Airport",
            closest_big_city=cls.kyiv,
        )
        cls.warsaw_airport = Airport.objects.create(
            name="Warsaw Chopin Airport",
            closest_big_city=cls.warsaw,
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

        cls.crew = Crew.objects.create(
            first_name="John",
            last_name="Smith",
        )


class CountrySerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_country_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = CountrySerializer(
            self.ukraine,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "name",
            },
        )

    def test_country_serializer_returns_data(
        self,
    ) -> None:
        serializer = CountrySerializer(
            self.ukraine,
        )

        self.assertEqual(
            serializer.data["id"],
            str(self.ukraine.pk),
        )
        self.assertEqual(
            serializer.data["name"],
            "Ukraine",
        )

    def test_country_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = CountrySerializer(
            data={
                "name": "Germany",
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_country_serializer_rejects_missing_name(
        self,
    ) -> None:
        serializer = CountrySerializer(
            data={},
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

    def test_country_serializer_rejects_duplicate_name(
        self,
    ) -> None:
        serializer = CountrySerializer(
            data={
                "name": self.ukraine.name,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

    def test_country_serializer_id_is_read_only(
        self,
    ) -> None:
        serializer = CountrySerializer(
            data={
                "id": uuid.uuid4(),
                "name": "Germany",
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "id",
            serializer.validated_data,
        )


class CitySerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_city_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = CitySerializer(
            self.kyiv,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "name",
                "country",
            },
        )

    def test_city_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = CitySerializer(
            data={
                "name": "Lviv",
                "country": self.ukraine.pk,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["country"],
            self.ukraine,
        )

    def test_city_serializer_rejects_missing_name(
        self,
    ) -> None:
        serializer = CitySerializer(
            data={
                "country": self.ukraine.pk,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

    def test_city_serializer_rejects_missing_country(
        self,
    ) -> None:
        serializer = CitySerializer(
            data={
                "name": "Lviv",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "country",
            serializer.errors,
        )

    def test_city_serializer_rejects_invalid_country(
        self,
    ) -> None:
        serializer = CitySerializer(
            data={
                "name": "Lviv",
                "country": uuid.uuid4(),
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "country",
            serializer.errors,
        )

    def test_city_serializer_rejects_duplicate_city_for_same_country(
        self,
    ) -> None:
        serializer = CitySerializer(
            data={
                "name": self.kyiv.name,
                "country": self.ukraine.pk,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

    def test_city_serializer_allows_same_name_for_different_country(
        self,
    ) -> None:
        serializer = CitySerializer(
            data={
                "name": self.kyiv.name,
                "country": self.poland.pk,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )


class CityListSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_city_list_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = CityListSerializer(
            self.kyiv,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "name",
                "country",
            },
        )

    def test_city_list_serializer_returns_country_name(
        self,
    ) -> None:
        serializer = CityListSerializer(
            self.kyiv,
        )

        self.assertEqual(
            serializer.data["country"],
            "Ukraine",
        )


class CityDetailSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_city_detail_serializer_returns_nested_country(
        self,
    ) -> None:
        serializer = CityDetailSerializer(
            self.kyiv,
        )

        self.assertEqual(
            serializer.data["country"],
            {
                "id": str(self.ukraine.pk),
                "name": "Ukraine",
            },
        )


class AirportSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_airport_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = AirportSerializer(
            self.boryspil,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "name",
                "closest_big_city",
            },
        )

    def test_airport_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = AirportSerializer(
            data={
                "name": "Kyiv International Airport",
                "closest_big_city": self.kyiv.pk,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["closest_big_city"],
            self.kyiv,
        )

    def test_airport_serializer_rejects_invalid_city(
        self,
    ) -> None:
        serializer = AirportSerializer(
            data={
                "name": "Test Airport",
                "closest_big_city": uuid.uuid4(),
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "closest_big_city",
            serializer.errors,
        )

    def test_airport_serializer_rejects_duplicate_name(
        self,
    ) -> None:
        serializer = AirportSerializer(
            data={
                "name": self.boryspil.name,
                "closest_big_city": self.warsaw.pk,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )


class AirportListSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_airport_list_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = AirportListSerializer(
            self.boryspil,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "name",
                "closest_big_city",
                "image",
            },
        )

    def test_airport_list_serializer_returns_city_name(
        self,
    ) -> None:
        serializer = AirportListSerializer(
            self.boryspil,
        )

        self.assertEqual(
            serializer.data["closest_big_city"],
            "Kyiv",
        )

    def test_airport_list_serializer_returns_null_image(
        self,
    ) -> None:
        serializer = AirportListSerializer(
            self.boryspil,
        )

        self.assertIsNone(
            serializer.data["image"],
        )


class AirportDetailSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_airport_detail_serializer_returns_nested_city(
        self,
    ) -> None:
        serializer = AirportDetailSerializer(
            self.boryspil,
        )

        city_data = serializer.data[
            "closest_big_city"
        ]

        self.assertEqual(
            city_data["id"],
            str(self.kyiv.pk),
        )
        self.assertEqual(
            city_data["name"],
            "Kyiv",
        )
        self.assertEqual(
            city_data["country"],
            {
                "id": str(self.ukraine.pk),
                "name": "Ukraine",
            },
        )

    def test_airport_detail_serializer_returns_image(
        self,
    ) -> None:
        serializer = AirportDetailSerializer(
            self.boryspil,
        )

        self.assertIn(
            "image",
            serializer.data,
        )


class AirportUploadImageSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_upload_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = AirportUploadImageSerializer(
            self.boryspil,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "image",
            },
        )

    def test_upload_serializer_id_is_read_only(
        self,
    ) -> None:
        serializer = AirportUploadImageSerializer(
            self.boryspil,
            data={
                "id": uuid.uuid4(),
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "id",
            serializer.validated_data,
        )


class AirportStatisticsSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_statistics_serializer_returns_expected_fields(
        self,
    ) -> None:
        statistics = SimpleNamespace(
            pk=self.boryspil.pk,
            name=self.boryspil.name,
            departing_routes_count=3,
            arriving_routes_count=2,
            upcoming_departures_count=4,
            upcoming_arrivals_count=5,
            total_upcoming_flights=9,
            active_tickets_count=20,
            cancelled_tickets_count=4,
            total_tickets_count=24,
        )

        serializer = AirportStatisticsSerializer(
            statistics,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "airport_id",
                "airport_name",
                "departing_routes_count",
                "arriving_routes_count",
                "upcoming_departures_count",
                "upcoming_arrivals_count",
                "total_upcoming_flights",
                "active_tickets_count",
                "cancelled_tickets_count",
                "total_tickets_count",
            },
        )

    def test_statistics_serializer_returns_values(
        self,
    ) -> None:
        statistics = SimpleNamespace(
            pk=self.boryspil.pk,
            name=self.boryspil.name,
            departing_routes_count=3,
            arriving_routes_count=2,
            upcoming_departures_count=4,
            upcoming_arrivals_count=5,
            total_upcoming_flights=9,
            active_tickets_count=20,
            cancelled_tickets_count=4,
            total_tickets_count=24,
        )

        serializer = AirportStatisticsSerializer(
            statistics,
        )

        self.assertEqual(
            serializer.data["airport_id"],
            str(self.boryspil.pk),
        )
        self.assertEqual(
            serializer.data["airport_name"],
            self.boryspil.name,
        )
        self.assertEqual(
            serializer.data["departing_routes_count"],
            3,
        )
        self.assertEqual(
            serializer.data["arriving_routes_count"],
            2,
        )
        self.assertEqual(
            serializer.data["upcoming_departures_count"],
            4,
        )
        self.assertEqual(
            serializer.data["upcoming_arrivals_count"],
            5,
        )
        self.assertEqual(
            serializer.data["total_upcoming_flights"],
            9,
        )
        self.assertEqual(
            serializer.data["active_tickets_count"],
            20,
        )
        self.assertEqual(
            serializer.data["cancelled_tickets_count"],
            4,
        )
        self.assertEqual(
            serializer.data["total_tickets_count"],
            24,
        )


class AirplaneTypeSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_airplane_type_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = AirplaneTypeSerializer(
            self.airplane_type,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "name",
            },
        )

    def test_airplane_type_serializer_returns_data(
        self,
    ) -> None:
        serializer = AirplaneTypeSerializer(
            self.airplane_type,
        )

        self.assertEqual(
            serializer.data["name"],
            "Boeing 737",
        )

    def test_airplane_type_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = AirplaneTypeSerializer(
            data={
                "name": "Airbus A320",
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_airplane_type_serializer_rejects_duplicate_name(
        self,
    ) -> None:
        serializer = AirplaneTypeSerializer(
            data={
                "name": self.airplane_type.name,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )


class AirplaneSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_airplane_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = AirplaneSerializer(
            self.airplane,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "name",
                "rows",
                "seats_in_row",
                "airplane_type",
                "capacity",
            },
        )

    def test_airplane_serializer_returns_capacity(
        self,
    ) -> None:
        serializer = AirplaneSerializer(
            self.airplane,
        )

        self.assertEqual(
            serializer.data["capacity"],
            120,
        )

    def test_airplane_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = AirplaneSerializer(
            data={
                "name": "UR-002",
                "rows": 25,
                "seats_in_row": 6,
                "airplane_type": self.airplane_type.pk,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_airplane_serializer_capacity_is_read_only(
        self,
    ) -> None:
        serializer = AirplaneSerializer(
            data={
                "name": "UR-002",
                "rows": 25,
                "seats_in_row": 6,
                "airplane_type": self.airplane_type.pk,
                "capacity": 9999,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "capacity",
            serializer.validated_data,
        )

    def test_airplane_serializer_rejects_zero_rows(
        self,
    ) -> None:
        serializer = AirplaneSerializer(
            data={
                "name": "UR-002",
                "rows": 0,
                "seats_in_row": 6,
                "airplane_type": self.airplane_type.pk,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "rows",
            serializer.errors,
        )

    def test_airplane_serializer_rejects_zero_seats_in_row(
        self,
    ) -> None:
        serializer = AirplaneSerializer(
            data={
                "name": "UR-002",
                "rows": 20,
                "seats_in_row": 0,
                "airplane_type": self.airplane_type.pk,
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "seats_in_row",
            serializer.errors,
        )

    def test_airplane_serializer_rejects_invalid_airplane_type(
        self,
    ) -> None:
        serializer = AirplaneSerializer(
            data={
                "name": "UR-002",
                "rows": 20,
                "seats_in_row": 6,
                "airplane_type": uuid.uuid4(),
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "airplane_type",
            serializer.errors,
        )


class AirplaneListSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_airplane_list_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = AirplaneListSerializer(
            self.airplane,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "name",
                "rows",
                "seats_in_row",
                "airplane_type",
                "capacity",
                "image",
            },
        )

    def test_airplane_list_serializer_returns_type_name(
        self,
    ) -> None:
        serializer = AirplaneListSerializer(
            self.airplane,
        )

        self.assertEqual(
            serializer.data["airplane_type"],
            "Boeing 737",
        )

    def test_airplane_list_serializer_returns_capacity(
        self,
    ) -> None:
        serializer = AirplaneListSerializer(
            self.airplane,
        )

        self.assertEqual(
            serializer.data["capacity"],
            120,
        )


class AirplaneDetailSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_airplane_detail_serializer_returns_nested_type(
        self,
    ) -> None:
        serializer = AirplaneDetailSerializer(
            self.airplane,
        )

        self.assertEqual(
            serializer.data["airplane_type"],
            {
                "id": str(self.airplane_type.pk),
                "name": "Boeing 737",
            },
        )

    def test_airplane_detail_serializer_returns_image(
        self,
    ) -> None:
        serializer = AirplaneDetailSerializer(
            self.airplane,
        )

        self.assertIn(
            "image",
            serializer.data,
        )


class AirplaneUploadImageSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_upload_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = AirplaneUploadImageSerializer(
            self.airplane,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "image",
            },
        )

    def test_upload_serializer_id_is_read_only(
        self,
    ) -> None:
        serializer = AirplaneUploadImageSerializer(
            self.airplane,
            data={
                "id": uuid.uuid4(),
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "id",
            serializer.validated_data,
        )


class CrewSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_crew_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = CrewSerializer(
            self.crew,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "first_name",
                "last_name",
            },
        )

    def test_crew_serializer_returns_data(
        self,
    ) -> None:
        serializer = CrewSerializer(
            self.crew,
        )

        self.assertEqual(
            serializer.data["first_name"],
            "John",
        )
        self.assertEqual(
            serializer.data["last_name"],
            "Smith",
        )

    def test_crew_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = CrewSerializer(
            data={
                "first_name": "Anna",
                "last_name": "Brown",
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_crew_serializer_rejects_missing_first_name(
        self,
    ) -> None:
        serializer = CrewSerializer(
            data={
                "last_name": "Brown",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "first_name",
            serializer.errors,
        )

    def test_crew_serializer_rejects_missing_last_name(
        self,
    ) -> None:
        serializer = CrewSerializer(
            data={
                "first_name": "Anna",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "last_name",
            serializer.errors,
        )


class CrewListSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_crew_list_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = CrewListSerializer(
            self.crew,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "full_name",
                "photo",
            },
        )

    def test_crew_list_serializer_returns_full_name(
        self,
    ) -> None:
        serializer = CrewListSerializer(
            self.crew,
        )

        self.assertEqual(
            serializer.data["full_name"],
            "John Smith",
        )

    def test_crew_list_serializer_returns_null_photo(
        self,
    ) -> None:
        serializer = CrewListSerializer(
            self.crew,
        )

        self.assertIsNone(
            serializer.data["photo"],
        )


class CrewDetailSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_crew_detail_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = CrewDetailSerializer(
            self.crew,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "first_name",
                "last_name",
                "photo",
            },
        )

    def test_crew_detail_serializer_returns_data(
        self,
    ) -> None:
        serializer = CrewDetailSerializer(
            self.crew,
        )

        self.assertEqual(
            serializer.data["first_name"],
            "John",
        )
        self.assertEqual(
            serializer.data["last_name"],
            "Smith",
        )
        self.assertIsNone(
            serializer.data["photo"],
        )


class CrewUploadPhotoSerializerTests(
    BaseReferenceSerializerTestCase,
):
    def test_upload_serializer_returns_expected_fields(
        self,
    ) -> None:
        serializer = CrewUploadPhotoSerializer(
            self.crew,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "photo",
            },
        )

    def test_upload_serializer_id_is_read_only(
        self,
    ) -> None:
        serializer = CrewUploadPhotoSerializer(
            self.crew,
            data={
                "id": uuid.uuid4(),
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "id",
            serializer.validated_data,
        )
