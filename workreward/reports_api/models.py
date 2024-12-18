from django.db import models

from tasks_api.models import Task


class TaskReport(models.Model):
    text = models.TextField(null=False, blank=False)
    efficiency_score = models.FloatField(null=True, blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
    task = models.OneToOneField(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report",
    )
