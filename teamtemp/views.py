from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.core.urlresolvers import reverse
from responses.forms import CreateSurveyForm, SurveyResponseForm, ResultsPasswordForm, ErrorBox, AddTeamForm
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
import unirest as Unirest
import os
from urlparse import urlparse
import errno
import urllib



def home(request):
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
                                     id = form_id)
            survey.save()
            team_details = Teams(request = survey,
                                team_name = team_name)
            team_details.save()
            return HttpResponseRedirect('/admin/%s/%s' % (form_id, team_name))
    else:
        form = CreateSurveyForm()
    return render(request, 'index.html', {'form': form})

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
    return render(request, 'form.html', {'form': form, 'thanks': thanks,
                                         'response_id': response_id})

def admin(request, survey_id, team_name=''):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    # if valid session token or valid password render results page
    password = None
    user = None
    survey_teams=[]
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

        return render(request, 'results.html',
                { 'id': survey_id, 'stats': stats,
                  'results': results, 'team_name':team_name,
                  'pretty_team_name':team_name.replace("_", " "),'survey_teams':survey_teams
                    } )
    else:
        return render(request, 'password.html', {'form': ResultsPasswordForm()})


def generate_wordcloud(word_list):

    mashape_key = os.environ.get('XMASHAPEKEY')
    if mashape_key != None:
        response = Unirest.post("https://gatheringpoint-word-cloud-maker.p.mashape.com/index.php",
                                headers={"X-Mashape-Key": mashape_key},
                                params={"config": "n/a", "height": 600, "textblock": word_list, "width": 800}
                                )
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



def bvc(request, survey_id, team_name='', archive_id= '', weeks_to_trend='12'):
    timezone.activate(pytz.timezone('Australia/Queensland'))
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    # if valid session token or valid password render results page
    password = None
    user = None
    num_rows = 0
    json_history_chart_table = None
    historical_options = {}
    stats_date = ''
    survey_teams=[]
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

        if num_rows > 0:
            history_chart_schema = {"archive_date": ("datetime", "Archive_Date")}
            history_chart_columns = ('archive_date',)
            team_index = 0
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
                    row[survey_summary.team_name] = float(survey_summary.average_score)
                elif row['archive_date'] != timezone.localtime(survey_summary.archive_date):
                    history_chart_data.append(row)
                    row = {}
                    row['archive_date'] = timezone.localtime(survey_summary.archive_date)
                    row[survey_summary.team_name] = float(survey_summary.average_score)
                else:
                    row[survey_summary.team_name] = float(survey_summary.average_score)
    
            history_chart_data.append(row)
    
            # Loading it into gviz_api.DataTable
            history_chart_table = gviz_api.DataTable(history_chart_schema)
            history_chart_table.LoadData(history_chart_data)
            
            # Creating a JSon string
            json_history_chart_table = history_chart_table.ToJSon(columns_order=(history_chart_columns))
            #TODO - set series to be line where team name = average
            historical_options = {
                'legendPosition': 'newRow',
                'title' : 'Team Temperature by Team',
                'vAxis': {'title': "Team Temperature"},
                'hAxis': {'title': "Month"},
                'seriesType': "bars",
                'vAxis': { 'ticks': [1,2,3,4,5,6,7,8,9,10] },
                'max': 12,
                'min': 0
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

        #generate word cloud
        words = ""
        word_cloudurl = ""
        for word in stats['words']:
            words = words + word['word'] + " "

        #TODO Write a better lookup and model to replace this hack
        word_cloud_index = WordCloudImage.objects.filter(word_list = words)

        if word_cloud_index:
            word_cloudurl =  word_cloud_index[0].image_url

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
                  'survey_teams': survey_teams, 'word_cloudurl':word_cloudurl
                } )
    else:
        return render(request, 'password.html', {'form': ResultsPasswordForm()})


def reset(request, survey_id):
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    # if valid session token or valid password render results page
    password = None
    user = None

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
        teamtemp = TeamTemperature.objects.get(pk=survey_id)
        request.session['userid'] = survey.creator.id

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
        Summary.save()


        return HttpResponseRedirect('/admin/%s' % survey_id)
    else:
        return render(request, 'password.html', {'form': ResultsPasswordForm()})


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
