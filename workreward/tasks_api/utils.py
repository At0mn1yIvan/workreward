from django.http import HttpRequest
from common.utils import send_email
from django.urls import reverse

from .models import Task


def send_task_assign_notification(task_pk: int, request: HttpRequest) -> None:
    """
    Отправка уведомления исполнителю о назначении его на задачу.

    Функция используется для отправки уведомления исполнителю о том,
    что ему была назначена задача менеджером. Уведомление отправляется
    на электронную почту исполнителя с ссылкой на задачу.


    Аргументы:
        - task_pk (int): Идентификатор задачи,
        на которую назначается исполнитель.
        - request (HttpRequest): Объект запроса, содержащий информацию
        о текущем пользователе (менеджере) и домене сайта.
    """
    task = Task.objects.select_related("task_performer").get(pk=task_pk)
    if not task.task_performer:
        return

    task_performer = task.task_performer
    manager = request.user
    my_tasks_url = request.build_absolute_uri("/my-tasks")
    subject = "Назначение на задачу"
    message = (
        f"Менеджер {manager.get_full_name()} назначил Вас на задачу '{task.title}'.\n"
        f"Список ваших задач: {my_tasks_url}"
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
    #         "Исполнитель назначен на задачу.\n"
    #         f"Ошибка при отправке уведомления: {str(e)}\n"
    #         "Возможно, исполнитель указал несуществующую почту."
    #     )
    #     raise Exception(error_message)
