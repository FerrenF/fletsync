from config import SECRET_KEY
from models.user import User
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    u = User.get_by_id(user_id)
    # Implement the logic to load the user object from the user ID
    return u  # Example implementation using a User model

def init_login_manager(app):
    login_manager.init_app(app)

