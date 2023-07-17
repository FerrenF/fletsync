import json

from flask import render_template
from flask_login import current_user
from util.misc import meta_data

def index():
    from models.restClientManager import fletsync_client_manager
    context = {'meta': meta_data()}
    if current_user.is_authenticated:
        etsy_api = fletsync_client_manager.get_client('etsy')
        etsy_api.associate_user(current_user.get_id())
        etsy_api.retrieve_saved_authorizations()

        wc_api = fletsync_client_manager.get_client('wc')
        wc_api.associate_user(current_user.get_id())
        wc_api.retrieve_saved_authorizations()

        context['etsy_api'] = etsy_api
        context['wc_api'] = wc_api

        if wc_api.authorized:
            test_command = wc_api.getProducts(context="view")
            product_list = test_command.content
            for product in product_list:
                print(product.get('name', 'Missing name...'))

        if etsy_api.authorized:
            test_command = etsy_api.getMe()
            print(test_command)

    return render_template('index.html', **context)
