from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.core.urlresolvers import reverse
from responses.forms import CreateSurveyForm, SurveyResponseForm, ResultsPasswordForm, ErrorBox, AddTeamForm, SurveySettingsForm
from responses.models import User, TeamTemperature, TemperatureResponse, TeamResponseHistory, Teams, WordCloudImage
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime
from pytz import timezone
import pytz
from django.utils import timezone
from datetime import timedelta
from teamtemp import utils, responses
from django.utils import simplejson as json
from django.core.serializers.json import DjangoJSONEncoder
import gviz_api
from django.http import HttpResponse
from django.http import Http404
import unirest as Unirest
import os
from urlparse import urlparse
import errno
import urllib
from django.conf import settings
import sys

def home(request, survey_type = 'TEAMTEMP'):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    if request.method == 'POST':
        form = CreateSurveyForm(request.POST, error_class=ErrorBox)
        if form.is_valid():
            csf = form.cleaned_data
            form_id = utils.random_string(8)
            userid = responses.get_or_create_userid(request)
            user, created = User.objects.get_or_create(id=userid)
            # TODO check that id is unique!
            team_name = csf['team_name'].replace(" ", "_")
            survey = TeamTemperature(creation_date = timezone.now(),
                                     password = make_password(csf['password']),
                                     creator = user,
                                     survey_type = survey_type,
                                     archive_date = timezone.now(),
                                     id = form_id)
            survey.save()
            team_details = Teams(request = survey,
                                team_name = team_name)
            team_details.save()
            return HttpResponseRedirect('/admin/%s/%s' % (form_id, team_name))
    else:
        form = CreateSurveyForm()
    return render(request, 'index.html', {'form': form})

def authenticated_user(request, survey_id):
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    
    #Retrieve User Token - if user does not exist return false
    try:
        userid = request.session.get('userid', '__nothing__')
        user = User.objects.get(id=userid)
    except User.DoesNotExist:
        return False

    if survey.creator.id == user.id:
        return True

    return False

def set(request, survey_id):
    thanks = ""
    rows_changed = 0
    survey_teams=[]

    if not authenticated_user(request, survey_id):
        return HttpResponseRedirect('/admin/%s' % survey_id)

    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    survey_teams = survey.teams_set.all()

    if request.method == 'POST':
        form = SurveySettingsForm(request.POST, error_class=ErrorBox)
        survey_settings_id = request.POST.get('id', None)
        if form.is_valid():
            srf = form.cleaned_data
            pw = survey.password
            if srf['password'] != '':
                pw = make_password(srf['password'])
                thanks = "Password Updated. "
            if srf['archive_schedule'] != survey.archive_schedule:
                if survey.archive_date == None:
                    survey.archive_date = timezone.now()
                thanks = thanks + "Schedule Updated. "
            if srf['survey_type'] != survey.survey_type:
                thanks = thanks + "Survey Type Updated. "
            if srf['current_team_name'] != '':
                rows_changed = change_team_name(srf['current_team_name'].replace(" ", "_"), srf['new_team_name'].replace(" ", "_"), survey.id)
                print >>sys.stderr,"Team Name Updated: " + " " + str(rows_changed) + " From: " + srf['current_team_name'] + " To: " +srf['new_team_name']

            survey_settings = TeamTemperature(id = survey.id,
                                              creation_date = survey.creation_date,
                                              creator = survey.creator,
                                              password = pw,
                                              archive_date = survey.archive_date,
                                              archive_schedule = srf['archive_schedule'],
                                              survey_type = srf['survey_type'])
            survey_settings.save()
            survey_settings_id = survey_settings.id
            form = SurveySettingsForm(instance=survey_settings)
            if srf['current_team_name'] != ''and srf['new_team_name'] != '':
                thanks = thanks + "Team Name Change Processed: " + str(rows_changed) + " rows updated. "
            if srf['current_team_name'] != '' and srf['new_team_name'] == '':
                thanks = thanks + "Team Name Change Processed: " + str(rows_changed) + " rows deleted. "

    else:
        try:
            previous = TeamTemperature.objects.get(id = survey_id)
            survey_settings_id = previous.id
        except TeamTemperature.DoesNotExist:
            previous = None
            survey_settings_id = None
        
        form = SurveySettingsForm(instance=previous)
    return render(request, 'set.html', {'form': form, 'thanks': thanks,
                  'survey_settings_id': survey_settings_id,
                  'survey_teams' : survey_teams})

