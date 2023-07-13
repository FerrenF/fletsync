import json
import urllib.request
from datetime import timedelta

import requests

from config import ETSY_API_KEY



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

    def __init__(self, version, servers, commands, schemas, security):
        self.command_dictionary = commands
        self.version = version
        self.servers = servers
        self.schema_dictionary = schemas
        self.security_dictionary = security
        self.requests_session = requests.Session()
        self.oauth_session = None
        self.associated_user = None

    def get_token_authorized_user(self):
        return self.oauth_session.get_token_id_prefix()

    def get_token_authorization_header(self):
        return self.oauth_session.get_authorization_header()

    def associate_user(self,user_id):
        self.associated_user = user_id
        if self.oauth_session is not None:
            self.oauth_session.associate_user(user_id)

    def get_server(self, index=0):
        if len(self.servers) > index:
            return self.servers[index]

    def get_server_uri(self, index=0):
        s = self.get_server(index)
        return s.get('url', None)

    @property
    def authorized(self):
        return self.oauth_session.authorized if self.oauth_session is not None else False

    def link_oauth(self, oauth_object):
        self.oauth_session = oauth_object

    def get_command_info(self, operation_name):
        if operation_name not in self.command_dictionary:
            return None
        return self.command_dictionary[operation_name]

    def get_command_response(self, operation_name, status):
        command_responses = self.get_command_responses(operation_name)
        return command_responses.get(status, None)

    def get_command_responses(self, operation_name):
        command_info = self.get_command_info(operation_name)
        if command_info is None:
            return None

        return command_info.get('responses', None)

    def make_command(self, operation_name, **kwargs):

        if operation_name not in self.command_dictionary:
            return None

        prepared_command = dict()
        command_info = self.get_command_info(operation_name)
        if command_info is None:
            return None
        prepared_command['route'] = command_info['route']
        prepared_command['method'] = command_info['method']
        prepared_command['body'] = None
        prepared_command['headers'] = dict()
        prepared_command['arguments'] = None
        prepared_command['scope'] = None

        h = prepared_command['headers']
        h['Content-Type'] = "application/x-www-form-urlencoded; charset=utf-8"

        required_security = command_info.get('security', None)
        if required_security is not None:
            for security_type in required_security:
                if 'api_key' in security_type:
                    h['x-api-key'] = ETSY_API_KEY
                if 'oauth2' in security_type:
                    prepared_command['scope'] = security_type['oauth2']
                    h = h.update(self.get_token_authorization_header())

        required_body = command_info.get('requestBody', None)
        required_arguments = command_info.get('parameters', None)
        if required_arguments is not None:
            for argument in required_arguments:
                required = argument.get('required', True)
                if argument['name'] not in kwargs.keys() and required:
                    raise(OpenAPI_CommandException(prepared_command,'argument','name',argument.get('description', "Missing required argument.")))
                s = prepared_command['route']
                sr = str(s)
                arg_n = argument['name']
                if argument['in'] == 'path' and arg_n in s:
                    p = kwargs.pop(kwargs[arg_n])
                    s_rep = sr.replace("{"+arg_n+"}", p)
                    prepared_command['route'] = s_rep

        if required_body is not None:
            required_body = required_body['content']
            prepared_command['body'] = required_body
            #TODO: Process body requirements for uploads. I don't need that immediately

        prepared_command['arguments'] = kwargs
        server = self.get_server_uri()
        prepared_command['server'] = server

        return prepared_command

    def send_command(self, command):

        session = self.requests_session
        session.headers.update(command['headers'])

        if command['method'] == 'get':
            return session.get(command['server']+command['route'], params=command['arguments'], data=command['body'])
        return None

    @staticmethod
    def from_remote_json(uri):
        from database.cache import UriCache
        response = UriCache.get_if_fresh(uri, timedelta(days=3))
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

            return OpenAPI_Interface(openapi_version, openapi_servers, command_dictionary, openapi_schemas, openapi_security_schemes)