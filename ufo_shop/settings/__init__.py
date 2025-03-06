from .local import *




LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'timestamped': {
            'format': '(%(levelname)s) %(asctime)s: %(message)s',
        },
        'message_only': {
            'format': '%(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'timestamped',
        },
        'console_message_only': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'message_only',
        },
    },
    'loggers': {
        'management_commands': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'ufo_shop': {
            'handlers': ['console', ],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.template': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}