from teamtemp import utils

def get_or_create_userid(request):
    if 'userid' not in request.session:
        request.session['userid'] = utils.random_string(8)
    return request.session['userid']
