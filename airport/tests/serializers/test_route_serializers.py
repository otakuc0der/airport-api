from airport.models import Airport, City, Route
from airport.serializers import (
    RouteSerializer, RouteDetailSerializer, RouteListSerializer,
)
from airport.tests.validation.test_flight_validators import (
    BaseFlightScheduleTestCase,
)


class RouteSerializerTests(BaseFlightScheduleTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.odesa = City.objects.create(
            name="Odesa",
            country=cls.country,
        )

        cls.odesa_airport = Airport.objects.create(
            name="Odesa International Airport",
            closest_big_city=cls.odesa,
        )

    def test_route_serializer_accepts_valid_data(self) -> None:
        data = {
            "source": self.source_airport.pk,
            "destination": self.odesa_airport.pk,
            "distance": 500,
        }

        serializer = RouteSerializer(data=data)

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["source"],
            self.source_airport,
        )
        self.assertEqual(
            serializer.validated_data["destination"],
            self.odesa_airport,
        )
        self.assertEqual(
            serializer.validated_data["distance"],
            500,
        )

    def test_route_serializer_rejects_same_source_and_destination(
        self,
    ) -> None:
        data = {
            "source": self.source_airport.pk,
            "destination": self.source_airport.pk,
            "distance": 500,
        }

        serializer = RouteSerializer(data=data)

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "destination": [
                    "Destination must differ from source.",
                ],
            },
        )

    def test_route_serializer_creates_route(self) -> None:
        data = {
            "source": self.source_airport.pk,
            "destination": self.odesa_airport.pk,
            "distance": 650,
        }

        serializer = RouteSerializer(data=data)

        serializer.is_valid(raise_exception=True)

        route = serializer.save()

        self.assertIsInstance(
            route,
            Route,
        )
        self.assertEqual(
            route.source,
            self.source_airport,
        )
        self.assertEqual(
            route.destination,
            self.odesa_airport,
        )
        self.assertEqual(
            route.distance,
            650,
        )
        self.assertTrue(
            Route.objects.filter(pk=route.pk).exists(),
        )

    def test_route_serializer_partial_update_uses_existing_source(
        self,
    ) -> None:
        serializer = RouteSerializer(
            self.route,
            data={
                "destination": self.odesa_airport.pk,
            },
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        route = serializer.save()

        self.assertEqual(
            route.source,
            self.source_airport,
        )
        self.assertEqual(
            route.destination,
            self.odesa_airport,
        )

    def test_route_serializer_partial_update_uses_existing_destination(
        self,
    ) -> None:
        serializer = RouteSerializer(
            self.route,
            data={
                "source": self.odesa_airport.pk,
            },
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        route = serializer.save()

        self.assertEqual(
            route.source,
            self.odesa_airport,
        )
        self.assertEqual(
            route.destination,
            self.destination_airport,
        )

    def test_route_serializer_rejects_invalid_partial_update_destination(
        self,
    ) -> None:
        serializer = RouteSerializer(
            self.route,
            data={
                "destination": self.source_airport.pk,
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "destination": [
                    "Destination must differ from source.",
                ],
            },
        )

    def test_route_serializer_rejects_invalid_partial_update_source(
        self,
    ) -> None:
        serializer = RouteSerializer(
            self.route,
            data={
                "source": self.destination_airport.pk,
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())

        self.assertEqual(
            serializer.errors,
            {
                "destination": [
                    "Destination must differ from source.",
                ],
            },
        )

    def test_route_serializer_updates_route(self) -> None:
        serializer = RouteSerializer(
            self.route,
            data={
                "source": self.source_airport.pk,
                "destination": self.odesa_airport.pk,
                "distance": 700,
            },
        )

        serializer.is_valid(raise_exception=True)

        route = serializer.save()

        self.assertEqual(
            route.destination,
            self.odesa_airport,
        )
        self.assertEqual(
            route.distance,
            700,
        )


class RouteRepresentationSerializerTests(
    BaseFlightScheduleTestCase,
):
    def test_route_list_serializer_returns_expected_data(
        self,
    ) -> None:
        serializer = RouteListSerializer(
            self.route,
        )

        self.assertEqual(
            serializer.data,
            {
                "id": str(self.route.id),
                "source_city": self.kyiv.name,
                "destination_city": self.lviv.name,
                "source_airport": self.source_airport.name,
                "destination_airport": self.destination_airport.name,
                "distance": self.route.distance,
            },
        )

    def test_route_detail_serializer_returns_nested_airports(
        self,
    ) -> None:
        serializer = RouteDetailSerializer(
            self.route,
        )

        data = serializer.data

        self.assertEqual(
            data["id"],
            str(self.route.id),
        )

        self.assertEqual(
            data["distance"],
            self.route.distance,
        )

        self.assertEqual(
            data["source"]["id"],
            str(self.source_airport.id),
        )
        self.assertEqual(
            data["source"]["name"],
            self.source_airport.name,
        )

        self.assertEqual(
            data["source"]["closest_big_city"]["id"],
            str(self.kyiv.id),
        )
        self.assertEqual(
            data["source"]["closest_big_city"]["name"],
            self.kyiv.name,
        )

        self.assertEqual(
            data["source"]["closest_big_city"]["country"]["id"],
            str(self.country.id),
        )
        self.assertEqual(
            data["source"]["closest_big_city"]["country"]["name"],
            self.country.name,
        )

        self.assertEqual(
            data["destination"]["id"],
            str(self.destination_airport.id),
        )
        self.assertEqual(
            data["destination"]["name"],
            self.destination_airport.name,
        )

        self.assertEqual(
            data["destination"]["closest_big_city"]["id"],
            str(self.lviv.id),
        )
        self.assertEqual(
            data["destination"]["closest_big_city"]["name"],
            self.lviv.name,
        )
