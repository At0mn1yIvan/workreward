from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"


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

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_manager:
            raise serializers.ValidationError(
                {"detail": "Только менеджеры могут создавать задачи."}
            )
        return data

    def create(self, validated_data):
        task_performer = validated_data.get("task_performer", None)
        task = Task.objects.create(**validated_data)

        if task_performer:
            task.time_start = timezone.now()
            task.save()

        return task


class TaskTakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ()

    def validate(self, data):
        user = self.context["request"].user
        if user.is_manager:
            raise serializers.ValidationError(
                {"detail": "Менеджер не может брать задачи."}
            )

        task = self.instance
        if task.task_performer:
            raise serializers.ValidationError(
                {"detail": "Задача уже имеет исполнителя."}
            )

        return data

    def update(self, instance, validated_data):
        instance.task_performer = self.context["request"].user
        instance.time_start = timezone.now()
        instance.save()

        return instance


class TaskAssignSerializer(serializers.ModelSerializer):
    task_performer = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_manager=False),
        required=True,
        allow_null=False,
    )

    class Meta:
        model = Task
        fields = ("task_performer",)

    def validate_task_performer(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError(
                {"task_performer": "Назначенный пользователь неактивен."}
            )
        return value

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_manager:
            raise serializers.ValidationError(
                {"detail": "Только менеджер может назначать задачи."}
            )

        task = self.instance
        if task.task_performer:
            raise serializers.ValidationError(
                {"detail": "Задача уже имеет исполнителя."}
            )

        return data

    def update(self, instance, validated_data):
        instance.task_performer = validated_data.get("task_performer")
        instance.time_start = timezone.now()
        instance.save()

        return instance
