import bcrypt
from flask import request, render_template, redirect, url_for
from flask_login import login_user, logout_user

from models.user import User
from util.misc import meta_data


def login():

    def verify_password(password, hash):
        return password and bcrypt.checkpw(password.encode('utf8'), hash)

    if request.method == 'POST':
        name = request.form.get('user_name')
        password = request.form.get('password')

        # Query the database to find the user based on the email
        user = User.get_by_name(name)
        if user:
            print("Logging in "+name)
            if user and verify_password(password, user.password_hash):
                # Log in the user
                login_user(user)
                return redirect(url_for('index'))
            else:
                print("Access denied")
                # Invalid credentials, show an error message
                return render_template('auth/login.html', error='Invalid email or password', meta=meta_data())

    # Render the login form
    return render_template('auth/login.html', meta=meta_data())


def logout():
    # Log out the user
    logout_user()
    return redirect(url_for('login'))
