import errno
import json
import os
import sys
import urllib
import wget
from urlparse import urlparse

import gviz_api
import unirest
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render
from django.urls import reverse
from django.views.static import serve as serve_static
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from responses.forms import AddTeamForm, CreateSurveyForm, ErrorBox, FilteredBvcForm, ResultsPasswordForm, \
    SurveyResponseForm, SurveySettingsForm
from responses.serializers import *
from teamtemp import responses, utils
from teamtemp.headers import header
from teamtemp.responses.models import *


class WordCloudImageViewSet(viewsets.ModelViewSet):
    queryset = WordCloudImage.objects.all()
    serializer_class = WordCloudImageSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter,)
    filter_fields = ('creation_date', 'word_hash', 'image_url',)
    order_fields = ('id', 'creation_date', 'word_hash')
    search_fields = ('word_list', 'word_hash', 'image_url')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('creation_date',)
    order_fields = ('id', 'creation_date')


class TeamTemperatureViewSet(viewsets.ModelViewSet):
    queryset = TeamTemperature.objects.all()
    serializer_class = TeamTemperatureSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('creator', 'survey_type', 'creation_date', 'modified_date')
    order_fields = ('id', 'creation_date', 'modified_date')


class TemperatureResponseViewSet(viewsets.ModelViewSet):
    queryset = TemperatureResponse.objects.all()
    serializer_class = TemperatureResponseSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('team_name', 'request', 'archived', 'response_date', 'archive_date')
    order_fields = ('response_date', 'archive_date', 'team_name', 'word', 'score')


class TeamResponseHistoryViewSet(viewsets.ModelViewSet):
    queryset = TeamResponseHistory.objects.all()
    serializer_class = TeamResponseHistorySerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter,)
    filter_fields = ('request', 'word_list', 'team_name', 'archive_date')
    order_fields = ('archive_date', 'team_name')
    search_fields = ('word_list',)


class TeamsViewSet(viewsets.ModelViewSet):
    queryset = Teams.objects.all()
    serializer_class = TeamSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('request', 'team_name', 'dept_name', 'site_name', 'region_name')
    order_fields = ('team_name',)


def health_check_view(_):
    return HttpResponse('ok', content_type='text/plain')


@header('Cache-Control', 'public, max-age=86400')
def robots_txt_view(_):
    return HttpResponse('', content_type='text/plain')


@header('Cache-Control', 'public, max-age=315360000')
def media_view(request, *args, **kwargs):
    return serve_static(request, *args, **kwargs)


def utc_timestamp():
    return "[%s UTC]" % str(timezone.localtime(timezone.now(), timezone=timezone.utc))


def home_view(request, survey_type='TEAMTEMP'):
    timezone.activate(timezone.utc)
    if request.method == 'POST':
        form = CreateSurveyForm(request.POST, error_class=ErrorBox)
        if form.is_valid():
            csf = form.cleaned_data
            survey_id = utils.random_string(8)
            user, created = get_or_create_user(request)
            dept_names = csf['dept_names']
            region_names = csf['region_names']
            site_names = csf['site_names']
            survey = TeamTemperature(password=make_password(csf['password']),
                                     creator=user,
                                     survey_type=survey_type,
                                     archive_date=timezone.now(),
                                     id=survey_id,
                                     dept_names=dept_names,
                                     region_names=region_names,
                                     site_names=site_names,
                                     archive_schedule=7,
                                     default_tz='UTC')
            survey.fill_next_archive_date()
            survey.full_clean()
            survey.save()

            responses.add_admin_for_survey(request, survey.id)

            return HttpResponseRedirect(reverse('team', kwargs={'survey_id': survey_id}))
    else:
        form = CreateSurveyForm()
    return render(request, 'index.html', {'form': form, 'survey_type': survey_type})


def authenticated_user(request, survey):
    if survey is None:
        raise Exception('Must supply a survey object')

    if responses.is_admin_for_survey(request, survey.id):
        return True

    # Retrieve User Token - if user does not exist return false
    try:
        user = get_user(request)
    except User.DoesNotExist:
        return False

    if user and survey.creator.id == user.id:
        responses.add_admin_for_survey(request, survey.id)
        return True

    return False


