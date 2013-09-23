from django.core.wsgi import get_wsgi_application
from dj_static import Cling
import os

application = Cling(get_wsgi_application())
