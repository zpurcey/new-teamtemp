import os
import dj_database_url

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ['TEAMTEMP_SECRET_KEY']

DATABASES = {'default': dj_database_url.config(conn_max_age=600)}
