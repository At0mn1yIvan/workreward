from django.contrib.auth.views import (LogoutView, PasswordChangeDoneView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.urls import path, reverse_lazy
from users import views

app_name = "users"


urlpatterns = [
    path("login/", views.LoginUser.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterUser.as_view(), name="register"),
    path(
        "password-change/",
        views.UserPasswordChange.as_view(),
        name="password_change"
    ),
    path(
        "password-change/done/",
        PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html",
            extra_context={"title": "Work-Reward. Завершение смены пароля"}),
        name="password_change_done",
    ),
    path(
        "password-reset/",
        PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            email_template_name="users/password_reset_email.html",
            extra_context={"title": "Work-Reward. Восстановление пароля"},
            success_url=reverse_lazy("users:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html",
            extra_context={"title": "Work-Reward. Сброс пароля"},
            ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            extra_context={"title": "Work-Reward. Новый пароль"},
            success_url=reverse_lazy("users:password_reset_complete")
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html",
            extra_context={"title": "Work-Reward. Пароль изменён"},
        ),
        name="password_reset_complete",
    ),
    path("register/done/", views.register_done, name="register_done"),
    path("profile/", views.ProfileUser.as_view(), name="profile"),
]
