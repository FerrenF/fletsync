import bcrypt
import bson
import typing

import pymongo.collection
from flask_login import UserMixin, current_user

from database.user_repository import UserRepository
from util.fl_session import get_user_in_session


class User(UserMixin):
    def __init__(self, user: typing.Dict = None):
        self.user_id = user.get('user_id', pymongo.collection.ObjectId().__str__())
        self.user_name = user.get('user_name', None)
        self.password_hash = user.get('password_hash', None)
        self.role = user.get('role', None)
        self.authenticated = False

    def to_dict(self):
        return dict({
            'user_name': self.user_name,
            'user_id': self.get_id(),
            'password_hash': self.password_hash,
            'role': self.role
                     })

    @staticmethod
    def get_by_id(user_id):
        user = UserRepository.get_user_by_id(user_id)
        return User(user) if user is not None else None

    @staticmethod
    def get_by_name(user_name):
        user = UserRepository.get_user_by_name(user_name)
        return User(user) if user is not None else None

    def get_id(self):
        return self.user_id

    def is_active(self):
        """True, as all users are active."""
        return True

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def save_to_db(self):
        #Trigger save changes to DB
        return UserRepository.save_user(self)