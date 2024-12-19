from django.db import models

from reports_api.models import TaskReport


class Reward(models.Model):
    """
    Модель вознаграждения за выполнение отчета по задаче.

    Атрибуты:
        - reward_sum (Decimal): Сумма вознаграждения. Хранит денежную сумму
        с точностью до двух знаков после запятой.
        - comment (TextField): Комментарий к вознаграждению. Позволяет указать
        дополнительные сведения о вознаграждении.
        - time_create (DateTimeField): Время создания вознаграждения.
        Автоматически устанавливается при создании объекта.
        - task_report (OneToOneField): Связь с отчетом по задаче.
        Каждое вознаграждение связано с одним отчетом по задаче.
        Если отчет по задаче удаляется, связанное вознаграждение остается,
        но поле task_report будет установлено в NULL.

    Методы:
        None
    """
    reward_sum = models.DecimalField(
        null=False,
        blank=False,
        max_digits=7,
        decimal_places=2,
    )
    comment = models.TextField(null=False, blank=False)
    time_create = models.DateTimeField(auto_now_add=True)
    task_report = models.OneToOneField(
        TaskReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reward",
    )
