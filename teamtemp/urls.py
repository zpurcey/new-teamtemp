from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.conf import settings

from teamtemp.views import home, admin, submit, register, result

urlpatterns = patterns('',
    url(r'^$', home, name='home'),
    url(r'^about$', TemplateView.as_view(template_name='about.html'),
        name='about'),
    url(r'^admin/([0-9a-zA-Z]{8})$', login_required(result), name='result'),
    url(r'^admin/$', login_required(admin), name='admin'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^accounts/register/$', register, name='register'),
    url(r'^([0-9a-zA-Z]{8})$', submit),
    url(r'^static/(.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)