def change_team_name(team_name, new_team_name, survey_id):
    data = {'team_name': new_team_name}
    num_rows = 0
    if new_team_name != '':
        num_rows = TemperatureResponse.objects.filter(request = survey_id, team_name = team_name).count()
        TemperatureResponse.objects.filter(request = survey_id, team_name = team_name).update(**data)
    
        num_rows = num_rows + TeamResponseHistory.objects.filter(request = survey_id, team_name = team_name).count()
        TeamResponseHistory.objects.filter(request = survey_id, team_name = team_name).update(**data)

        num_rows = num_rows + Teams.objects.filter(request = survey_id, team_name = team_name).count()
        Teams.objects.filter(request = survey_id, team_name = team_name).update(**data)
    else:
        num_rows = TemperatureResponse.objects.filter(request = survey_id, team_name = team_name).count()
        TemperatureResponse.objects.filter(request = survey_id, team_name = team_name).delete()
        
        num_rows = num_rows + TeamResponseHistory.objects.filter(request = survey_id, team_name = team_name).count()
        TeamResponseHistory.objects.filter(request = survey_id, team_name = team_name).delete()
        
        num_rows = num_rows + Teams.objects.filter(request = survey_id, team_name = team_name).count()
        Teams.objects.filter(request = survey_id, team_name = team_name).delete()

    return num_rows

def submit(request, survey_id, team_name=''):
    userid = responses.get_or_create_userid(request)
    user, created = User.objects.get_or_create(id=userid)
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    thanks = ""
    if request.method == 'POST':
        form = SurveyResponseForm(request.POST, error_class=ErrorBox)
        response_id = request.POST.get('id', None)
        if form.is_valid():
            srf = form.cleaned_data
            # TODO check that id is unique!
            response = TemperatureResponse(id = response_id,
                                           request = survey,
                                           score = srf['score'],
                                           word = srf['word'],
                                           responder = user,
                                           team_name = team_name,
                                           response_date = timezone.now())
            response.save()
            response_id = response.id
            form = SurveyResponseForm(instance=response)
            thanks = "Thank you for submitting your answers. You can " \
                     "amend them now or later if you need to"
    else:
        try: 
            previous = TemperatureResponse.objects.get(request = survey_id, 
                                                       responder = user,
                                                       team_name = team_name,
                                                       archived = False) 
            response_id = previous.id
        except TemperatureResponse.DoesNotExist:
            previous = None
            response_id = None

        form = SurveyResponseForm(instance=previous)

    survey_type_title = 'Team Temperature'
    temp_question_title = 'Temperature (1-10) (1 is very negative, 6 is OK, 10 is very positive):'
    word_question_title = 'One word to describe how you are feeling:'
    if survey.survey_type == 'CUSTOMERFEEDBACK':
        survey_type_title = 'Customer Feedback'
        temp_question_title = 'Please give feedback on our team performance (1 - 10) (1 is very poor - 10 is very positive):'
        word_question_title = 'Please suggest one word to describe how you are feeling about the team and service:'

    return render(request, 'form.html', {'form': form, 'thanks': thanks,
                                         'response_id': response_id, 'survey_type_title' : survey_type_title,
                                         'temp_question_title' : temp_question_title,
                                         'word_question_title' : word_question_title,
                                         'team_name': team_name.replace("_", " ")})

def admin(request, survey_id, team_name=''):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    # if valid session token or valid password render results page
    password = None
    user = None
    survey_teams=[]
    next_archive_date = timezone.now()
    
    if request.method == 'POST':
        form = ResultsPasswordForm(request.POST, error_class=ErrorBox)
        if form.is_valid():
            rpf = form.cleaned_data
            password = rpf['password'].encode('utf-8')
    else: 
        try: 
            userid = request.session.get('userid', '__nothing__')
            user = User.objects.get(id=userid)
        except User.DoesNotExist:
            return render(request, 'password.html', {'form': ResultsPasswordForm()})
    if user and survey.creator.id == user.id or check_password(password, survey.password):
        request.session['userid'] = survey.creator.id
        teamtemp = TeamTemperature.objects.get(pk=survey_id)
        if team_name != '':
            team_found = teamtemp.teams_set.filter(team_name = team_name).count()
            if team_found == 0:
                TeamDetails = Teams(request = survey,team_name = team_name)
                TeamDetails.save()
            results = teamtemp.temperatureresponse_set.filter(team_name = team_name, archived = False)
        else:
            results = teamtemp.temperatureresponse_set.filter(archived = False)

        survey_teams = teamtemp.teams_set.all()

        if team_name != '':
            stats = survey.team_stats(team_name=team_name)
        else:
            stats = survey.stats()

        if survey.archive_schedule > 0:
            next_archive_date = timezone.localtime(survey.archive_date) + timedelta(days=(survey.archive_schedule))
            if next_archive_date < timezone.now():
                next_archive_date = timezone.now() + timedelta(days=1)

        return render(request, 'results.html',
                { 'id': survey_id, 'stats': stats,
                  'results': results, 'team_name':team_name,
                      'pretty_team_name':team_name.replace("_", " "),'survey_teams':survey_teams,
                      'archive_schedule' : survey.archive_schedule, 'next_archive_date' : next_archive_date.strftime("%A %d %B %Y")
                    } )
    else:
        return render(request, 'password.html', {'form': ResultsPasswordForm()})

