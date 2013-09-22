from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from responses.forms import CreateSurveyForm, SurveyResponseForm
from responses.models import User, TeamTemperature, TemperatureResponse
from datetime import datetime
import utils
import responses

def home(request):
    if request.method == 'POST':
        form = CreateSurveyForm(request.POST)
        if form.is_valid():
            csf = form.cleaned_data
            form_id = utils.random_string(8)
            userid = responses.get_or_create_userid(request)
            user, created = User.objects.get_or_create(id=userid)
            # TODO check that id is unique!
            survey = TeamTemperature(creation_date = datetime.now(),
                                     duration = csf['duration'],
                                     password = csf['password'],
                                     creator_id = user,
                                     id = form_id)
            survey.save()
            return HttpResponseRedirect('/admin/%s' % form_id)
    else:
        form = CreateSurveyForm()
    return render(request, 'index.html', {'form': form})

def submit(request, id):
    userid = responses.get_or_create_userid(request)
    user, created = User.objects.get_or_create(id=userid)
    try:
        survey = TeamTemperature.objects.get(id = id)
    except TeamTemperature.DoesNotExist:
        return '404'
    if request.method == 'POST':
        form = SurveyResponseForm(request.POST)
        if form.is_valid():
            srf = form.cleaned_data
            # TODO check that id is unique!
            response = TemperatureResponse(request_id = survey,
                                           score = srf['score'],
                                           word = srf['word'],
                                           responder_id = user)
            response.save()
            form = SurveyResponseForm(instance=response)
    else:
        try: 
            previous = TemperatureResponse.objects.get(request_id = id, 
                                                       responder_id = user) 
        except TemperatureResponse.DoesNotExist:
            previous = None
         
        form = SurveyResponseForm(instance=previous)
    return render(request, 'form.html', {'form': form})

def admin(request, survey_id):
    # if valid session token or valid password render results page
    if request.method == 'POST':
        form = ResultsPasswordForm(request.POST)
        if form.is_valid():
            rpf = form.cleaned_data
            password = rpf['password']
        else:
            return render(request, 'password.html', {'form': ResultsPasswordForm()})
    else: 
        try: 
            userid = request.session.get('userid', '__nothing__')
            user = User.objects.get(id=userid)
        except User.DoesNotExist:
            return render(request, 'password.html', {'form': ResultsPasswordForm()})
    survey = TeamTemperature.objects.get(id=survey_id)
    if survey.creator_id.id == user.id or survey.password == password:
        return render(request, 'results.html', 
                { 'id': survey_id, 'stats': survey.stats()})

