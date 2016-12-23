from teamtemp import utils

ADMIN_KEY = 'admin_for_surveys'


def get_userid(request, default=None):
    if 'userid' in request.session:
        return request.session['userid']

    return default


def set_userid(request, value):
    request.session['userid'] = value
    return request.session['userid']


def create_userid(request):
    request.session['userid'] = utils.random_string(32)
    return request.session['userid']


def get_admin_for_surveys(request):
    if ADMIN_KEY in request.session:
        return set(request.session[ADMIN_KEY])

    return set()


def add_admin_for_survey(request, survey_id):
    admin_for_list = get_admin_for_surveys(request)
    admin_for_list.add(survey_id)

    request.session[ADMIN_KEY] = list(admin_for_list)

    return admin_for_list


def is_admin_for_survey(request, survey_id):
    admin_for_list = get_admin_for_surveys(request) or set()
    return survey_id in admin_for_list
