from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from airport.admin import (
    AirplaneAdmin,
    AirportAdmin,
    CityAdmin,
    FlightAdmin,
    FlightAdminForm,
    OrderAdmin,
    RouteAdmin,
    TicketAdmin,
    TicketInline,
)
from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Crew,
    Flight,
    Order,
    Route,
    Ticket,
)


class BaseAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = (
            get_user_model()
            .objects
            .create_superuser(
                email="admin@example.com",
                password="testpass123",
            )
        )

        cls.country = Country.objects.create(
            name="Ukraine",
        )

        cls.source_city = City.objects.create(
            name="Kyiv",
            country=cls.country,
        )

        cls.destination_city = (
            City.objects.create(
                name="Lviv",
                country=cls.country,
            )
        )

        cls.source_airport = (
            Airport.objects.create(
                name=(
                    "Boryspil International "
                    "Airport"
                ),
                closest_big_city=(
                    cls.source_city
                ),
            )
        )

        cls.destination_airport = (
            Airport.objects.create(
                name=(
                    "Lviv International "
                    "Airport"
                ),
                closest_big_city=(
                    cls.destination_city
                ),
            )
        )

        cls.airplane_type = (
            AirplaneType.objects.create(
                name="Boeing 737",
            )
        )

        cls.airplane = Airplane.objects.create(
            name="UR-001",
            rows=20,
            seats_in_row=6,
            airplane_type=cls.airplane_type,
        )

        cls.route = Route.objects.create(
            source=cls.source_airport,
            destination=cls.destination_airport,
            distance=470,
        )

        cls.departure_time = (
            timezone.now()
            + timedelta(days=5)
        )

        cls.arrival_time = (
            cls.departure_time
            + timedelta(hours=2)
        )

        cls.flight = Flight.objects.create(
            route=cls.route,
            airplane=cls.airplane,
            departure_time=cls.departure_time,
            arrival_time=cls.arrival_time,
        )

        cls.crew = Crew.objects.create(
            first_name="John",
            last_name="Smith",
        )

        cls.flight.crew.add(
            cls.crew,
        )

        cls.order = Order.objects.create(
            user=cls.admin_user,
        )

        cls.ticket = Ticket.objects.create(
            order=cls.order,
            flight=cls.flight,
            row=1,
            seat=1,
        )

    def setUp(self) -> None:
        self.factory = RequestFactory()

        self.request = self.factory.get(
            "/admin/",
        )
        self.request.user = self.admin_user


