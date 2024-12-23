from django.utils import timezone
from rest_framework import serializers

from reports_api.models import TaskReport
from tasks_api.serializers import TaskSerializer
from .utils import calculate_performer_efficiency


class TaskReportSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели отчётов.

    Этот сериализатор используется для преобразования экземпляров отчётов
    по задачам в формат JSON. Содержит все поля модели задачи.
    """

    task = TaskSerializer(read_only=True)

    class Meta:
        model = TaskReport
        fields = "__all__"


class TaskReportCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания отчёта по задаче.

    Этот сериализатор используется для валидации и создания нового отчёта
    по задаче на основе предоставленных данных. Он проверяет, является ли
    пользователь исполнителем задачи, завершена ли задача, и существует ли
    уже отчёт для этой задачи.

    Атрибуты:
        - text (str): Текст отчёта, обязательный для создания.

    Методы:
        - validate(): Выполняет все необходимые проверки
        перед созданием отчёта.
        - create(): Создаёт новый отчёт по задаче,
        вычисляя эффективность исполнителя.
    """

    text = serializers.CharField(required=True)

    class Meta:
        model = TaskReport
        fields = (
            "id",
            "task",
            "text",
            "efficiency_score",
        )
        read_only_fields = (
            "id",
            "task",
            "efficiency_score",
        )

    def validate(self, data):
        task = self.context["task"]
        user = self.context["request"].user

        if user.is_manager:
            raise serializers.ValidationError(
                {"detail": "Менеджер не может создать отчёт по задаче."}
            )

        if task.task_performer != user:
            raise serializers.ValidationError(
                {"detail": "Вы не являетесь исполнителем данной задачи."}
            )

        if not task.time_completion:
            raise serializers.ValidationError(
                {"detail": "Задача ещё не завершена."}
            )

        if TaskReport.objects.filter(task=task).exists():
            raise serializers.ValidationError(
                {"detail": "Отчёт для этой задачи уже создан."}
            )

        data["task_obj"] = task
        return data

    def create(self, validated_data):
        task = validated_data.get("task_obj")

        report = TaskReport.objects.create(
            text=validated_data["text"],
            efficiency_score=calculate_performer_efficiency(task),
            time_create=timezone.localtime(timezone.now()),
            task=task,
        )

        return report