def generate_wordcloud(word_list):

    mashape_key = os.environ.get('XMASHAPEKEY')
    if mashape_key != None:
        Unirest.timeout(20)
        print >>sys.stderr, str(timezone.now()) + " Start Word Cloud Generation: " + word_list
        response = Unirest.post("https://gatheringpoint-word-cloud-maker.p.mashape.com/index.php",
                                headers={"X-Mashape-Key": mashape_key},
                                params={"config": "n/a", "height": 500, "textblock": word_list, "width": 800}
                                )
        print >>sys.stderr, str(timezone.now()) + " Finish Word Cloud Generation: " + word_list
        if response.code == 200:
            return save_url(response.body['url'], 'media/wordcloud_images')
    return None


def require_dir(path):
    try:
        os.makedirs(path)
    except OSError, exc:
        if exc.errno != errno.EEXIST:
            raise

def save_url(url, directory):

    image_name = urlparse(url).path.split('/')[-1]
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), directory)
    require_dir(directory)
    filename = os.path.join(directory, image_name)

    if not os.path.exists(filename):
        urllib.urlretrieve(url, filename)
       #TODO if error return None

    return os.path.relpath(filename,os.path.dirname(os.path.abspath(__file__)))

def bvc(request, survey_id, team_name='', archive_id= '', weeks_to_trend='12', num_iterations='0'):
    #Check if *any* scheduled archive surveys are overdue for archiving
    auto_archive_surveys(request)

    timezone.activate(pytz.timezone('Australia/Queensland'))
    survey = get_object_or_404(TeamTemperature, pk=survey_id)

    password = None
    user = None
    num_rows = 0
    json_history_chart_table = None
    historical_options = {}
    stats_date = ''
    survey_teams=[]
    ignore_bvc_auth = False
    
    if settings.IGNORE_BVC_AUTH:
        ignore_bvc_auth = settings.IGNORE_BVC_AUTH

    #Process POST return results from Password Form Submit:
    if request.method == 'POST':
        form = ResultsPasswordForm(request.POST, error_class=ErrorBox)
        if form.is_valid():
            rpf = form.cleaned_data
            password = rpf['password'].encode('utf-8')
            if check_password(password, survey.password):
                request.session['userid'] = survey.creator.id

    #Retrieve User Token - if user does not exist present password entry form
    try:
        userid = request.session.get('userid', '__nothing__')
        user = User.objects.get(id=userid)
    except User.DoesNotExist:
        if not ignore_bvc_auth:
            return render(request, 'password.html', {'form': ResultsPasswordForm()})

    #If authenticated via user token or ignoring auth for bvc rendering
    if ignore_bvc_auth or (user and survey.creator.id == user.id):
        survey_type_title = 'Team Temperature'
        if survey.survey_type == 'CUSTOMERFEEDBACK':
            survey_type_title = 'Customer Feedback'

        if not ignore_bvc_auth:
            request.session['userid'] = survey.creator.id
        teamtemp = TeamTemperature.objects.get(pk=survey_id)
        if team_name != '':
            if archive_id == '':
                results = teamtemp.temperatureresponse_set.filter(team_name = team_name, archived = False)
            else:
                past_date = teamtemp.temperatureresponse_set.filter(id=archive_id).values('archive_date')[0]
                results = teamtemp.temperatureresponse_set.filter(team_name = team_name, archived = True,archive_date=past_date['archive_date'])
                stats_date = past_date['archive_date']
            team_history = teamtemp.teamresponsehistory_set.filter(team_name = team_name).order_by('archive_date')
            num_rows = teamtemp.teamresponsehistory_set.filter(team_name = team_name).count()
            teams = teamtemp.teamresponsehistory_set.filter(team_name = team_name).values('team_name').distinct()
            archived_dates = teamtemp.temperatureresponse_set.filter(team_name = team_name, archived = True).values('archive_date','id').distinct('archive_date')
        else:
            if archive_id == '':
                results = teamtemp.temperatureresponse_set.filter(archived = False)
            else:
                past_date = teamtemp.temperatureresponse_set.filter(id=archive_id).values('archive_date')[0]
                results = teamtemp.temperatureresponse_set.filter( archive_date=past_date['archive_date'] )
                stats_date = past_date['archive_date']
            team_history = teamtemp.teamresponsehistory_set.all().order_by('archive_date')
            num_rows = teamtemp.teamresponsehistory_set.all().count()
            teams = teamtemp.teamresponsehistory_set.all().values('team_name').distinct()
            archived_dates = teamtemp.temperatureresponse_set.filter(archived = True).values('archive_date','id').distinct('archive_date')

        trend_period = timedelta(weeks=int(float(weeks_to_trend)))
        buffer_max = timedelta(days=3)
        max_date = timezone.now() + buffer_max
        min_date = max_date - trend_period - buffer_max

        team_index = 0
        if num_rows > 0:
            history_chart_schema = {"archive_date": ("datetime", "Archive_Date")}
            history_chart_columns = ('archive_date',)
            average_index = None
            for team in teams:
                history_chart_schema.update({team['team_name'] :  ("number",team['team_name'].replace("_", " "))})
                history_chart_columns = history_chart_columns + (team['team_name'],)
                if team['team_name'] == 'Average':
                    average_index = team_index
                team_index += 1
            
            history_chart_data = []
            row = None
            for survey_summary in team_history:
                if row == None:
                    row = {}
                    row['archive_date'] = timezone.localtime(survey_summary.archive_date)
                elif row['archive_date'] != timezone.localtime(survey_summary.archive_date):
                    history_chart_data.append(row)
                    row = {}
                    row['archive_date'] = timezone.localtime(survey_summary.archive_date)
                row[survey_summary.team_name] = (float(survey_summary.average_score), str(float(survey_summary.average_score)) + " (" + str(survey_summary.responder_count) + " Responses)")
    
            history_chart_data.append(row)
    
            # Loading it into gviz_api.DataTable
            history_chart_table = gviz_api.DataTable(history_chart_schema)
            history_chart_table.LoadData(history_chart_data)
            
            # Creating a JSon string
            json_history_chart_table = history_chart_table.ToJSon(columns_order=(history_chart_columns))

            historical_options = {
                'legendPosition': 'newRow',
                'title' : survey_type_title + ' by Team',
                'vAxis': {'title': survey_type_title},
                'hAxis': {'title': "Month"},
                'seriesType': "bars",
                'vAxis': { 'ticks': [1,2,3,4,5,6,7,8,9,10] },
                'max': 12,
                'min': 0,
                'focusTarget': 'category',
                'tooltip': { 'trigger': 'selection', 'isHtml': 'true' },
            }
            if average_index != None:
                historical_options.update({'series': {average_index: {'type': "line"}}})



        if team_name != '' and stats_date == '':
            stats = survey.team_stats(team_name=team_name)
        elif team_name == '' and stats_date != '':
            stats = survey.archive_stats(archive_date=stats_date)
        elif team_name != '' and stats_date != '':
            stats = survey.archive_team_stats(team_name=team_name,archive_date=stats_date)
        else:
            stats = survey.stats()

        survey_teams = teamtemp.teams_set.all()

        if int(float(num_iterations)) > 0:
            multi_stats = calc_multi_iteration_average(team_name, survey, int(float(num_iterations)))
            if multi_stats:
                stats = multi_stats

        #generate word cloud
        words = ""
        word_cloudurl = ""
        word_count = 0
        for word in stats['words']:
            for i in range(0,word['id__count']):
                words = words + word['word'] + " "
                word_count += 1

        #TODO Write a better lookup and model to replace this hack
        word_cloud_index = WordCloudImage.objects.filter(word_list = words)

        if word_cloud_index:
            if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), word_cloud_index[0].image_url)):
                word_cloudurl =  word_cloud_index[0].image_url
            else:
                #Files have been deleted remove from db and then regenerate
                WordCloudImage.objects.filter(word_list = words).delete()

        if word_cloudurl == "" and words != "":
            word_cloudurl = generate_wordcloud(words)
            if word_cloudurl:
                word_cloud = WordCloudImage(creation_date = timezone.now(),
                                            word_list = words, image_url = word_cloudurl)
                word_cloud.save()

        return render(request, 'bvc.html',
                { 'id': survey_id, 'stats': stats, 
                  'results': results, 'team_name':team_name, 'archive_date':stats_date,
                  'pretty_team_name':team_name.replace("_", " "),
                  'team_history' : team_history ,
                  'json_historical_data' : json_history_chart_table, 'min_date' : min_date, 'max_date' : max_date,
                  'historical_options' : historical_options, 'archived_dates': archived_dates,
                  'survey_teams': survey_teams, 'word_cloudurl':word_cloudurl, 'num_iterations':num_iterations,
                  'team_count' : team_index, 'survey_type_title' : survey_type_title
                } )
    else:
        return render(request, 'password.html', {'form': ResultsPasswordForm()})


