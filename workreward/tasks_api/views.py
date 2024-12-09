from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users_api.renderers import UserJSONRenderer
from common.utils import send_email
from .permissions import IsManager
from .serializers import TaskCreateSerializer


class TaskCreateAPIView(APIView):
    permission_classes = (IsAuthenticated, IsManager)
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
        if task_performer:
            try:
                manager = request.user
                send_email(
                    subject="Назначение на задачу",
                    message=f"Менеджер {manager.get_full_name()} назначил Вас на задачу '{task.title}'.",
                    recipient_list=[task_performer.email],
                )
            except Exception as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
