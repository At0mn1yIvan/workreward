from typing import Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели задачи.

    Этот сериализатор используется для преобразования экземпляров модели
    задачи в формат JSON. Содержит все поля модели задачи.

    Методы:
        - get_task_creator(self, obj):
            Возвращает полное имя создателя задачи.

            - Аргументы:
                - obj - Экземпляр задачи

        - get_task_performer(self, obj):
            Возвращает полное имя исполнителя задачи.

            - Аргументы:
                - obj - Экземпляр задачи
    """

    task_creator = serializers.SerializerMethodField()
    task_performer = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "difficulty",
            "task_duration",
            "time_create",
            "time_completion",
            "time_start",
            "task_creator",
            "task_performer",
        )

    def get_task_creator(self, obj: Task) -> Optional[str]:
        task_creator = obj.task_creator
        if not task_creator:
            return None

        return task_creator.get_full_name()

    def get_task_performer(self, obj: Task) -> Optional[str]:
        task_performer = obj.task_performer
        if not task_performer:
            return None

        return task_performer.get_full_name()


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания новой задачи.

    Используется для проверки входных данных, назначения создателя задачи и
    определения времени начала задачи, если назначен исполнитель.

    Атрибуты:
        - title (CharField): Название задачи. Обязательное поле,
        уникальное для каждой задачи.
        - description (TextField): Описание задачи. Обязательное поле.
        - difficulty (IntegerField): Уровень сложности задачи.
        Обязательное поле, принимает значения от 1 до 5.
        - task_duration (DurationField): Предполагаемая продолжительность
        выполнения задачи. Обязательное поле.
        - task_creator (PrimaryKeyRelatedField): Пользователь,
        создавший задачу. Поле заполняется автоматически
        и доступно только для чтения.
        - task_performer (PrimaryKeyRelatedField): Пользователь,
        назначенный исполнителем задачи. Необязательное поле
        (исполнитель может быть назначен позже), может быть указано
        только для активных пользователей, которые не являются менеджерами.

    Методы:
        - validate_task_performer(value):
            Проверяет, активен ли назначенный исполнитель задачи.

            - Если исполнитель неактивен, поднимает ValidationError.
            - Возвращает валидированное значение.

        - validate(data):
            Проверяет, является ли текущий пользователь менеджером.

            - Если пользователь не менеджер, поднимает ValidationError.
            - Автоматически добавляет текущего пользователя как
            создателя задачи.

        - create(validated_data):
            Создаёт задачу на основе валидированных данных.

            - Если указан исполнитель, устанавливает время начала задачи.
            - Возвращает созданный объект задачи.
    """

    task_performer = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_manager=False),
        required=False,
        allow_null=False,
    )

    task_creator = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "difficulty",
            "task_duration",
            "task_creator",
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

        data["task_creator"] = user
        return data

    def create(self, validated_data):
        task_performer = validated_data.get("task_performer", None)
        task = Task.objects.create(**validated_data)

        if task_performer:
            task.time_start = timezone.localtime(timezone.now())
            task.save()

        return task


class TaskTakeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для взятия задачи исполнителем.

    Используется для проверки возможности взять задачу и обновления её статуса,
    назначая текущего пользователя исполнителем.

    Методы:
        - validate(data):
            Проверяет:
            - Является ли текущий пользователь менеджером (менеджер
            не может брать задачи).
            - Не назначен ли уже исполнитель для задачи.
            Возвращает валидированные данные, если проверка пройдена.

        - update(instance, validated_data):
            Обновляет экземпляр задачи:
            - Назначает текущего пользователя исполнителем.
            - Устанавливает время начала задачи на текущее локальное время.
            - Сохраняет изменения и возвращает обновлённый экземпляр.
    """

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
        instance.time_start = timezone.localtime(timezone.now())
        instance.save()

        return instance


class TaskAssignSerializer(serializers.ModelSerializer):
    """
    Сериализатор для назначения задачи исполнителю.

    Используется для проверки и обновления задачи с назначением
    нового исполнителя. Только менеджер, создавший задачу,
    может назначать исполнителей.

    Атрибуты:
        - task_performer (PrimaryKeyRelatedField):
        Поле для выбора исполнителя. Доступны только активные пользователи,
        которые не являются менеджерами. Обязательное поле.

    Методы:
        - validate_task_performer(value):
            Проверяет, активен ли назначенный пользователь.
            Если пользователь неактивен, выбрасывает ValidationError.

        - validate(data):
            Проверяет:
            - Является ли текущий пользователь менеджером.
            - Создал ли текущий пользователь задачу.
            - Не назначен ли уже исполнитель для задачи.
            - Возвращает валидированные данные, если все проверки пройдены.

        - update(instance, validated_data):
            Обновляет экземпляр задачи:
            - Назначает переданного исполнителя.
            - Устанавливает время начала задачи на текущее локальное время.
            - Сохраняет изменения и возвращает обновлённый экземпляр.
    """

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
        if task.task_creator != user:
            raise serializers.ValidationError(
                {"detail": "Вы не можете назначать исполнителей на задачи другого менеджера."}
            )

        if task.task_performer:
            raise serializers.ValidationError(
                {"detail": "Задача уже имеет исполнителя."}
            )

        return data

    def update(self, instance, validated_data):
        instance.task_performer = validated_data.get("task_performer")
        instance.time_start = timezone.localtime(timezone.now())
        instance.save()

        return instance


class TaskCompleteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для завершения задачи.

    Используется для отметки задачи как завершённой. Проверяет, является ли
    текущий пользователь исполнителем задачи и не завершена ли уже задача.

    Атрибуты:
        - нет дополнительных атрибутов в данном сериализаторе.

    Методы:
        - validate(data):
            Проверяет:
            - Является ли текущий пользователь менеджером.
            Менеджеры не могут завершать задачи.
            - Является ли текущий пользователь исполнителем задачи.
            - Не была ли задача уже завершена.
            Возвращает валидированные данные, если все проверки пройдены.

        - update(instance, validated_data):
            Обновляет задачу, устанавливая время завершения на текущее
            локальное время. Сохраняет изменения и возвращает
            обновлённый экземпляр задачи.
    """

    class Meta:
        model = Task
        fields = ()

    def validate(self, data):
        user = self.context["request"].user
        if user.is_manager:
            raise serializers.ValidationError(
                {"detail": "Менеджер не может сдать задачу."}
            )

        task = self.instance
        if task.task_performer != user:
            raise serializers.ValidationError(
                {"detail": "Вы не являетесь исполнителем этой задачи."}
            )

        if task.time_completion:
            raise serializers.ValidationError(
                {"detail": "Эта задача уже завершена."}
            )

        return data

    def update(self, instance, validated_data):
        instance.time_completion = timezone.localtime(timezone.now())
        instance.save()

        return instance
