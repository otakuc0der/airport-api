import os
import tempfile
import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airplane, AirplaneType
from airport.serializers import (
    AirplaneDetailSerializer,
    AirplaneListSerializer,
)


AIRPLANE_URL = reverse("airport:airplane-list")


def airplane_detail_url(airplane_id: uuid.UUID) -> str:
    return reverse(
        "airport:airplane-detail",
        args=[airplane_id],
    )


def airplane_image_upload_url(
    airplane_id: uuid.UUID,
) -> str:
    return reverse(
        "airport:airplane-upload-airplane-image",
        args=[airplane_id],
    )


class BaseAirplaneApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.boeing_type = AirplaneType.objects.create(
            name="Boeing 737",
        )
        cls.airbus_type = AirplaneType.objects.create(
            name="Airbus A320",
        )

        cls.boeing = Airplane.objects.create(
            name="UR-BOEING",
            rows=20,
            seats_in_row=6,
            airplane_type=cls.boeing_type,
        )

        cls.airbus = Airplane.objects.create(
            name="UR-AIRBUS",
            rows=25,
            seats_in_row=6,
            airplane_type=cls.airbus_type,
        )

        cls.boeing_second = Airplane.objects.create(
            name="UR-BOEING-002",
            rows=30,
            seats_in_row=6,
            airplane_type=cls.boeing_type,
        )

    def setUp(self) -> None:
        cache.clear()


