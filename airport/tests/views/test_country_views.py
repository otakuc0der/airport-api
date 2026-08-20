import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Country
from airport.serializers import CountrySerializer


COUNTRY_URL = reverse("airport:country-list")


def country_detail_url(country_id: uuid.UUID) -> str:
    return reverse(
        "airport:country-detail",
        args=[country_id],
    )


class UnauthenticatedCountryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.country_1 = Country.objects.create(
            name="Ukraine",
        )
        cls.country_2 = Country.objects.create(
            name="Poland",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    def test_list_countries(self) -> None:
        response = self.client.get(
            path=COUNTRY_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

        countries = Country.objects.all()
        serializer = CountrySerializer(
            countries,
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_country(self) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CountrySerializer(
            self.country_1,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_create_country_unauthorized(self) -> None:
        response = self.client.post(
            path=COUNTRY_URL,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertFalse(
            Country.objects.filter(
                name="Germany",
            ).exists(),
        )

    def test_update_country_unauthorized(self) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.put(
            path=url,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.country_1.refresh_from_db()

        self.assertEqual(
            self.country_1.name,
            "Ukraine",
        )

    def test_partial_update_country_unauthorized(
        self,
    ) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.patch(
            path=url,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.country_1.refresh_from_db()

        self.assertEqual(
            self.country_1.name,
            "Ukraine",
        )

    def test_delete_country_unauthorized(
        self,
    ) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.delete(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertTrue(
            Country.objects.filter(
                pk=self.country_1.pk,
            ).exists(),
        )


class AuthenticatedCountryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )

        cls.country_1 = Country.objects.create(
            name="Ukraine",
        )
        cls.country_2 = Country.objects.create(
            name="Poland",
        )

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user,
        )

    def test_list_countries(self) -> None:
        response = self.client.get(
            path=COUNTRY_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        countries = Country.objects.all()
        serializer = CountrySerializer(
            countries,
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_country(self) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CountrySerializer(
            self.country_1,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_create_country_forbidden(self) -> None:
        response = self.client.post(
            path=COUNTRY_URL,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            Country.objects.filter(
                name="Germany",
            ).exists(),
        )

    def test_update_country_forbidden(self) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.put(
            path=url,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.country_1.refresh_from_db()

        self.assertEqual(
            self.country_1.name,
            "Ukraine",
        )

    def test_partial_update_country_forbidden(
        self,
    ) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.patch(
            path=url,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.country_1.refresh_from_db()

        self.assertEqual(
            self.country_1.name,
            "Ukraine",
        )

    def test_delete_country_forbidden(self) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.delete(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Country.objects.filter(
                pk=self.country_1.pk,
            ).exists(),
        )


class AdminCountryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
        )

        cls.country_1 = Country.objects.create(
            name="Ukraine",
        )
        cls.country_2 = Country.objects.create(
            name="Poland",
        )

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.admin,
        )

    def test_list_countries(self) -> None:
        response = self.client.get(
            path=COUNTRY_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        countries = Country.objects.all()
        serializer = CountrySerializer(
            countries,
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_country(self) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CountrySerializer(
            self.country_1,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_create_country(self) -> None:
        payload = {
            "name": "Germany",
        }

        response = self.client.post(
            path=COUNTRY_URL,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        country = Country.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            country.name,
            payload["name"],
        )

    def test_create_country_with_duplicate_name(
        self,
    ) -> None:
        response = self.client.post(
            path=COUNTRY_URL,
            data={
                "name": self.country_1.name,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Country.objects.filter(
                name=self.country_1.name,
            ).count(),
            1,
        )

    def test_update_country(self) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.put(
            path=url,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.country_1.refresh_from_db()

        self.assertEqual(
            self.country_1.name,
            "Germany",
        )

    def test_partial_update_country(self) -> None:
        url = country_detail_url(
            self.country_1.pk,
        )

        response = self.client.patch(
            path=url,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.country_1.refresh_from_db()

        self.assertEqual(
            self.country_1.name,
            "Germany",
        )

    def test_delete_country(self) -> None:
        country_id = self.country_1.pk

        url = country_detail_url(
            country_id,
        )

        response = self.client.delete(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Country.objects.filter(
                pk=country_id,
            ).exists(),
        )

    def test_retrieve_nonexistent_country(
        self,
    ) -> None:
        url = country_detail_url(
            uuid.uuid4(),
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_nonexistent_country(
        self,
    ) -> None:
        url = country_detail_url(
            uuid.uuid4(),
        )

        response = self.client.put(
            path=url,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_partial_update_nonexistent_country(
        self,
    ) -> None:
        url = country_detail_url(
            uuid.uuid4(),
        )

        response = self.client.patch(
            path=url,
            data={
                "name": "Germany",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_nonexistent_country(
        self,
    ) -> None:
        url = country_detail_url(
            uuid.uuid4(),
        )

        response = self.client.delete(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
