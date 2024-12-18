from common.utils import send_email
from reports_api.models import TaskReport
from .models import Reward


def send_reward_notification(reward_pk: int, request) -> None:
    reward = Reward.objects.select_related(
        "task_report", "task_report__task", "task_report__task__task_performer"
    ).get(pk=reward_pk)

    task = reward.task_report.task
    task_performer = task.task_performer
    manager = request.user

    subject = "Уведомление о получении премии."
    message = (
        f"Менеджер {manager.get_full_name()} назначил вам премию в {reward.reward_sum} рублей за задачу '{task.title}'.\n"
        f"Комментарий менеджера: {reward.comment}"
    )
    try:
        send_email(
            subject=subject,
            message=message,
            recipient_list=[task_performer.email],
        )
    except Exception as e:
        error_message = (
            f"Ошибка при отправке уведомления: {str(e)}\n"
            "Возможно, исполнитель указал несуществующую почту."
        )
        raise Exception(error_message)
