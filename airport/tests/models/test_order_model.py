from django.contrib.auth import get_user_model
from django.test import TestCase

from airport.models import Order


class OrderModelTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="password123",
        )

    def test_default_status_is_confirmed(self) -> None:
        order = Order.objects.create(
            user=self.user,
        )

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

    def test_can_create_cancelled_order(self) -> None:
        order = Order.objects.create(
            user=self.user,
            status=Order.Status.CANCELLED,
        )

        self.assertEqual(
            order.status,
            Order.Status.CANCELLED,
        )

    def test_created_at_is_set_automatically(
        self,
    ) -> None:
        order = Order.objects.create(
            user=self.user,
        )

        self.assertIsNotNone(
            order.created_at,
        )

    def test_str(self) -> None:
        order = Order.objects.create(
            user=self.user,
        )

        self.assertEqual(
            str(order),
            (
                f"Order created at {order.created_at} "
                f"by {self.user.email}"
            ),
        )
