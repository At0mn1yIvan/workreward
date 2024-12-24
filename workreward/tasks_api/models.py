from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Task(models.Model):
    """
    Модель задачи.

    Поля:
        - title (CharField): Название задачи, уникальное.
        Обязательное поле.
        - description (TextField): Подробное описание задачи.
        Обязательное поле.
        - difficulty (IntegerField): Уровень сложности задачи.
        Выбирается из диапазона 1-5 (по возрастанию сложности).
        - task_duration (DurationField): Ожидаемая продолжительность
        выполнения задачи. Обязательное поле.
        - time_create (DateTimeField): Время создания задачи.
        Заполняется автоматически.
        - time_completion (DateTimeField): Время завершения задачи.
        Заполняется автоматически при сдаче задачи.
        - time_start (DateTimeField): Время начала выполнения задачи.
        Заполняется автоматически при сдаче задачи.
        - task_creator (ForeignKey): Ссылка на пользователя, создавшего задачу.
        Если пользователь удалён, значение становится NULL.
        - task_performer (ForeignKey): Ссылка на пользователя, выполняющего
        задачу. Если пользователь удалён, значение становится NULL.

    Методы:
        - __str__: Возвращает строковое представление задачи (её название).
    """
    title = models.CharField(
        max_length=255, null=False, blank=False, unique=True
    )
    description = models.TextField(null=False, blank=False)
    difficulty = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], null=False, blank=False
    )
    task_duration = models.DurationField(null=False, blank=False)
    time_create = models.DateTimeField(auto_now_add=True)
    time_completion = models.DateTimeField(null=True, blank=True)
    time_start = models.DateTimeField(null=True, blank=True)
    task_creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
    )
    task_performer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_tasks",
    )

    def __str__(self):
        return self.title
