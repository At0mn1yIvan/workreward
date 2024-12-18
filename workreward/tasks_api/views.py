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
    permission_classes = (IsAuthenticated,)
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskSerializer
    pagination_class = APIListPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_manager:
            return Task.objects.filter(
                task_creator=user
            ).select_related("task_creator", "task_performer")
        else:
            return Task.objects.filter(
                task_performer__isnull=True
            ).select_related("task_creator", "task_performer")


class UserTasksAPIView(ListAPIView):
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
