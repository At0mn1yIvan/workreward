from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Task


class TaskCreateSerializer(serializers.ModelSerializer):
    task_performer = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_manager=False),
        required=False,
        allow_null=False,
    )

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "difficulty",
            "task_duration",
            "task_performer",
        )
        extra_kwargs = {
            "title": {"required": True},
            "description": {"required": True},
            "difficulty": {"required": True},
            "task_duration": {"required": True},
        }

    def validate_task_performer(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError(
                {"task_performer": "Назначенный пользователь неактивен."}
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_manager:
            raise serializers.ValidationError(
                {"detail": "Только менеджеры могут создавать задачи."}
            )

        task_performer = validated_data.get("task_performer", None)
        task = Task.objects.create(**validated_data)

        if task_performer:
            task.time_start = timezone.now()
            task.save()

        return task
