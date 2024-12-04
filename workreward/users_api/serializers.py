from datetime import datetime

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from users.models import ManagerCode


class ManagerCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagerCode
        fields = "__all__"


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={"input_type": "password"},
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True, required=True
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

    def is_valid(self, raise_exception=False):
        all_errors = {}

        try:
            super().is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            all_errors.update(e.detail)

        try:
            self.validate(self.initial_data)
        except serializers.ValidationError as e:
            all_errors.update(e.detail)

        if all_errors:
            if raise_exception:
                raise serializers.ValidationError(all_errors)
            return False

        return True

    def validate(self, data):
        errors = {}
        if get_user_model().objects.filter(email=data["email"]).exists():
            errors["email"] = ["Такой E-mail уже существует"]

        if data["password"] != data["password2"]:
            errors["password"] = ["Пароли не совпадают"]

        manager_code = data.get("manager_code")
        if manager_code:
            try:
                ManagerCode.objects.get(code=manager_code, is_used=False)
            except ManagerCode.DoesNotExist:
                errors["manager_code"] = ["Неверный или использованный код"]
        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):

        user = get_user_model().objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            patronymic=validated_data["patronymic"],
        )
        user.set_password(validated_data.get("password"))

        code = validated_data.get("manager_code", None)
        if code:
            code_obj = ManagerCode.objects.get(code=code)
            user.is_manager = True
            code_obj.is_used = True
            code_obj.used_at = datetime.now()
            code_obj.save()

        user.save()
        return user


# class LoginUserSerializer(serializers.Serializer):
#     email = serializers.CharField(max_length=255, read_only=True)
#     username = serializers.CharField(max_length=255)
#     password = serializers.CharField(max_length=128, write_only=True)

#     def validate(self, data):
#         username = data.get("username", None)
#         password = data.get("password", None)

#         user = authenticate(username=username, password=password)

#         if user is None:
#             raise serializers.ValidationError(
#                 "Пользователь с введёнными данными не найден"
#             )

#         if not user.is_active:
#             raise serializers.ValidationError("Пользователь был деактивирован")

#         return user
