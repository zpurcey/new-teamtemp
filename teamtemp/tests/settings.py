from teamtemp.settings import *

SECRET_KEY = 'fake-key'
INSTALLED_APPS = [ app for app in INSTALLED_APPS if app != 'bootstrap3' ]
