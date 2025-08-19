"""
Middleware utilities for production hardening.

NormalizeHostMiddleware mitigates issues where upstream proxies (e.g., Nginx)
forward multiple Host headers that end up combined into a comma-separated
string by the WSGI server. Django rejects such values as invalid HTTP_HOST.

This middleware normalizes HTTP_HOST by taking the first value before a comma.
It is intentionally minimal and only prepended in production settings.
"""
from typing import Callable


class NormalizeHostMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get('HTTP_HOST')
        if host and ',' in host:
            # Take the first host value, strip whitespace
            first = host.split(',')[0].strip()
            # Overwrite the header in META so Django sees a valid host
            request.META['HTTP_HOST'] = first
        return self.get_response(request)
