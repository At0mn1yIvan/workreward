from django.urls import reverse
from common.utils import send_email
from users.models import User
from .models import Task


def send_task_notification(task: Task, manager: User, request) -> None:
    if not task.task_performer:
        return

    task_performer = task.task_performer
    manager = request.user
    task_url = request.build_absolute_uri(
        reverse("tasks_api:task_detail", kwargs={"pk": task.pk})
    )
    subject = "Назначение на задачу"
    message = (
        f"Менеджер {manager.get_full_name()} назначил Вас на задачу '{task.title}'.\n"
        f"Посмотреть задачу: {task_url}"
    )
    try:
        send_email(
            subject=subject,
            message=message,
            recipient_list=[task_performer.email],
        )
    except Exception as e:
        error_message = (
            "Исполнитель назначен на задачу.\n"
            f"Ошибка при отправке уведомления: {str(e)}\n"
            "Возможно, исполнитель указал несуществующую почту."
        )
        raise Exception(error_message)