class CityAdminTests(BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.model_admin = CityAdmin(
            City,
            admin.site,
        )

    def test_get_country_name(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_country_name(
                self.source_city,
            ),
            "Ukraine",
        )


class AirportAdminTests(BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.model_admin = AirportAdmin(
            Airport,
            admin.site,
        )

    def test_get_closest_big_city(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_closest_big_city(
                self.source_airport,
            ),
            "Kyiv",
        )

    def test_get_country(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_country(
                self.source_airport,
            ),
            "Ukraine",
        )

    def test_closest_big_city_foreign_key_queryset(
        self,
    ) -> None:
        field = Airport._meta.get_field(
            "closest_big_city"
        )

        form_field = (
            self.model_admin
            .formfield_for_foreignkey(
                field,
                self.request,
            )
        )

        self.assertIsNotNone(
            form_field,
        )

        self.assertIn(
            self.source_city,
            form_field.queryset,
        )


class AirplaneAdminTests(BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.model_admin = AirplaneAdmin(
            Airplane,
            admin.site,
        )

    def test_get_airplane_type(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_airplane_type(
                self.airplane,
            ),
            "Boeing 737",
        )


class RouteAdminTests(BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.model_admin = RouteAdmin(
            Route,
            admin.site,
        )

    def test_get_source(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_source(
                self.route,
            ),
            (
                "Boryspil International "
                "Airport"
            ),
        )

    def test_get_destination(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_destination(
                self.route,
            ),
            (
                "Lviv International "
                "Airport"
            ),
        )

    def test_get_source_destination(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_source_destination(
                self.route,
            ),
            "Kyiv ➝ Lviv",
        )

    def test_get_queryset_contains_route(
        self,
    ) -> None:
        queryset = (
            self.model_admin
            .get_queryset(
                self.request,
            )
        )

        self.assertIn(
            self.route,
            queryset,
        )

    def test_source_foreign_key_queryset(
        self,
    ) -> None:
        field = Route._meta.get_field(
            "source"
        )

        form_field = (
            self.model_admin
            .formfield_for_foreignkey(
                field,
                self.request,
            )
        )

        self.assertIn(
            self.source_airport,
            form_field.queryset,
        )

    def test_destination_foreign_key_queryset(
        self,
    ) -> None:
        field = Route._meta.get_field(
            "destination"
        )

        form_field = (
            self.model_admin
            .formfield_for_foreignkey(
                field,
                self.request,
            )
        )

        self.assertIn(
            self.destination_airport,
            form_field.queryset,
        )


class FlightAdminTests(BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.model_admin = FlightAdmin(
            Flight,
            admin.site,
        )

    def test_custom_admin_form_is_used(
        self,
    ) -> None:
        self.assertIs(
            self.model_admin.form,
            FlightAdminForm,
        )

    def test_get_route(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_route(
                self.flight,
            ),
            (
                "Kyiv (Ukraine) ➝ "
                "Lviv (Ukraine)"
            ),
        )

    def test_get_airplane(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_airplane(
                self.flight,
            ),
            (
                "UR-001 | "
                "Boeing 737 | "
                "120 seats"
            ),
        )

    def test_get_current_state(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_current_state(
                self.flight,
            ),
            Flight.Status.SCHEDULED,
        )

    def test_get_queryset_contains_flight(
        self,
    ) -> None:
        queryset = (
            self.model_admin
            .get_queryset(
                self.request,
            )
        )

        self.assertIn(
            self.flight,
            queryset,
        )

    def test_route_foreign_key_queryset(
        self,
    ) -> None:
        field = Flight._meta.get_field(
            "route"
        )

        form_field = (
            self.model_admin
            .formfield_for_foreignkey(
                field,
                self.request,
            )
        )

        self.assertIn(
            self.route,
            form_field.queryset,
        )

    def test_airplane_foreign_key_queryset(
        self,
    ) -> None:
        field = Flight._meta.get_field(
            "airplane"
        )

        form_field = (
            self.model_admin
            .formfield_for_foreignkey(
                field,
                self.request,
            )
        )

        self.assertIn(
            self.airplane,
            form_field.queryset,
        )

    def test_scheduled_flight_can_be_changed(
        self,
    ) -> None:
        self.flight.status = (
            Flight.Status.SCHEDULED
        )

        self.assertTrue(
            self.model_admin
            .has_change_permission(
                self.request,
                self.flight,
            )
        )

    def test_delayed_flight_can_be_changed(
        self,
    ) -> None:
        self.flight.status = (
            Flight.Status.DELAYED
        )

        self.assertTrue(
            self.model_admin
            .has_change_permission(
                self.request,
                self.flight,
            )
        )

    def test_cancelled_flight_cannot_be_changed(
        self,
    ) -> None:
        self.flight.status = (
            Flight.Status.CANCELLED
        )

        self.assertFalse(
            self.model_admin
            .has_change_permission(
                self.request,
                self.flight,
            )
        )

    def test_general_change_permission(
        self,
    ) -> None:
        self.assertTrue(
            self.model_admin
            .has_change_permission(
                self.request,
                None,
            )
        )


class TicketInlineTests(BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.inline = TicketInline(
            Order,
            admin.site,
        )

    def test_get_queryset_contains_ticket(
        self,
    ) -> None:
        queryset = self.inline.get_queryset(
            self.request,
        )

        self.assertIn(
            self.ticket,
            queryset,
        )

    def test_flight_foreign_key_queryset(
        self,
    ) -> None:
        field = Ticket._meta.get_field(
            "flight"
        )

        form_field = (
            self.inline
            .formfield_for_foreignkey(
                field,
                self.request,
            )
        )

        self.assertIn(
            self.flight,
            form_field.queryset,
        )

    def test_status_is_read_only(
        self,
    ) -> None:
        self.assertIn(
            "status",
            self.inline.readonly_fields,
        )

    def test_minimum_one_ticket_is_required(
        self,
    ) -> None:
        self.assertEqual(
            self.inline.min_num,
            1,
        )

        self.assertTrue(
            self.inline.validate_min,
        )


class TicketAdminTests(BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.model_admin = TicketAdmin(
            Ticket,
            admin.site,
        )

    def test_get_ticket_route(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_ticket_route(
                self.ticket,
            ),
            (
                "Kyiv (Ukraine) → "
                "Lviv (Ukraine)"
            ),
        )

    def test_departure_time(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.departure_time(
                self.ticket,
            ),
            self.flight.departure_time,
        )

    def test_arrival_time(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.arrival_time(
                self.ticket,
            ),
            self.flight.arrival_time,
        )

    def test_get_user(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.get_user(
                self.ticket,
            ),
            self.admin_user.email,
        )

    def test_direct_ticket_creation_is_disabled(
        self,
    ) -> None:
        self.assertFalse(
            self.model_admin
            .has_add_permission(
                self.request,
            )
        )

    def test_get_queryset_contains_ticket(
        self,
    ) -> None:
        queryset = (
            self.model_admin
            .get_queryset(
                self.request,
            )
        )

        self.assertIn(
            self.ticket,
            queryset,
        )

    def test_flight_foreign_key_queryset(
        self,
    ) -> None:
        field = Ticket._meta.get_field(
            "flight"
        )

        form_field = (
            self.model_admin
            .formfield_for_foreignkey(
                field,
                self.request,
            )
        )

        self.assertIn(
            self.flight,
            form_field.queryset,
        )

    def test_order_foreign_key_queryset(
        self,
    ) -> None:
        field = Ticket._meta.get_field(
            "order"
        )

        form_field = (
            self.model_admin
            .formfield_for_foreignkey(
                field,
                self.request,
            )
        )

        self.assertIn(
            self.order,
            form_field.queryset,
        )

    def test_status_is_read_only(
        self,
    ) -> None:
        self.assertIn(
            "status",
            self.model_admin.readonly_fields,
        )


class OrderAdminTests(BaseAdminTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.model_admin = OrderAdmin(
            Order,
            admin.site,
        )

    def test_get_queryset_contains_order(
        self,
    ) -> None:
        queryset = (
            self.model_admin
            .get_queryset(
                self.request,
            )
        )

        self.assertIn(
            self.order,
            queryset,
        )

    def test_tickets_count(
        self,
    ) -> None:
        queryset = (
            self.model_admin
            .get_queryset(
                self.request,
            )
        )

        order = queryset.get(
            pk=self.order.pk,
        )

        self.assertEqual(
            self.model_admin.tickets_count(
                order,
            ),
            1,
        )

    def test_tickets_count_returns_zero_without_annotation(
        self,
    ) -> None:
        self.assertEqual(
            self.model_admin.tickets_count(
                self.order,
            ),
            0,
        )

    def test_status_is_read_only(
        self,
    ) -> None:
        self.assertIn(
            "status",
            self.model_admin.readonly_fields,
        )

    def test_created_at_is_read_only(
        self,
    ) -> None:
        self.assertIn(
            "created_at",
            self.model_admin.readonly_fields,
        )
