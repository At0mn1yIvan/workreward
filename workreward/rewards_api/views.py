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
    """
    ViewSet для получения объектов премий.

    Атрибуты:
        - permission_classes (tuple): Кортеж, определяющий классы разрешений.
        В данном случае доступ к API разрешен только пользователям,
        не являющимся менеджерами.
        - renderer_classes (tuple): Кортеж с рендерами,
        определяющий формат вывода данных. В данном случае используется
        кастомный рендерер RewardJSONRenderer.
        - serializer_class: Сериализатор для работы с моделью `Reward`.
        Определяет, как данные вознаграждений будут
        сериализованы и десериализованы.
        - pagination_class: Класс пагинации для разбиения
        списка вознаграждений на страницы.

    Методы:
        - get_queryset():
            Возвращает список вознаграждений для текущего пользователя
            (исполнителя задачи). Фильтрует вознаграждения по
            пользователю-исполнителю задачи, для которой был создан отчет.
    """

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
    """
    Представление для создания (выдачи) нового вознаграждения (премии)
    за выполнение задачи.

    Данное представление используется менеджерами для назначения премии
    исполнителю задачи на основе отчета о выполнении задачи.
    Премия назначается только в случае, если отчет существует и
    еще не была выдана премия за данную задачу.

    Атрибуты:
        - permission_classes (tuple): Кортеж, определяющий классы разрешений.
        Доступ предоставляется только менеджерам.
        - renderer_classes (tuple): Кортеж с рендерами,
        определяющий формат вывода данных. В данном случае используется
        кастомный рендерер RewardJSONRenderer.
        - class_serializer: Сериализатор, используемый для обработки данных,
        создания вознаграждения.

    Методы:
        - post(request, report_pk, *args, **kwargs):
            Создает новое вознаграждение для исполнителя задачи.
            Процесс включает в себя:
                - Получение отчета по задаче через `report_pk`.
                - Валидация данных через сериализатор.
                - Вычисление суммы вознаграждения на основе данных отчета.
                - Отправка уведомления пользователю (исполнителю задачи)
                о назначении премии.
                - Возврат созданного вознаграждения в ответе.

            В случае ошибок при создании или отправке уведомления,
            возвращается ошибка с кодом 500.
    """

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

        send_reward_notification(reward.pk, request)

        # try:
        #     send_reward_notification(reward.pk, request)
        # except Exception as e:
        #     return Response(
        #         {"detail": str(e)},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
