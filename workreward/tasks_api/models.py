from django.contrib.auth import get_user_model
from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    difficulty = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], null=False, blank=False
    )
    task_duration = models.DurationField(null=True, blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_completion = models.DateTimeField(null=True, blank=True)
    time_start = models.DateTimeField(null=True, blank=True)
    task_creator = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="created_tasks",
    )
    task_performer = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_tasks",
    )

    def __str__(self):
        return self.title
