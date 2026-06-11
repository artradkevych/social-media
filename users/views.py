from typing import Dict, Any, Type, Optional

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, viewsets, status, mixins, filters
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from users.models import Profile
from users.permissions import IsOwnerOrReadOnly
from users.serializers import (
    ProfileDetailSerializer,
    ProfileListSerializer,
    ProfileWriteSerializer,
    RegisterSerializer,
)


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email", write_only=True)
    password = serializers.CharField(
        label="Password",
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        email = attrs.get("email")
        password = attrs.get("password")
        if email and password:
            user = authenticate(
                request=self.context.get("request"), username=email, password=password
            )
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials.", code="authorization"
                )
        else:
            raise serializers.ValidationError(
                "Must include 'email' and 'password'.", code="authorization"
            )
        attrs["user"] = user
        return attrs


@extend_schema(
    summary="Register a new user",
    description="Creates a new user account along with a profile.",
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = ()


@extend_schema(
    summary="Login",
    description="Authenticate with email and password to receive an auth token.",
)
class LoginView(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})


@extend_schema(summary="Logout", description="Invalidates the current auth token.")
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request) -> Response:
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        summary="List profiles",
        description="Returns all user profiles. Supports search by username, first or last name.",
    ),
    retrieve=extend_schema(summary="Get profile detail"),
    update=extend_schema(summary="Update profile"),
    partial_update=extend_schema(summary="Partially update profile"),
    destroy=extend_schema(summary="Delete profile and user account"),
)
class ProfileViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Profile.objects.select_related("user").prefetch_related(
        "following", "followers"
    )
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("user__username", "first_name", "last_name")

    def get_permissions(self) -> list:
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()

    def get_serializer_class(self) -> Type[serializers.Serializer]:
        if self.action == "list":
            return ProfileListSerializer
        if self.action in ("update", "partial_update"):
            return ProfileWriteSerializer
        return ProfileDetailSerializer

    def perform_destroy(self, instance: Profile) -> None:
        instance.user.delete()

    @extend_schema(
        summary="Follow or unfollow a user",
        description="Toggles follow on a profile. Returns 201 if followed, 200 if unfollowed. Cannot follow yourself.",
        responses={200: None, 201: None, 400: None},
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def follow(self, request, pk: Optional[int] = None) -> Response:
        target_profile = self.get_object()
        my_profile = request.user.profile

        if target_profile.pk == my_profile.pk:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if my_profile.following.filter(pk=target_profile.pk).exists():
            my_profile.following.remove(target_profile)
            return Response({"detail": "Unfollowed."}, status=status.HTTP_200_OK)

        my_profile.following.add(target_profile)
        return Response({"detail": "Followed."}, status=status.HTTP_201_CREATED)
