# https://flask.palletsprojects.com/en/2.2.x/tutorial/
# https://realpython.com/flask-google-login/
# https://github.com/realpython/materials/tree/master/flask-google-login
# To run: . venv/bin/activate
#         flask --debug run --cert=adhoc --port=2705

# Python standard libraries
from datetime import timedelta
import os
from time import time

# Third-party libraries
from flask import Flask, redirect, url_for, session, render_template, jsonify, request, flash, Markup
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from humanize import naturaltime

from app.inventory import find_item_in_inventory, get_inventory_update_time, update_inventory
from app.roster import find_char_in_roster, get_roster_update_time, update_roster
from app.settings import get_msftools_sheetid, set_msftools_sheetid

# Internal imports
# from app.db import init_db_command
from .user import User
from .msf_api import get_msf_api, API_SERVER
from .gold import get_gold, update_gold
from .farming import get_farming, get_farming_table_html, get_farming_table_html2
from .gear import get_gear

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'msf_api_flask.sqlite'),
    )
    #app.secret_key = os.environ.get("SECRET_KEY")
    
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=600)

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

    #init_msf_api()

    @app.route("/")
    def index():
        gold_text = {}
        updated = {}
        if current_user.is_authenticated:
            gold = get_gold()
            left = gold["goal"] - gold["current_points"]
            if left < 0:
                left = 0
            gold_text["current"] = "{:,}".format(gold["current_points"])
            gold_text["goal"] = "{:,}".format(gold["goal"])
            gold_text["left"] = "{:,}".format(left)
            gold_text["updated"] = "{}".format(naturaltime(time() - gold["updated"]))
            gold_text["updated_timestamp"] = gold["updated"]

            updated["inventory"] = get_inventory_update_time()
            updated["roster"] = get_roster_update_time()

        # Sitemap
        # https://stackoverflow.com/questions/13151161/display-links-to-new-webpages-created/13161594#13161594
        # https://stackoverflow.com/questions/13317536/get-list-of-all-routes-defined-in-the-flask-app
        def has_no_empty_params(rule):
            defaults = rule.defaults if rule.defaults is not None else ()
            arguments = rule.arguments if rule.arguments is not None else ()
            return len(defaults) >= len(arguments)
        links = []
        for rule in app.url_map.iter_rules():
            # Filter out rules we can't navigate to in a browser
            # and rules that require parameters
            if "GET" in rule.methods and has_no_empty_params(rule):
                url = url_for(rule.endpoint, **(rule.defaults or {}))
                links.append((url, rule.endpoint))
        # links is now a list of url, endpoint tuples
      
        return render_template('index.html', gold_text=gold_text, links=links, updated = updated, time=time, naturaltime=naturaltime)

    @app.route("/debug")
    def debug():
        return render_template('debug.html', debug=get_gear("SHARD_SILVERSURFER"))

    @app.route("/debug2")
    def debug2():
        update_inventory()
        update_roster()
        return jsonify(find_char_in_roster("AimControl_Infect"))

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
        login_user(user, remember=True, duration=timedelta(days=600))
        session["token"] = token
        session.permanent = True
        # g.msf_api = msf_api

        return redirect(url_for("index"))
        # return (json.dumps(card.json()) + json.dumps(token['userinfo']) + json.dumps(a))

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.route("/update/gold")
    @login_required
    def update_gold_route():
        update_gold()
        return redirect(url_for("index"))
    
    @app.route("/update/inventory")
    @login_required
    def update_inventory_route():
        update_inventory()
        return redirect(url_for("index"))

    @app.route("/update/roster")
    @login_required
    def update_roster_route():
        update_roster()
        return redirect(url_for("index"))

    @app.route("/farming")
    @login_required
    def farming():
        return (get_farming())

    @app.route("/farming2")
    @login_required
    def farming2():
        return render_template('farming.html', content=Markup(get_farming_table_html()))

    @app.route("/farming3")
    @login_required
    def farming3():
        return render_template('farming.html', content=Markup(get_farming_table_html2()))

    @app.route('/settings', methods=('GET', 'POST'))
    @login_required
    def settings():
        msf_tools_sheetid = get_msftools_sheetid()

        if request.method == 'POST':
            msf_tools_sheetid = request.form['msf_tools_sheetid']
            set_msftools_sheetid(msf_tools_sheetid)
            flash("Saved")

        return render_template('settings.html', msf_tools_sheetid=msf_tools_sheetid)

    from . import db
    db.init_app(app)

    return app