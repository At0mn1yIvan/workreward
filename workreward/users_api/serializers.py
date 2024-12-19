from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from .models import ManagerCode


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя.

    Этот сериализатор используется для преобразования экземпляров модели
    пользователя в формат JSON. Содержит основные поля модели пользователя,
    такие как ID, никнейм пользователя, email, имя, фамилия, отчество и статус
    менеджера (является ли им).
    """

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "is_manager",
        )


class LoginUserSerializer(serializers.Serializer):
    """
    Сериализатор для аутентификации пользователя.

    Этот сериализатор используется для проверки введённых данных
    (имя пользователя и пароль) и аутентификации пользователя.

    Атрибуты:
        - username (CharField): Поле для имени пользователя или E-Mail,
        обязательное.
        - password (CharField): Поле для пароля, обязательное.

    Методы:
        - validate(data):
            Проверяет, существует ли пользователь с введёнными именем
            и паролем. Если пользователь не найден, выбрасывает
            ValidationError. При успешной аутентификации
            добавляет объект пользователя в данные.
    """

    username = serializers.CharField(
        max_length=150,
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

        data["user_obj"] = user
        return data


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.

    Используется для создания нового пользователя. Включает проверку паролей,
    проверки наличия электронной почты в базе данных и валидацию кода
    менеджера, если он предоставлен.

    Атрибуты:
        - username (CharField): Имя пользователя. Обязательное поле,
        используется как уникальный идентификатор.
        - email (CharField): Адрес электронной почты пользователя.
        Обязательное поле, должно быть уникальным.
        - first_name (CharField): Имя пользователя. Обязательное поле.
        - last_name (CharField): Фамилия пользователя. Обязательное поле.
        - patronymic (CharField): Отчество пользователя. Необязательное поле.
        - password (CharField): Пароль пользователя. Обязательное поле,
        доступно только для записи. Проходит валидацию
        через`validate_password`.
        - password2 (CharField): Подтверждение пароля. Обязательное поле,
        используется для проверки совпадения с основным паролем.
        - manager_code (CharField): Код менеджера. Необязательное поле.
        Используется для получения прав менеджера.


    Методы:
        validate(data):
            Проверяет данные на корректность:
            - Проверяет уникальность email.
            - Проверяет совпадение пароля и подтверждения пароля.
            - Проверяет валидность и статус кода менеджера.
            Добавляет объект ManagerCode в данные, если код валиден.

        create(validated_data):
            Создаёт нового пользователя с указанными данными.
            Устанавливает пароль пользователя.
            Если предоставлен и валиден код менеджера, устанавливает
            пользователя как менеджера и помечает код как использованный.
    """

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

        manager_code = data.get("manager_code", None)
        if manager_code:
            try:
                code_instance = ManagerCode.objects.get(
                    code=manager_code, is_used=False
                )
            except ManagerCode.DoesNotExist:
                errors["manager_code"] = ["Неверный или использованный код."]
        else:
            code_instance = None

        if errors:
            raise serializers.ValidationError(errors)

        data["manager_code_instance"] = code_instance
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
            code.used_at = timezone.localtime(timezone.now())
            code.save()

        user.save()
        return user


class ProfileUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра и обновления профиля пользователя.

    Используется для отображения данных пользователя и редактирования
    его личной информации, такой как имя, фамилия и отчество. Данные
    о имени пользователя, электронной почте и статусе менеджера
    доступны только для чтения.

    Атрибуты:
        - username (CharField): Имя пользователя.Доступно только для чтения.
        - email (CharField): Адрес электронной почты пользователя.
        Доступно только для чтения.
        - first_name (CharField): Имя пользователя.
        Обязательное поле для обновления.
        - last_name (CharField): Фамилия пользователя.
        Обязательное поле для обновления.
        - patronymic (CharField): Отчество пользователя.
        Необязательное поле для обновления.
        - is_manager (BooleanField): Флаг, указывающий, является ли
        пользователь менеджером. Доступно только для чтения.

    Методы:
        - update:
            Обновляет данные профиля пользователя. Обновляются поля
            `first_name`, `last_name` и `patronymic`.
            Все остальные поля, такие как `username`, `email` и `is_manager`,
            доступны только для чтения.
    """

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "is_manager",
        )
        extra_kwargs = {
            "username": {"read_only": True},
            "email": {"read_only": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "patronymic": {"required": False},
            "is_manager": {"read_only": True},
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
    """
    Сериализатор для изменения пароля пользователя.

    Этот сериализатор используется для валидации и изменения пароля
    пользователя. Он проверяет старый пароль, сравнивает новый пароль
    с подтверждением, а также удостоверяется, что новый пароль не совпадает
    с текущим. После успешной валидации пароля новый пароль сохраняется.

    Атрибуты:
        - old_password (CharField): Старый пароль пользователя.
        Требуется для валидации.
        - new_password1 (CharField): Новый пароль пользователя.
        Требуется для валидации.
        - new_password2 (CharField): Подтверждение нового пароля.
        Требуется для валидации.

    Методы:
        - validate:
            Проверяет, что старый пароль правильный, что новый пароль
            совпадает с его подтверждением, и что новый пароль
            не совпадает с текущим.
        - save:
            Сохраняет новый пароль пользователя, если валидация прошла успешно.
    """

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
        user = self.context["request"].user
        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError(
                {"old_password": "Старый пароль введён неверно."}
            )

        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError(
                {"new_password2": "Пароли не совпадают."}
            )

        if data["old_password"] == data["new_password2"]:
            raise serializers.ValidationError(
                {"new_password2": "Новый пароль не может совпадать со старым."}
            )

        return data

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password1"])
        user.save()


class UserPasswordResetRequestSerializer(serializers.Serializer):
    """
    Сериализатор для запроса сброса пароля пользователя.

    Этот сериализатор используется для обработки запроса на сброс пароля.
    Он проверяет, существует ли пользователь с указанным электронным адресом.
    Если пользователь найден, возвращается объект пользователя для дальнейшей
    обработки. Если пользователь не найден, генерируется ошибка валидации.

    Атрибуты:
        - email (EmailField): Электронная почта пользователя,
        для которого требуется сброс пароля.

    Методы:
        - validate:
            Проверяет, существует ли пользователь с указанным E-mail.
            Если пользователя с таким E-mail не существует,
            генерируется ошибка валидации.
    """

    email = serializers.EmailField(max_length=254, required=True)

    def validate(self, data):
        user_model = get_user_model()
        user = None

        try:
            user = user_model.objects.get(email=data["email"])
        except user_model.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Пользователя с таким E-mail не существует."}
            )

        data["user_obj"] = user
        return data


class UserPasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения сброса пароля пользователя.

    Этот сериализатор используется для обработки подтверждения сброса пароля.
    Он проверяет, совпадают ли два введённых пароля, а также валидирует ссылку
    и токен для сброса пароля. Если данные корректны, то новый пароль
    сохраняется для пользователя.

    Атрибуты:
        - new_password1 (CharField): Новый пароль пользователя.
        Обязательное поле.
        - new_password2 (CharField): Подтверждение нового пароля.
        Обязательное поле.
        - uidb64 (CharField): Идентификатор пользователя в base64-формате.
        Обязательное поле.
        - token (CharField): Токен для сброса пароля. Обязательное поле.

    Методы:
        - validate:
            Проверяет, совпадают ли два введённых пароля, а также валидирует
            идентификатор пользователя и токен для сброса пароля.
            Если токен или ссылка неправильные, генерируется ошибка валидации.

        - save:
            Сохраняет новый пароль пользователя после его валидации.
    """
    new_password1 = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
    )
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError(
                {"new_password2": "Пароли не совпадают."}
            )

        user_model = get_user_model()
        user = None

        try:
            uid = urlsafe_base64_decode(data["uidb64"]).decode()
            user = user_model.objects.get(pk=uid)

        except (user_model.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({"uidb64": "Неверная ссылка."})

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError(
                {"token": "Неверный или истёкший токен."}
            )

        data["user_obj"] = user
        return data

    def save(self):
        user = self.validated_data["user_obj"]
        new_password = self.validated_data["new_password1"]
        user.set_password(new_password)
        user.save()
        return user
