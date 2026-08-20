import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer


AIRPLANE_TYPE_URL = reverse("airport:airplane-type-list")


def airplane_type_detail_url(
    airplane_type_id: uuid.UUID,
) -> str:
    return reverse(
        "airport:airplane-type-detail",
        args=[airplane_type_id],
    )


class BaseAirplaneTypeApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.boeing = AirplaneType.objects.create(
            name="Boeing 737",
        )

        cls.airbus = AirplaneType.objects.create(
            name="Airbus A320",
        )

    def setUp(self) -> None:
        cache.clear()


class UnauthenticatedAirplaneTypeApiTests(
    BaseAirplaneTypeApiTestCase,
):
    def setUp(self) -> None:
        super().setUp()

        self.client = APIClient()

    def test_list_airplane_types(self) -> None:
        response = self.client.get(
            path=AIRPLANE_TYPE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        airplane_types = AirplaneType.objects.all()

        serializer = AirplaneTypeSerializer(
            airplane_types,
            many=True,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_airplane_type(self) -> None:
        response = self.client.get(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = AirplaneTypeSerializer(
            self.boeing,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_retrieve_nonexistent_airplane_type(
        self,
    ) -> None:
        response = self.client.get(
            path=airplane_type_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_create_airplane_type_unauthorized(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_TYPE_URL,
            data={
                "name": "Embraer E190",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertFalse(
            AirplaneType.objects.filter(
                name="Embraer E190",
            ).exists(),
        )

    def test_update_airplane_type_unauthorized(
        self,
    ) -> None:
        response = self.client.put(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "Updated Boeing",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "Boeing 737",
        )

    def test_partial_update_airplane_type_unauthorized(
        self,
    ) -> None:
        response = self.client.patch(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "Updated Boeing",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "Boeing 737",
        )

    def test_delete_airplane_type_unauthorized(
        self,
    ) -> None:
        airplane_type_id = self.boeing.pk

        response = self.client.delete(
            path=airplane_type_detail_url(
                airplane_type_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertTrue(
            AirplaneType.objects.filter(
                pk=airplane_type_id,
            ).exists(),
        )


class AuthenticatedAirplaneTypeApiTests(
    BaseAirplaneTypeApiTestCase,
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

    def test_list_airplane_types(self) -> None:
        response = self.client.get(
            path=AIRPLANE_TYPE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        airplane_types = AirplaneType.objects.all()

        serializer = AirplaneTypeSerializer(
            airplane_types,
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_airplane_type(self) -> None:
        response = self.client.get(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = AirplaneTypeSerializer(
            self.boeing,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_create_airplane_type_forbidden(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_TYPE_URL,
            data={
                "name": "Embraer E190",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            AirplaneType.objects.filter(
                name="Embraer E190",
            ).exists(),
        )

    def test_update_airplane_type_forbidden(
        self,
    ) -> None:
        response = self.client.put(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "Updated Boeing",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "Boeing 737",
        )

    def test_partial_update_airplane_type_forbidden(
        self,
    ) -> None:
        response = self.client.patch(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "Updated Boeing",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "Boeing 737",
        )

    def test_delete_airplane_type_forbidden(
        self,
    ) -> None:
        airplane_type_id = self.boeing.pk

        response = self.client.delete(
            path=airplane_type_detail_url(
                airplane_type_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            AirplaneType.objects.filter(
                pk=airplane_type_id,
            ).exists(),
        )


class AdminAirplaneTypeApiTests(
    BaseAirplaneTypeApiTestCase,
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

    def test_list_airplane_types(self) -> None:
        response = self.client.get(
            path=AIRPLANE_TYPE_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        airplane_types = AirplaneType.objects.all()

        serializer = AirplaneTypeSerializer(
            airplane_types,
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_airplane_type(self) -> None:
        response = self.client.get(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = AirplaneTypeSerializer(
            self.boeing,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_create_airplane_type(self) -> None:
        payload = {
            "name": "Embraer E190",
        }

        response = self.client.post(
            path=AIRPLANE_TYPE_URL,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        airplane_type = AirplaneType.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            airplane_type.name,
            payload["name"],
        )

    def test_create_airplane_type_with_duplicate_name(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_TYPE_URL,
            data={
                "name": self.boeing.name,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            AirplaneType.objects.filter(
                name=self.boeing.name,
            ).count(),
            1,
        )

    def test_create_airplane_type_without_name(
        self,
    ) -> None:
        response = self.client.post(
            path=AIRPLANE_TYPE_URL,
            data={},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "name",
            response.data,
        )

    def test_update_airplane_type(self) -> None:
        response = self.client.put(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "Boeing 777",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "Boeing 777",
        )

    def test_update_airplane_type_rejects_duplicate_name(
        self,
    ) -> None:
        response = self.client.put(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": self.airbus.name,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "Boeing 737",
        )

    def test_partial_update_airplane_type(
        self,
    ) -> None:
        response = self.client.patch(
            path=airplane_type_detail_url(
                self.boeing.pk,
            ),
            data={
                "name": "Boeing 777",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.boeing.refresh_from_db()

        self.assertEqual(
            self.boeing.name,
            "Boeing 777",
        )

    def test_delete_airplane_type(self) -> None:
        airplane_type = AirplaneType.objects.create(
            name="Embraer E190",
        )

        airplane_type_id = airplane_type.pk

        response = self.client.delete(
            path=airplane_type_detail_url(
                airplane_type_id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            AirplaneType.objects.filter(
                pk=airplane_type_id,
            ).exists(),
        )

    def test_retrieve_nonexistent_airplane_type(
        self,
    ) -> None:
        response = self.client.get(
            path=airplane_type_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_nonexistent_airplane_type(
        self,
    ) -> None:
        response = self.client.put(
            path=airplane_type_detail_url(
                uuid.uuid4(),
            ),
            data={
                "name": "Embraer E190",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_partial_update_nonexistent_airplane_type(
        self,
    ) -> None:
        response = self.client.patch(
            path=airplane_type_detail_url(
                uuid.uuid4(),
            ),
            data={
                "name": "Embraer E190",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_nonexistent_airplane_type(
        self,
    ) -> None:
        response = self.client.delete(
            path=airplane_type_detail_url(
                uuid.uuid4(),
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
