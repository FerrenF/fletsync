class AuthType:

    # AuthType is the base class for any authentication related alterations made to an open api request.
    # It could be an OAuth2 alteration adding the correct token to the header, or an api key added to the request body.

    # In any case, the only requirements are that the derived classes provide:
    # a method to alter requests in such a way that satisfies the authentication type.
    # a method to determine whether an AuthType is authorized.

    # For example, an api-key authorization type is implicitly always authorized.
    # An OAuth2 auth type is not always in an authorized state, and must periodically refresh.

    def __init__(self, auth_type=None):
        self.type = auth_type

    @property
    def authorized(self):
        return False

    def wrap_command(self, **command):
        return command

    @property
    def app_registered(self):
        return True

    def register_app(self, app):
        pass

    def associate_user(self, user_id):
        pass

    # Not every type of authorization scheme will need to store something.
    def retrieve_saved_authorization(self):
        pass
