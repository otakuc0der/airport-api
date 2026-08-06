from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
)
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminOrReadOnly(BasePermission):
    def has_permission(
        self,
        request: Request,
        view: APIView,
    ) -> bool:
        if request.method in SAFE_METHODS:
            return True

        return bool(
            request.user.is_authenticated
            and request.user.is_staff
        )
