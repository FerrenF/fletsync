import datetime

from authlib.common.security import generate_token
from database.authorization_repository import AuthorizationRepository
from util.openapi.oauth.etsy_oauth_scopes import EtsyOAuthScope


class AuthorizationInstance:

    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, name, **kwargs):
        self.user_id = kwargs.get('user_id', None)
        self.name = name
        self.error = kwargs.get('error', None)
        self.authorization_code = kwargs.get('authorization_code', None)
        self.authorization_token = kwargs.get('authorization_token', None)
        self.refresh_token = kwargs.get('refresh_token', None)
        self.expiration_date = kwargs.get('expiration_date', None)
        self.authorization_state = kwargs.get('authorization_state', None)
        self.code_verifier = kwargs.get('code_verifier', generate_token(64))
        self.scope = EtsyOAuthScope(kwargs.get('scope', None))

        self.authorization_type = 'initial'
        # Types: initial, refresh - because the refresh token can be used when expired

    def to_dict(self):
        return {
            'user_id' : self.user_id,
            'name': self.name,
            'error': self.error,
            'authorization_code': self.authorization_code,
            'authorization_token': self.authorization_token,
            'refresh_token': self.refresh_token,
            'expiration_date': self.expiration_date,
            'authorization_state': self.authorization_state,
            'code_verifier': self.code_verifier,
            'scope': self.scope.toJSON(),
            'authorization_type': self.authorization_type
        }
    @property
    def expiration_datetime(self):
        if self.expiration_date is None:
            return None
        return datetime.datetime.strptime(self.expiration_date, AuthorizationInstance.DATE_FORMAT)

    def store(self):
        AuthorizationInstance.store_instance(self)

    def time_left(self):
        if self.expiration_date is not None:
            now = datetime.datetime.now()
            then = self.expiration_datetime
            return then - now
        return -1

    def is_expired(self):
        if self.expiration_date is not None:
            now = datetime.datetime.now()
            then = self.expiration_datetime
            if now > then:
                return True
        return False

    def has_valid_token(self):
        return self.authorization_token is not None and not self.is_expired()

    def ready_for_token(self):
        return self.error is None and self.authorization_code is not None and self.authorization_state is not None

    def set_authorize(self, token, refresh_token, expiration_date):
        self.authorization_token = token
        self.refresh_token = refresh_token
        self.expiration_date = expiration_date

    @staticmethod
    def purge_request(req):
        result = AuthorizationRepository.delete_authorization_for_user_id(req.user_id, req.name)
        return result > 0

    @staticmethod
    def store_instance(instance, to_user_id=None):
        if to_user_id is not None:
            instance.user_id = to_user_id
        if instance.user_id is not None:
            AuthorizationRepository.store_authorization(instance)

    @staticmethod
    def retrieve_request_by(name, from_user_id):
        """
        :param name: Assigned to request when stored.
        :param from_user_id: User_ID associated with request.
        :return: AuthorizationInstance or None
        """
        params = AuthorizationRepository.get_authorization_from_user_id(from_user_id, name)

        return AuthorizationInstance(**params) if params is not None else None

