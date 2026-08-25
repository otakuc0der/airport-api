from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any
import uuid

from decouple import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from airport.models import (
    Flight,
    Order,
    Ticket,
)


PASSWORD = config(
    "FIXTURE_PASSWORD",
    default="password123",
)

MAX_TICKETS_PER_ORDER = config(
    "MAX_TICKETS_PER_ORDER",
    default=3,
    cast=int,
)


def make_uuid(name: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"airport-api-{name}",
        )
    )


class Command(BaseCommand):
    help = "Generate complete airport service fixture"

    def handle(
        self,
        *args: Any,
        **options: Any,
    ) -> None:
        fixture: list[dict[str, Any]] = []

        country_ids = self.generate_countries(
            fixture,
        )

        city_ids = self.generate_cities(
            fixture=fixture,
            country_ids=country_ids,
        )

        airport_ids = self.generate_airports(
            fixture=fixture,
            city_ids=city_ids,
        )

        airplane_type_ids = self.generate_airplane_types(
            fixture,
        )

        airplanes = self.generate_airplanes(
            fixture=fixture,
            airplane_type_ids=airplane_type_ids,
        )

        crew_ids = self.generate_crew(
            fixture,
        )

        route_ids = self.generate_routes(
            fixture=fixture,
            airport_ids=airport_ids,
        )

        (
            flight_ids,
            flight_departures,
            flight_statuses,
        ) = self.generate_flights(
            fixture=fixture,
            route_ids=route_ids,
            airplanes=airplanes,
            crew_ids=crew_ids,
        )

        user_ids = self.generate_users(
            fixture,
        )

        self.generate_orders_and_tickets(
            fixture=fixture,
            user_ids=user_ids,
            flight_ids=flight_ids,
            flight_departures=flight_departures,
            flight_statuses=flight_statuses,
            airplanes=airplanes,
        )

        output_path = (
            Path(settings.BASE_DIR)
            / "airport"
            / "fixtures"
            / "airport_service_data_fixture.json"
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                fixture,
                file,
                indent=2,
                ensure_ascii=False,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Fixture created: {output_path}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Objects created: {len(fixture)}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Password for all users: {PASSWORD}"
            )
        )

    @staticmethod
    def generate_countries(
        fixture: list[dict[str, Any]],
    ) -> dict[str, str]:
        countries = [
            "Ukraine",
            "Poland",
            "Germany",
            "France",
            "Italy",
            "Spain",
            "Czech Republic",
            "Austria",
        ]

        country_ids: dict[str, str] = {}

        for country_name in countries:
            country_id = make_uuid(
                f"country-{country_name}"
            )

            country_ids[
                country_name
            ] = country_id

            fixture.append(
                {
                    "model": "airport.country",
                    "pk": country_id,
                    "fields": {
                        "name": country_name,
                    },
                }
            )

        return country_ids

    @staticmethod
    def generate_cities(
        fixture: list[dict[str, Any]],
        country_ids: dict[str, str],
    ) -> dict[str, str]:
        cities = [
            ("Kyiv", "Ukraine"),
            ("Lviv", "Ukraine"),
            ("Odesa", "Ukraine"),
            ("Warsaw", "Poland"),
            ("Krakow", "Poland"),
            ("Berlin", "Germany"),
            ("Munich", "Germany"),
            ("Paris", "France"),
            ("Rome", "Italy"),
            ("Milan", "Italy"),
            ("Madrid", "Spain"),
            ("Prague", "Czech Republic"),
        ]

        city_ids: dict[str, str] = {}

        for city_name, country_name in cities:
            city_id = make_uuid(
                f"city-{city_name}-{country_name}"
            )

            city_ids[
                city_name
            ] = city_id

            fixture.append(
                {
                    "model": "airport.city",
                    "pk": city_id,
                    "fields": {
                        "name": city_name,
                        "country": country_ids[
                            country_name
                        ],
                    },
                }
            )

        return city_ids

    @staticmethod
    def generate_airports(
        fixture: list[dict[str, Any]],
        city_ids: dict[str, str],
    ) -> dict[str, str]:
        airports = [
            (
                "Boryspil International Airport",
                "Kyiv",
            ),
            (
                "Lviv International Airport",
                "Lviv",
            ),
            (
                "Odesa International Airport",
                "Odesa",
            ),
            (
                "Warsaw Chopin Airport",
                "Warsaw",
            ),
            (
                "Krakow John Paul II Airport",
                "Krakow",
            ),
            (
                "Berlin Brandenburg Airport",
                "Berlin",
            ),
            (
                "Munich International Airport",
                "Munich",
            ),
            (
                "Paris Charles de Gaulle Airport",
                "Paris",
            ),
            (
                "Rome Fiumicino Airport",
                "Rome",
            ),
            (
                "Milan Malpensa Airport",
                "Milan",
            ),
            (
                "Madrid Barajas Airport",
                "Madrid",
            ),
            (
                "Prague Vaclav Havel Airport",
                "Prague",
            ),
        ]

        airport_ids: dict[str, str] = {}

        for airport_name, city_name in airports:
            airport_id = make_uuid(
                f"airport-{airport_name}"
            )

            airport_ids[
                city_name
            ] = airport_id

            fixture.append(
                {
                    "model": "airport.airport",
                    "pk": airport_id,
                    "fields": {
                        "name": airport_name,
                        "closest_big_city": city_ids[
                            city_name
                        ],
                        "image": "",
                    },
                }
            )

        return airport_ids

    @staticmethod
    def generate_airplane_types(
        fixture: list[dict[str, Any]],
    ) -> list[str]:
        airplane_types = [
            "Boeing 737-800",
            "Boeing 737 MAX 8",
            "Boeing 777-300ER",
            "Boeing 787-9 Dreamliner",
            "Airbus A319",
            "Airbus A320neo",
            "Airbus A321neo",
            "Embraer E195-E2",
        ]

        airplane_type_ids: list[str] = []

        for index, type_name in enumerate(
            airplane_types,
            start=1,
        ):
            airplane_type_id = make_uuid(
                f"airplane-type-{index}"
            )

            airplane_type_ids.append(
                airplane_type_id
            )

            fixture.append(
                {
                    "model": "airport.airplanetype",
                    "pk": airplane_type_id,
                    "fields": {
                        "name": type_name,
                    },
                }
            )

        return airplane_type_ids

    @staticmethod
    def generate_airplanes(
        fixture: list[dict[str, Any]],
        airplane_type_ids: list[str],
    ) -> list[dict[str, Any]]:
        airplanes_data = [
            (
                "Sky Voyager UR-001",
                20,
                6,
                0,
            ),
            (
                "Sky Voyager UR-002",
                22,
                6,
                1,
            ),
            (
                "European Star UR-003",
                28,
                8,
                2,
            ),
            (
                "Dream Flight UR-004",
                26,
                8,
                3,
            ),
            (
                "City Runner UR-005",
                18,
                6,
                4,
            ),
            (
                "City Runner UR-006",
                21,
                6,
                5,
            ),
            (
                "Continental Express UR-007",
                24,
                6,
                6,
            ),
            (
                "Continental Express UR-008",
                19,
                5,
                7,
            ),
            (
                "Global Wings UR-009",
                25,
                6,
                0,
            ),
            (
                "Global Wings UR-010",
                23,
                6,
                5,
            ),
        ]

        airplanes: list[
            dict[str, Any]
        ] = []

        for index, (
            name,
            rows,
            seats_in_row,
            airplane_type_index,
        ) in enumerate(
            airplanes_data,
            start=1,
        ):
            airplane_id = make_uuid(
                f"airplane-{index}"
            )

            airplane = {
                "id": airplane_id,
                "rows": rows,
                "seats_in_row": seats_in_row,
            }

            airplanes.append(
                airplane
            )

            fixture.append(
                {
                    "model": "airport.airplane",
                    "pk": airplane_id,
                    "fields": {
                        "name": name,
                        "rows": rows,
                        "seats_in_row": seats_in_row,
                        "airplane_type": (
                            airplane_type_ids[
                                airplane_type_index
                            ]
                        ),
                        "image": "",
                    },
                }
            )

        return airplanes

    @staticmethod
    def generate_crew(
        fixture: list[dict[str, Any]],
    ) -> list[str]:
        crew_members = [
            ("John", "Smith"),
            ("Anna", "Wilson"),
            ("Michael", "Brown"),
            ("Olivia", "Taylor"),
            ("Daniel", "Martin"),
            ("Sophia", "Anderson"),
            ("James", "Thomas"),
            ("Emma", "White"),
            ("William", "Harris"),
            ("Mia", "Clark"),
            ("Benjamin", "Lewis"),
            ("Charlotte", "Walker"),
            ("Lucas", "Hall"),
            ("Amelia", "Young"),
            ("Henry", "King"),
            ("Evelyn", "Wright"),
        ]

        crew_ids: list[str] = []

        for index, (
            first_name,
            last_name,
        ) in enumerate(
            crew_members,
            start=1,
        ):
            crew_id = make_uuid(
                f"crew-{index}"
            )

            crew_ids.append(
                crew_id
            )

            fixture.append(
                {
                    "model": "airport.crew",
                    "pk": crew_id,
                    "fields": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "photo": "",
                    },
                }
            )

        return crew_ids

    @staticmethod
    def generate_routes(
        fixture: list[dict[str, Any]],
        airport_ids: dict[str, str],
    ) -> list[str]:
        routes = [
            ("Kyiv", "Lviv", 470),
            ("Lviv", "Kyiv", 470),
            ("Kyiv", "Warsaw", 690),
            ("Warsaw", "Kyiv", 690),
            ("Lviv", "Krakow", 340),
            ("Krakow", "Lviv", 340),
            ("Warsaw", "Berlin", 520),
            ("Berlin", "Warsaw", 520),
            ("Berlin", "Paris", 880),
            ("Paris", "Berlin", 880),
            ("Paris", "Madrid", 1050),
            ("Madrid", "Paris", 1050),
            ("Rome", "Milan", 480),
            ("Milan", "Rome", 480),
            ("Prague", "Munich", 300),
            ("Munich", "Prague", 300),
            ("Kyiv", "Prague", 1140),
            ("Prague", "Kyiv", 1140),
            ("Odesa", "Rome", 1300),
            ("Rome", "Odesa", 1300),
        ]

        route_ids: list[str] = []

        for index, (
            source_city,
            destination_city,
            distance,
        ) in enumerate(
            routes,
            start=1,
        ):
            route_id = make_uuid(
                f"route-{index}"
            )

            route_ids.append(
                route_id
            )

            fixture.append(
                {
                    "model": "airport.route",
                    "pk": route_id,
                    "fields": {
                        "source": airport_ids[
                            source_city
                        ],
                        "destination": (
                            airport_ids[
                                destination_city
                            ]
                        ),
                        "distance": distance,
                    },
                }
            )

        return route_ids

    @staticmethod
    def generate_flights(
        fixture: list[dict[str, Any]],
        route_ids: list[str],
        airplanes: list[dict[str, Any]],
        crew_ids: list[str],
    ) -> tuple[
        list[str],
        dict[str, datetime],
        dict[str, str],
    ]:
        first_departure = datetime(
            2026,
            9,
            1,
            6,
            0,
            tzinfo=timezone.utc,
        )

        flight_ids: list[str] = []
        flight_departures: dict[
            str,
            datetime,
        ] = {}
        flight_statuses: dict[
            str,
            str,
        ] = {}

        for index in range(48):
            flight_number = index + 1

            flight_id = make_uuid(
                f"flight-{flight_number}"
            )

            flight_ids.append(
                flight_id
            )

            departure_time = (
                first_departure
                + timedelta(
                    hours=index * 6
                )
            )

            duration_hours = (
                2 + index % 3
            )

            arrival_time = (
                departure_time
                + timedelta(
                    hours=duration_hours
                )
            )

            flight_departures[
                flight_id
            ] = departure_time

            if flight_number % 12 == 0:
                flight_status = (
                    Flight.Status.CANCELLED
                )

            elif flight_number % 5 == 0:
                flight_status = (
                    Flight.Status.DELAYED
                )

            else:
                flight_status = (
                    Flight.Status.SCHEDULED
                )

            flight_statuses[
                flight_id
            ] = flight_status

            first_crew_index = (
                index * 3
            ) % len(crew_ids)

            flight_crew = [
                crew_ids[
                    first_crew_index
                ],
                crew_ids[
                    (
                        first_crew_index
                        + 1
                    )
                    % len(crew_ids)
                ],
                crew_ids[
                    (
                        first_crew_index
                        + 2
                    )
                    % len(crew_ids)
                ],
            ]

            fixture.append(
                {
                    "model": "airport.flight",
                    "pk": flight_id,
                    "fields": {
                        "route": route_ids[
                            index
                            % len(route_ids)
                        ],
                        "airplane": (
                            airplanes[
                                index
                                % len(airplanes)
                            ]["id"]
                        ),
                        "departure_time": (
                            departure_time.isoformat()
                        ),
                        "arrival_time": (
                            arrival_time.isoformat()
                        ),
                        "crew": flight_crew,
                        "status": flight_status,
                    },
                }
            )

        return (
            flight_ids,
            flight_departures,
            flight_statuses,
        )

    @staticmethod
    def generate_users(
        fixture: list[dict[str, Any]],
    ) -> list[int]:
        user = get_user_model()
        user_model = (
            user._meta.label_lower
        )

        users_data = [
            (
                "passenger1@example.com",
                False,
                False,
            ),
            (
                "passenger2@example.com",
                False,
                False,
            ),
            (
                "passenger3@example.com",
                False,
                False,
            ),
            (
                "passenger4@example.com",
                False,
                False,
            ),
            (
                "passenger5@example.com",
                False,
                False,
            ),
            (
                "passenger6@example.com",
                False,
                False,
            ),
            (
                "passenger7@example.com",
                False,
                False,
            ),
            (
                "passenger8@example.com",
                False,
                False,
            ),
            (
                "passenger9@example.com",
                False,
                False,
            ),
            (
                "passenger10@example.com",
                False,
                False,
            ),
            (
                "passenger11@example.com",
                False,
                False,
            ),
            (
                "passenger12@example.com",
                False,
                False,
            ),
            (
                "passenger13@example.com",
                False,
                False,
            ),
            (
                "passenger14@example.com",
                False,
                False,
            ),
            (
                "passenger15@example.com",
                False,
                False,
            ),
            (
                "staff1@example.com",
                True,
                False,
            ),
            (
                "staff2@example.com",
                True,
                False,
            ),
            (
                "staff3@example.com",
                True,
                False,
            ),
            (
                "admin@example.com",
                True,
                True,
            ),
        ]

        user_ids: list[int] = []

        date_joined = datetime(
            2026,
            8,
            1,
            10,
            0,
            tzinfo=timezone.utc,
        )

        for user_id, (
            email,
            is_staff,
            is_superuser,
        ) in enumerate(
            users_data,
            start=1,
        ):
            user_ids.append(
                user_id
            )

            local_name = email.split(
                "@"
            )[0]

            fixture.append(
                {
                    "model": user_model,
                    "pk": user_id,
                    "fields": {
                        "password": make_password(
                            PASSWORD
                        ),
                        "last_login": None,
                        "is_superuser": (
                            is_superuser
                        ),
                        "email": email,
                        "first_name": (
                            local_name.capitalize()
                        ),
                        "last_name": "User",
                        "is_staff": is_staff,
                        "is_active": True,
                        "date_joined": (
                            date_joined.isoformat()
                        ),
                        "groups": [],
                        "user_permissions": [],
                    },
                }
            )

        return user_ids

    @staticmethod
    def generate_orders_and_tickets(
        fixture: list[dict[str, Any]],
        user_ids: list[int],
        flight_ids: list[str],
        flight_departures: dict[
            str,
            datetime,
        ],
        flight_statuses: dict[
            str,
            str,
        ],
        airplanes: list[dict[str, Any]],
    ) -> None:
        airplane_by_flight: dict[
            str,
            dict[str, Any],
        ] = {}

        for (
            flight_index,
            flight_id,
        ) in enumerate(
            flight_ids
        ):
            airplane_by_flight[
                flight_id
            ] = airplanes[
                flight_index
                % len(airplanes)
            ]

        used_seats: set[
            tuple[str, int, int]
        ] = set()

        global_order_index = 0

        for (
            user_index,
            user_id,
        ) in enumerate(
            user_ids
        ):
            orders_count = (
                2 + user_index % 3
            )

            for order_index in range(
                orders_count
            ):
                global_order_index += 1

                flight_index = (
                    user_index * 5
                    + order_index * 7
                ) % len(flight_ids)

                flight_id = (
                    flight_ids[
                        flight_index
                    ]
                )

                airplane = (
                    airplane_by_flight[
                        flight_id
                    ]
                )

                flight_status = (
                    flight_statuses[
                        flight_id
                    ]
                )

                order_id = make_uuid(
                    f"order-{user_id}-"
                    f"{order_index + 1}"
                )

                departure_time = (
                    flight_departures[
                        flight_id
                    ]
                )

                created_at = (
                    departure_time
                    - timedelta(
                        days=(
                            10
                            + user_index
                            + order_index
                        )
                    )
                )

                if (
                    flight_status
                    == Flight.Status.CANCELLED
                ):
                    order_status = (
                        Order.Status.CANCELLED
                    )

                elif (
                    global_order_index
                    % 7
                    == 0
                ):
                    order_status = (
                        Order.Status.CANCELLED
                    )

                else:
                    order_status = (
                        Order.Status.CONFIRMED
                    )

                fixture.append(
                    {
                        "model": "airport.order",
                        "pk": order_id,
                        "fields": {
                            "user": user_id,
                            "created_at": (
                                created_at.isoformat()
                            ),
                            "status": (
                                order_status
                            ),
                        },
                    }
                )

                tickets_count = min(
                    (
                        2
                        + (
                            user_index
                            + order_index
                        )
                        % 2
                    ),
                    MAX_TICKETS_PER_ORDER,
                )

                for ticket_index in range(
                    tickets_count
                ):
                    (
                        row,
                        seat,
                    ) = (
                        Command.find_available_seat(
                            flight_id=flight_id,
                            rows=airplane[
                                "rows"
                            ],
                            seats_in_row=(
                                airplane[
                                    "seats_in_row"
                                ]
                            ),
                            used_seats=(
                                used_seats
                            ),
                        )
                    )

                    ticket_id = make_uuid(
                        f"ticket-{user_id}-"
                        f"{order_index + 1}-"
                        f"{ticket_index + 1}"
                    )

                    if (
                        order_status
                        == Order.Status.CANCELLED
                    ):
                        ticket_status = (
                            Ticket.Status.CANCELLED
                        )

                    else:
                        ticket_status = (
                            Ticket.Status.ACTIVE
                        )

                    fixture.append(
                        {
                            "model": (
                                "airport.ticket"
                            ),
                            "pk": ticket_id,
                            "fields": {
                                "row": row,
                                "seat": seat,
                                "flight": (
                                    flight_id
                                ),
                                "order": (
                                    order_id
                                ),
                                "status": (
                                    ticket_status
                                ),
                            },
                        }
                    )

    @staticmethod
    def find_available_seat(
        flight_id: str,
        rows: int,
        seats_in_row: int,
        used_seats: set[
            tuple[str, int, int]
        ],
    ) -> tuple[int, int]:
        for row in range(
            1,
            rows + 1,
        ):
            for seat in range(
                1,
                seats_in_row + 1,
            ):
                seat_key = (
                    flight_id,
                    row,
                    seat,
                )

                if (
                    seat_key
                    in used_seats
                ):
                    continue

                used_seats.add(
                    seat_key
                )

                return (
                    row,
                    seat,
                )

        raise ValueError(
            (
                "No available seats "
                f"for flight {flight_id}"
            )
        )
