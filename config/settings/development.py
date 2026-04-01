"""
Development settings for ecommerce project.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Use SQLite for local development (no PostgreSQL required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = [
    '127.0.0.1',
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/hour',
    'user': '10000/hour',
}

# Logging to console in development
LOGGING['loggers']['django']['handlers'] = ['console']
LOGGING['loggers']['apps']['handlers'] = ['console']
