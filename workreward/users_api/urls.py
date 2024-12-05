from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .renderers import UserJSONRenderer
from .views import (
    ChangePasswordAPIView,
    GetCodesAPIView,
    LoginAPIView,
    ProfileAPIView,
    RegisterAPIView,
)

app_name = "users_api"
urlpatterns = [
    path(
        "login/",
        LoginAPIView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "login/refresh/",
        TokenRefreshView.as_view(renderer_classes=(UserJSONRenderer,)),
        name="token_refresh",
    ),
    path(
        "register/",
        RegisterAPIView.as_view(),
        name="register",
    ),
    path(
        "profile/",
        ProfileAPIView.as_view(),
        name="profile",
    ),
    path(
        "password-change/",
        ChangePasswordAPIView.as_view(),
        name="password_change",
    ),
    path("codeslist/", GetCodesAPIView.as_view({"get": "list"}), name="list"),
]
