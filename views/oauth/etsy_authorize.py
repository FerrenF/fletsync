from flask import redirect, url_for




def redirect_on_success():
    return redirect(url_for('index'))


def redirect_on_failure(error):
    return redirect(url_for('index'))


def etsy_authorize():
    from util.openapi.etsy_openapi import etsy_api
    from flask_login import current_user
    if current_user.is_authenticated:
        etsy_api.associate_user(current_user.get_id())
        etsy_api.retrieve_saved_authorization()
        return etsy_api.oauth_session.receive_authorization_and_fetch(redirect_on_success, redirect_on_failure)
    return redirect(url_for('index'))


def etsy_purge_authorization():
    from util.openapi.etsy_openapi import etsy_api
    from flask_login import current_user
    if current_user.is_authenticated:
        etsy_api.associate_user(current_user.get_id())
        etsy_api.retrieve_saved_authorization()
        etsy_api.oauth_session.purge_request_instance()
    return redirect(url_for('index'))
