from functools import wraps
from typing import Sequence

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail

from django.shortcuts import redirect, resolve_url
from urllib.parse import urlparse


def ufoshop_send_email(recipient_list: Sequence[str], subject: str, html_message: str):
    send_mail(
        subject=subject,
        message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
        html_message=html_message
    )


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
