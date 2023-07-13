from flask import render_template
from flask_login import current_user

from util.misc import meta_data



def index():

    from util.openapi.etsy_openapi import etsy_api
    context = {'meta': meta_data()}
    if current_user.is_authenticated:
        etsy_api.associate_user(current_user.get_id())
        etsy_api.retrieve_saved_authorization()
        context['etsy_api'] = etsy_api

        if etsy_api.authorized:
            etsy_api.getMe()

    return render_template('index.html', **context)
