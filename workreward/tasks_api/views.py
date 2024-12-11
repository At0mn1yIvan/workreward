from common.utils import send_email
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import APIListPagination
from .renderers import TaskJSONRenderer
from django.utils import timezone
from .models import Task
from common.permissions import IsManager
from . import serializers


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    permission_classes = (AllowAny,)
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskSerializer
    pagination_class = APIListPagination


class TaskCreateAPIView(APIView):
    permission_classes = (
        IsAuthenticated,
        IsManager,
    )
    renderer_classes = (TaskJSONRenderer,)
    serializer_class = serializers.TaskCreateSerializer

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


class TaskTakeAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (TaskJSONRenderer,)

    def patch(self, request, pk, *args, **kwargs):
        try:
            task = get_object_or_404(Task, pk=pk)
        except Http404:
            return Response(
                {"detail": "Задача с указанным идентификатором не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if task.task_performer:
            return Response(
                {"detail": "Задача уже взята."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if user.is_manager:
            return Response(
                {"detail": "Менеджер не может брать задачи."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.task_performer = user
        task.time_start = timezone.now()
        task.save()

        return Response(
            {"detail": f"Вы успешно взяли задачу с id: {task.pk}."},
            status=status.HTTP_200_OK,
        )
