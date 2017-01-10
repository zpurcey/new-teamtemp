from teamtemp import utils

USER_ID_KEY = 'user_id'
ADMIN_KEY = 'admin_for_surveys'


def get_userid(request):
    if USER_ID_KEY in request.session:
        return request.session[USER_ID_KEY]

    return None


def set_userid(request, value):
    request.session[USER_ID_KEY] = value
    return request.session[USER_ID_KEY]


def create_userid(request):
    request.session[USER_ID_KEY] = utils.random_string(32)
    return request.session[USER_ID_KEY]


def get_admin_for_surveys(request):
    if ADMIN_KEY in request.session:
        return set(request.session[ADMIN_KEY])

    return set()


def add_admin_for_survey(request, survey_id):
    admin_for_surveys_set = get_admin_for_surveys(request)
    admin_for_surveys_set.add(survey_id)

    request.session[ADMIN_KEY] = list(admin_for_surveys_set)

    return admin_for_surveys_set


def is_admin_for_survey(request, survey_id):
    admin_for_surveys_set = get_admin_for_surveys(request) or set()
    return survey_id in admin_for_surveys_set
