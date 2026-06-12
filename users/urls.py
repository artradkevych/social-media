from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileViewSet,
)

router = DefaultRouter()
router.register("profiles", ProfileViewSet, basename="profile")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", include(router.urls)),
]

app_name = "users"
