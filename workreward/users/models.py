from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Расширенная модель пользователя на основе стандартной модели Django AbstractUser.

    Добавляет дополнительные поля к стандартной модели пользователя для реализации специфических требований приложения.

    Атрибуты:
        first_name (CharField): Имя пользователя. Обязательное поле, не может быть пустым.
        last_name (CharField): Фамилия пользователя. Обязательное поле, не может быть пустым.
        patronymic (CharField): Отчество пользователя. Необязательное поле, может быть пустым.
        is_manager (BooleanField): Флаг, указывающий, является ли пользователь менеджером. По умолчанию False (не менеджер).
    """

    first_name = models.CharField(max_length=150, null=False, blank=False)
    last_name = models.CharField(max_length=150, null=False, blank=False)
    patronymic = models.CharField(max_length=150, null=True, blank=True)
    is_manager = models.BooleanField(default=False)

    def get_full_name(self) -> str:
        full_name = (
            f"{self.last_name} {self.first_name} {self.patronymic or ''}"
        )
        return full_name.strip()


class ManagerCode(models.Model):
    """
    Модель для хранения кодов менеджеров, используемых при регистрации пользователей.

    Атрибуты:
        code (CharField): Уникальный код для подтверждения прав менеджера. Максимальная длина — 50 символов.
        is_used (BooleanField): Флаг, указывающий, был ли код использован. По умолчанию False.
        created_at (DateTimeField): Дата и время создания кода. Устанавливается автоматически при создании записи.
        used_at (DateTimeField): Дата и время использования кода. Может быть пустым (null), если код ещё не использован.

    Методы:
        __str__(): Возвращает строковое представление кода.
    """

    code = models.CharField(max_length=50, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code
