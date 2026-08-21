from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from user.admin import UserAdmin
from user.models import User


class UserAdminTests(TestCase):
    def setUp(self) -> None:
        self.model_admin = UserAdmin(
            User,
            admin.site,
        )

    def test_user_model_is_registered_in_admin(
        self,
    ) -> None:
        self.assertIn(
            User,
            admin.site._registry,
        )

    def test_registered_admin_class_is_user_admin(
        self,
    ) -> None:
        registered_admin = admin.site._registry[
            User
        ]

        self.assertIsInstance(
            registered_admin,
            UserAdmin,
        )

    def test_list_display(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.list_display,
            (
                "email",
                "first_name",
                "last_name",
                "is_staff",
            ),
        )

    def test_search_fields(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.search_fields,
            (
                "email",
                "first_name",
                "last_name",
            ),
        )

    def test_ordering(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.ordering,
            (
                "email",
            ),
        )

    def test_fieldsets_contains_email_and_password(
        self,
    ) -> None:
        fields = self.model_admin.fieldsets[0][1][
            "fields"
        ]

        self.assertEqual(
            fields,
            (
                "email",
                "password",
            ),
        )

    def test_fieldsets_contains_personal_information(
        self,
    ) -> None:
        fields = self.model_admin.fieldsets[1][1][
            "fields"
        ]

        self.assertEqual(
            fields,
            (
                "first_name",
                "last_name",
            ),
        )

    def test_fieldsets_contains_permissions(
        self,
    ) -> None:
        fields = self.model_admin.fieldsets[2][1][
            "fields"
        ]

        self.assertEqual(
            fields,
            (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        )

    def test_fieldsets_contains_important_dates(
        self,
    ) -> None:
        fields = self.model_admin.fieldsets[3][1][
            "fields"
        ]

        self.assertEqual(
            fields,
            (
                "last_login",
                "date_joined",
            ),
        )

    def test_add_fieldsets_contains_expected_fields(
        self,
    ) -> None:
        add_fields = (
            self.model_admin
            .add_fieldsets[0][1]["fields"]
        )

        self.assertEqual(
            add_fields,
            (
                "email",
                "password1",
                "password2",
            ),
        )

    def test_add_fieldsets_uses_wide_class(
        self,
    ) -> None:
        classes = (
            self.model_admin
            .add_fieldsets[0][1]["classes"]
        )

        self.assertEqual(
            classes,
            (
                "wide",
            ),
        )

    def test_username_is_not_in_fieldsets(
        self,
    ) -> None:
        all_fields = []

        for _, options in (
            self.model_admin.fieldsets
        ):
            all_fields.extend(
                options["fields"]
            )

        self.assertNotIn(
            "username",
            all_fields,
        )

    def test_username_is_not_in_add_fieldsets(
        self,
    ) -> None:
        all_fields = []

        for _, options in (
            self.model_admin.add_fieldsets
        ):
            all_fields.extend(
                options["fields"]
            )

        self.assertNotIn(
            "username",
            all_fields,
        )

    def test_username_is_not_in_search_fields(
        self,
    ) -> None:
        self.assertNotIn(
            "username",
            self.model_admin.search_fields,
        )


class UserAdminPageTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.superuser = (
            get_user_model()
            .objects
            .create_superuser(
                email="admin@example.com",
                password="testpass123",
            )
        )

        cls.user = (
            get_user_model()
            .objects
            .create_user(
                email="user@example.com",
                password="testpass123",
                first_name="John",
                last_name="Smith",
            )
        )

    def setUp(self) -> None:
        self.client.force_login(
            self.superuser,
        )

    def test_user_changelist_page_available(
        self,
    ) -> None:
        url = reverse(
            "admin:user_user_changelist",
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_user_change_page_available(
        self,
    ) -> None:
        url = reverse(
            "admin:user_user_change",
            args=[
                self.user.pk,
            ],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_user_add_page_available(
        self,
    ) -> None:
        url = reverse(
            "admin:user_user_add",
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_user_search_by_email(
        self,
    ) -> None:
        url = reverse(
            "admin:user_user_changelist",
        )

        response = self.client.get(
            url,
            {
                "q": "user@example.com",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "user@example.com",
        )
