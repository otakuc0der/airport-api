from django.contrib.auth import get_user_model
from django.test import TestCase

from user.serializers import UserSerializer


class UserSerializerTests(TestCase):
    def test_user_serializer_accepts_valid_data(
        self,
    ) -> None:
        serializer = UserSerializer(
            data={
                "email": "test@example.com",
                "password": "password123",
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_user_serializer_creates_user_with_hashed_password(
        self,
    ) -> None:
        serializer = UserSerializer(
            data={
                "email": "test@example.com",
                "password": "password123",
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.save()

        self.assertEqual(
            user.email,
            "test@example.com",
        )

        self.assertTrue(
            user.check_password("password123"),
        )

        self.assertNotEqual(
            user.password,
            "password123",
        )

    def test_user_serializer_rejects_short_password(
        self,
    ) -> None:
        serializer = UserSerializer(
            data={
                "email": "test@example.com",
                "password": "1234",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "password",
            serializer.errors,
        )

    def test_user_serializer_rejects_invalid_email(
        self,
    ) -> None:
        serializer = UserSerializer(
            data={
                "email": "not-email",
                "password": "password123",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "email",
            serializer.errors,
        )

    def test_user_serializer_rejects_duplicate_email(
        self,
    ) -> None:
        get_user_model().objects.create_user(
            email="test@example.com",
            password="password123",
        )

        serializer = UserSerializer(
            data={
                "email": "test@example.com",
                "password": "anotherpassword",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "email",
            serializer.errors,
        )

    def test_user_serializer_id_is_read_only(
        self,
    ) -> None:
        serializer = UserSerializer(
            data={
                "id": 999,
                "email": "test@example.com",
                "password": "password123",
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "id",
            serializer.validated_data,
        )

    def test_user_serializer_is_staff_is_read_only(
        self,
    ) -> None:
        serializer = UserSerializer(
            data={
                "email": "test@example.com",
                "password": "password123",
                "is_staff": True,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.assertNotIn(
            "is_staff",
            serializer.validated_data,
        )

    def test_user_serializer_password_is_write_only(
        self,
    ) -> None:
        user = get_user_model().objects.create_user(
            email="test@example.com",
            password="password123",
        )

        serializer = UserSerializer(
            user,
        )

        self.assertNotIn(
            "password",
            serializer.data,
        )

    def test_user_serializer_updates_email(
        self,
    ) -> None:
        user = get_user_model().objects.create_user(
            email="old@example.com",
            password="password123",
        )

        serializer = UserSerializer(
            user,
            data={
                "email": "new@example.com",
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        updated_user = serializer.save()

        self.assertEqual(
            updated_user.email,
            "new@example.com",
        )

    def test_user_serializer_updates_password(
        self,
    ) -> None:
        user = get_user_model().objects.create_user(
            email="test@example.com",
            password="oldpassword123",
        )

        serializer = UserSerializer(
            user,
            data={
                "password": "newpassword123",
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        updated_user = serializer.save()

        self.assertTrue(
            updated_user.check_password(
                "newpassword123",
            ),
        )

        self.assertFalse(
            updated_user.check_password(
                "oldpassword123",
            ),
        )

    def test_user_serializer_keeps_password_when_not_provided(
        self,
    ) -> None:
        user = get_user_model().objects.create_user(
            email="old@example.com",
            password="password123",
        )

        original_password = user.password

        serializer = UserSerializer(
            user,
            data={
                "email": "new@example.com",
            },
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        updated_user = serializer.save()

        self.assertEqual(
            updated_user.password,
            original_password,
        )
