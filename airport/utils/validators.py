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


def validate_ticket_rows_and_seats_in_row(
    flight: Any | None,
    row: int | None,
    seat: int | None,
    error_to_raise: ValidationErrorType,
) -> None:
    if flight is None or row is None or seat is None:
        return

    airplane = flight.airplane

    if not 1 <= row <= airplane.rows:
        raise error_to_raise(
            {
                "row": [
                    f"Row must be between 1 and {airplane.rows}.",
                ],
            }
        )

    if not 1 <= seat <= airplane.seats_in_row:
        raise error_to_raise(
            {
                "seat": [
                    (
                        "Seat must be between 1 and "
                        f"{airplane.seats_in_row}."
                    ),
                ],
            }
        )
