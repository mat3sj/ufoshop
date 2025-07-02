from typing import Dict, Any, Sequence, Optional

from django.conf import settings
from django.core.mail import send_mail

from django.template.loader import render_to_string
from django.utils.html import strip_tags


def render_email_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render an email template with the given context.

    Args:
        template_name: The name of the template to render
        context: The context to use for rendering

    Returns:
        The rendered template as a string
    """
    return render_to_string(template_name, context)


def ufoshop_send_email(
    recipient_list: Sequence[str],
    subject: str,
    html_message: str,
    plain_message: Optional[str] = None
):
    """
    Send an email with both HTML and plain text versions.

    Args:
        recipient_list: List of email addresses to send to
        subject: Email subject
        html_message: HTML content of the email
        plain_message: Plain text content of the email (if None, will be generated from HTML)
    """
    # If no plain text message is provided, strip HTML tags from the HTML message
    if plain_message is None:
        plain_message = strip_tags(html_message)

    # If DEBUG is True, print email to a console instead of sending
    if settings.DEBUG:
        print("\n---------------------- EMAIL DEBUG ----------------------")
        print(f"To: {', '.join(recipient_list)}")
        print(f"From: {settings.DEFAULT_FROM_EMAIL}")
        print(f"Subject: {subject}")
        print("\n--- Plain Text Content ---")
        print(plain_message)
        print("\n--- HTML Content ---")
        print(html_message)
        print("---------------------- END EMAIL ----------------------\n")
    else:
        # Only send email if not in DEBUG mode
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_message
        )


def send_template_email(
    recipient_list: Sequence[str],
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    plain_template_name: Optional[str] = None
):
    """
    Send an email using a template.

    Args:
        recipient_list: List of email addresses to send to
        subject: Email subject
        template_name: Name of the HTML template to use
        context: Context to render the template with
        plain_template_name: Name of the plain text template (if None, will strip HTML from HTML template)
    """
    # Render the HTML template
    html_message = render_email_template(template_name, context)

    # Render the plain text template if provided, otherwise strip HTML tags
    plain_message = None
    if plain_template_name:
        plain_message = render_email_template(plain_template_name, context)

    # Send the email
    ufoshop_send_email(recipient_list, subject, html_message, plain_message)
