from django.conf import settings
from django.core.mail import send_mail
import typing


def ufoshop_send_email(recipient_list: typing.Iterable, subject: str, html_message: str):
    send_mail(
        subject=subject,
        message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
        html_message=html_message
    )
