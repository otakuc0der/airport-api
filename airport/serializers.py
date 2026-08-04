from rest_framework import serializers

from airport.models import (
    Crew,
    Country,
    City,
    Airport,
    AirplaneType,
    Airplane,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name", "country"]


class CityListSerializer(CitySerializer):
    country = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


class CityDetailSerializer(CitySerializer):
    country = CountrySerializer(read_only=True)


class AirportSerializer(serializers.ModelSerializer):
    closest_big_city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.select_related("country")
    )

    class Meta:
        model = Airport
        fields = ["id", "name", "closest_big_city", "image"]


class AirportListSerializer(AirportSerializer):
    closest_big_city = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )


class AirportDetailSerializer(AirportSerializer):
    closest_big_city = CityDetailSerializer(read_only=True)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = [
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "image",
            "capacity",
        ]


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = [
            "id",
            "first_name",
            "last_name",
            "photo",
        ]
