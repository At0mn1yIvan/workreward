from common.pagination import APIListPagination
from common.permissions import IsNotManager
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from tasks_api.models import Task
from .utils import send_report_done_notification

from . import serializers
from .models import TaskReport
from .renderers import ReportJSONRenderer


class TaskReportViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ReportJSONRenderer,)
    serializer_class = serializers.TaskReportSerializer
    pagination_class = APIListPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return TaskReport.objects.filter(
                task__task_creator=user
            ).select_related("task")
        else:
            return TaskReport.objects.filter(
                task__task_performer=user
            ).select_related("task")


class TaskReportCreateAPIView(APIView):
    permission_classes = (IsNotManager,)
    renderer_classes = (ReportJSONRenderer,)
    class_serializer = serializers.TaskReportCreateSerializer

    def post(self, request, task_pk, *args, **kwargs):
        task = get_object_or_404(Task.objects.select_related("task_creator"), pk=task_pk)

        serializer = self.class_serializer(
            data=request.data, context={"request": request, "task": task}
        )
        serializer.is_valid(raise_exception=True)
        task_report = serializer.save()

        try:
            send_report_done_notification(task_report, request)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