def reset(request, survey_id):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    # if valid session token or valid password render results page

    if not authenticated_user(request, survey_id):
        return HttpResponseRedirect('/admin/%s' % survey_id)

    teamtemp = TeamTemperature.objects.get(pk=survey_id)

    #Save Survey Summary for all survey teams
    arch_date = timezone.now()
    data = {'archived': True, 'archive_date': timezone.now()}
    teams = teamtemp.temperatureresponse_set.filter(archived = False).values('team_name').distinct()
    average_total = 0
    average_count = 0
    average_responder_total = 0
    for team in teams:
        Summary = None
        team_stats = None
        summary_word_list = ""
        team_stats = teamtemp.team_stats(team['team_name'])
        for word in team_stats['words'] :
            summary_word_list = summary_word_list + word['word'] + " "
        Summary = TeamResponseHistory(request = survey,
            average_score = team_stats['average']['score__avg'],
            word_list = summary_word_list,
            responder_count = team_stats['count'],
            team_name = team['team_name'],
            archive_date = arch_date)
        Summary.save()
        average_total = average_total + team_stats['average']['score__avg']
        average_count = average_count + 1
        average_responder_total = average_responder_total + team_stats['count']

        TemperatureResponse.objects.filter(request = survey_id, team_name = team['team_name'], archived = False).update(**data)

    #Save Survey Summary as AGREGATE AVERAGE for all teams
    data = {'archived': True, 'archive_date': timezone.now()}
    teams = teamtemp.temperatureresponse_set.filter(archived = False).values('team_name').distinct()
    Summary = None
    team_stats = None
    summary_word_list = ""
    team_stats = teamtemp.stats()
        
    if average_count > 0:
        Summary = TeamResponseHistory(request = survey,
            average_score = average_total/float(average_count),
            word_list = summary_word_list,
            responder_count = average_responder_total,
            team_name = 'Average',
            archive_date = arch_date)

    if Summary:
        Summary.save()
        nowstamp = timezone.now()
        data = {'archive_date': nowstamp}
        TeamTemperature.objects.filter(pk=teamtemp.id).update(**data)
        print >>sys.stderr,"Archiving: " + " " + teamtemp.id + " at " + str(nowstamp)

    return HttpResponseRedirect('/admin/%s' % survey_id)

