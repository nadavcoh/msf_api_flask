# https://flask.palletsprojects.com/en/2.2.x/tutorial/
# https://realpython.com/flask-google-login/
# https://github.com/realpython/materials/tree/master/flask-google-login
# To run: . venv/bin/activate
#         flask --debug run --cert=adhoc --port=2705

# Python standard libraries
import os
from time import time

# Third-party libraries
from flask import Flask, redirect, url_for, session
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from humanize import naturaltime

# Internal imports
# from app.db import init_db_command
from .user import User
from .msf_api import get_msf_api, API_SERVER
from .gold import get_gold, update_gold
from .farming import get_farming

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    #app.secret_key = os.environ.get("SECRET_KEY")

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
 
    # User session management setup
    # https://flask-login.readthedocs.io/en/latest
    login_manager = LoginManager()
    login_manager.init_app(app)

    # Flask-Login helper to retrieve a user from our db
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            resp = ("<p>Hello, {}! You're logged in! AUD: {}</p>"
                   "<div><p>Profile Picture:</p>"
                '<img src="{}" alt="Icon"></img>'
                '<img src="{}" alt="Frame"></img></div>'
                '<a class="button" href="/logout">Logout</a>'.format(
                    current_user.name, current_user.id, current_user.icon, current_user.frame)
                #+ json.dumps(get_gear("SHARD_TASKMASTER"))
                
                + '<a class="button" href="/gold">Update</a>')
            gold = get_gold()
            left = gold["goal"] - gold["current_points"]
            if left < 0:
                left = 0
            resp += "Gold: {:,}/{:,} Left: {:,} Upadated {}".format(gold["current_points"], gold["goal"], left, naturaltime(time() - gold["updated"]))
            
            return ((resp))
        else:
            return '<a class="button" href="/login">Login</a>'

    @app.route("/login")
    def login():
        msf_api = get_msf_api()
        return msf_api.authorize_redirect()

    @app.route("/callback")
    def callback():
        msf_api = get_msf_api()
        # Get authorization code Google sent back to you
        token = msf_api.authorize_access_token()
        # you can save the token into database
        # session['user'] = token['userinfo']
        # profile = msf_api.get('/user', token=token)
        # a = msf_api.userinfo()
        
        user_id = token["userinfo"]["aud"][0]

        endpoint = "/player/v1/card"
        response = msf_api.get(endpoint)
        card = response.json()
        user_name = card["data"]["name"]
        user_icon = card["data"]["icon"]
        user_frame = card["data"]["frame"]
        current_hash = card["meta"]["hashes"]

        user = User(id_ = user_id, name = user_name, icon = user_icon, frame = user_frame)
        if not user.get(user_id):
            User.create(id_ = user_id, name = user_name, icon = user_icon, frame = user_frame)
        login_user(user)
        session["token"] = token
        # g.msf_api = msf_api

        return redirect(url_for("index"))
        # return (json.dumps(card.json()) + json.dumps(token['userinfo']) + json.dumps(a))

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.route("/gold")
    @login_required
    def gold():
        update_gold()
        return redirect(url_for("index"))

    @app.route("/farming")
    @login_required
    def farming():
        return (get_farming())

    from . import db
    db.init_app(app)

    return app