import os
import uuid

from django.db import models
from django.utils.text import slugify


class Crew(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

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


class Airport(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    closest_big_city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="airports"
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
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/airplanes", filename)


class Airplane(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255, unique=True)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()
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
