from flask import redirect, url_for


def etsy_login():

    from util.openapi.etsy_openapi import etsy_api
    from flask_login import current_user
    if current_user.is_authenticated:
        etsy_api.associate_user(current_user.get_id())
        etsy_api.retrieve_saved_authorization()
        destination = etsy_api.oauth_session.create_authorization_endpoint()

    else:
        destination = url_for('index')
    return redirect(destination)
