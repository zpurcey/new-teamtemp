from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.core.urlresolvers import reverse
from responses.forms import CreateSurveyForm, SurveyResponseForm, ResultsPasswordForm, ErrorBox
from responses.models import User, TeamTemperature, TemperatureResponse
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime
from teamtemp import utils, responses

def home(request):
    if request.method == 'POST':
        form = CreateSurveyForm(request.POST, error_class=ErrorBox)
        if form.is_valid():
            csf = form.cleaned_data
            form_id = utils.random_string(8)
            userid = responses.get_or_create_userid(request)
            user, created = User.objects.get_or_create(id=userid)
            # TODO check that id is unique!
            survey = TeamTemperature(creation_date = datetime.now(),
                                     password = make_password(csf['password']),
                                     creator = user,
                                     id = form_id)
            survey.save()
            return HttpResponseRedirect('/admin/%s' % form_id)
    else:
        form = CreateSurveyForm()
    return render(request, 'index.html', {'form': form})

def submit(request, survey_id):
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
                                           responder = user)
            response.save()
            response_id = response.id
            form = SurveyResponseForm(instance=response)
            thanks = "Thank you for submitting your answers. You can " \
                     "amend them now or later if you need to"
    else:
        try: 
            previous = TemperatureResponse.objects.get(request = survey_id, 
                                                       responder = user) 
            response_id = previous.id
        except TemperatureResponse.DoesNotExist:
            previous = None
            response_id = None

        form = SurveyResponseForm(instance=previous)
    return render(request, 'form.html', {'form': form, 'thanks': thanks,
                                         'response_id': response_id})

def admin(request, survey_id):
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
        request.session['userid'] = survey.creator.id
        teamtemp = TeamTemperature.objects.get(pk=survey_id)
        results = teamtemp.temperatureresponse_set.all()

        return render(request, 'results.html', 
                { 'id': survey_id, 'stats': survey.stats(), 
                  'results': results})
    else:
        return render(request, 'password.html', {'form': ResultsPasswordForm()})