def cron(request, pin):

    cron_pin = '0000'
    if settings.CRON_PIN:
        cron_pin = settings.CRON_PIN

    if pin == cron_pin:
        auto_archive_surveys(request)
        return HttpResponse()
    else:
        raise Http404

def auto_archive_surveys(request):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    print >>sys.stderr,"auto_archive_surveys: Start at " + str(timezone.now())

    teamtemps = TeamTemperature.objects.filter(archive_schedule__gt=0)
    nowstamp = timezone.now()
    data = {'archive_date': nowstamp}

    for teamtemp in teamtemps:
        next_archive_date = timezone.localtime(teamtemp.archive_date) + timedelta(days=(teamtemp.archive_schedule))

        if teamtemp.archive_date is None or (timezone.now().date() >= (timezone.localtime(teamtemp.archive_date) + timedelta(days=(teamtemp.archive_schedule))):
            scheduled_archive(request, teamtemp.id)
            TeamTemperature.objects.filter(pk=teamtemp.id).update(**data)
            print >>sys.stderr,"Archiving: " + " " + teamtemp.id + " at " + str(nowstamp)

    print >>sys.stderr,"auto_archive_surveys: Stop at " + str(timezone.now())


def scheduled_archive(request, survey_id):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    
    teamtemp = TeamTemperature.objects.get(pk=survey_id)
    
    #Save Survey Summary for all survey teams
    arch_date = timezone.now()
    data = {'archived': True, 'archive_date': timezone.now()}
    teams = teamtemp.temperatureresponse_set.filter(archived = False).values('team_name').distinct()
    average_total = 0
    average_count = 0
    average_responder_total = 0
    
    for team in teams:
        Summary = None
        team_stats = None
        summary_word_list = ""
        team_stats = teamtemp.team_stats(team['team_name'])
        for word in team_stats['words'] :
            summary_word_list = summary_word_list + word['word'] + " "
        Summary = TeamResponseHistory(request = survey,
                                      average_score = team_stats['average']['score__avg'],
                                      word_list = summary_word_list,
                                      responder_count = team_stats['count'],
                                      team_name = team['team_name'],
                                      archive_date = arch_date)
        Summary.save()
        average_total = average_total + team_stats['average']['score__avg']
        average_count = average_count + 1
        average_responder_total = average_responder_total + team_stats['count']
    
        TemperatureResponse.objects.filter(request = survey_id, team_name = team['team_name'], archived = False).update(**data)

    #Save Survey Summary as AGREGATE AVERAGE for all teams
    data = {'archived': True, 'archive_date': timezone.now()}
    teams = teamtemp.temperatureresponse_set.filter(archived = False).values('team_name').distinct()
    Summary = None
    team_stats = None
    summary_word_list = ""
    team_stats = teamtemp.stats()

    if average_count > 0:
        Summary = TeamResponseHistory(request = survey,
                                  average_score = average_total/float(average_count),
                                  word_list = summary_word_list,
                                  responder_count = average_responder_total,
                                  team_name = 'Average',
                                  archive_date = arch_date)

    if Summary:
        Summary.save()

    return

def team(request, survey_id):
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    # if valid session token or valid password render results page

    if request.method == 'POST':
        form = AddTeamForm(request.POST, error_class=ErrorBox)
        if form.is_valid():
            csf = form.cleaned_data
            team_name = csf['team_name'].replace(" ", "_")
            team_found = survey.teams_set.filter(team_name = team_name).count()
            if team_found == 0:
                team_details = Teams(request = survey,
                                team_name = team_name)
                team_details.save()
            return HttpResponseRedirect('/admin/%s' % survey_id)
    else:
        return render(request, 'team.html', {'form': AddTeamForm()})


def populate_chart_data_structures(survey_type_title, teams, team_history):
    #Populate GVIS History Chart Data Structures
    #In:
    #    teams: team list
    #    bvc_data['team_history']: query set of team or teams history temp data to chart
    #Out:
    #    historical_options
    #    json_history_chart_table
    #
    timezone.activate(pytz.timezone('Australia/Queensland'))
    num_rows = 0
    team_index = 0
    history_chart_schema = {"archive_date": ("datetime", "Archive_Date")}
    history_chart_columns = ('archive_date',)
    average_index = None
    for team in teams:
        history_chart_schema.update({team['team_name'] :  ("number",team['team_name'].replace("_", " "))})
        history_chart_columns = history_chart_columns + (team['team_name'],)
        if team['team_name'] == 'Average':
            average_index = team_index
        team_index += 1
    
    history_chart_data = []
    row = None
    for survey_summary in team_history:
        if row == None:
            row = {}
            row['archive_date'] = timezone.localtime(survey_summary.archive_date)
        elif row['archive_date'] != timezone.localtime(survey_summary.archive_date):
            history_chart_data.append(row)
            row = {}
            row['archive_date'] = timezone.localtime(survey_summary.archive_date)
        row[survey_summary.team_name] = (float(survey_summary.average_score), str(float(survey_summary.average_score)) + " (" + str(survey_summary.responder_count) + " Responses)")
    
    history_chart_data.append(row)
    
    # Loading it into gviz_api.DataTable
    history_chart_table = gviz_api.DataTable(history_chart_schema)
    history_chart_table.LoadData(history_chart_data)
    
    # Creating a JSon string
    json_history_chart_table = history_chart_table.ToJSon(columns_order=(history_chart_columns))
    
    historical_options = {
        'legendPosition': 'newRow',
        'title' : survey_type_title + ' by Team',
        'vAxis': {'title': survey_type_title},
        'hAxis': {'title': "Month"},
        'seriesType': "bars",
        'vAxis': { 'ticks': [1,2,3,4,5,6,7,8,9,10] },
        'max': 12,
        'min': 0,
        'focusTarget': 'category',
        'tooltip': { 'trigger': 'selection', 'isHtml': 'true' },
    }
    if average_index != None:
        historical_options.update({'series': {average_index: {'type': "line"}}})

    return historical_options, json_history_chart_table, team_index

def populate_bvc_data(survey_id_list, team_name, archive_id, num_iterations):
    #in: survey_id, team_name and archive_id
    #out:
    #    populate bvc_data['archived_dates']       For Drop Down List
    #    populate bvc_data['archive_date']         For displaying above guage for an archived BVC
    #    populate bvc_data['archived']             Are these results archived results
    #    populate bvc_data['stats_date']           Archive date for these stats - they are for an archived iteration
    #    populate bvc_data['team_history']         Set of responses
    #    populate bvc_data['survey_teams']         All teams for this survey
    #    populate bvc_data['survey_id']            This survey id
    #    populate bvc_data['team_name']            '' for multi team or specific team name to filter to
    #    populate bvc_data['pretty_team_name']     no spaces in team name above
    #    populate bvc_data['survey_type_title']    survey type Team Temperature or Customer Feedback
    
    bvc_data={}
    bvc_data['stats_date'] = ''
    bvc_data['survey_teams']=[]
    bvc_data['archived'] = False
    bvc_data['archive_date'] = None
    bvc_data['word_cloudurl'] = ''
    
    survey_filter = { 'request__in' : survey_id_list }
    
    bvc_data['survey_teams'] = Teams.objects.filter(**survey_filter)
    bvc_data['team_name'] = team_name
    bvc_data['pretty_team_name'] = team_name.replace("_", " ")
    
    #if any survey's are customer feedback surveys display customer BVC
    num_teamtemp_surveys = TeamTemperature.objects.filter(pk__in = survey_id_list, survey_type = 'TEAMTEMP').count
    num_cust_surveys = TeamTemperature.objects.filter(pk__in = survey_id_list, survey_type = 'CUSTOMERFEEDBACK').count
    #Bug here
    #what does count return for an empty set?
    #is None greater than 0?
    bvc_data['survey_type_title'] = 'Team Temperature'
    if num_teamtemp_surveys == 0 and num_cust_surveys > 0:
        bvc_data['survey_type_title'] = 'Customer Feedback'

    if team_name != '':
        team_filter = dict({ 'team_name' : team_name }, **survey_filter)
    else:
        team_filter = survey_filter
    
    bvc_data['team_history'] = TeamResponseHistory.objects.filter(**team_filter).order_by('archive_date')
    bvc_data['teams'] = TeamResponseHistory.objects.filter(**team_filter).values('team_name').distinct()
    bvc_data['num_rows'] = TeamResponseHistory.objects.filter(**team_filter).count()

    if archive_id == '':
        filter = dict({ 'archived' : False }, **team_filter)
    else:
        archive_set = TemperatureResponse.objects.filter(request__in=survey_id_list, id=archive_id).values('archive_date')
        filter = dict({ 'archived' : True }, **team_filter)
        if archive_set:
            bvc_data['stats_date'] = archive_set[0]['archive_date']
            filter = dict({ 'archive_date' : bvc_data['stats_date'] }, **filter)
    
    results = TemperatureResponse.objects.filter(**filter)

    if results:
        bvc_data['archived'] = results[0].archived
        bvc_data['archive_date'] = results[0].archive_date


    archived_filter = dict({'archived' : True }, **team_filter)
    bvc_data['archived_dates'] = TemperatureResponse.objects.filter(**archived_filter).values('archive_date','id').distinct('archive_date')

    bvc_data['stats'] = generate_bvc_stats(survey_id_list, team_name, bvc_data['stats_date'], num_iterations)

    return bvc_data

def cached_word_cloud(word_list):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    words = ""
    word_cloudurl = ""
    word_count = 0

    for word in word_list:
        for i in range(0,word['id__count']):
            words = words + word['word'] + " "
            word_count += 1
    
    #TODO Write a better lookup and model to replace this hack
    word_cloud_index = WordCloudImage.objects.filter(word_list = words)
    
    if word_cloud_index:
        if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), word_cloud_index[0].image_url)):
            word_cloudurl =  word_cloud_index[0].image_url
        else:
            #Files have been deleted remove from db and then regenerate
            WordCloudImage.objects.filter(word_list = words).delete()
    
    if word_cloudurl == "" and words != "":
        word_cloudurl = generate_wordcloud(words)
        if word_cloudurl:
            word_cloud = WordCloudImage(creation_date = timezone.now(),
                                        word_list = words, image_url = word_cloudurl)
            word_cloud.save()
    return word_cloudurl

