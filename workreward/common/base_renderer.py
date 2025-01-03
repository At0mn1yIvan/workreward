import json

from rest_framework.renderers import JSONRenderer


class BaseJSONRenderer(JSONRenderer):
    """
    Класс рендерера для сериализации данных в JSON с корневым ключом "data".

    Этот класс расширяет стандартный рендерер JSONRenderer и изменяет поведение
    рендеринга так, чтобы результат всегда включал корневой ключ "data".

    Атрибуты:
        - charset (str): Устанавливает кодировку, используемую
        для рендеринга JSON. По умолчанию "utf-8".
        - root_key (str): Устанавливает корневой ключ для JSON-объекта.
        По умолчанию "data".

    Методы:
        - render(): Переопределяет метод рендеринга данных в формат JSON.
    """

    charset = "utf-8"
    root_key = "data"

    def render(self, data, media_type=None, renderer_context=None) -> str:
        """
        Переопределённый метод рендеринга для преобразования данных
        в формат JSON с корневым ключом "data".

        Этот метод добавляет обёртку вокруг переданных данных, помещая
        их в объект JSON под ключом `root_key`. Например, если данные
        представляют собой словарь или список, они будут вложены в объект,
        как `{"data": ...}`.

        Параметры:
            - data (Any): Данные, которые будут сериализованы в JSON.
            - media_type (str, optional): Тип медиа, с которым работает
            рендерер. Не используется в данном случае.
            - renderer_context (dict, optional): Контекст рендерера,
            предоставляющий дополнительные данные.
            Не используется в данном случае.

        Возвращает:
            - str: Сериализованные данные в формате
            JSON с корневым ключом "data".
        """
        return json.dumps({self.root_key: data})
