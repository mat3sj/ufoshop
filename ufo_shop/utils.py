from functools import wraps
from typing import Sequence, Dict, Any, Optional, Union

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.shortcuts import redirect, resolve_url
from urllib.parse import urlparse


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


def user_passes_test(test_func, redirect_to=None, raise_error=PermissionDenied):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                path = request.build_absolute_uri()
                resolved_login_url = resolve_url(settings.LOGIN_URL)
                # If the login url is the same scheme and net location then just
                # use the path as the "next" url.
                login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
                current_scheme, current_netloc = urlparse(path)[:2]
                if (
                        (not login_scheme or login_scheme == current_scheme) and
                        (not login_netloc or login_netloc == current_netloc)
                ):
                    path = request.get_full_path()
                return redirect_to_login(path, resolved_login_url)

            if (
                    user.is_authenticated and
                    user.is_active and
                    test_func(user)
            ):
                return view_func(request, *args, **kwargs)

            if redirect_to:
                return redirect(redirect_to)
            else:
                raise raise_error

        return _wrapped_view

    return decorator


salesman_required = user_passes_test(lambda user: user.is_merchandiser or user.is_superuser)
