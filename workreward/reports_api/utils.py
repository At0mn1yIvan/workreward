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
    """
    Вычисление эффективности исполнителя задачи
    на основе времени выполнения задачи и её сложности.

    Эффективность определяется как отношение
    предполагаемого времени выполнения задачи
    к фактическому времени выполнения, с учетом сложности задачи.

    Формула вычисления:
    - Эффективность времени = (предполагаемое время выполнения / фактическое время выполнения) * стабилизирующий коэффициент
    - Эффективность по сложности = (уровень сложности задачи / количество уровней сложности)
    - Общая эффективность = (эффективность времени) * (1 + эффективность по сложности)

    Аргументы:
        - task (Task): Объект задачи, для которой рассчитывается эффективность.

    Возвращаемое значение:
        - float: Значение эффективности исполнителя задачи.
        Если время выполнения задачи некорректно (меньше или равно нулю),
        возвращается 0.
    """
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
    """
    Отправка уведомления менеджеру о завершении задачи
    и создании отчёта исполнителем.

    Уведомление включает информацию о завершённой задаче, имени исполнителя
    и ссылке на созданный отчёт. Уведомление отправляется на электронную почту
    менеджера, который является создателем задачи.


    Аргументы:
        - task_report_pk (int): Идентификатор отчёта,
        для которого отправляется уведомление.
        - request (HttpRequest): Объект запроса, содержащий информацию
        о текущем пользователе (менеджере) и домене сайта.
    """
    task_report = TaskReport.objects.select_related(
        "task", "task__task_creator"
    ).get(pk=task_report_pk)
    task_performer = request.user
    manager = task_report.task.task_creator
    my_reports_url = request.build_absolute_uri("/reports")
    subject = "Уведомление о завершении задачи. Отчёт оформлен."
    message = (
        f"Исполнитель {task_performer.get_full_name()} завершил задачу '{task_report.task.title}' и создал отчёт.\n"
        f"Отчёты по созданным вами задачам: {my_reports_url}"
    )

    try:
        send_email(
            subject=subject,
            message=message,
            recipient_list=[manager.email],
        )
    except Exception:
        pass


class ReportGenerator:
    """
    Генератор отчётов для задач, который создаёт PDF документ с информацией
    о задаче и её исполнении.

    Класс используется для создания PDF отчётов
    с подробной информацией о задаче, её исполнителе, длительности,
    сложности и эффективности исполнения.

    Атрибуты:
        - task_report (TaskReport): Объект отчёта, содержащий информацию
        о задаче и её выполнении.
        - response (HttpResponse): Ответ HTTP,
        в который будет записан сгенерированный PDF файл.
        - doc (SimpleDocTemplate): Объект для создания PDF документа.
        - styles (StyleSheet1): Набор стандартных стилей
        для форматирования текста в PDF.
        - normal_style (ParagraphStyle): Кастомный стиль для обычного текста.
        - bold_style (ParagraphStyle): Кастомный стиль для жирного текста.
        - title_style (ParagraphStyle): Кастомный стиль для заголовков.

    Методы:
        - _initialize_fonts(): Регистрирует шрифты для использования в PDF.
        - _create_styles(): Создаёт кастомные стили для текста.
        - format_timedelta(td_object): Форматирует объект timedelta
        в строку с информацией о времени.
        - generate_report_data(): Генерирует данные для отчёта в виде словаря.
        - build_pdf(): Строит и генерирует PDF файл с отчётом по задаче.

    Примечания:
        - Шрифты DejaVu Sans Condensed и DejaVu Sans Condensed Bold
        используются для текстов в отчёте и использованы
        для корректного отображения кириллицы.
        - Все данные для отчёта извлекаются из объекта TaskReport,
        связанного с задачей.
    """

    def __init__(self, task_report, response):
        """
        Инициализирует объект генератора отчёта.

        Аргументы:
            - task_report (TaskReport): Объект отчёта, содержащий информацию
            о задаче и её выполнении.
            - response (HttpResponse): Ответ HTTP, в который будет записан
            сгенерированный PDF файл.
        """
        self.task_report = task_report
        self.response = response
        self.doc = SimpleDocTemplate(
            response, pagesize=letter, leftMargin=20 * mm, rightMargin=20 * mm
        )
        self.styles = getSampleStyleSheet()
        self._initialize_fonts()
        self._create_styles()

    def _initialize_fonts(self):
        """
        Регистрирует шрифты для использования в PDF.
        """
        font_path = settings.BASE_DIR / "reports_api" / "fonts"

        pdfmetrics.registerFont(
            TTFont("DejaVu", font_path / "DejaVuSansCondensed.ttf")
        )
        pdfmetrics.registerFont(
            TTFont("DejaVu-Bold", font_path / "DejaVuSansCondensed-Bold.ttf")
        )

    def _create_styles(self) -> None:
        """
        Создаёт кастомные стили для текста, которые используются в отчёте.
        """
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
        """
        Форматирует объект timedelta в строку
        с информацией о времени (дни, часы, минуты, секунды).

        Аргументы:
            - td_object (timedelta): Объект времени для форматирования.

        Возвращаемое значение:
            - str: Строка, представляющая временной интервал
            в формате "дни: X | часы: Y | минуты: Z | секунды: W".
        """
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
        """
        Генерирует данные для отчёта в виде словаря.

        Возвращаемое значение:
            - dict: Словарь, содержащий данные отчёта.
        """
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
        """
        Строит и генерирует PDF файл с отчётом по задаче.
        """
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
    """
    Генерирует PDF отчет по задаче и отправляет его в ответ.

    Эта функция использует класс `ReportGenerator` для создания PDF документа,
    который содержит информацию о задаче и её исполнении, и передает его в
    объект `response`.

    Аргументы:
        - task_report (TaskReport): Объект отчёта, содержащий информацию
        о задаче и её выполнении.
        - response (HttpResponse): Ответ HTTP,
        в который будет записан сгенерированный PDF файл.

    Возвращаемое значение:
        - None
    """
    report = ReportGenerator(task_report, response)
    report.build_pdf()
