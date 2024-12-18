from typing import Optional
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from .models import User


class EmailAuthBackend(BaseBackend):
    """
    Кастомный бэкенд для аутентификации пользователей
    по адресу электронной почты.

    Этот бэкенд позволяет пользователям входить в систему с использованием
    E-mail вместо стандартного логина. Проверяет, существует ли пользователь
    с указанным E-mail и совпадает ли пароль.

    Методы:
        - authenticate(request, username=None, password=None, **kwargs):
            Аутентифицирует пользователя на основе его email и пароля.
            Возвращает объект пользователя, если учетные данные верны,
            иначе возвращает None.

        - get_user(user_id):
            Возвращает объект пользователя по его ID
            (восстановление объекта пользователя из идентификатора).
            Если пользователь не найден, возвращает None.
    """

    def authenticate(
        self,
        request,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ) -> Optional[User]:
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
            return None

    def get_user(self, user_id: int) -> Optional[User]:
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
