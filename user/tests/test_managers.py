from django.contrib.auth import get_user_model
from django.test import TestCase


class UserManagerTests(TestCase):
    def test_create_user_with_email_successful(self) -> None:
        email = "test@example.com"
        password = "password123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(
            user.email,
            email,
        )
        self.assertTrue(
            user.check_password(password),
        )
        self.assertFalse(
            user.is_staff,
        )
        self.assertFalse(
            user.is_superuser,
        )

    def test_create_user_normalizes_email(self) -> None:
        email = "Test@EXAMPLE.COM"

        user = get_user_model().objects.create_user(
            email=email,
            password="password123",
        )

        self.assertEqual(
            user.email,
            "Test@example.com",
        )

    def test_create_user_without_email_raises_value_error(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as context:
            get_user_model().objects.create_user(
                email="",
                password="password123",
            )

        self.assertEqual(
            str(context.exception),
            "The given email must be set",
        )

    def test_create_superuser_successful(self) -> None:
        user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="password123",
        )

        self.assertTrue(
            user.is_staff,
        )
        self.assertTrue(
            user.is_superuser,
        )
        self.assertTrue(
            user.check_password("password123"),
        )

    def test_create_superuser_with_is_staff_false_raises_value_error(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as context:
            get_user_model().objects.create_superuser(
                email="admin@example.com",
                password="password123",
                is_staff=False,
            )

        self.assertEqual(
            str(context.exception),
            "Superuser must have is_staff=True.",
        )

    def test_create_superuser_with_is_superuser_false_raises_value_error(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as context:
            get_user_model().objects.create_superuser(
                email="admin@example.com",
                password="password123",
                is_superuser=False,
            )

        self.assertEqual(
            str(context.exception),
            "Superuser must have is_superuser=True.",
        )
