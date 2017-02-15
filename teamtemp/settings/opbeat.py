import os

from teamtemp.settings.secure import *

INSTALLED_APPS += (
    'opbeat.contrib.django',
)

OPBEAT = {
    'ORGANIZATION_ID': '22fdc1be48ba4fc298f7bf9ce8b3c9bf',
    'APP_ID':          os.environ['OPBEAT_APP_ID'],
    'SECRET_TOKEN':    os.environ['OPBEAT_SECRET_TOKEN'],
}

MIDDLEWARE_CLASSES.insert(0, 'opbeat.contrib.django.middleware.OpbeatAPMMiddleware')
