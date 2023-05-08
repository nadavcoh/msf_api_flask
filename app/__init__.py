# https://flask.palletsprojects.com/en/2.2.x/tutorial/
# https://realpython.com/flask-google-login/
# https://github.com/realpython/materials/tree/master/flask-google-login
# To run: . venv/bin/activate
#         flask --debug run --cert=adhoc --port=2705

# Python standard libraries
from datetime import timedelta
from logging.config import dictConfig
import os
from time import time
from io import StringIO
import whatismyip

# Third-party libraries
from flask import Flask, current_app, redirect, send_from_directory, url_for, session, render_template, jsonify, request, flash, Markup
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from humanize import naturaltime
from app.char import get_chars

from app.inventory import get_inventory_update_time, update_inventory
from app.roster import find_char_in_roster, get_roster_update_time, update_roster
from app.settings import get_msftools_sheetid, set_msftools_sheetid

# Internal imports
# from app.db import init_db_command
from .user import User
from .msf_api import get_msf_api, API_SERVER
from .gold import get_gold, update_gold
from .farming import get_farming_table, get_farming_table_html_char_all, get_farming_table_html_char_shards, get_farming_table_html_gear_gold_teal, get_farming_table_html_gear_purple_blue_green, get_farming_table_html_iso8, get_farming_table_html_misc
from .gear import get_gear
from .gear_calculator import all_teams, gear_calculator
from .hashes import hashes

def create_app(test_config=None):
    # Logger https://betterstack.com/community/guides/logging/how-to-start-logging-with-flask/
    # https://stackoverflow.com/questions/31999627/storing-logger-messages-in-a-string
    # https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook
    # https://docs.python.org/3/library/io.html
    log_stream = StringIO()

    def filter_maker(level):
        def filter(record):
            return (record.module != "_internal")
        return filter

    dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "filters": {
            "no_internal": {
                "()" : filter_maker,
                "level": "INFO"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "stream": {
                "class": "logging.StreamHandler",
                "stream": log_stream,
                "formatter": "default",
                "filters": ["no_internal"]
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "instance/msf-api-flask.log",
                "formatter": "default",
            },
        },
        "root": {"level": "INFO", "handlers": ["console", "file", "stream"]},
    }
    )
    
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
        app.config.from_pyfile('/etc/secrets/config.py', silent=True)
        app.config.from_pyfile('config.py', silent=True)
        app.config.from_prefixed_env()
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
        current_app.logger.info (whatismyip.whatismyip()
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
    @login_required
    def debug():
        return render_template('debug.html', debug=get_gear("SHARD_SILVERSURFER"))

    @app.route("/debug2")
    @login_required
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
        
        # user_id = token["userinfo"]["sub"]
        endpoint = "/player/v1/card"
        response = msf_api.get(endpoint)
        card = response.json()
        user_id = card["data"]["name"]
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

    @app.route("/farming/char/needed")
    @login_required
    def farming_char_shards():
        return render_template('farming.html', content=Markup(get_farming_table_html_char_shards()))

    @app.route("/farming/gear/gold-teal")
    @login_required
    def farming_gear_gold_teal():
        return render_template('farming.html', content=Markup(get_farming_table_html_gear_gold_teal()))

    @app.route("/farming/gear/purple-blue-green")
    @login_required
    def farming_gear_purple_blue_green():
        return render_template('farming.html', content=Markup(get_farming_table_html_gear_purple_blue_green()))

    @app.route("/farming/iso8")
    @login_required
    def farming_iso8():
        return render_template('farming.html', content=Markup(get_farming_table_html_iso8()))

    @app.route("/farming/char/all")
    @login_required
    def farming_char_all():
        return render_template('farming.html', content=Markup(get_farming_table_html_char_all()))

    @app.route("/farming/misc")
    @login_required
    def farming_misc():
        return render_template('farming.html', content=Markup(get_farming_table_html_misc()))

    @app.route("/log")
    @login_required
    def log():
        log = log_stream.getvalue()
        log_stream.truncate(0)
        return jsonify(log)

    @app.route("/sqlite")
    @login_required
    def sqlite():
        folder = app.instance_path
        return send_from_directory(directory=app.instance_path, path='msf_api_flask.sqlite') 

    @app.route('/settings', methods=('GET', 'POST'))
    @login_required
    def settings():
        #msf_tools_sheetid = get_msftools_sheetid()

        if request.method == 'POST':
            msf_tools_sheetid = request.form['msf_tools_sheetid']
            #set_msftools_sheetid(msf_tools_sheetid)
            flash("Saved")

        return render_template('settings.html', msf_tools_sheetid=msf_tools_sheetid)

    @app.errorhandler(500)
    def error(e):
        # note that we set the 500 status explicitly
        dump = vars()
        current_app.logger.info (dump)
        current_app.logger.info (whatismyip.whatismyip())
        return render_template('error.html', content = dump), 500

    app.register_blueprint(gear_calculator)
    app.register_blueprint(hashes)

    from . import db
    db.init_app(app)

    return app
