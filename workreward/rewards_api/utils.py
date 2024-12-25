from django.http import HttpRequest
from common.utils import send_email

from .models import Reward


def send_reward_notification(reward_pk: int, request: HttpRequest) -> None:
    """
    Отправка уведомления исполнителю о назначении премии за выполнение задачи.

    Функция извлекает информацию о вознаграждении, связанной задаче
    и исполнителе, а затем отправляет уведомление на электронную почту
    исполнителя. Уведомление содержит информацию о сумме вознаграждения
    и комментарии менеджера.


    Аргументы:
        - task_pk (int): Идентификатор задачи,
        на которую назначается исполнитель.
        - request (HttpRequest): Объект запроса, содержащий информацию
        о текущем пользователе (менеджере) и домене сайта.
    """
    reward = Reward.objects.select_related(
        "task_report", "task_report__task", "task_report__task__task_performer"
    ).get(pk=reward_pk)

    task = reward.task_report.task
    task_performer = task.task_performer
    manager = request.user

    subject = "Уведомление о получении премии."
    message = (
        f"Менеджер {manager.get_full_name()} назначил вам премию в {reward.reward_sum} рублей за задачу '{task.title}'.\n\n"
        f"Комментарий менеджера: {reward.comment}"
    )

    try:
        send_email(
            subject=subject,
            message=message,
            recipient_list=[task_performer.email],
        )
    except Exception:
        pass

    # try:
    #     send_email(
    #         subject=subject,
    #         message=message,
    #         recipient_list=[task_performer.email],
    #     )
    # except Exception as e:
    #     error_message = (
    #         f"Ошибка при отправке уведомления: {str(e)}\n"
    #         "Возможно, исполнитель указал несуществующую почту."
    #     )
    #     raise Exception(error_message)
