from flask import render_template
from flask_login import current_user

from util.misc import meta_data


def index():

    context = {'meta': meta_data()}
    if current_user.is_authenticated:
        context['auth_status'] = None
    return render_template('index.html', **context)
