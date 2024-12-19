from django.db import models

from tasks_api.models import Task


class TaskReport(models.Model):
    """
    Модель отчёта по задаче.

    Этот класс представляет собой отчёт о выполнении задачи,
    содержащий текст отчёта, оценку эффективности исполнителя,
    время создания отчёта и связь с задачей.

    Атрибуты:
        - text (TextField): Текст отчёта, обязательное поле.
        - efficiency_score (FloatField): Оценка эффективности
        исполнителя по задаче. Может быть пустым (null),
        если не установлена.
        - time_create (DateTimeField): Время создания отчёта.
        Заполняется автоматически при добавлении объекта отчёта.
        - task (OneToOneField): Связь с задачей.
        Один отчёт может быть привязан только к одной задаче.
        Может быть пустым (null), если задача не указана или удалена.
    """

    text = models.TextField(null=False, blank=False)
    efficiency_score = models.FloatField(null=False, blank=False)
    time_create = models.DateTimeField(auto_now_add=True)
    task = models.OneToOneField(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report",
    )
