from collections.abc import Callable
from datetime import datetime
from typing import Any


ValidationErrorType = Callable[
    [dict[str, list[str]]],
    Exception,
]


def validate_route_source_destination(
    source: Any | None,
    destination: Any | None,
    error_to_raise: ValidationErrorType,
) -> None:
    if (
        source is not None
        and destination is not None
        and source == destination
    ):
        raise error_to_raise(
            {
                "destination": [
                    "Destination must differ from source.",
                ],
            }
        )


def validate_flight_departure_and_arrival_time(
    departure_time: datetime | None,
    arrival_time: datetime | None,
    error_to_raise: ValidationErrorType,
) -> None:
    if (
        departure_time is not None
        and arrival_time is not None
        and arrival_time <= departure_time
    ):
        raise error_to_raise(
            {
                "arrival_time": [
                    "Arrival time must be later than departure time.",
                ],
            }
        )
