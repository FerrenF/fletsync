import json

import requests
from flask import render_template, request, render_template_string
from flask_login import login_required, current_user

from util.misc import meta_data
from util.openapi.openapi_interface import APIResponse, OpenAPI_CommandException


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




def process_console_input(data):

    form_data = data.copy()
    from models.restClientManager import fletsync_client_manager
    user_id = form_data.pop('user_id', None)
    selected_interface = form_data.pop('interface', None)

    if user_id is None:
        return APIResponse({}, False, 400, "Missing user_id in request.")
    if selected_interface is None:
        return APIResponse({}, False, 400, "Missing interface selection.")

    command = form_data.pop('operationName', None)
    if command is None:
        return APIResponse({}, False, 400, "Missing operation.")

    # Time to put together a command.
    api = fletsync_client_manager.get_client(selected_interface)

    if api is None:
        return APIResponse({}, False, 400, "API does not exist.")

    api.associate_user(user_id)
    api.retrieve_saved_authorizations()

    if not api.authorized:
        return APIResponse({}, False, 401, "API is not authorized for user_id.")

    try:
        command_builder = api.make_command(command, **form_data)
    except OpenAPI_CommandException as e:
        return APIResponse({}, False, 400, "Command building failed: "+e.description)
    if command_builder is None:
        return APIResponse({}, False, 400, "Command processed, but it's empty.")


    result = api.send_command(command_builder)
    return result


def console_input():

    if request.method == "POST":
        b = request.form
        response = process_console_input(b)

        return render_template_string(response.to_json())

    return render_template_string("Butts.")
