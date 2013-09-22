from django.shortcuts import render, HttpResponseRedirect
from responses.forms import CreateSurveyForm
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
    # if no data render survey form
    # if errors render survey form
    # else render survey submission success page
    return render(request, 'form.html', {'id': id})

def admin(request, id):
    # if valid session token or valid password render results page
    # otherwise ask for password
    return render(request, 'results.html', {'id': id})
