from teamtemp import utils

USER_ID_KEY = 'user_id'
ADMIN_KEY = 'admin_for_surveys'


def get_userid(request):
    if USER_ID_KEY not in request.session:
        request.session[USER_ID_KEY] = None

    return request.session[USER_ID_KEY]


def set_userid(request, value):
    request.session[USER_ID_KEY] = value

    return request.session[USER_ID_KEY]


def create_userid(request):
    request.session[USER_ID_KEY] = utils.random_string(32)

    request.session.save()

    return request.session[USER_ID_KEY]


def get_admin_for_surveys(request):
    if ADMIN_KEY not in request.session:
        request.session[ADMIN_KEY] = []

    return request.session[ADMIN_KEY]


def add_admin_for_survey(request, survey_id):
    admin_for_surveys_set = set(get_admin_for_surveys(request))

    admin_for_surveys_set.add(survey_id)

    request.session[ADMIN_KEY] = list(admin_for_surveys_set)

    request.session.save()


    return request.session[ADMIN_KEY]

def is_admin_for_survey(request, survey_id):
    return survey_id in get_admin_for_surveys(request)
