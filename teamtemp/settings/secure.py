import os

from teamtemp.settings.base import *

SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = (
    r'^healthcheck\/?$',
    r'^robots\.txt$',
)

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
