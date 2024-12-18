from django.db import models

from reports_api.models import TaskReport


class Reward(models.Model):
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
