from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .renderers import UserJSONRenderer
from . import views

app_name = "users_api"
urlpatterns = [
    path(
        "list/",
        views.UserViewSet.as_view({"get": "list"}),
        name="users_list",
    ),
    path(
        "list/<int:pk>/",
        views.UserViewSet.as_view({"get": "retrieve"}),
        name="user_detail",
    ),
    path(
        "login/",
        views.LoginAPIView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "login/refresh/",
        TokenRefreshView.as_view(renderer_classes=(UserJSONRenderer,)),
        name="token_refresh",
    ),
    path(
        "register/",
        views.RegisterAPIView.as_view(),
        name="register",
    ),
    path(
        "profile/",
        views.ProfileAPIView.as_view(),
        name="profile",
    ),
    path(
        "password-change/",
        views.ChangePasswordAPIView.as_view(),
        name="password_change",
    ),
    path(
        "password-reset/",
        views.PasswordResetRequestAPIView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset-confirm/",
        views.PasswordResetConfirmAPIView.as_view(),
        name="password_reset_confirm",
    ),
]
