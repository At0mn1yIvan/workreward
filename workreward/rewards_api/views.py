from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsManager, IsNotManager
from reports_api.models import TaskReport
from common.pagination import APIListPagination
from .models import Reward
from .utils import send_reward_notification
from .renderers import RewardJSONRenderer
from . import serializers


class RewardViewSet(viewsets.ModelViewSet):
    permission_classes = (IsNotManager,)
    renderer_classes = (RewardJSONRenderer,)
    serializer_class = serializers.RewardSerializer
    pagination_class = APIListPagination

    def get_queryset(self):
        user = self.request.user
        return Reward.objects.filter(
            task_report__task__task_performer=user
        )


class RewardCreateAPIView(APIView):
    permission_classes = (IsManager,)
    renderer_classes = (RewardJSONRenderer,)
    class_serializer = serializers.RewardCreateSerializer

    def post(self, request, report_pk, *args, **kwargs):
        report = get_object_or_404(
            TaskReport.objects.select_related("task"), pk=report_pk
        )

        serializer = self.class_serializer(
            data=request.data, context={"request": request, "report": report}
        )
        serializer.is_valid(raise_exception=True)
        reward = serializer.save()

        try:
            send_reward_notification(reward.pk, request)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
