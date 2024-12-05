from datetime import datetime

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from users.models import ManagerCode


class ManagerCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagerCode
        fields = "__all__"


class LoginUserSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=255,
        required=True,
    )
    password = serializers.CharField(
        max_length=128,
        required=True,
        write_only=True,
    )

    def validate(self, data):
        username = data.get("username", None)
        password = data.get("password", None)

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError(
                {"detail": "Пользователь с введёнными данными не найден."}
            )

        return user


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
    )
    manager_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "password",
            "password2",
            "manager_code",
        )
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "patronymic": {"required": False},
        }

    def validate(self, data):
        errors = {}
        if get_user_model().objects.filter(email=data["email"]).exists():
            errors["email"] = ["Такой E-mail уже существует."]

        if data["password"] != data["password2"]:
            errors["password"] = ["Пароли не совпадают."]

        manager_code = data.get("manager_code")
        if manager_code:
            try:
                code_instance = ManagerCode.objects.get(
                    code=manager_code, is_used=False
                )
                data["manager_code_instance"] = code_instance
            except ManagerCode.DoesNotExist:
                errors["manager_code"] = ["Неверный или использованный код."]
        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        patronymic = validated_data.get("patronymic", None)
        code = validated_data.get("manager_code_instance", None)

        user = get_user_model().objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            patronymic=patronymic,
        )
        user.set_password(validated_data.get("password"))

        if code:
            user.is_manager = True
            code.is_used = True
            code.used_at = datetime.now()
            code.save()

        user.save()
        return user


class ProfileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("username", "email", "first_name", "last_name", "patronymic")
        extra_kwargs = {
            "username": {"read_only": True},
            "email": {"read_only": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "patronymic": {"required": False},
        }

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get(
            "first_name", instance.first_name
        )
        instance.last_name = validated_data.get(
            "last_name", instance.last_name
        )
        instance.patronymic = validated_data.get(
            "patronymic", instance.patronymic
        )
        instance.save()
        return instance


class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        max_length=128,
        write_only=True,
        required=True,
    )
    new_password1 = serializers.CharField(
        max_length=128,
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    new_password2 = serializers.CharField(
        max_length=128,
        write_only=True,
        required=True,
    )

    def validate(self, data):
        errors = {}
        user = self.context["request"].user
        if not user.check_password(data["old_password"]):
            errors["old_password"] = ["Старый пароль введён неверно."]

        if data["new_password1"] != data["new_password2"]:
            errors["new_password2"] = ["Пароли не совпадают."]

        if errors:
            raise serializers.ValidationError(errors)
        return data

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password1"])
        user.save()