def set_view(request, survey_id):
    thanks = ""
    rows_changed = 0

    survey = get_object_or_404(TeamTemperature, pk=survey_id)

    if not authenticated_user(request, survey):
        return HttpResponseRedirect(reverse('admin', kwargs={'survey_id': survey_id}))

    survey_teams = survey.teams.all()

    if request.method == 'POST':
        form = SurveySettingsForm(request.POST, error_class=ErrorBox)
        if form.is_valid():
            srf = form.cleaned_data
            if srf['password'] != '':
                survey.password = make_password(srf['password'])
                thanks = "Password Updated. "
            if srf['archive_schedule'] != survey.archive_schedule:
                survey.archive_schedule = srf['archive_schedule']
                thanks += "Schedule Updated. "
                survey.fill_next_archive_date(overwrite=True)
                thanks += "Next Archive Date Updated to %s. " % survey.next_archive_date
            elif srf['next_archive_date'] != survey.next_archive_date:
                survey.next_archive_date = srf['next_archive_date']
                thanks += "Next Archive Date Updated to %s. " % survey.next_archive_date
            if srf['survey_type'] != survey.survey_type:
                survey.survey_type = srf['survey_type']
                thanks += "Survey Type Updated. "
            if srf['dept_names'] != survey.dept_names:
                survey.dept_names = srf['dept_names']
                thanks += "Dept Names Updated. "
            if srf['region_names'] != survey.region_names:
                survey.region_names = srf['region_names']
                thanks += "Region Names Updated. "
            if srf['site_names'] != survey.site_names:
                survey.site_names = srf['site_names']
                thanks += "Site Names Updated. "
            if srf['default_tz'] != survey.default_tz:
                survey.default_tz = srf['default_tz']
                thanks += "Default Timezone Updated. "
            if srf['max_word_count'] != survey.max_word_count:
                survey.max_word_count = srf['max_word_count']
                thanks += "Max Word Count Updated. "

            if srf['current_team_name'] != '':
                rows_changed = change_team_name(srf['current_team_name'].replace(" ", "_"),
                                                srf['new_team_name'].replace(" ", "_"), survey.id)
                thanks += "Team Name Updated: From: '" + srf['current_team_name'] + "' To: '" + srf[
                    'new_team_name'] + "'. " + str(rows_changed) + " records updated. "

            if srf['censored_word'] != '':
                rows_changed = censor_word(srf['censored_word'], survey.id)
                thanks += "Word removed: " + str(rows_changed) + " responses updated. "

            survey.full_clean()
            survey.save()

            if srf['current_team_name'] != '' and srf['new_team_name'] != '':
                thanks += "Team Name Change Processed: " + str(rows_changed) + " rows updated. "
            if srf['current_team_name'] != '' and srf['new_team_name'] == '':
                thanks += "Team Name Change Processed: " + str(rows_changed) + " rows deleted. "
    else:
        form = SurveySettingsForm(instance=survey)

    return render(request, 'set.html', {'form': form, 'thanks': thanks,
                                        'survey': survey,
                                        'survey_teams': survey_teams})


def censor_word(censored_word, survey_id):
    data = {'word': ''}

    response_set = TemperatureResponse.objects.filter(request=survey_id, word=censored_word.lower())
    num_rows = response_set.count()
    response_set.update(**data)

    print >> sys.stderr, "Word removed:  " + str(num_rows) + " word removed: " + censored_word

    return num_rows


@transaction.atomic
def change_team_name(team_name, new_team_name, survey_id):
    response_objects = TemperatureResponse.objects.filter(request=survey_id, team_name=team_name)
    history_objects = TeamResponseHistory.objects.filter(request=survey_id, team_name=team_name)
    team_objects = Teams.objects.filter(request=survey_id, team_name=team_name)

    num_rows = response_objects.count() + history_objects.count() + team_objects.count()

    if new_team_name != '':
        data = {'team_name': new_team_name}

        response_objects.update(**data)
        history_objects.update(**data)
        team_objects.update(**data)
    else:
        response_objects.delete()
        history_objects.delete()
        team_objects.delete()

    print >> sys.stderr, "Team Name Updated: %d From: '%s' To: '%s'" % (num_rows, team_name, new_team_name)

    return num_rows


