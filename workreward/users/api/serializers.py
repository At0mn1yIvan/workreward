from datetime import datetime

from django.contrib.auth import get_user_model
from models import ManagerCode
from rest_framework import serializers


class RegisterUserSerializer(serializers.ModelSerializer):
    patronymic = serializers.CharField(required=False)
    manager_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "password",
            "manager_code",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        if get_user_model().objects.filter(email=value).exists():
            raise serializers.ValidationError(
                {"email": "Такой E-mail уже существует"}
            )
        return value

    def validate(self, attrs):
        manager_code = attrs.get("manager_code")
        if manager_code:
            try:
                code = ManagerCode.objects.get(
                    code=manager_code, is_used=False
                )
                attrs["manager_code_instance"] = code
            except ManagerCode.DoesNotExist:
                raise serializers.ValidationError(
                    {"manager_code": "Неверный или использованный код"}
                )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        manager_code_instance = validated_data.pop(
            "manager_code_instance", None
        )

        user = get_user_model().objects.create(**validated_data)
        user.set_password(password)

        if manager_code_instance:
            user.is_manager = True
            manager_code_instance.is_used = True
            manager_code_instance.used_at = datetime.now()
            manager_code_instance.save()

        user.save()
        return user
