from django.core.mail import send_mail
from workreward.settings import EMAIL_HOST_USER


def send_email(
    subject: str,
    message: str,
    recipient_list: list[str],
    from_email: str = EMAIL_HOST_USER,
) -> None:
    """
        Переопределенная функция отправки электронного письма.
    """
    try:
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        raise Exception(f"Ошибка при отправке письма: {str(e)}")
