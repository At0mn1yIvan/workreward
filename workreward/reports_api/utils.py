from datetime import datetime, timedelta
from typing import Any

from django.http import HttpRequest

from workreward import settings
from common.utils import send_email
from django.urls import reverse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from tasks_api.models import Task

from .models import TaskReport


def calculate_performer_efficiency(task: Task) -> float:
    time_taken_seconds = (
        task.time_completion - task.time_start
    ).total_seconds()
    if time_taken_seconds <= 0:
        return 0

    task_duration_seconds = task.task_duration.total_seconds()

    STABILIZING_COEF = 0.8
    time_efficiency = (
        task_duration_seconds / time_taken_seconds
    ) * STABILIZING_COEF

    DIFF_LEVELS = 5
    difficulty_efficiency = task.difficulty / DIFF_LEVELS

    return time_efficiency * (1 + difficulty_efficiency)


def send_report_done_notification(task_report_pk: int, request: HttpRequest) -> None:
    task_report = TaskReport.objects.select_related(
        "task", "task__task_creator"
    ).get(pk=task_report_pk)
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


class ReportGenerator:
    def __init__(self, task_report, response):
        self.task_report = task_report
        self.response = response
        self.doc = SimpleDocTemplate(
            response, pagesize=letter, leftMargin=20 * mm, rightMargin=20 * mm
        )
        self.styles = getSampleStyleSheet()
        self._initialize_fonts()
        self._create_styles()

    def _initialize_fonts(self):
        font_path = settings.BASE_DIR / "reports_api" / "fonts"

        pdfmetrics.registerFont(
            TTFont("DejaVu", font_path / "DejaVuSansCondensed.ttf")
        )
        pdfmetrics.registerFont(
            TTFont("DejaVu-Bold", font_path / "DejaVuSansCondensed-Bold.ttf")
        )

    def _create_styles(self) -> None:
        self.normal_style = ParagraphStyle(
            "CustomStyle",
            parent=self.styles["Normal"],
            fontName="DejaVu",
            fontSize=14,
            leading=20,
        )
        self.bold_style = ParagraphStyle(
            "BoldStyle",
            parent=self.styles["Normal"],
            fontName="DejaVu-Bold",
            fontSize=14,
            leading=20,
        )
        self.title_style = ParagraphStyle(
            "TitleStyle",
            parent=self.styles["Heading1"],
            fontName="DejaVu",
            fontSize=22,
            leading=30,
        )

    def format_timedelta(self, td_object: timedelta) -> str:
        total_seconds = td_object.total_seconds()
        DAY_SECONDS = 86400
        HOUR_SECONDS = 3600
        MIN_SECONDS = 60

        days, remainder = divmod(total_seconds, DAY_SECONDS)
        hours, remainder = divmod(remainder, HOUR_SECONDS)
        minutes, seconds = divmod(remainder, MIN_SECONDS)

        time_str = f"часы: {int(hours)} | минуты: {int(minutes)} | секунды: {int(seconds)}"
        if days:
            return f"дни: {int(days)} |" + time_str
        else:
            return time_str

    def generate_report_data(self) -> dict[str, Any]:
        actual_task_duration = (
            self.task_report.task.time_completion
            - self.task_report.task.time_start
        )

        return {
            "Задача:": self.task_report.task.title,
            "Описание задачи:": self.task_report.task.description,
            "Сложность задачи:": self.task_report.task.difficulty,
            "Предполагаемая длительность задачи:": self.format_timedelta(
                self.task_report.task.task_duration
            ),
            "Фактическое время выполнения задачи:": self.format_timedelta(
                actual_task_duration
            ),
            "Исполнитель задачи:": self.task_report.task.task_performer.get_full_name(),
            "Создатель задачи (менеджер):": self.task_report.task.task_creator.get_full_name(),
            "Эффективность исполнителя в текущей задаче:": round(
                self.task_report.efficiency_score, 2
            ),
            "Текст отчёта:": self.task_report.text,
            "Дата создания отчёта:": datetime.strftime(
                self.task_report.time_create, "%d/%m/%Y %H:%M:%S"
            ),
        }

    def build_pdf(self) -> None:
        report_data = self.generate_report_data()
        elements = []
        elements.append(
            Paragraph(
                f"Отчёт по задаче №{self.task_report.id}", self.title_style
            )
        )
        elements.append(Spacer(1, 12))

        for title, data in report_data.items():
            elements.append(Paragraph(title, self.bold_style))
            elements.append(Paragraph(f"{data}", self.normal_style))
            elements.append(Spacer(1, 6))

        self.doc.build(elements)


def generate_task_report_pdf(task_report, response) -> None:
    report = ReportGenerator(task_report, response)
    report.build_pdf()
