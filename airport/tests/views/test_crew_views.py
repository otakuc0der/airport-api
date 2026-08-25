import os
import tempfile
import uuid
from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

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
from airport.serializers import (
    CrewDetailSerializer,
    CrewListSerializer,
)


CREW_URL = reverse("airport:crew-list")


def crew_detail_url(crew_id: uuid.UUID) -> str:
    return reverse(
        "airport:crew-detail",
        args=[crew_id],
    )


def crew_photo_upload_url(crew_id: uuid.UUID) -> str:
    return reverse(
        "airport:crew-upload-photo",
        args=[crew_id],
    )


class BaseCrewApiTestCase(TestCase):
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

        cls.route = Route.objects.create(
            source=cls.source_airport,
            destination=cls.destination_airport,
            distance=470,
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

        cls.crew_1 = Crew.objects.create(
            first_name="John",
            last_name="Smith",
        )
        cls.crew_2 = Crew.objects.create(
            first_name="Anna",
            last_name="Brown",
        )
        cls.crew_3 = Crew.objects.create(
            first_name="Michael",
            last_name="Smith",
        )

        cls.flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane,
            departure_time=datetime(
                2026,
                9,
                10,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            arrival_time=datetime(
                2026,
                9,
                10,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )
        cls.flight.crew.add(
            cls.crew_1,
            cls.crew_2,
        )

    def setUp(self) -> None:
        cache.clear()


class UnauthenticatedCrewApiTests(
    BaseCrewApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_list_crew(self) -> None:
        response = self.client.get(
            path=CREW_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        crew = Crew.objects.all()
        serializer = CrewListSerializer(
            crew,
            many=True,
        )

        self.assertEqual(
            response.data["count"],
            3,
        )
        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_crew_member(self) -> None:
        response = self.client.get(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CrewDetailSerializer(
            self.crew_1,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_retrieve_nonexistent_crew_member(
        self,
    ) -> None:
        response = self.client.get(
            path=crew_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_filter_crew_by_first_name(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "first_name": "John",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.crew_1.pk),
        )

    def test_filter_crew_by_first_name_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "first_name": "joHN",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_filter_crew_by_first_name_partial_match(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "first_name": "Mich",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.crew_3.pk),
        )

    def test_filter_crew_by_last_name(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "last_name": "Smith",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            member["id"]
            for member in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.crew_1.pk),
                str(self.crew_3.pk),
            },
        )

    def test_filter_crew_by_last_name_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "last_name": "sMiTh",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            2,
        )

    def test_filter_crew_by_first_and_last_name(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "first_name": "Michael",
                "last_name": "Smith",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            str(self.crew_3.pk),
        )

    def test_filter_crew_by_flight(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "flight": self.flight.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            member["id"]
            for member in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.crew_1.pk),
                str(self.crew_2.pk),
            },
        )

        self.assertNotIn(
            str(self.crew_3.pk),
            returned_ids,
        )

    def test_filter_crew_by_nonexistent_flight_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "flight": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "flight",
            response.data,
        )

    def test_filter_crew_by_invalid_flight_id_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "flight": "invalid-id",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "flight",
            response.data,
        )

    def test_filter_crew_returns_empty_results_when_not_found(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
            data={
                "first_name": "Nonexistent",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            0,
        )
        self.assertEqual(
            response.data["results"],
            [],
        )

    def test_create_crew_member_unauthorized(
        self,
    ) -> None:
        response = self.client.post(
            path=CREW_URL,
            data={
                "first_name": "Robert",
                "last_name": "Wilson",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertFalse(
            Crew.objects.filter(
                first_name="Robert",
                last_name="Wilson",
            ).exists(),
        )

    def test_update_crew_member_unauthorized(
        self,
    ) -> None:
        response = self.client.put(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
            data={
                "first_name": "Robert",
                "last_name": "Wilson",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.crew_1.refresh_from_db()

        self.assertEqual(
            self.crew_1.first_name,
            "John",
        )

    def test_partial_update_crew_member_unauthorized(
        self,
    ) -> None:
        response = self.client.patch(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
            data={
                "first_name": "Robert",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_delete_crew_member_unauthorized(
        self,
    ) -> None:
        crew_id = self.crew_1.pk

        response = self.client.delete(
            path=crew_detail_url(
                crew_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertTrue(
            Crew.objects.filter(
                pk=crew_id,
            ).exists(),
        )


class AuthenticatedCrewApiTests(
    BaseCrewApiTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )

    def setUp(self) -> None:
        super().setUp()

        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user,
        )

    def test_list_crew(self) -> None:
        response = self.client.get(
            path=CREW_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CrewListSerializer(
            Crew.objects.all(),
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_crew_member(self) -> None:
        response = self.client.get(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CrewDetailSerializer(
            self.crew_1,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_create_crew_member_forbidden(
        self,
    ) -> None:
        response = self.client.post(
            path=CREW_URL,
            data={
                "first_name": "Robert",
                "last_name": "Wilson",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            Crew.objects.filter(
                first_name="Robert",
                last_name="Wilson",
            ).exists(),
        )

    def test_update_crew_member_forbidden(
        self,
    ) -> None:
        response = self.client.put(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
            data={
                "first_name": "Robert",
                "last_name": "Wilson",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_partial_update_crew_member_forbidden(
        self,
    ) -> None:
        response = self.client.patch(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
            data={
                "first_name": "Robert",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_crew_member_forbidden(
        self,
    ) -> None:
        response = self.client.delete(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class AdminCrewApiTests(
    BaseCrewApiTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
        )

    def setUp(self) -> None:
        super().setUp()

        self.client = APIClient()
        self.client.force_authenticate(
            user=self.admin,
        )

    def test_create_crew_member(
        self,
    ) -> None:
        payload = {
            "first_name": "Robert",
            "last_name": "Wilson",
        }

        response = self.client.post(
            path=CREW_URL,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        crew_member = Crew.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            crew_member.first_name,
            payload["first_name"],
        )
        self.assertEqual(
            crew_member.last_name,
            payload["last_name"],
        )

    def test_create_crew_member_without_first_name(
        self,
    ) -> None:
        response = self.client.post(
            path=CREW_URL,
            data={
                "last_name": "Wilson",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "first_name",
            response.data,
        )

    def test_create_crew_member_without_last_name(
        self,
    ) -> None:
        response = self.client.post(
            path=CREW_URL,
            data={
                "first_name": "Robert",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "last_name",
            response.data,
        )

    def test_update_crew_member(
        self,
    ) -> None:
        response = self.client.put(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
            data={
                "first_name": "Robert",
                "last_name": "Wilson",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.crew_1.refresh_from_db()

        self.assertEqual(
            self.crew_1.first_name,
            "Robert",
        )
        self.assertEqual(
            self.crew_1.last_name,
            "Wilson",
        )

    def test_partial_update_crew_member_first_name(
        self,
    ) -> None:
        original_last_name = self.crew_1.last_name

        response = self.client.patch(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
            data={
                "first_name": "Robert",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.crew_1.refresh_from_db()

        self.assertEqual(
            self.crew_1.first_name,
            "Robert",
        )
        self.assertEqual(
            self.crew_1.last_name,
            original_last_name,
        )

    def test_partial_update_crew_member_last_name(
        self,
    ) -> None:
        original_first_name = self.crew_1.first_name

        response = self.client.patch(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
            data={
                "last_name": "Wilson",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.crew_1.refresh_from_db()

        self.assertEqual(
            self.crew_1.first_name,
            original_first_name,
        )
        self.assertEqual(
            self.crew_1.last_name,
            "Wilson",
        )

    def test_delete_crew_member(
        self,
    ) -> None:
        crew_member = Crew.objects.create(
            first_name="Delete",
            last_name="Me",
        )

        crew_id = crew_member.pk

        response = self.client.delete(
            path=crew_detail_url(
                crew_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Crew.objects.filter(
                pk=crew_id,
            ).exists(),
        )

    def test_retrieve_nonexistent_crew_member(
        self,
    ) -> None:
        response = self.client.get(
            path=crew_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_nonexistent_crew_member(
        self,
    ) -> None:
        response = self.client.put(
            path=crew_detail_url(
                uuid.uuid4(),
            ),
            data={
                "first_name": "Robert",
                "last_name": "Wilson",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_partial_update_nonexistent_crew_member(
        self,
    ) -> None:
        response = self.client.patch(
            path=crew_detail_url(
                uuid.uuid4(),
            ),
            data={
                "first_name": "Robert",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_nonexistent_crew_member(
        self,
    ) -> None:
        response = self.client.delete(
            path=crew_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class CrewPhotoUploadTests(
    BaseCrewApiTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.admin = get_user_model().objects.create_user(
            email="admin-photo@example.com",
            password="testpass123",
            is_staff=True,
        )

        cls.user = get_user_model().objects.create_user(
            email="user-photo@example.com",
            password="testpass123",
        )

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def tearDown(self) -> None:
        self.crew_1.refresh_from_db()

        if self.crew_1.photo:
            self.crew_1.photo.delete(
                save=False,
            )

    def test_admin_can_upload_crew_photo(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.admin,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
        ) as image_file:
            image = Image.new(
                "RGB",
                (10, 10),
            )
            image.save(
                image_file,
                format="JPEG",
            )
            image_file.seek(0)

            response = self.client.post(
                path=crew_photo_upload_url(
                    self.crew_1.pk,
                ),
                data={
                    "photo": image_file,
                },
                format="multipart",
            )

        self.crew_1.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "photo",
            response.data,
        )

        self.assertTrue(
            bool(self.crew_1.photo),
        )

        self.assertTrue(
            os.path.exists(
                self.crew_1.photo.path,
            ),
        )

    def test_admin_cannot_upload_invalid_crew_photo(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=crew_photo_upload_url(
                self.crew_1.pk,
            ),
            data={
                "photo": "not-an-image",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_authenticated_user_cannot_upload_crew_photo(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.user,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
        ) as image_file:
            image = Image.new(
                "RGB",
                (10, 10),
            )
            image.save(
                image_file,
                format="JPEG",
            )
            image_file.seek(0)

            response = self.client.post(
                path=crew_photo_upload_url(
                    self.crew_1.pk,
                ),
                data={
                    "photo": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unauthenticated_user_cannot_upload_crew_photo(
        self,
    ) -> None:
        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
        ) as image_file:
            image = Image.new(
                "RGB",
                (10, 10),
            )
            image.save(
                image_file,
                format="JPEG",
            )
            image_file.seek(0)

            response = self.client.post(
                path=crew_photo_upload_url(
                    self.crew_1.pk,
                ),
                data={
                    "photo": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_upload_photo_to_nonexistent_crew_member_returns_not_found(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.admin,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
        ) as image_file:
            image = Image.new(
                "RGB",
                (10, 10),
            )
            image.save(
                image_file,
                format="JPEG",
            )
            image_file.seek(0)

            response = self.client.post(
                path=crew_photo_upload_url(
                    uuid.uuid4(),
                ),
                data={
                    "photo": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_crew_list_contains_photo_field(
        self,
    ) -> None:
        response = self.client.get(
            path=CREW_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "photo",
            response.data["results"][0],
        )

    def test_crew_detail_contains_photo_field(
        self,
    ) -> None:
        response = self.client.get(
            path=crew_detail_url(
                self.crew_1.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "photo",
            response.data,
        )