def submit_view(request, survey_id, team_name=''):
    user, created = get_or_create_user(request)

    survey = get_object_or_404(TeamTemperature, pk=survey_id)

    # ensure team exists
    team = get_object_or_404(Teams, request_id=survey_id, team_name=team_name) if team_name != '' else None

    response = None
    if request.method == 'POST' and request.POST.get('id', None):
        try:
            response = TemperatureResponse.objects.get(id=request.POST.get('id'))
        except TemperatureResponse.DoesNotExist:
            pass

    if response is None:
        try:
            response = TemperatureResponse.objects.get(request=survey_id,
                                                       responder=user,
                                                       team_name=team_name,
                                                       archived=False)
        except TemperatureResponse.DoesNotExist:
            pass

    thanks = ""
    if request.method == 'POST':
        form = SurveyResponseForm(request.POST, error_class=ErrorBox, max_word_count=survey.max_word_count)

        if form.is_valid():
            srf = form.cleaned_data
            if response is None:
                response = TemperatureResponse(request=survey,
                                               responder=user,
                                               team_name=team_name,
                                               response_date=timezone.now())
            response.score = srf['score']
            response.word = srf['word']
            response.response_date = timezone.now()

            response.full_clean()
            response.save()

            thanks = "Thank you for submitting your answers. You can " \
                     "amend them now or later using this browser only if you need to."
    else:
        form = SurveyResponseForm(instance=response, max_word_count=survey.max_word_count)

    survey_type_title = 'Team Temperature'
    temp_question_title = 'Temperature (1-10) (1 is very negative, 6 is OK, 10 is very positive):'
    word_question_title = 'One word to describe how you are feeling:'
    numbers = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]
    if 1 < survey.max_word_count <= 10:
        word_question_title = numbers[survey.max_word_count] + ' words to describe how you are feeling:'
    if survey.survey_type == 'CUSTOMERFEEDBACK':
        survey_type_title = 'Customer Feedback'
        temp_question_title = 'Please give feedback on our team performance (1 - 10) (1 is very poor - 10 is very positive):'
        word_question_title = 'Please suggest one word to describe how you are feeling about the team and service:'

    return render(request, 'form.html', {'form': form, 'thanks': thanks,
                                         'response_id': response.id if response else None,
                                         'survey_type_title': survey_type_title,
                                         'temp_question_title': temp_question_title,
                                         'word_question_title': word_question_title,
                                         'team_name': team_name,
                                         'pretty_team_name': team.pretty_team_name if team else '',
                                         'id': survey_id})


def user_view(request):
    user, _ = get_or_create_user(request)
    if not user:
        raise Http404

    admin_survey_ids = responses.get_admin_for_surveys(request)
    if len(admin_survey_ids) > 0:
        admin_surveys = TeamTemperature.objects.filter(id__in=admin_survey_ids)
    else:
        admin_surveys = set()

    return render(request, 'user.html', {'user': user, 'admin_surveys': admin_surveys})


def admin_view(request, survey_id, team_name=''):
    survey = get_object_or_404(TeamTemperature, pk=survey_id)

    timezone.activate(pytz.timezone(survey.default_tz or 'UTC'))

    form = None
    if request.method == 'POST':
        form = ResultsPasswordForm(request.POST, error_class=ErrorBox)
        if form.is_valid():
            rpf = form.cleaned_data
            password = rpf['password'].encode('utf-8')
            if check_password(password, survey.password):
                responses.add_admin_for_survey(request, survey.id)
                return HttpResponseRedirect(reverse('admin', kwargs={'survey_id': survey_id}))

    if not authenticated_user(request, survey):
        if form is None:
            form = ResultsPasswordForm()
        return render(request, 'password.html', {'form': form})

    if team_name != '':
        team = get_object_or_404(Teams, request_id=survey_id, team_name=team_name)
        results = survey.temperature_responses.filter(team_name=team_name, archived=False)
        stats, _ = survey.team_stats(team_name_list=[team_name])
        pretty_team_name = team.pretty_team_name()
    else:
        results = survey.temperature_responses.filter(archived=False)
        stats, _ = survey.stats()
        pretty_team_name = ''

    survey_teams = survey.teams.all()
    next_archive_date = None
    if survey.archive_schedule > 0:
        survey.fill_next_archive_date()
        next_archive_date = survey.next_archive_date.strftime("%A %d %B %Y")

    return render(request, 'results.html',
                  {'id': survey_id, 'stats': stats,
                   'results': results, 'team_name': team_name, 
                   'pretty_team_name': pretty_team_name,  
                   'survey_teams': survey_teams,
                   'archive_schedule': survey.archive_schedule,
                   'next_archive_date': next_archive_date
                   })


def generate_wordcloud(word_list, word_hash):
    word_cloud_key = os.environ.get('XMASHAPEKEY')
    if word_cloud_key is not None:
        timeout = 25
        unirest.timeout(timeout)
        word_list = word_list.lower()
        fixed_asp = "FALSE"
        rotate = "FALSE"
        word_count = len(word_list.split())
        if word_count < 20:
            fixed_asp = "TRUE"
            rotate = "TRUE"
        print >> sys.stderr, "Start Word Cloud Generation: [%s] %s" % (word_hash, word_list)
        response = unirest.post("https://www.teamtempapp.com/wordcloud/api/v1.0/generate_wc",
                                headers={"Content-Type": "application/json", "Word-Cloud-Key": word_cloud_key},
                                params=json.dumps({"textblock": word_list, "height": 500, "width": 600, "s_fit": "TRUE",
                                                   "fixed_asp": fixed_asp, "rotate": rotate})
                                )
        print >> sys.stderr, "Finish Word Cloud Generation: [%s] response_code=%d" % (word_hash, response.code)
        if response.code == 200:
            return save_url(response.body['url'], 'wordcloud_images', word_hash)

    return None


def require_dir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


def media_dir(directory):
    media_directory = os.path.join(settings.MEDIA_ROOT, directory)
    require_dir(media_directory)
    return media_directory


