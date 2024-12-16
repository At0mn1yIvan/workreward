from django.urls import reverse
from tasks_api.models import Task
from common.utils import send_email

from .models import TaskReport


def calculate_performer_efficiency(task: Task) -> float:
    time_taken_seconds = (task.time_completion - task.time_start).total_seconds()
    if time_taken_seconds <= 0:
        return 0

    task_duration_seconds = task.task_duration.total_seconds()

    STABILIZING_COEF = 0.8
    time_efficiency = (task_duration_seconds / time_taken_seconds) * STABILIZING_COEF

    DIFF_LEVELS = 5
    difficulty_efficiency = task.difficulty / DIFF_LEVELS

    return time_efficiency * (1 + difficulty_efficiency)


def send_report_done_notification(task_report: TaskReport, request) -> None:

    task_performer = request.user
    manager = task_report.task.task_creator
    report_url = request.build_absolute_uri(
        reverse("reports_api:report_detail", kwargs={"pk": task_report.pk})
    )
    subject = "Уведомление о завершении задачи. Отчёт оформлен."
    message = (
        f"Исполнитель {task_performer.get_full_name()} завершил задачу '{task_report.task.title}' и создал отчёт.\n"
        f"Посмотреть отчёт: {report_url}"
    )
    try:
        send_email(
            subject=subject,
            message=message,
            recipient_list=[manager.email],
        )
    except Exception as e:
        error_message = (
            f"Ошибка при отправке уведомления: {str(e)}\n"
            "Возможно, менеджер указал несуществующую почту."
        )
        raise Exception(error_message)
