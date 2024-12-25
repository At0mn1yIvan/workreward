from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers

from .models import Reward


class RewardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели премий.

    Этот сериализатор используется для преобразования экземпляров премий
    в формат JSON. Содержит все поля модели задачи.
    """

    class Meta:
        model = Reward
        fields = "__all__"


class RewardCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания вознаграждения (премии) за задачу.

    Используется для валидации данных, проверки прав пользователя,
    вычисления суммы премии и создания записи о вознаграждении для задачи.

    Атрибуты:
        - reward_sum (DecimalField): Сумма вознаграждения.
        Это поле вычисляется на основе эффективности выполнения задачи
        и ограничено максимальной суммой (10000).
        - comment (CharField): Комментарий менеджера. Обязательное поле.
        - task_report (PrimaryKeyRelatedField): Связь с отчетом по задаче.
        Обязательное поле. Это поле доступно только для записи.
        Не может быть изменено.

    Методы:
        - validate(data):
            Проверяет, является ли текущий пользователь менеджером
            и проверяет права пользователя по отношению к задаче.

            - Если пользователь не является менеджером,
            поднимает ValidationError.
            - Если пользователь не является создателем задачи,
            поднимает ValidationError.
            - Если вознаграждение для задачи уже выдано,
            поднимает ValidationError.

        - create(validated_data):
            Создает вознаграждение на основе валидированных данных.

            - Вычисляет сумму премии в зависимости от эффективности
            выполнения задачи, но не более установленного лимита.
            - Возвращает созданную запись о вознаграждении.
    """

    comment = serializers.CharField(required=True)

    class Meta:
        model = Reward
        fields = (
            "reward_sum",
            "comment",
            "task_report",
        )
        read_only_fields = ("reward_sum", "task_report")

    def validate(self, data):
        report = self.context["report"]
        user = self.context["request"].user

        if not user.is_manager:
            raise serializers.ValidationError(
                {"detail": "Только менеджер может выдавать премии."}
            )

        if report.task.task_creator != user:
            raise serializers.ValidationError(
                {"detail": "Вы не являетесь создателем данной задачи."}
            )

        if Reward.objects.filter(task_report=report).exists():
            raise serializers.ValidationError(
                {"detail": "Премия за эту задачу уже выдана."}
            )

        data["report_obj"] = report
        return data

    def create(self, validated_data):
        report = validated_data.get("report_obj", None)

        BASE_RATE = Decimal("500.00")
        THRESHOLD = Decimal("10000.00")
        reward_sum = BASE_RATE * Decimal(
            str(report.efficiency_score)
        ).quantize(Decimal(".01"))

        if reward_sum > THRESHOLD:
            reward_sum = THRESHOLD

        reward = Reward.objects.create(
            reward_sum=reward_sum,
            comment=validated_data["comment"],
            time_create=timezone.localtime(timezone.now()),
            task_report=report,
        )

        report.is_awarded = True
        report.save(update_fields=["is_awarded"])

        return reward
