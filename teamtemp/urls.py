from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib import admin as djadmin

from teamtemp.views import home, admin, submit, reset, bvc, team, cron, set, filter, healthcheck, robots_txt

urlpatterns = [
    url(r'^cs$', home, {'survey_type' : 'CUSTOMERFEEDBACK'}),
    url(r'^drs$', home, {'survey_type' : 'DEPT-REGION-SITE'}),
    url(r'^$', home, name='home'),
    url(r'^about$', TemplateView.as_view(template_name='about.html'),
        name='about'),
    url(r'^admin/(?P<survey_id>[0-9a-zA-Z]{8})$', admin, name='admin'),
    url(r'^set/(?P<survey_id>[0-9a-zA-Z]{8})$', set, name='set'),
    url(r'^admin/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<team_name>[-\w]{1,64})$', admin, name='admin'),
    url(r'^(?P<survey_id>[0-9a-zA-Z]{8})/(?P<team_name>[-\w]{1,64})$', submit, name='submit'),

    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/i(?P<num_iterations>[0-9]{1,3})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<team_name>[-\w]{1,64})/i(?P<num_iterations>[0-9]{1,3})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<archive_id>[0-9]{1,20})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<team_name>[-\w]{1,64})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<team_name>[-\w]{1,64})/(?P<archive_id>[0-9]{1,20})$', bvc, name='bvc'),

    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/region=(?P<region_names>[-\w\,]{1,64})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/site=(?P<site_names>[-\w\,]{1,64})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/dept=(?P<dept_names>[-\w\,]{1,64})$', bvc, name='bvc'),

    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<archive_id>[0-9]{1,20})/dept=(?P<dept_names>[-\w\,]{0,64})/region=(?P<region_names>[-\w\,]{0,64})/site=(?P<site_names>[-\w\,]{0,64})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/dept=(?P<dept_names>[-\w\,]{0,64})/region=(?P<region_names>[-\w\,]{0,64})/site=(?P<site_names>[-\w\,]{0,64})$', bvc, name='bvc'),

    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<archive_id>[0-9]{1,20})/region=(?P<region_name>[-\w\,]{1,64})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<archive_id>[0-9]{1,20})/site=(?P<site_name>[-\w\,]{1,64})$', bvc, name='bvc'),
    url(r'^bvc/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<archive_id>[0-9]{1,20})/dept=(?P<dept_name>[-\w\,]{1,64})$', bvc, name='bvc'),

    url(r'^reset/(?P<survey_id>[0-9a-zA-Z]{8})$', reset, name='reset'),
    url(r'^cron/(?P<pin>[0-9]{4})$', cron),
    url(r'^team/(?P<survey_id>[0-9a-zA-Z]{8})/(?P<team_name>[-\w]{1,64})$', team, name='team'),
    url(r'^team/(?P<survey_id>[0-9a-zA-Z]{8})$', team, name='team'),
    url(r'^filter/(?P<survey_id>[0-9a-zA-Z]{8})$', filter),
    url(r'^static/(.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    url(r'^media/(.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'^healthcheck/?$', healthcheck, name='healthcheck'),
    url(r'^robots\.txt', robots_txt, name='robots_txt'),
    url(r'^favicon\.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico')), name='favicon'),
    url(r'^djadmin/', include(djadmin.site.urls)),
]
