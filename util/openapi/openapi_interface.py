import json
import urllib.request
from datetime import timedelta
from dataclasses import dataclass
import requests
from flask import Flask
from requests import Response

from config import ETSY_API_KEY



@dataclass(eq=True, repr=True)
class PreparedOpenAPICommand:
    route: str = None
    method: str = ""
    body: dict = None
    headers: dict = None
    arguments: dict = None
    scope: str = None
    server: str = None
    name: str = None

@dataclass
class APIResponse:
    content: dict
    success: bool
    code: int
    description: str


class OpenAPI_CommandException(Exception):
    def __init__(self, command, type, entity, description):
        super().__init__()
        self.description=description
        self.entity=entity
        self.type=type
        self.command=command
    def __str__(self):
        return self.description


class OpenAPI_Interface:

    def __init__(self, version, servers, commands, schemas, security, app: Flask = None):
        self.auth_types = dict()
        self.command_dictionary = commands
        self.version = version
        self.servers = servers
        self.schema_dictionary = schemas
        self.security_dictionary = security
        self.requests_session = requests.Session()
        self.oauth_session = None
        self.associated_user = None
        self.registered_app: Flask = app

    @property
    def app_registered(self):
        return self.registered_app is not None

    def register_app(self, app: Flask):
        self.registered_app = app
        for auth_type in self.auth_types.values():
            auth_type.register_app(app)

    def get_token_authorized_user(self):
        return self.oauth_session.get_token_id_prefix()

    def get_token_authorization_header(self):
        return self.oauth_session.get_authorization_header()

    def associate_user(self, user_id):
        self.associated_user = user_id
        for auth_type in self.auth_types.values():
            auth_type.associate_user(user_id)

    def retrieve_saved_authorizations(self):
        for auth_type in self.auth_types.values():
            auth_type.retrieve_saved_authorization()

    def get_server(self, index=0):
        if len(self.servers) > index:
            return self.servers[index]

    def get_server_uri(self, index=0):
        s = self.get_server(index)
        return s.get('url', None)

    @property
    def authorized(self):
        authorized = True
        for auth in self.auth_types.values():
            if not auth.authorized:
                authorized = False
        return authorized

    def auth_type_exists(self, typeof):
        return typeof in self.auth_types

    def get_auth_type(self, obj):
        result = self.auth_types.get(obj, None)
        return result

    def add_auth_type(self, auth_type):
        self.auth_types[type(auth_type)] = auth_type

    def process_auth_types_on(self, prepared_command: PreparedOpenAPICommand):
        """
        :param prepared_command: PreparedOpenAPICommand to process auth_types on
        :return: prepared_command
        """
        for auth_type in self.auth_types.values():
            auth_type.wrap_command(prepared_command)
        return prepared_command

    def get_command_info(self, operation_name):
        if operation_name not in self.command_dictionary:
            return None
        return self.command_dictionary[operation_name]

    def get_command_body_requirements(self, operation_name):
        inf = self.get_command_info(operation_name)
        return inf['body'].get('content', None)

    def get_command_response(self, operation_name, status):
        command_responses = self.get_command_responses(operation_name)
        result = command_responses.get(str(status), None)
        return result

    def get_command_responses(self, operation_name):
        command_info = self.get_command_info(operation_name)
        if command_info is None:
            return None

        return command_info.get('responses', None)

    def make_command(self, operation_name, **kwargs):

        command_info = self.get_command_info(operation_name)
        if command_info is None:
            print("Failed command creation at lookup 1")
            return None

        prepared_command = PreparedOpenAPICommand(name=operation_name,
                                                  route=command_info.get("route", None),
                                                  method=command_info.get("method", 'get'))
        prepared_command.headers = dict()
        h = prepared_command.headers
        h['Content-Type'] = "application/x-www-form-urlencoded; charset=utf-8"

        required_body = command_info.get('requestBody', None)
        required_arguments = command_info.get('parameters', None)
        if required_arguments is not None:
            for argument in required_arguments:
                required = argument.get('required', "true")
                if argument['name'] not in kwargs.keys() and required == "true":
                    raise(OpenAPI_CommandException(prepared_command,'argument','name',argument.get('description', "Missing required argument.")))

                sr = str(prepared_command.route)
                arg_n = argument['name']
                if argument['in'] == 'path' and arg_n in prepared_command.route:
                    p = kwargs.pop(kwargs[arg_n])
                    s_rep = sr.replace("{"+arg_n+"}", p)
                    prepared_command.route = s_rep

        if required_body is not None:
            if kwargs.get('body', None) is not None:
                raise(OpenAPI_CommandException(prepared_command, 'component','body','Missing required request body.'))
            else:
                prepared_command.body = kwargs['body']
            #TODO: Process body requirements for uploads. I don't need that immediately

        prepared_command.arguments = kwargs
        server = self.get_server_uri()
        prepared_command.server = server

        # Finally, process authorization types on the command
        prepared_command = self.process_auth_types_on(prepared_command)

        return prepared_command

    def send_command(self, command):

        if command is None:
            print("Problem with command.")
            return None
        session = requests.session()
        session.headers.update(command.headers)
        response = None
        result = APIResponse({}, False, -1, "Empty result")
        if command.method == 'get':
            response = session.get(command.server+command.route, params=command.arguments, data=command.body)

        if response is not None:
            result = self.parse_command_response(command.name, response)

        return result
    def parse_command_response(self, operation, response : Response):

        code = response.status_code
        respo = self.get_command_response(operation, code)
        body = None
        success = (code == 200)
        description = respo.get("description", "Missing response description.")
        if success:
            body = json.loads(response.text)

        return APIResponse(body, success, code, description)
    @staticmethod
    def from_remote_json(uri, app=None):
        from database.cache import UriCache
        response = UriCache.get_if_fresh(uri, timedelta(days=1))
        if response is None:
            req = urllib.request.Request(uri)
            response = urllib.request.urlopen(req, timeout=3000)
            resp = response.read()
            UriCache.store_uri(uri, resp)
            response = resp

        command_dictionary = dict()
        json_doc = json.loads(response)
        openapi_version = json_doc.get("openapi", None)

        openapi_servers = json_doc.get("servers", None)
        openapi_paths = json_doc.get("paths", None)

        openapi_components = json_doc.get("components", None)
        openapi_security_schemes = openapi_components.get("securitySchemes",
                                                          None) if openapi_components is not None else None
        openapi_schemas = openapi_components.get("schemas",
                                                          None) if openapi_components is not None else None

        for openapi_path in openapi_paths:
            path_information = openapi_paths[openapi_path]
            for operation_type in path_information:

                operation = path_information[operation_type]

                command_name = operation.get('operationId', None)

                command_desc = operation.get('description', None)
                command_parameters = operation.get('parameters', None)
                command_responses = operation.get('responses', None)
                command_body = operation.get('requestBody', None)
                command_security = operation.get('security', None)
                if not (command_name and command_responses):

                    continue

                command_dictionary[command_name] = {
                            "description": command_desc,
                            "parameters": command_parameters,
                            "responses": command_responses,
                            "route": openapi_path,
                            "method": operation_type,
                            "body": command_body,
                            "security": command_security
                        }

        return OpenAPI_Interface(openapi_version, openapi_servers, commands=command_dictionary, schemas=openapi_schemas, security=openapi_security_schemes, app=app)