def generate_bvc_stats(survey_id_list, team_name, archive_date, num_iterations):
    #Generate Stats for Team Temp Average for guage and wordcloud - look here for BT BANK Guage and Word Cloud
    #we can't do history as archive isn't syncronised...
    #BVC.html uses stats.count and stats.average.score__avg and cached word cloud uses stats.words below
    
    survey_count = 0
    agg_stats = {}
    agg_stats['count'] = 0
    agg_stats['average'] = 0.00
    agg_stats['words'] = []

    survey_filter = { 'id__in' : survey_id_list }
    survey_set = TeamTemperature.objects.filter(**survey_filter)

    for survey in survey_set:
        if team_name != '' and archive_date == '':
            stats = survey.team_stats(team_name=team_name)
        elif team_name == '' and archive_date != '':
            stats = survey.archive_stats(archive_date=archive_date)
        elif team_name != '' and archive_date != '':
            stats = survey.archive_team_stats(team_name=team_name,archive_date=archive_date)
        else:
            stats = survey.stats()

        #Calculate and average and word cloud over multiple iterations (changes date range but same survey id):
        if int(float(num_iterations)) > 0:
            multi_stats = calc_multi_iteration_average(team_name, survey, int(float(num_iterations)))
            if multi_stats:
                stats = multi_stats

        survey_count += 1
        agg_stats['count'] = agg_stats['count'] + stats['count']
        
        if stats['average']['score__avg']:
            agg_stats['average'] = (agg_stats['average'] + stats['average']['score__avg']) / survey_count
        agg_stats['words'] = agg_stats['words'] + list(stats['words'])

    return agg_stats

