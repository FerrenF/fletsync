from util.openapi.authorization.auth_type import AuthType
from util.openapi.openapi_interface import PreparedOpenAPICommand


class ApiKeyHandler(AuthType):
    def __init__(self, api_key):
        super().__init__(type(self))
        self.api_key = api_key

    @property
    def authorized(self):
        return True

    def wrap_command(self, command : PreparedOpenAPICommand):
        command.headers.update({"x-api-key": self.api_key})
        return command
