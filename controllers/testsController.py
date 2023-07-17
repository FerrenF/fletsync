from flask import render_template
from flask_login import login_required, current_user

from util.misc import meta_data


@login_required
def tests_page():
    from models.restClientManager import fletsync_client_manager
    etsy_api = fletsync_client_manager.get_client('etsy')
    etsy_api.associate_user(current_user.get_id())
    etsy_api.retrieve_saved_authorizations()

    wc_api = fletsync_client_manager.get_client('wc')
    wc_api.associate_user(current_user.get_id())
    wc_api.retrieve_saved_authorizations()

    context = {'etsy_api': etsy_api, 'wc_api': wc_api}
    return render_template('tests.html', meta=meta_data(), **context)