from common.base_renderer import BaseJSONRenderer


class RewardJSONRenderer(BaseJSONRenderer):
    """
    Класс для рендеринга данных пользователя в формате JSON.

    Этот класс используется для того, чтобы обернуть данные пользователя
    в корневой ключ "reward" при рендеринге в JSON-формате.
    Он наследуется от BaseJSONRenderer и переопределяет атрибут root_key.

    Атрибуты:
        - root_key (str): Ключ, который будет использоваться
        как корневой в JSON-ответе. В данном случае это "reward".
    """

    root_key = "reward"
