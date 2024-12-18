from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers

from .models import Reward


class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = "__all__"


class RewardCreateSerializer(serializers.ModelSerializer):
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

        return reward
