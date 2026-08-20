from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from airport.utils.validators import validate_route_source_destination


class RouteValidationTests(SimpleTestCase):
    SOURCE_ID = "936346c29b4a438b86ea152834097f42"
    DESTINATION_ID = "8f454fac21414a5e86ef4ac75fa66c17"

    ERROR_MSG = {
        "destination": [
            "Destination must differ from source.",
        ],
    }

    def test_validate_route_source_destination_allows_different_objects(
        self,
    ) -> None:
        validate_route_source_destination(
            source=self.SOURCE_ID,
            destination=self.DESTINATION_ID,
            error_to_raise=ValidationError,
        )

    def test_validate_route_source_destination_rejects_same_object(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_route_source_destination(
                source=self.SOURCE_ID,
                destination=self.SOURCE_ID,
                error_to_raise=ValidationError,
            )

        self.assertEqual(
            context.exception.detail,
            self.ERROR_MSG,
        )

    def test_validate_route_source_destination_ignores_missing_source(
        self,
    ) -> None:
        validate_route_source_destination(
            source=None,
            destination=self.DESTINATION_ID,
            error_to_raise=ValidationError,
        )

    def test_validate_route_source_destination_ignores_missing_destination(
        self,
    ) -> None:
        validate_route_source_destination(
            source=self.SOURCE_ID,
            destination=None,
            error_to_raise=ValidationError,
        )

    def test_validate_route_source_destination_ignores_missing_both(
        self,
    ) -> None:
        validate_route_source_destination(
            source=None,
            destination=None,
            error_to_raise=ValidationError,
        )
