from typing import Any

from django.db.models.deletion import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(
    exc: Exception,
    context: dict[str, Any],
) -> Response | None:
    if isinstance(exc, ProtectedError):
        return Response(
            {
                "detail": (
                    "This object cannot be deleted because "
                    "it is used by other records."
                ),
            },
            status=400,
        )

    return exception_handler(exc, context)