def calc_multi_iteration_average(team_name, survey, num_iterations=2):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    iteration_index = 0
    if num_iterations > 0:
        iteration_index = num_iterations - 1
    else:
        return None
    
    archive_dates = survey.temperatureresponse_set.filter(archive_date__isnull=False).values('archive_date').distinct().order_by('-archive_date')
    
    if archive_dates.count() < num_iterations and archive_dates.count() > 0:
        iteration_index = archive_dates.count() - 1 #oldest archive date if less than target iteration count
    
    if archive_dates.count() > iteration_index:
        response_dates = survey.temperatureresponse_set.filter(archive_date = archive_dates[iteration_index]['archive_date']).values('response_date').order_by('response_date')
        
        if team_name != '':
            accumulated_stats = survey.accumulated_team_stats(team_name,timezone.now(),response_dates[0]['response_date'])
        else:
            accumulated_stats = survey.accumulated_stats(timezone.now(),response_dates[0]['response_date'])
        
        return accumulated_stats
    
    return None

def _bvc(request, survey_id, team_name='', archive_id= '', num_iterations='0', add_survey_ids=None):
    survey_ids = request.REQUEST.get('add_survey_ids',add_survey_ids)

    survey_id_list = [survey_id]
    if survey_ids:
        survey_id_list = survey_id_list + survey_ids.split(',')

    timezone.activate(pytz.timezone('Australia/Queensland'))
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    
    json_history_chart_table = None
    historical_options = {}
    bvc_data={}
    team_index = 0
    
    #Populate data for BVC including previously archived BVC
    #bvc_data['archived_dates'] & ['archive_date'] & ['archived'] & ['stats_date'] & ['team_history'] & ['survey_teams']
    bvc_data = populate_bvc_data(survey_id_list, team_name, archive_id, num_iterations)
    bvc_data['survey_id'] = survey_id

    #If there is history to chart generate all data required for historical charts
    if bvc_data['num_rows'] > 0:
        historical_options, json_history_chart_table, team_index = populate_chart_data_structures(bvc_data['survey_type_title'], bvc_data['teams'], bvc_data['team_history'])
    #raise Exception(historical_options,json_history_chart_table,team_index)

    #Cached word cloud
    if bvc_data['stats']['words']:
        bvc_data['word_cloudurl'] = cached_word_cloud(bvc_data['stats']['words'])

    return render(request, '_bvc.html',
                  {
                  'bvc_data' : bvc_data,
                  'json_historical_data' : json_history_chart_table,
                  'historical_options' : historical_options,
                  'team_count' : team_index,
                  'num_iterations':num_iterations
                  } )

