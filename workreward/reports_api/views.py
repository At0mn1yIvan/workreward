from django.http import HttpResponse
from common.pagination import APIListPagination
from common.permissions import IsManager, IsNotManager
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from tasks_api.models import Task
from .utils import generate_task_report_pdf, send_report_done_notification

from . import serializers
from .models import TaskReport
from .renderers import ReportJSONRenderer


class TaskReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet для получения объектов отчётов по задачам.

    Атрибуты:
        - permission_classes (tuple): Определяет, что доступ к данному API
        имеют только аутентифицированные пользователи.
        - renderer_classes (tuple): Определяет, что ответы будут рендериться
        в формате JSON с использованием рендерера ReportJSONRenderer.
        - serializer_class (serializers.TaskReportSerializer): Сериализатор для
        преобразования данных отчёта в JSON и обратно.
        - pagination_class (APIListPagination): Класс пагинации для разделения
        результатов на страницы.

    Методы:
        - get_queryset(): Определяет, какие отчёты могут быть получены
        пользователем в зависимости от его роли (менеджер или исполнитель).
    """

    permission_classes = (IsAuthenticated,)
    renderer_classes = (ReportJSONRenderer,)
    serializer_class = serializers.TaskReportSerializer
    pagination_class = APIListPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            queryset = TaskReport.objects.filter(
                task__task_creator=user
            )
        else:
            queryset = TaskReport.objects.filter(
                task__task_performer=user
            )
        return queryset.select_related("task")


class TaskReportCreateAPIView(APIView):
    """
    Представление для создания отчёта по задаче.

    Этот класс предоставляет API для создания отчётов по задачам, и доступен
    только для пользователей, которые не являются менеджерами. После создания
    отчёта, отправляется уведомление о завершении задачи.

    Атрибуты:
        - permission_classes (tuple): Определяет, что доступ к данному API
        имеют пользователи, которые не являются менеджерами.
        - renderer_classes (tuple): Определяет, что ответы будут рендериться
        в формате JSON с использованием рендерера ReportJSONRenderer.
        - class_serializer (serializers.TaskReportCreateSerializer):
        Сериализатор для создания отчётов по задачам.

    Методы:
        - post(): Создаёт отчёт по задаче,
        проверяя права доступа и валидируя данные.
    """

    permission_classes = (IsNotManager,)
    renderer_classes = (ReportJSONRenderer,)
    class_serializer = serializers.TaskReportCreateSerializer

    def post(self, request, task_pk, *args, **kwargs):
        task = get_object_or_404(Task, pk=task_pk)

        serializer = self.class_serializer(
            data=request.data, context={"request": request, "task": task}
        )
        serializer.is_valid(raise_exception=True)
        task_report = serializer.save()

        send_report_done_notification(task_report.pk, request)

        # try:
        #     send_report_done_notification(task_report.pk, request)
        # except Exception as e:
        #     return Response(
        #         {"detail": str(e)},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskReportDownloadAPIView(APIView):
    """
    Представление для скачивания отчёта по задаче в формате PDF.

    Атрибуты:
        - permission_classes (tuple): Определяет, что доступ
        к данному API имеют только менеджеры.

    Методы:
        - get(): Обрабатывает GET-запрос, генерирует PDF-отчёт по задаче
          и возвращает его в виде ответа.
    """

    permission_classes = (IsManager,)

    def get(self, request, pk, *args, **kwargs):
        task_report = get_object_or_404(
            TaskReport.objects.select_related(
                "task", "task__task_creator", "task__task_performer"
            ),
            pk=pk,
        )

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f"attachment; filename=report_{task_report.pk}.pdf"
        )

        generate_task_report_pdf(task_report, response)

        return response
