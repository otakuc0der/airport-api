from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from django.db.models import (
    CharField,
    DateTimeField,
    ExpressionWrapper,
    F,
    QuerySet,
    Value,
)
from django.db.models.functions import Concat
from django.utils import timezone

if TYPE_CHECKING:
    from airport.models import (
        Airplane,
        Crew,
        Flight,
        Order,
    )


ValidationErrorType = Callable[
    [dict[str, list[str]]],
    Exception,
]

FieldValidationErrorType = Callable[
    [list[str]],
    Exception,
]

FLIGHT_SCHEDULE_BUFFER = timedelta(minutes=30)


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
    flight: Flight | None,
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


def validate_flight_crew_presence(
    crew: Sequence[Crew] | None,
    error_to_raise: ValidationErrorType,
) -> None:
    if not crew:
        raise error_to_raise(
            {
                "crew": [
                    "A flight must have at least one crew member.",
                ],
            }
        )


def get_conflicting_flights(
    *,
    departure_time: datetime,
    arrival_time: datetime,
    current_flight: Flight | None = None,
    **filters: Any,
) -> QuerySet[Flight]:
    from airport.models import Flight

    conflicting_flights = (
        Flight.objects
        .filter(**filters)
        .exclude(status=Flight.Status.CANCELLED)
    )

    if current_flight is not None:
        conflicting_flights = conflicting_flights.exclude(
            pk=current_flight.pk,
        )

    return (
        conflicting_flights
        .annotate(
            adjusted_departure=ExpressionWrapper(
                F("departure_time") - FLIGHT_SCHEDULE_BUFFER,
                output_field=DateTimeField(),
            ),
            adjusted_arrival=ExpressionWrapper(
                F("arrival_time") + FLIGHT_SCHEDULE_BUFFER,
                output_field=DateTimeField(),
            ),
        )
        .filter(
            adjusted_departure__lt=arrival_time,
            adjusted_arrival__gt=departure_time,
        )
        .distinct()
    )


def validate_flight_crew_schedule(
    crew: Sequence[Crew] | None,
    current_flight: Flight | None,
    departure_time: datetime | None,
    arrival_time: datetime | None,
    error_to_raise: ValidationErrorType,
) -> None:
    from airport.models import Crew

    if (
        crew is None
        or departure_time is None
        or arrival_time is None
    ):
        return

    conflicting_flights = get_conflicting_flights(
        departure_time=departure_time,
        arrival_time=arrival_time,
        current_flight=current_flight,
        crew__in=crew,
    )

    conflicting_crew = (
        Crew.objects
        .filter(
            flights__in=conflicting_flights,
            pk__in=[member.pk for member in crew],
        )
        .annotate(
            crew_full_name=Concat(
                F("first_name"),
                Value(" "),
                F("last_name"),
                output_field=CharField(),
            )
        )
        .order_by("crew_full_name")
        .values_list("crew_full_name", flat=True)
        .distinct()
    )

    conflicting_crew_names = ", ".join(conflicting_crew)

    if conflicting_crew_names:
        raise error_to_raise(
            {
                "crew": [
                    (
                        "The following crew members are unavailable "
                        "for this flight and its required 30-minute "
                        f"buffer: {conflicting_crew_names}."
                    ),
                ],
            }
        )


def validate_flight_airplane_schedule(
    airplane: Airplane | None,
    current_flight: Flight | None,
    departure_time: datetime | None,
    arrival_time: datetime | None,
    error_to_raise: ValidationErrorType,
) -> None:
    if (
        airplane is None
        or departure_time is None
        or arrival_time is None
    ):
        return

    conflicting_flights = get_conflicting_flights(
        departure_time=departure_time,
        arrival_time=arrival_time,
        current_flight=current_flight,
        airplane=airplane,
    )

    if conflicting_flights.exists():
        raise error_to_raise(
            {
                "airplane": [
                    (
                        "This airplane is unavailable during the selected "
                        "time or the required 30-minute interval "
                        "between flights."
                    ),
                ],
            }
        )


def validate_ticket_flight(
    flight: Flight | None,
    error_to_raise: ValidationErrorType,
) -> None:
    from airport.models import Flight

    if flight is None:
        return

    if flight.status == Flight.Status.CANCELLED:
        raise error_to_raise(
            {
                "flight": [
                    "Tickets cannot be purchased for a cancelled flight.",
                ],
            }
        )

    if flight.departure_time <= timezone.now():
        raise error_to_raise(
            {
                "flight": [
                    "Tickets cannot be purchased after departure.",
                ],
            }
        )


def validate_flight_modification(
    flight: Flight | None,
    error_to_raise: ValidationErrorType,
) -> None:
    from airport.models import Flight

    if (
        flight is not None
        and flight.status == Flight.Status.CANCELLED
    ):
        raise error_to_raise(
            {
                "status": [
                    "A cancelled flight cannot be modified.",
                ],
            }
        )


def validate_flight_status_change(
    status: str | None,
    error_to_raise: ValidationErrorType,
) -> None:
    from airport.models import Flight

    if status and status == Flight.Status.CANCELLED:
        raise error_to_raise(
            {
                "status": [
                    "Use the flight cancel endpoint to cancel a flight.",
                ],
            }
        )


def validate_flight_cancellation(
    flight: Flight,
    error_to_raise: ValidationErrorType,
) -> None:
    from airport.models import Flight

    if flight.status == Flight.Status.CANCELLED:
        raise error_to_raise(
            {
                "status": [
                    "Flight is already cancelled.",
                ],
            }
        )

    if flight.departure_time <= timezone.now():
        raise error_to_raise(
            {
                "status": [
                    "A flight cannot be cancelled after departure.",
                ],
            }
        )


def validate_order_cancellation(
    order: Order,
    error_to_raise: ValidationErrorType,
) -> None:
    from airport.models import Flight, Order, Ticket

    if order.status == Order.Status.CANCELLED:
        raise error_to_raise(
            {
                "detail": [
                    "Order is already cancelled.",
                ],
            }
        )

    has_departed_flights = (
        order.tickets
        .filter(
            status=Ticket.Status.ACTIVE,
            flight__departure_time__lte=timezone.now(),
        )
        .exclude(
            flight__status=Flight.Status.CANCELLED,
        )
        .exists()
    )

    if has_departed_flights:
        raise error_to_raise(
            {
                "detail": [
                    "Order cannot be cancelled after flight departure.",
                ],
            }
        )


def validate_tickets_flights(
    tickets: list[dict[str, Any]],
    error_to_raise: FieldValidationErrorType,
) -> None:
    flight_ids = {
        ticket["flight"].pk
        for ticket in tickets
    }

    if len(flight_ids) > 1:
        raise error_to_raise(
            [
                "All tickets in an order must belong to the same flight.",
            ]
        )


def validate_flight_airplane_change(
    flight: Flight | None,
    new_airplane: Airplane | None,
    error_to_raise: ValidationErrorType,
) -> None:
    from airport.models import Ticket

    if (
        flight is None
        or new_airplane is None
        or new_airplane == flight.airplane
    ):
        return

    if flight.tickets.filter(
        status=Ticket.Status.ACTIVE,
    ).exists():
        raise error_to_raise(
            {
                "airplane": [
                    (
                        "The airplane cannot be changed because "
                        "active tickets already exist for this flight."
                    ),
                ],
            }
        )
