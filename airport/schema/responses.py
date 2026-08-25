from drf_spectacular.utils import OpenApiResponse


BAD_REQUEST_RESPONSE = OpenApiResponse(
    description=(
        "The request contains invalid data. "
        "The response includes details about the validation errors."
    ),
)

UNAUTHORIZED_RESPONSE = OpenApiResponse(
    description=(
        "Authentication credentials are missing, invalid, or expired. "
        "A valid JWT access token is required."
    ),
)

FORBIDDEN_RESPONSE = OpenApiResponse(
    description=(
        "The authenticated user does not have permission "
        "to perform this operation."
    ),
)

NOT_FOUND_RESPONSE = OpenApiResponse(
    description=(
        "The requested object was not found."
    ),
)

NO_CONTENT_RESPONSE = OpenApiResponse(
    description=(
        "The object was deleted successfully. "
        "The response has no content."
    ),
)

TOO_MANY_REQUESTS_RESPONSE = OpenApiResponse(
    description=(
        "The request rate limit was exceeded. "
        "Try again later."
    ),
)

PROTECTED_OBJECT_RESPONSE = OpenApiResponse(
    description=(
        "The object cannot be deleted because it is used "
        "by other related objects."
    ),
)