def media_filename(src, basename=None):
    name = urlparse(src).path.split('/')[-1]
    if basename:
        ext = name.split('.')[-1]
        if ext:
            return '.'.join([basename, ext])
        else:
            return basename
    return name


def media_url(src, directory, basename=None):
    image_name = media_filename(src, basename)
    url = os.path.join(settings.MEDIA_URL, os.path.join(directory, image_name))
    return url


def media_file(src, directory, basename=None):
    image_name = media_filename(src, basename)
    media_directory = media_dir(directory)
    filename = os.path.join(media_directory, image_name)
    return filename


def save_url(url, directory, basename):
    return_url = media_url(url, directory, basename)
    filename = media_file(url, directory, basename)

    print >> sys.stderr, "Saving Word Cloud: %s as %s" % (url, filename)

    if not os.path.exists(filename):
        try:
            wget.download(url, out=filename)
        except IOError as exc:
            print >> sys.stderr, "Failed Saving Word Cloud: IOError:%s %s as %s" % (str(exc), url, filename)
            return None
        except urllib.ContentTooShortError as exc:
            print >> sys.stderr, "Failed Saving Word Cloud: ContentTooShortError:%s %s as %s" % (
                str(exc), url, filename)
            return None

    return return_url


def reset_view(request, survey_id):
    survey = get_object_or_404(TeamTemperature, pk=survey_id)

    timezone.activate(pytz.timezone(survey.default_tz or 'UTC'))

    result = "\n"
    if authenticated_user(request, survey):
        if archive_survey(request, survey):
            result = "ok\n"
        else:
            result = "failed\n"

    return HttpResponseRedirect(
        reverse('admin', kwargs={'survey_id': survey_id}), content=result, content_type='text/plain')


def cron_view(request, pin):
    cron_pin = '0000'
    if settings.CRON_PIN:
        cron_pin = settings.CRON_PIN

    if pin == cron_pin:
        auto_archive_surveys(request)
        prune_word_cloud_cache(request)
        return HttpResponse("ok\n", content_type='text/plain')
    else:
        print >> sys.stderr, "Cron 404: pin = " + pin + " expected = " + cron_pin
        raise Http404


def prune_word_cloud_cache(_):
    timezone.activate(timezone.utc)
    print >> sys.stderr, "prune_word_cloud_cache: Start at " + utc_timestamp()

    yesterday = timezone.now() + timedelta(days=-1)

    WordCloudImage.objects.filter(creation_date__lte=yesterday).delete()

    for word_cloud in WordCloudImage.objects.all():
        if not os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), word_cloud.image_url)):
            word_cloud.delete()

    print >> sys.stderr, "prune_word_cloud_cache: Stop at " + utc_timestamp()


def auto_archive_surveys(request):
    timezone.activate(timezone.utc)
    print >> sys.stderr, "auto_archive_surveys: Start at " + utc_timestamp()

    team_temperatures = TeamTemperature.objects.filter(archive_schedule__gt=0)

    now = timezone.now()
    now_date = timezone.localtime(now).date()

    for team_temp in team_temperatures:
        team_temp.fill_next_archive_date()

        print >> sys.stderr, "auto_archive_surveys: Survey %s: Comparing %s >= %s == %s" % (
            team_temp.id, now_date, team_temp.next_archive_date, (now_date >= team_temp.next_archive_date))

        if now_date >= team_temp.next_archive_date:
            archive_survey(request, team_temp, archive_date=now)

    print >> sys.stderr, "auto_archive_surveys: Stop at " + utc_timestamp()


@transaction.atomic
def archive_survey(_, survey, archive_date=timezone.now()):
    timezone.activate(pytz.timezone(survey.default_tz or 'UTC'))

    print >> sys.stderr, "Archiving %s: Archive Date %s UTC" % (survey.id, str(archive_date))

    # Save Survey Summary for all survey teams
    teams = survey.temperature_responses.filter(archived=False).values('team_name').distinct()

    average_total = 0
    average_count = 0
    average_responder_total = 0
    average_word_list = ""

    for team in teams:
        team_stats, team_response_objects = survey.team_stats(team_name_list=[team['team_name']])

        word_list = " ".join(map(lambda word: word['word'], team_stats['words']))

        average_word_list += word_list + " "

        history = TeamResponseHistory(request=survey,
                                      average_score=("%.5f" % float(team_stats['average']['score__avg'])),
                                      word_list=word_list,
                                      responder_count=team_stats['count'],
                                      team_name=team['team_name'],
                                      archive_date=archive_date)
        history.save()

        average_total += team_stats['average']['score__avg']
        average_count += 1
        average_responder_total += team_stats['count']

        team_response_objects.update(archived=True, archive_date=archive_date)

    # Save Survey Summary as AGGREGATE AVERAGE for all teams
    if average_count > 0:
        history = TeamResponseHistory(request=survey,
                                      average_score=("%.5f" % float(average_total / float(average_count))),
                                      word_list=average_word_list.strip(),
                                      responder_count=average_responder_total,
                                      team_name='Average',
                                      archive_date=archive_date)
        history.save()

    survey.advance_next_archive_date()
    survey.archive_date = archive_date

    print >> sys.stderr, "Archiving %s: Next Archive Date %s" % (survey.id, survey.next_archive_date)

    survey.full_clean()
    survey.save()

    return True


