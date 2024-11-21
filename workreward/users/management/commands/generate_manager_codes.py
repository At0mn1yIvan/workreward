import random
import string

from django.core.management.base import BaseCommand
from users.models import ManagerCode


class Command(BaseCommand):
    help = "Генерация кодов для менеджеров"

    def add_arguments(self, parser):
        parser.add_argument("count", type=int, help="Количество кодов для генерации")
        parser.add_argument(
            "--length",
            type=int,
            default=8,
            help="Длина каждого кода (по умолчанию 8 символов)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        length = options["length"]

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
