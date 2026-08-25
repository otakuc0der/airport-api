from typing import Any

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from user.serializers import UserSerializer


@extend_schema_view(
    post=extend_schema(
        summary="Create user",
        tags=["Users"],
    )
)
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


@extend_schema(tags=["Tokens"])
class MyTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]


@extend_schema(tags=["Tokens"])
class MyTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


@extend_schema(tags=["Tokens"])
class MyTokenVerifyView(TokenVerifyView):
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        summary="Manage user",
        tags=["Users"],
    ),
    put=extend_schema(
        summary="Update user",
        tags=["Users"],
    ),
    patch=extend_schema(
        summary="Partial update user",
        tags=["Users"],
    ),
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> Any:
        return self.request.user
