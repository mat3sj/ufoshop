"""
WSGI config for ufo_shop project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ufo_shop.settings')

# Initialize Sentry (if configured via settings)
try:
    from django.conf import settings as _settings
    import logging
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    if getattr(_settings, 'SENTRY_DSN', None):
        logging_integration = LoggingIntegration(
            level=logging.INFO,      # breadcrumbs for INFO and above
            event_level=logging.ERROR,  # send events for ERROR and above
        )
        sentry_sdk.init(
            dsn=_settings.SENTRY_DSN,
            integrations=[DjangoIntegration(), logging_integration],
            environment=getattr(_settings, 'SENTRY_ENVIRONMENT', None) or ('production' if not _settings.DEBUG else 'development'),
            traces_sample_rate=getattr(_settings, 'SENTRY_TRACES_SAMPLE_RATE', 0.0),
            profiles_sample_rate=getattr(_settings, 'SENTRY_PROFILES_SAMPLE_RATE', 0.0),
            send_default_pii=True,
        )
except Exception:
    # Sentry is optional; ignore init errors
    pass

application = get_wsgi_application()
