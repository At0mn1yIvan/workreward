import random
import string

from django.core.management.base import BaseCommand
from users.models import ManagerCode


class Command(BaseCommand):
    """
    Класс, описывающий команду для генерации уникальных кодов менеджеров и сохранения их в базе данных.

    Эта команда создаёт заданное количество уникальных кодов определённой длины и сохраняет их
    в модель ManagerCode. Каждый код состоит из заглавных латинских букв и цифр.

    Атрибуты:
        help (str): Краткое описание команды для справки.

    Методы:
        add_arguments(parser):
            Добавляет аргументы (количество кодов, длина кодов) командной строки для управления генерацией кодов.

        handle(*args, **kwargs):
            Основная логика выполнения команды: генерирует и сохраняет коды.

    Аргументы командной строки:
        count (int): Обязательный аргумент. Количество кодов для генерации.
        --length (int): Необязательный аргумент. Длина каждого кода (по умолчанию 8 символов).

    Пример использования:
        python manage.py generate_manager_codes 10 --length 12
        Этот пример создаст 10 уникальных кодов длиной по 12 символов.
    """

    help = "Генерация кодов для менеджеров"

    def add_arguments(self, parser):
        parser.add_argument("count", type=int, help="Количество кодов для генерации")
        parser.add_argument(
            "--length",
            type=int,
            default=8,
            help="Длина каждого кода (по умолчанию 8 символов)",
        )

    def handle(self, *args, **kwargs):
        count = kwargs["count"]
        length = kwargs["length"]

        codes = []
        for _ in range(count):
            while True:
                code = "".join(
                    random.choices(string.ascii_uppercase + string.digits, k=length)
                )
                if not ManagerCode.objects.filter(code=code).exists():
                    break
            codes.append(ManagerCode(code=code))

        ManagerCode.objects.bulk_create(codes)
