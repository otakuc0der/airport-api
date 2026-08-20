import uuid
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from airport.utils.files import generate_image_file_path
from airport.utils.validators import (
    validate_flight_departure_and_arrival_time,
    validate_route_source_destination,
    validate_ticket_rows_and_seats_in_row,
)


def crew_photo_file_path(
    instance: "Crew",
    filename: str,
) -> str:
    full_name = f"{instance.first_name}-{instance.last_name}"
    return generate_image_file_path(
        full_name,
        filename,
        "uploads/crews"
    )


class Crew(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    photo = models.ImageField(
        null=True,
        blank=True,
        upload_to=crew_photo_file_path
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Country(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )

    class Meta:
        verbose_name_plural = "countries"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class City(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        max_length=255,
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="cities"
    )

    class Meta:
        verbose_name_plural = "cities"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "country"],
                name="unique_city_name_country"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.country.name})"


def airport_image_file_path(
    instance: "Airport",
    filename: str,
) -> str:
    return generate_image_file_path(
        instance.name,
        filename,
        "uploads/airports"
    )


class Airport(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255, unique=True)
    closest_big_city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="airports"
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=airport_image_file_path
    )

    class Meta:
        ordering = [
            "name",
        ]

    def __str__(self) -> str:
        return (
            f"{self.name} (closest city: "
            f"{self.closest_big_city.name})"
        )


class AirplaneType(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


def airplane_image_file_path(
    instance: "Airplane",
    filename: str,
) -> str:
    return generate_image_file_path(
        instance.name,
        filename,
        "uploads/airplanes"
    )


class Airplane(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255, unique=True)
    rows = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )
    seats_in_row = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.PROTECT,
        related_name="airplanes"
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=airplane_image_file_path
    )

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return (
            f"{self.name} | {self.airplane_type.name}"
            f" (rows: {self.rows}, seats in row: "
            f"{self.seats_in_row})"
        )


class Route(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    source = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="source_routes",
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="destination_routes",
    )
    distance = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "destination"],
                name="unique_route_source_destination"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        validate_route_source_destination(
            self.source_id,
            self.destination_id,
            ValidationError
        )

    def save(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"Source: {self.source}; "
            f"Destination: {self.destination}; "
            f"Distance: {self.distance}"
        )


class Flight(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.PROTECT,
        related_name="flights",
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.PROTECT,
        related_name="flights",
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(
        Crew,
        related_name="flights",
    )

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        DELAYED = "delayed", "Delayed"
        CANCELLED = "cancelled", "Cancelled"


    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )

    @property
    def flight_duration(self) -> timedelta:
        return self.arrival_time - self.departure_time

    @property
    def flight_state(self) -> str:
        now = timezone.now()

        if self.status == self.Status.CANCELLED:
            return "cancelled"

        if now < self.departure_time:
            return self.status

        if self.departure_time <= now < self.arrival_time:
            return "departed"

        return "arrived"

    class Meta:
        ordering = ["-departure_time"]

    def clean(self) -> None:
        super().clean()
        validate_flight_departure_and_arrival_time(
            self.departure_time,
            self.arrival_time,
            ValidationError
        )

    def save(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        departure_time = timezone.localtime(
            self.departure_time
        ).strftime("%Y-%m-%d %H:%M")

        arrival_time = timezone.localtime(
            self.arrival_time
        ).strftime("%Y-%m-%d %H:%M")

        return (
            f"Flight '{self.route.source.closest_big_city}-"
            f"{self.route.destination.closest_big_city}' "
            f"(departure time: {departure_time}; "
            f"arrival time: {arrival_time})"
        )


class Order(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"


    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"Order created at {self.created_at} "
            f"by {self.user.email}"
        )


class Ticket(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.PROTECT,
        related_name="tickets",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"


    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["flight", "row", "seat"],
                condition=Q(status="active"),
                name="unique_ticket_flight_row_seat"
            )
        ]

    def clean(self) -> None:
        super().clean()

        flight = self.flight if self.flight_id else None

        validate_ticket_rows_and_seats_in_row(
            flight,
            self.row,
            self.seat,
            ValidationError,
        )

    def save(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"Ticket for flight: |{self.flight}| "
            f"(row: {self.row}, seat: {self.seat})"
        )
