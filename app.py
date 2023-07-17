from flask import Flask

from bootstrap.appRegisterGlobals import app_register_globals
from bootstrap.appRegisterRoutes import app_register_routes
from config import APP_NAME
from flask import g


app = Flask(APP_NAME)
app.config.from_pyfile('config.py')

app_register_globals(app)
app_register_routes(app)

if __name__ == "main":
    app.run()




