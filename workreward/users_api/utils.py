from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest
from django.utils.http import urlsafe_base64_encode

from common.utils import send_email
from .models import User


def send_password_reset_link(user: User, email: str, request: HttpRequest) -> None:
    """
    Отправка ссылки для сброса пароля пользователю.

    Этот метод генерирует уникальную ссылку для сброса пароля с использованием
    URL-safe кодирования ID пользователя и токена, а затем отправляет эту
    ссылку на указанный email пользователя.

    Аргументы:
        - user (User): Пользователь, для которого генерируется ссылка
        для сброса пароля.
        - email (str): Адрес электронной почты пользователя,
        на который будет отправлена ссылка.
        - request (HttpRequest): Запрос, используемый для построения
        абсолютного URL для сброса пароля.
    """
    uid = urlsafe_base64_encode(str(user.pk).encode())
    token = default_token_generator.make_token(user)
    reset_link = request.build_absolute_uri(
        f"/password-reset-confirm/{uid}/{token}/"
    )
    subject = "Запрос на сброс пароля"
    message = (
        f"Перейдите по ссылке, чтобы сбросить ваш пароль: {reset_link}"
    )

    send_email(
        subject=subject,
        message=message,
        recipient_list=[email],
    )

    # try:
    #     send_email(
    #         subject=subject,
    #         message=message,
    #         recipient_list=[email],
    #     )
    # except Exception as e:
    #     error_message = (
    #         f"Ошибка при отправке уведомления: {str(e)}\n"
    #         "Возможно, пользователь указал несуществующую почту."
    #     )
    #     raise Exception(error_message)