def team_view(request, survey_id, team_name=None):
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    team = None
    if team_name is not None:
        team = get_object_or_404(Teams, request_id=survey_id, team_name=team_name)

    dept_names_list = survey.dept_names.split(',')
    region_names_list = survey.region_names.split(',')
    site_names_list = survey.site_names.split(',')

    if request.method == 'POST':
        form = AddTeamForm(request.POST, error_class=ErrorBox, dept_names_list=dept_names_list,
                           region_names_list=region_names_list, site_names_list=site_names_list)
        if form.is_valid():
            csf = form.cleaned_data
            new_team_name = csf['team_name'].replace(" ", "_")
            dept_name = csf['dept_name']
            region_name = csf['region_name']
            site_name = csf['site_name']

            existing_teams = survey.teams.filter(team_name=new_team_name)
            if team:
                existing_teams = existing_teams.exclude(id=team.id)

            if existing_teams.count() > 0:
                form.add_error('team_name', "Team name '%s' already exists for this survey" % new_team_name)
            else:
                with transaction.atomic():
                    if team:
                        if new_team_name != team.team_name:
                            rows_changed = change_team_name(team.team_name, new_team_name, survey.id)

                        team.team_name = new_team_name
                        team.dept_name = dept_name
                        team.region_name = region_name
                        team.site_name = site_name
                    else:
                        team = Teams(id=None,
                                     request=survey,
                                     team_name=new_team_name,
                                     dept_name=dept_name,
                                     region_name=region_name,
                                     site_name=site_name)

                    team.full_clean()
                    team.save()

                return HttpResponseRedirect(reverse('admin', kwargs={'survey_id': survey_id}))
    else:
        form = AddTeamForm(instance=team, dept_names_list=dept_names_list, region_names_list=region_names_list,
                           site_names_list=site_names_list)

    return render(request, 'team.html', {'form': form, 'survey': survey})


