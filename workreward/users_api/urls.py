from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import GetUsersAPIView, RegisterAPIView

app_name = "users_api"
# Для логина использовать login/; Для обновления токена login/refresh/.
urlpatterns = [
    path(
        "login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "login/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "register/",
        RegisterAPIView.as_view(),
        name="register",
    ),
    # path(
    #     "login/my/",
    #     LoginAPIView.as_view(),
    #     name="login",
    # ),
    path(
        "codeslist/",
        GetUsersAPIView.as_view({'get': 'list'}),
        name="list"),
]