class UnauthenticatedAirplaneApiTests(
    BaseAirplaneApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_list_airplanes(self) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        airplanes = Airplane.objects.select_related(
            "airplane_type",
        )

        serializer = AirplaneListSerializer(
            airplanes,
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

    def test_retrieve_airplane(self) -> None:
        response = self.client.get(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = AirplaneDetailSerializer(
            self.boeing,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_retrieve_nonexistent_airplane(
        self,
    ) -> None:
        response = self.client.get(
            path=airplane_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_filter_airplanes_by_airplane_type(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            airplane["id"]
            for airplane in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.boeing.pk),
                str(self.boeing_second.pk),
            },
        )

    def test_filter_airplanes_by_airplane_type_name(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "airplane_type_name": "boeing",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            airplane["id"]
            for airplane in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.boeing.pk),
                str(self.boeing_second.pk),
            },
        )

    def test_filter_airplanes_by_airplane_type_name_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "airplane_type_name": "BOEING",
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

    def test_filter_airplanes_by_name(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "name": "AIRBUS",
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
            str(self.airbus.pk),
        )

    def test_filter_airplanes_by_name_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "name": "ur-airbus",
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

    def test_filter_airplanes_by_multiple_filters(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "airplane_type": self.boeing_type.pk,
                "name": "002",
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
            str(self.boeing_second.pk),
        )

    def test_filter_airplanes_by_nonexistent_airplane_type_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "airplane_type": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "airplane_type",
            response.data,
        )

    def test_filter_airplanes_by_invalid_airplane_type_id_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "airplane_type": "invalid-id",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "airplane_type",
            response.data,
        )

    def test_filter_airplanes_returns_empty_results_when_not_found(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
            data={
                "name": "NONEXISTENT",
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

    def test_create_airplane_unauthorized(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": "UR-NEW",
                "rows": 20,
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertFalse(
            Airplane.objects.filter(
                name="UR-NEW",
            ).exists(),
        )

    def test_update_airplane_unauthorized(
        self,
    ) -> None:
        response = self.client.put(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "UR-UPDATED",
                "rows": 22,
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "UR-BOEING",
        )

    def test_partial_update_airplane_unauthorized(
        self,
    ) -> None:
        response = self.client.patch(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "UR-UPDATED",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_delete_airplane_unauthorized(
        self,
    ) -> None:
        airplane_id = self.boeing.pk

        response = self.client.delete(
            path=airplane_detail_url(
                airplane_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertTrue(
            Airplane.objects.filter(
                pk=airplane_id,
            ).exists(),
        )


class AuthenticatedAirplaneApiTests(
    BaseAirplaneApiTestCase,
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

    def test_list_airplanes(self) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        airplanes = Airplane.objects.select_related(
            "airplane_type",
        )

        serializer = AirplaneListSerializer(
            airplanes,
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_airplane(self) -> None:
        response = self.client.get(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_create_airplane_forbidden(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": "UR-NEW",
                "rows": 20,
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            Airplane.objects.filter(
                name="UR-NEW",
            ).exists(),
        )

    def test_update_airplane_forbidden(
        self,
    ) -> None:
        response = self.client.put(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "UR-UPDATED",
                "rows": 22,
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_partial_update_airplane_forbidden(
        self,
    ) -> None:
        response = self.client.patch(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "UR-UPDATED",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_airplane_forbidden(
        self,
    ) -> None:
        response = self.client.delete(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class AdminAirplaneApiTests(
    BaseAirplaneApiTestCase,
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

    def test_create_airplane(
        self,
    ) -> None:
        payload = {
            "name": "UR-NEW",
            "rows": 20,
            "seats_in_row": 6,
            "airplane_type": self.boeing_type.pk,
        }

        response = self.client.post(
            path=AIRPLANE_URL,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        airplane = Airplane.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            airplane.name,
            payload["name"],
        )

        self.assertEqual(
            airplane.rows,
            payload["rows"],
        )

        self.assertEqual(
            airplane.seats_in_row,
            payload["seats_in_row"],
        )

        self.assertEqual(
            airplane.airplane_type,
            self.boeing_type,
        )

        self.assertEqual(
            response.data["capacity"],
            120,
        )

    def test_create_airplane_with_duplicate_name(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": self.boeing.name,
                "rows": 20,
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_airplane_with_invalid_airplane_type(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": "UR-NEW",
                "rows": 20,
                "seats_in_row": 6,
                "airplane_type": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "airplane_type",
            response.data,
        )

    def test_create_airplane_without_name(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "rows": 20,
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "name",
            response.data,
        )

    def test_create_airplane_without_rows(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": "UR-NEW",
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "rows",
            response.data,
        )

    def test_create_airplane_without_seats_in_row(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": "UR-NEW",
                "rows": 20,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "seats_in_row",
            response.data,
        )

    def test_create_airplane_without_airplane_type(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": "UR-NEW",
                "rows": 20,
                "seats_in_row": 6,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "airplane_type",
            response.data,
        )

    def test_create_airplane_rejects_zero_rows(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": "UR-NEW",
                "rows": 0,
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "rows",
            response.data,
        )

    def test_create_airplane_rejects_zero_seats_in_row(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_URL,
            data={
                "name": "UR-NEW",
                "rows": 20,
                "seats_in_row": 0,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "seats_in_row",
            response.data,
        )

    def test_update_airplane(
        self,
    ) -> None:
        response = self.client.put(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "UR-UPDATED",
                "rows": 30,
                "seats_in_row": 8,
                "airplane_type": self.airbus_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "UR-UPDATED",
        )

        self.assertEqual(
            self.boeing.rows,
            30,
        )

        self.assertEqual(
            self.boeing.seats_in_row,
            8,
        )

        self.assertEqual(
            self.boeing.airplane_type,
            self.airbus_type,
        )

        self.assertEqual(
            self.boeing.capacity,
            240,
        )

    def test_partial_update_airplane(
        self,
    ) -> None:
        original_type = self.boeing.airplane_type
        original_rows = self.boeing.rows

        response = self.client.patch(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "UR-UPDATED",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "UR-UPDATED",
        )

        self.assertEqual(
            self.boeing.rows,
            original_rows,
        )

        self.assertEqual(
            self.boeing.airplane_type,
            original_type,
        )

    def test_delete_airplane(
        self,
    ) -> None:
        airplane = Airplane.objects.create(
            name="UR-DELETE",
            rows=15,
            seats_in_row=4,
            airplane_type=self.boeing_type,
        )

        airplane_id = airplane.pk

        response = self.client.delete(
            path=airplane_detail_url(
                airplane_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Airplane.objects.filter(
                pk=airplane_id,
            ).exists(),
        )

    def test_retrieve_nonexistent_airplane(
        self,
    ) -> None:
        response = self.client.get(
            path=airplane_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_nonexistent_airplane(
        self,
    ) -> None:
        response = self.client.put(
            path=airplane_detail_url(
                uuid.uuid4(),
            ),
            data={
                "name": "UR-NEW",
                "rows": 20,
                "seats_in_row": 6,
                "airplane_type": self.boeing_type.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_partial_update_nonexistent_airplane(
        self,
    ) -> None:
        response = self.client.patch(
            path=airplane_detail_url(
                uuid.uuid4(),
            ),
            data={
                "name": "UR-NEW",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_nonexistent_airplane(
        self,
    ) -> None:
        response = self.client.delete(
            path=airplane_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class AirplaneImageUploadTests(
    BaseAirplaneApiTestCase,
):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
        )

        cls.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def tearDown(self) -> None:
        self.boeing.refresh_from_db()

        if self.boeing.image:
            self.boeing.image.delete(
                save=False,
            )

    def test_admin_can_upload_airplane_image(
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
                path=airplane_image_upload_url(
                    self.boeing.pk,
                ),
                data={
                    "image": image_file,
                },
                format="multipart",
            )

        self.boeing.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "image",
            response.data,
        )

        self.assertTrue(
            bool(self.boeing.image),
        )

        self.assertTrue(
            os.path.exists(
                self.boeing.image.path,
            ),
        )

    def test_admin_cannot_upload_invalid_airplane_image(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            path=airplane_image_upload_url(
                self.boeing.pk,
            ),
            data={
                "image": "not-an-image",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_authenticated_user_cannot_upload_airplane_image(
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
                path=airplane_image_upload_url(
                    self.boeing.pk,
                ),
                data={
                    "image": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unauthenticated_user_cannot_upload_airplane_image(
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
                path=airplane_image_upload_url(
                    self.boeing.pk,
                ),
                data={
                    "image": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_upload_image_to_nonexistent_airplane_returns_not_found(
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
                path=airplane_image_upload_url(
                    uuid.uuid4(),
                ),
                data={
                    "image": image_file,
                },
                format="multipart",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_airplane_list_contains_image_field(
        self,
    ) -> None:
        response = self.client.get(
            path=AIRPLANE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "image",
            response.data["results"][0],
        )

    def test_airplane_detail_contains_image_field(
        self,
    ) -> None:
        response = self.client.get(
            path=airplane_detail_url(
                self.boeing.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "image",
            response.data,
        )