def populate_chart_data_structures(survey_type_title, teams, team_history, tz='UTC'):
    # Populate GVIS History Chart Data Structures
    # In:
    #    teams: team list
    #    bvc_data['team_history']: query set of team or teams history temp data to chart
    # Out:
    #    historical_options
    #    json_history_chart_table
    #
    timezone.activate(pytz.timezone(tz))
    team_index = 0
    history_chart_schema = {"archive_date": ("datetime", "Archive_Date")}
    history_chart_columns = ('archive_date',)
    average_index = None
    for team in teams:
        if team['team_name'] != 'Average':
            history_chart_schema.update({team['team_name']: ("number", team['team_name'].replace("_", " "))})
            history_chart_columns += team['team_name'],
            team_index += 1

    # Add average heading if not already added for adhoc filtering
    if team_index > 1:
        average_index = team_index
    history_chart_schema.update({'Average': ("number", 'Average')})
    history_chart_columns += 'Average',

    history_chart_data = []
    row = None
    num_scores = 0
    score_sum = 0
    responder_sum = 0
    for survey_summary in team_history:
        if survey_summary.team_name != 'Average':
            if row is None:
                row = {'archive_date': timezone.localtime(survey_summary.archive_date)}
            elif row['archive_date'] != timezone.localtime(survey_summary.archive_date):
                # TODO can it recalculate the average here for adhoc filtering
                if num_scores > 0:
                    average_score = score_sum / num_scores
                    row['Average'] = (float(average_score),
                                      str("%.2f" % float(average_score)) + " (" + str(responder_sum) + " Responses)")
                    score_sum = 0
                    num_scores = 0
                    responder_sum = 0
                history_chart_data.append(row)
                row = {'archive_date': timezone.localtime(survey_summary.archive_date)}

            # Accumulate for average calc
            score_sum += survey_summary.average_score
            num_scores += 1
            responder_sum += survey_summary.responder_count

            row[survey_summary.team_name] = (float(survey_summary.average_score),
                                             str("%.2f" % float(survey_summary.average_score)) + " (" + str(
                                                 survey_summary.responder_count) + " Responses)")

    average_score = score_sum / num_scores
    row['Average'] = (
        float(average_score), str("%.2f" % float(average_score)) + " (" + str(responder_sum) + " Responses)")

    history_chart_data.append(row)

    # Loading it into gviz_api.DataTable
    history_chart_table = gviz_api.DataTable(history_chart_schema)
    history_chart_table.LoadData(history_chart_data)

    # Creating a JSon string
    json_history_chart_table = history_chart_table.ToJSon(columns_order=history_chart_columns)

    historical_options = {
        'legendPosition': 'newRow',
        'title': survey_type_title + ' by Team',
        'vAxis': {'title': survey_type_title,
                  'ticks': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
        'hAxis': {'title': "Month"},
        'seriesType': "bars",
        'max': 10,
        'min': 0,
        'focusTarget': 'category',
        'tooltip': {'trigger': 'selection', 'isHtml': 'true'},
    }
    if average_index is not None:
        historical_options.update({'series': {average_index: {'type': "line"}}})

    return historical_options, json_history_chart_table, team_index


def populate_bvc_data(survey_id_list, team_name, archive_id, num_iterations, dept_name='', region_name='', site_name='',
                      survey_type='TEAMTEMP'):
    # in: survey_id, team_name and archive_id
    # out:
    #    populate bvc_data['archived_dates']       For Drop Down List
    #    populate bvc_data['archive_date']         For displaying above gauge for an archived BVC
    #    populate bvc_data['archived']             Are these results archived results
    #    populate bvc_data['stats_date']           Archive date for these stats - they are for an archived iteration
    #    populate bvc_data['team_history']         Set of responses
    #    populate bvc_data['survey_teams']         All teams for this survey
    #    populate bvc_data['survey_id']            This survey id
    #    populate bvc_data['team_name']            '' for multi team or specific team name to filter to
    #    populate bvc_data['pretty_team_name']     no spaces in team name above
    #    populate bvc_data['survey_type_title']    survey type Team Temperature or Customer Feedback

    survey_filter = {'request__in': survey_id_list}
    team_objects = Teams.objects.filter(**survey_filter)

    bvc_data = {
        'stats_date': '',
        'survey_teams': team_objects,
        'archived': False,
        'archive_date': None,
        'archive_id': archive_id,
        'word_cloudurl': '',
        'team_filter': team_objects,
        'team_name': team_name,
        'pretty_team_name': team_name.replace("_", " "),
        'dept_names': dept_name,
        'region_names': region_name,
        'site_names': site_name,
        'survey_type': survey_type
    }
    # print >>sys.stderr,"dept_names",bvc_data['dept_names'],"end"

    bvc_teams_list = [team_name]

    # if any survey's are customer feedback surveys display customer BVC
    num_teamtemp_surveys = TeamTemperature.objects.filter(pk__in=survey_id_list,
                                                          survey_type__in=['TEAMTEMP', 'DEPT-REGION-SITE']).count()
    num_cust_surveys = TeamTemperature.objects.filter(pk__in=survey_id_list, survey_type='CUSTOMERFEEDBACK').count()
    # Bug here
    # what does count return for an empty set?
    # is None greater than 0?
    bvc_data['survey_type_title'] = 'Team Temperature'
    if num_teamtemp_surveys == 0 and num_cust_surveys > 0:
        bvc_data['survey_type_title'] = 'Customer Feedback'

    if team_name != '':
        team_filter = dict({'team_name': team_name}, **survey_filter)
    else:
        if region_name != '':
            region_name_list = region_name.split(',')
            region_filter = dict({'region_name__in': region_name_list}, **survey_filter)
        else:
            region_filter = survey_filter

        # print >>sys.stderr,"region_filter:",region_filter

        if site_name != '':
            site_name_list = site_name.split(',')
            site_filter = dict({'site_name__in': site_name_list}, **region_filter)
        else:
            site_filter = region_filter
        # print >>sys.stderr,"site_filter:",site_filter

        if dept_name != '':
            dept_name_list = dept_name.split(',')
            dept_filter = dict({'dept_name__in': dept_name_list}, **site_filter)
        else:
            dept_filter = site_filter
        # print >>sys.stderr,"dept_filter:",dept_filter

        if dept_filter != survey_filter:
            filtered_teams = Teams.objects.filter(**dept_filter).values('team_name')
            filtered_team_list = []
            for team in filtered_teams:
                filtered_team_list.append(team['team_name'])
            team_filter = dict({'team_name__in': filtered_team_list}, **survey_filter)
            bvc_teams_list = filtered_team_list
        else:
            team_filter = survey_filter
            # print >>sys.stderr,"team_filter:",team_filter,dept_name, region_name, site_name
    bvc_data['team_history'] = TeamResponseHistory.objects.filter(**team_filter).order_by('archive_date')
    bvc_data['teams'] = TeamResponseHistory.objects.filter(**team_filter).values('team_name').distinct()
    bvc_data['num_rows'] = TeamResponseHistory.objects.filter(**team_filter).count()
    bvc_data['survey_teams_filtered'] = Teams.objects.filter(**team_filter)

    tempresponse_filter = dict({'archived': False}, **team_filter)
    if archive_id != '':
        archive_set = TemperatureResponse.objects.filter(request__in=survey_id_list, id=archive_id).values(
            'archive_date')
        tempresponse_filter = dict({'archived': True}, **team_filter)
        if archive_set:
            bvc_data['stats_date'] = archive_set[0]['archive_date']
            tempresponse_filter = dict({'archive_date': bvc_data['stats_date']}, **tempresponse_filter)

    results = TemperatureResponse.objects.filter(**tempresponse_filter)

    if results:
        bvc_data['archived'] = results[0].archived
        bvc_data['archive_date'] = results[0].archive_date

    archived_filter = dict({'archived': True}, **team_filter)
    bvc_data['archived_dates'] = TemperatureResponse.objects.filter(**archived_filter).values('archive_date',
                                                                                              'id').distinct(
        'archive_date').order_by('-archive_date')

    bvc_data['stats'] = generate_bvc_stats(survey_id_list, bvc_teams_list, bvc_data['stats_date'], num_iterations)

    return bvc_data


def cached_word_cloud(word_list):
    words = ""
    word_count = 0

    # we want these to include and count duplicates
    for word in word_list:
        for i in range(0, word['id__count']):
            words += word['word'] + " "
            word_count += 1

    words = words.lower().strip()

    if words == "":
        return None

    word_hash = hashlib.sha1(words).hexdigest()

    # most recent word cloud first
    word_cloud_objects = WordCloudImage.objects.filter(word_hash=word_hash).order_by('-id')

    if word_cloud_objects:
        word_cloud_image = word_cloud_objects[0]
        filename = media_file(word_cloud_image.image_url, 'wordcloud_images')

        if os.path.isfile(filename):
            print >> sys.stderr, "Cached Word Cloud: " + filename + " found"
            return word_cloud_image.image_url
        else:
            print >> sys.stderr, "Cached Word Cloud: " + filename + " not found"
            # Most recent word cloud has been deleted: remove all for this word list from db and then regenerate
            word_cloud_objects.delete()

    word_cloudurl = generate_wordcloud(words, word_hash)

    if word_cloudurl:
        word_cloud = WordCloudImage(word_list=words, word_hash=word_hash,
                                    image_url=word_cloudurl)
        word_cloud.full_clean()
        word_cloud.save()

    return word_cloudurl


def generate_bvc_stats(survey_id_list, team_name_list, archive_date, num_iterations):
    # Generate Stats for Team Temp Average for gauge and wordcloud - look here for Gauge and Word Cloud
    # BVC.html uses stats.count and stats.average.score__avg and cached word cloud uses stats.words below

    survey_count = 0
    agg_stats = {'count': 0, 'average': 0.00, 'words': []}

    survey_filter = {'id__in': survey_id_list}

    for survey in TeamTemperature.objects.filter(**survey_filter):
        if team_name_list != [''] and archive_date == '':
            stats, _ = survey.team_stats(team_name_list=team_name_list)
        elif team_name_list == [''] and archive_date != '':
            stats, _ = survey.archive_stats(archive_date=archive_date)
        elif team_name_list != [''] and archive_date != '':
            stats, _ = survey.archive_team_stats(team_name_list=team_name_list, archive_date=archive_date)
        else:
            stats, _ = survey.stats()

        # Calculate and average and word cloud over multiple iterations (changes date range but same survey id):
        if int(float(num_iterations)) > 0:
            multi_stats = calc_multi_iteration_average(team_name_list, survey, int(float(num_iterations)), survey.default_tz)
            if multi_stats:
                stats = multi_stats

        survey_count += 1
        agg_stats['count'] = agg_stats['count'] + stats['count']

        if stats['average']['score__avg']:
            agg_stats['average'] = (agg_stats['average'] + stats['average']['score__avg']) / survey_count
        agg_stats['words'] += list(stats['words'])

    return agg_stats


def calc_multi_iteration_average(team_name, survey, num_iterations=2, tz='UTC'):
    timezone.activate(pytz.timezone(tz))
    if num_iterations <= 0:
        return None

    iteration_index = num_iterations - 1

    archive_dates = survey.temperature_responses.filter(archive_date__isnull=False).values(
        'archive_date').distinct().order_by('-archive_date')

    if num_iterations > archive_dates.count() > 0:
        iteration_index = archive_dates.count() - 1  # oldest archive date if less than target iteration count

    if archive_dates.count() > iteration_index:
        response_dates = survey.temperature_responses.filter(
            archive_date=archive_dates[iteration_index]['archive_date']).values('response_date').order_by(
            'response_date')

        if team_name != '':
            accumulated_stats, _ = survey.accumulated_team_stats(team_name, timezone.now(),
                                                                 response_dates[0]['response_date'])
        else:
            accumulated_stats, _ = survey.accumulated_stats(timezone.now(), response_dates[0]['response_date'])

        return accumulated_stats

    return None


def bvc_view(request, survey_id, team_name='', archive_id='', num_iterations='0', add_survey_ids=None,
             region_names='', site_names='', dept_names=''):
    survey_ids = request.GET.get('add_survey_ids', add_survey_ids)

    survey_id_list = [survey_id]
    if survey_ids:
        survey_id_list += survey_ids.split(',')

    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    timezone.activate(pytz.timezone(survey.default_tz or 'UTC'))

    json_history_chart_table = None
    historical_options = {}
    team_index = 0

    # Populate data for BVC including previously archived BVC
    bvc_data = populate_bvc_data(survey_id_list, team_name, archive_id, num_iterations, dept_names, region_names,
                                 site_names, survey.survey_type)
    bvc_data['survey_id'] = survey_id

    # If there is history to chart generate all data required for historical charts
    if bvc_data['num_rows'] > 0:
        historical_options, json_history_chart_table, team_index = populate_chart_data_structures(
            bvc_data['survey_type_title'], bvc_data['teams'], bvc_data['team_history'], survey.default_tz)

    # Cached word cloud
    if bvc_data['stats']['words']:
        bvc_data['word_cloudurl'] = cached_word_cloud(bvc_data['stats']['words'])

    all_dept_names = set()
    all_region_names = set()
    all_site_names = set()

    filter_dept_names = ''
    filter_region_names = ''
    filter_site_names = ''

    for survey_team in bvc_data['survey_teams']:
        teams = survey.teams.filter(team_name=survey_team.team_name).values('dept_name', 'region_name', 'site_name')
        for team in teams:
            all_dept_names.add(team['dept_name'])
            all_region_names.add(team['region_name'])
            all_site_names.add(team['site_name'])

    if len(all_dept_names) < 2:
        all_dept_names = []
    if len(all_region_names) < 2:
        all_region_names = []
    if len(all_site_names) < 2:
        all_site_names = []

    dept_names_list_on = all_dept_names if dept_names == '' else dept_names.split(',')
    region_names_list_on = all_region_names if region_names == '' else region_names.split(',')
    site_names_list_on = all_site_names if site_names == '' else site_names.split(',')

    filter_this_bvc = False
    if request.method == 'POST':
        form = FilteredBvcForm(request.POST, error_class=ErrorBox,
                               dept_names_list=sorted(all_dept_names),
                               region_names_list=sorted(all_region_names),
                               site_names_list=sorted(all_site_names))
        if form.is_valid():
            csf = form.cleaned_data
            if len(all_dept_names) > len(csf['filter_dept_names']) \
                    or len(all_region_names) > len(csf['filter_region_names']) \
                    or len(all_site_names) > len(csf['filter_site_names']):
                filter_this_bvc = True

            print >> sys.stderr, "len(all_dept_names)", len(all_dept_names), "len(csf['filter_dept_names']", len(
                csf['filter_dept_names'])

            filter_dept_names = ','.join(csf['filter_dept_names'])
            filter_region_names = ','.join(csf['filter_region_names'])
            filter_site_names = ','.join(csf['filter_site_names'])

            print >> sys.stderr, "Filter this bvc:", filter_this_bvc

            return HttpResponseRedirect(reverse('bvc', kwargs={'survey_id': survey_id,
                                                               'dept_names': filter_dept_names,
                                                               'region_names': filter_region_names,
                                                               'site_names': filter_site_names}))
        else:
            raise Exception('Form Is Not Valid:', form)
    else:
        return render(request, 'bvc.html',
                      {
                          'bvc_data': bvc_data,
                          'json_historical_data': json_history_chart_table,
                          'historical_options': historical_options,
                          'team_count': team_index,
                          'num_iterations': num_iterations,
                          'dept_names': dept_names, 'region_names': region_names, 'site_names': site_names,
                          'form': FilteredBvcForm(dept_names_list=sorted(all_dept_names),
                                                  region_names_list=sorted(all_region_names),
                                                  site_names_list=sorted(all_site_names),
                                                  dept_names_list_on=sorted(dept_names_list_on),
                                                  region_names_list_on=sorted(region_names_list_on),
                                                  site_names_list_on=sorted(site_names_list_on))
        })


def get_user(request):
    userid = responses.get_userid(request)
    if userid:
        return User.objects.get(id=userid)


def get_or_create_user(request):
    userid = responses.get_userid(request)

    if userid:
        return User.objects.get_or_create(id=userid)
    else:
        user = None
        tries = 5
        while user is None and tries >= 0:
            tries -= 1
            userid = responses.create_userid(request)
            user = User.objects.create(id=userid)
            if user:
                return user, True

    raise Exception("Can't create unique user")
