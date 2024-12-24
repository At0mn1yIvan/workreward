from common.pagination import APIListPagination
from common.permissions import IsManager, IsNotManager
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import serializers
from .models import Task
from .renderers import TaskJSONRenderer
from .utils import send_task_assign_notification


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для получения объектов задач.

    Доступ к задачам ограничен в зависимости от роли пользователя:
    - Менеджеры могут просматривать и управлять только задачами,
    которые они создали.
    - Исполнители могут просматривать только те задачи,
    которые ещё не имеют исполнителя.

    Атрибуты:
        - permission_classes (tuple): Кортеж с разрешениями для доступа.
        В данном случае требуется, чтобы пользователь был аутентифицирован.
        - renderer_classes (tuple): Кортеж с рендерами,
        определяющий формат вывода данных. В данном случае используется
        кастомный рендерер TaskJSONRenderer.
        - serializer_class (serializers.TaskSerializer): Сериализатор,
        используемый для преобразования данных модели Task в формат JSON.
        - pagination_class (APIListPagination): Класс пагинации
        для разбиения списка задач на страницы.

    Методы:
        - get_queryset():
            Определяет, какие задачи доступны для пользователя,
            основываясь на его роли:
            - Менеджеры могут видеть только задачи, которые они создали.
            - Исполнители могут видеть задачи, которые
            ещё не имеют исполнителя.
    """

    permission_classes = (IsAuthenticated,)
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskSerializer
    pagination_class = APIListPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_manager:
            queryset = Task.objects.filter(
                task_creator=user
            )
        else:
            queryset = Task.objects.filter(
                task_performer__isnull=True
            )
        return queryset.select_related("task_creator", "task_performer")


class UserTasksAPIView(ListAPIView):
    """
    Представление для получения списка задач,
    назначенных текущему пользователю.

    Это представление доступно только для исполнителей.
    Менеджеры не могут иметь свои задачи.

    Атрибуты:
        - permission_classes (tuple): Кортеж с разрешениями для доступа.
        В данном случае доступ разрешен только тем, кто не является менеджером.
        - renderer_classes (tuple): Кортеж с рендерами, определяющий формат
        вывода данных. Используется кастомный рендерер TaskJSONRenderer.
        - serializer_class (serializers.TaskSerializer): Сериализатор,
        используемый для преобразования данных модели Task в формат JSON.
        - pagination_class (APIListPagination): Класс пагинации для разбиения
        списка задач на страницы.

    Методы:
        - get_queryset():
            Получает список задач, назначенных текущему пользователю,
            если он не является менеджером. Если пользователь — менеджер,
            выбрасывается ошибка валидации.
    """

    permission_classes = (IsNotManager,)
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskSerializer
    pagination_class = APIListPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return serializers.ValidationError(
                {"detail": "У менеджеров не может быть своих задач."},
            )
        return Task.objects.filter(task_performer=user)


class TaskCreateAPIView(APIView):
    """
    Представление для создания новой задачи.

    Это представление доступно только для менеджеров,
    которые могут создавать задачи для назначения исполнителям.

    Атрибуты:
        - permission_classes (tuple): Кортеж с разрешениями для доступа.
        В данном случае доступ разрешен только менеджерам.
        - renderer_classes (tuple): Кортеж с рендерами, определяющий
        формат вывода данных. Используется кастомный рендерер TaskJSONRenderer.
        - serializer_class (serializers.TaskCreateSerializer):
        Сериализатор, используемый для преобразования данных,
        полученных от клиента, в формат задачи.

    Методы:
        - post(request, *args, **kwargs):
            Создает новую задачу на основе данных из запроса. После создания
            задачи отправляется уведомление назначенному исполнителю.
            В случае ошибки при отправке уведомления возвращается ошибка.
    """

    permission_classes = (IsManager,)
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        try:
            send_task_assign_notification(task.pk, request)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskTakeAPIView(APIView):
    """
    Представление для того, чтобы пользователь взял задачу.

    Это представление доступно пользователям, которые не являются менеджерами,
    чтобы они могли взять задачи, назначенные для выполнения. Задача будет
    назначена текущему пользователю, и будет зафиксировано время начала задачи.

    Атрибуты:
        - permission_classes (tuple): Кортеж с разрешениями для доступа.
        Это представление доступно только не-менеджерам.
        - renderer_classes (tuple): Кортеж с рендерами, определяющий
        формат вывода данных. Используется кастомный рендерер TaskJSONRenderer.
        - serializer_class (serializers.TaskTakeSerializer): Сериализатор,
        используемый для обработки данных при взятии задачи.

    Методы:
        - patch(request, pk, *args, **kwargs):
            Обрабатывает запрос на взятие задачи, присваивает текущего
            пользователя как исполнителя, записывает время начала
            выполнения задачи.
    """

    permission_classes = (IsNotManager,)
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskTakeSerializer

    def patch(self, request, pk, *args, **kwargs):
        task = get_object_or_404(Task, pk=pk)

        serializer = self.serializer_class(
            instance=task,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": f"Вы успешно взяли задачу с id: {task.pk}."},
            status=status.HTTP_200_OK,
        )


class TaskAssignAPIView(APIView):
    """
    Представление для назначения задачи исполнителю.

    Это представление доступно только менеджерам и позволяет им назначить
    исполнителя для задачи. После назначения отправляется
    уведомление исполнителю.

    Атрибуты:
        - permission_classes (tuple): Кортеж с разрешениями для доступа.
        Это представление доступно только менеджерам.
        - renderer_classes (tuple): Кортеж с рендерами, определяющий
        формат вывода данных. Используется кастомный рендерер TaskJSONRenderer.
        - serializer_class (serializers.TaskAssignSerializer): Сериализатор
        для назначения задачи исполнителю.

    Методы:
        - patch(request, pk, *args, **kwargs):
            Обрабатывает запрос на назначение задачи исполнителю,
            отправляет уведомление о назначении задачи.
    """

    permission_classes = (IsManager,)
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskAssignSerializer

    def patch(self, request, pk, *args, **kwargs):
        task = get_object_or_404(Task, pk=pk)

        serializer = self.serializer_class(
            instance=task,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        task_assigned = serializer.save()

        try:
            send_task_assign_notification(task_assigned.pk, request)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "detail": (
                    f"Задача с id '{task_assigned.pk}' назначена пользователю {task_assigned.task_performer.get_full_name()}."
                )
            },
            status=status.HTTP_200_OK,
        )


class TaskCompleteAPIView(APIView):
    """
    Представление для завершения задачи.

    Это представление доступно только для исполнителей задач.
    Оно позволяет завершить задачу, если она была назначена
    исполнителю, и обновить время завершения задачи.

    Атрибуты:
        - permission_classes (tuple): Кортеж с разрешениями для доступа.
        Это представление доступно только исполнителям.
        - renderer_classes (tuple): Кортеж с рендерами, определяющий
        формат вывода данных. Используется кастомный рендерер TaskJSONRenderer.
        - serializer_class (serializers.TaskCompleteSerializer):
        Сериализатор для завершения задачи.

    Методы:
        - patch(request, pk, *args, **kwargs):
            Обрабатывает запрос на завершение задачи и обновляет ее статус.
    """

    permission_classes = (IsNotManager,)
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskCompleteSerializer

    def patch(self, request, pk, *args, **kwargs):
        task = get_object_or_404(Task, pk=pk)

        serializer = self.serializer_class(
            instance=task,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": f"Задача с id '{task.pk}' успешно завершена."},
            status=status.HTTP_200_OK,
        )
