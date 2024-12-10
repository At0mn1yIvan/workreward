from rest_framework.generics import ListAPIView
from common.utils import send_email
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users_api.renderers import UserJSONRenderer

from .models import Task
from .permissions import IsManager
from .serializers import TaskCreateSerializer, TaskSerializer


class TaskCreateAPIView(APIView):
    permission_classes = (
        IsAuthenticated,
        IsManager,
    )
    renderer_classes = (UserJSONRenderer,)
    serializer_class = TaskCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        task_performer = task.task_performer
        manager = request.user
        task_url = request.build_absolute_uri(f"/api/v1/tasks/{task.pk}/")

        if task_performer:
            try:
                send_email(
                    subject="Назначение на задачу",
                    message=(
                        f"Менеджер {manager.get_full_name()} назначил Вас на задачу '{task.title}'.\n"
                        f"Посмотреть задачу: {task_url}"
                    ),
                    recipient_list=[task_performer.email],
                )
            except Exception as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = TaskSerializer

    def get(self, request, task_id, *args, **kwargs):
        try:
            task = get_object_or_404(Task, pk=task_id)
        except Http404:
            return Response(
                {"detail": "Задача с указанным идентификатором не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.serializer_class(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskListAPIView(ListAPIView):
    queryset = Task.objects.all()
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = TaskSerializer
