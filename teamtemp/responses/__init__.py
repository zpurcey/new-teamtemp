from teamtemp import utils

USER_ID_KEY = 'user_id'
ADMIN_KEY = 'admin_for_surveys'


def get_userid(request):
    session = request.session
    if USER_ID_KEY not in session:
        session[USER_ID_KEY] = None
        session.save()

    return session[USER_ID_KEY]


def set_userid(request, value):
    session = request.session
    session[USER_ID_KEY] = value

    return session[USER_ID_KEY]


def create_userid(request):
    session = request.session
    session[USER_ID_KEY] = utils.random_string(32)

    session.save()

    return session[USER_ID_KEY]


def get_admin_for_surveys(request):
    session = request.session
    if ADMIN_KEY not in session:
        session[ADMIN_KEY] = []
        session.save()

    return session[ADMIN_KEY]


def add_admin_for_survey(request, survey_id):
    admin_for_surveys_set = set(get_admin_for_surveys(request))

    admin_for_surveys_set.add(survey_id)

    session = request.session
    session[ADMIN_KEY] = list(admin_for_surveys_set)
    session.save()

    return session[ADMIN_KEY]


def is_admin_for_survey(request, survey_id):
    return survey_id in get_admin_for_surveys(request)
