from teamtemp import utils


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
