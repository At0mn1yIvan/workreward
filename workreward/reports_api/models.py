from django.db import models

from tasks_api.models import Task


class TaskReport(models.Model):
    task = models.OneToOneField(
        Task,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="report",
    )
    text = models.TextField()
    efficiency_score = models.FloatField(null=True, blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
