import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import City, Country
from airport.serializers import (
    CityDetailSerializer,
    CityListSerializer,
)


CITY_URL = reverse("airport:city-list")


def city_detail_url(city_id: uuid.UUID) -> str:
    return reverse(
        "airport:city-detail",
        args=[city_id],
    )


class UnauthenticatedCityApiTests(TestCase):
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
        cls.lviv = City.objects.create(
            name="Lviv",
            country=cls.ukraine,
        )
        cls.warsaw = City.objects.create(
            name="Warsaw",
            country=cls.poland,
        )

    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()

    def test_list_cities(self) -> None:
        response = self.client.get(
            path=CITY_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        cities = City.objects.select_related(
            "country",
        )

        serializer = CityListSerializer(
            cities,
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

    def test_retrieve_city(self) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CityDetailSerializer(
            self.kyiv,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_filter_cities_by_country(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country": self.ukraine.pk,
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

        returned_ids = {
            city["id"]
            for city in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.kyiv.pk),
                str(self.lviv.pk),
            },
        )

    def test_filter_cities_by_country_name(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country_name": "ukr",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            city["id"]
            for city in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {
                str(self.kyiv.pk),
                str(self.lviv.pk),
            },
        )

    def test_filter_cities_by_country_name_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country_name": "UKRAINE",
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

    def test_filter_cities_by_name(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "name": "Ky",
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
            str(self.kyiv.pk),
        )

    def test_filter_cities_by_name_is_case_insensitive(
        self,
    ) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "name": "kYiV",
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
            str(self.kyiv.pk),
        )

    def test_filter_cities_by_country_and_name(
        self,
    ) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country": self.ukraine.pk,
                "name": "Lviv",
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
            str(self.lviv.pk),
        )

    def test_filter_cities_by_nonexistent_country_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "country",
            response.data,
        )

    def test_filter_cities_by_invalid_country_id_returns_bad_request(
        self,
    ) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country": "invalid-id",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "country",
            response.data,
        )

    def test_filter_cities_returns_empty_result_when_name_not_found(
        self,
    ) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "name": "Berlin",
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

    def test_retrieve_nonexistent_city(self) -> None:
        url = city_detail_url(
            uuid.uuid4(),
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_create_city_unauthorized(self) -> None:
        response = self.client.post(
            path=CITY_URL,
            data={
                "name": "Odesa",
                "country": self.ukraine.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertFalse(
            City.objects.filter(
                name="Odesa",
                country=self.ukraine,
            ).exists(),
        )

    def test_update_city_unauthorized(self) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.put(
            path=url,
            data={
                "name": "Kyiv Updated",
                "country": self.ukraine.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.kyiv.refresh_from_db()

        self.assertEqual(
            self.kyiv.name,
            "Kyiv",
        )

    def test_partial_update_city_unauthorized(
        self,
    ) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.patch(
            path=url,
            data={
                "name": "Kyiv Updated",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.kyiv.refresh_from_db()

        self.assertEqual(
            self.kyiv.name,
            "Kyiv",
        )

    def test_delete_city_unauthorized(self) -> None:
        city_id = self.kyiv.pk

        url = city_detail_url(
            city_id,
        )

        response = self.client.delete(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertTrue(
            City.objects.filter(
                pk=city_id,
            ).exists(),
        )


class AuthenticatedCityApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )

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
        cls.lviv = City.objects.create(
            name="Lviv",
            country=cls.ukraine,
        )
        cls.warsaw = City.objects.create(
            name="Warsaw",
            country=cls.poland,
        )

    def setUp(self) -> None:
        self.client = APIClient()

        self.client.force_authenticate(
            user=self.user,
        )

    def test_list_cities(self) -> None:
        response = self.client.get(
            path=CITY_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        cities = City.objects.select_related(
            "country",
        )

        serializer = CityListSerializer(
            cities,
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_city(self) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CityDetailSerializer(
            self.kyiv,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_filter_cities_by_country(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country": self.ukraine.pk,
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

    def test_filter_cities_by_country_name(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country_name": "Pol",
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
            str(self.warsaw.pk),
        )

    def test_filter_cities_by_name(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "name": "Lviv",
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
            str(self.lviv.pk),
        )

    def test_create_city_forbidden(self) -> None:
        response = self.client.post(
            path=CITY_URL,
            data={
                "name": "Odesa",
                "country": self.ukraine.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            City.objects.filter(
                name="Odesa",
                country=self.ukraine,
            ).exists(),
        )

    def test_update_city_forbidden(self) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.put(
            path=url,
            data={
                "name": "Kyiv Updated",
                "country": self.ukraine.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.kyiv.refresh_from_db()

        self.assertEqual(
            self.kyiv.name,
            "Kyiv",
        )

    def test_partial_update_city_forbidden(
        self,
    ) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.patch(
            path=url,
            data={
                "name": "Kyiv Updated",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.kyiv.refresh_from_db()

        self.assertEqual(
            self.kyiv.name,
            "Kyiv",
        )

    def test_delete_city_forbidden(self) -> None:
        city_id = self.kyiv.pk

        url = city_detail_url(
            city_id,
        )

        response = self.client.delete(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            City.objects.filter(
                pk=city_id,
            ).exists(),
        )


class AdminCityApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
        )

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
        cls.lviv = City.objects.create(
            name="Lviv",
            country=cls.ukraine,
        )
        cls.warsaw = City.objects.create(
            name="Warsaw",
            country=cls.poland,
        )

    def setUp(self) -> None:
        self.client = APIClient()

        self.client.force_authenticate(
            user=self.admin,
        )

    def test_list_cities(self) -> None:
        response = self.client.get(
            path=CITY_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        cities = City.objects.select_related(
            "country",
        )

        serializer = CityListSerializer(
            cities,
            many=True,
        )

        self.assertEqual(
            response.data["results"],
            serializer.data,
        )

    def test_retrieve_city(self) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        serializer = CityDetailSerializer(
            self.kyiv,
        )

        self.assertEqual(
            response.data,
            serializer.data,
        )

    def test_create_city(self) -> None:
        payload = {
            "name": "Odesa",
            "country": self.ukraine.pk,
        }

        response = self.client.post(
            path=CITY_URL,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        city = City.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            city.name,
            payload["name"],
        )

        self.assertEqual(
            city.country,
            self.ukraine,
        )

    def test_create_city_with_duplicate_name_in_same_country(
        self,
    ) -> None:
        response = self.client.post(
            path=CITY_URL,
            data={
                "name": self.kyiv.name,
                "country": self.ukraine.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_city_with_same_name_in_different_country(
        self,
    ) -> None:
        response = self.client.post(
            path=CITY_URL,
            data={
                "name": self.kyiv.name,
                "country": self.poland.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            City.objects.filter(
                name=self.kyiv.name,
                country=self.poland,
            ).exists(),
        )

    def test_create_city_with_invalid_country_id(
        self,
    ) -> None:
        response = self.client.post(
            path=CITY_URL,
            data={
                "name": "Odesa",
                "country": uuid.uuid4(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "country",
            response.data,
        )

    def test_create_city_without_country(
        self,
    ) -> None:
        response = self.client.post(
            path=CITY_URL,
            data={
                "name": "Odesa",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "country",
            response.data,
        )

    def test_update_city(self) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        payload = {
            "name": "Kyiv Updated",
            "country": self.poland.pk,
        }

        response = self.client.put(
            path=url,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.kyiv.refresh_from_db()

        self.assertEqual(
            self.kyiv.name,
            payload["name"],
        )

        self.assertEqual(
            self.kyiv.country,
            self.poland,
        )

    def test_update_city_rejects_duplicate_name_country_pair(
        self,
    ) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.put(
            path=url,
            data={
                "name": self.lviv.name,
                "country": self.ukraine.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.kyiv.refresh_from_db()

        self.assertEqual(
            self.kyiv.name,
            "Kyiv",
        )

    def test_partial_update_city_name(self) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.patch(
            path=url,
            data={
                "name": "Kyiv Updated",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.kyiv.refresh_from_db()

        self.assertEqual(
            self.kyiv.name,
            "Kyiv Updated",
        )

        self.assertEqual(
            self.kyiv.country,
            self.ukraine,
        )

    def test_partial_update_city_country(self) -> None:
        url = city_detail_url(
            self.kyiv.pk,
        )

        response = self.client.patch(
            path=url,
            data={
                "country": self.poland.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.kyiv.refresh_from_db()

        self.assertEqual(
            self.kyiv.name,
            "Kyiv",
        )

        self.assertEqual(
            self.kyiv.country,
            self.poland,
        )

    def test_delete_city(self) -> None:
        city = City.objects.create(
            name="Odesa",
            country=self.ukraine,
        )

        city_id = city.pk

        url = city_detail_url(
            city_id,
        )

        response = self.client.delete(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            City.objects.filter(
                pk=city_id,
            ).exists(),
        )

    def test_retrieve_nonexistent_city(self) -> None:
        url = city_detail_url(
            uuid.uuid4(),
        )

        response = self.client.get(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_nonexistent_city(self) -> None:
        url = city_detail_url(
            uuid.uuid4(),
        )

        response = self.client.put(
            path=url,
            data={
                "name": "Odesa",
                "country": self.ukraine.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_partial_update_nonexistent_city(
        self,
    ) -> None:
        url = city_detail_url(
            uuid.uuid4(),
        )

        response = self.client.patch(
            path=url,
            data={
                "name": "Odesa",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_nonexistent_city(
        self,
    ) -> None:
        url = city_detail_url(
            uuid.uuid4(),
        )

        response = self.client.delete(
            path=url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_filter_cities_by_country(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country": self.poland.pk,
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
            str(self.warsaw.pk),
        )

    def test_filter_cities_by_country_name(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "country_name": "pol",
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
            str(self.warsaw.pk),
        )

    def test_filter_cities_by_name(self) -> None:
        response = self.client.get(
            path=CITY_URL,
            data={
                "name": "War",
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
            str(self.warsaw.pk),
        )
