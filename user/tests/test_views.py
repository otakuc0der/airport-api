from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
TOKEN_REFRESH_URL = reverse("user:token_refresh")
TOKEN_VERIFY_URL = reverse("user:token_verify")
ME_URL = reverse("user:manage")


class CreateUserApiTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()

    def test_create_user(self) -> None:
        payload = {
            "email": "test@example.com",
            "password": "password123",
        }

        response = self.client.post(
            path=CREATE_USER_URL,
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = get_user_model().objects.get(
            email=payload["email"],
        )

        self.assertTrue(
            user.check_password(
                payload["password"],
            ),
        )

        self.assertNotIn(
            "password",
            response.data,
        )

    def test_create_user_rejects_short_password(
        self,
    ) -> None:
        response = self.client.post(
            path=CREATE_USER_URL,
            data={
                "email": "test@example.com",
                "password": "1234",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "password",
            response.data,
        )

    def test_create_user_rejects_duplicate_email(
        self,
    ) -> None:
        get_user_model().objects.create_user(
            email="test@example.com",
            password="password123",
        )

        response = self.client.post(
            path=CREATE_USER_URL,
            data={
                "email": "test@example.com",
                "password": "anotherpassword",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_user_cannot_set_is_staff(
        self,
    ) -> None:
        response = self.client.post(
            path=CREATE_USER_URL,
            data={
                "email": "test@example.com",
                "password": "password123",
                "is_staff": True,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = get_user_model().objects.get(
            email="test@example.com",
        )

        self.assertFalse(
            user.is_staff,
        )


class ManageUserApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="password123",
        )

    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()

    def test_manage_user_requires_authentication(
        self,
    ) -> None:
        response = self.client.get(
            path=ME_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_retrieve_authenticated_user(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            path=ME_URL,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            self.user.email,
        )

        self.assertEqual(
            response.data["id"],
            self.user.pk,
        )

        self.assertNotIn(
            "password",
            response.data,
        )

    def test_update_authenticated_user(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.put(
            path=ME_URL,
            data={
                "email": "update@example.com",
                "password": "newpassword123",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.email,
            "update@example.com",
        )

        self.assertTrue(
            self.user.check_password(
                "newpassword123",
            ),
        )

    def test_partial_update_authenticated_user(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            path=ME_URL,
            data={
                "email": "patch@example.com",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.email,
            "patch@example.com",
        )

    def test_user_cannot_make_self_staff(
        self,
    ) -> None:
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            path=ME_URL,
            data={
                "is_staff": True,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertFalse(
            self.user.is_staff,
        )


class TokenApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.email = "token@example.com"
        cls.password = "password123"

        cls.user = get_user_model().objects.create_user(
            email=cls.email,
            password=cls.password,
        )

    def setUp(self) -> None:
        cache.clear()
        self.client = APIClient()

    def test_obtain_token_pair(
        self,
    ) -> None:
        response = self.client.post(
            path=TOKEN_URL,
            data={
                "email": self.email,
                "password": self.password,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_obtain_token_rejects_invalid_credentials(
        self,
    ) -> None:
        response = self.client.post(
            path=TOKEN_URL,
            data={
                "email": self.email,
                "password": "wrongpassword",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_refresh_token(
        self,
    ) -> None:
        token_response = self.client.post(
            path=TOKEN_URL,
            data={
                "email": self.email,
                "password": self.password,
            },
        )

        refresh = token_response.data["refresh"]

        response = self.client.post(
            path=TOKEN_REFRESH_URL,
            data={
                "refresh": refresh,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

    def test_verify_valid_access_token(
        self,
    ) -> None:
        token_response = self.client.post(
            path=TOKEN_URL,
            data={
                "email": self.email,
                "password": self.password,
            },
        )

        access = token_response.data["access"]

        response = self.client.post(
            path=TOKEN_VERIFY_URL,
            data={
                "token": access,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_verify_invalid_token(
        self,
    ) -> None:
        response = self.client.post(
            path=TOKEN_VERIFY_URL,
            data={
                "token": "invalidtoken",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
