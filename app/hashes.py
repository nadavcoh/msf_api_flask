from flask import (
    Blueprint, Response, flash, g, jsonify, redirect, render_template, request, session, stream_template, stream_with_context, url_for, current_app
)
from flask_login import current_user, login_required
import pandas as pd
from markupsafe import Markup

from app.char import get_chars
from app.farming import get_farming_table
from app.gear_calculator import all_teams
from app.msf_api import get_msf_api

from app.nadavcoh_redis import get_data_from_cache, get_redis

hashes = Blueprint('hashes', __name__, url_prefix='/hahses')

@hashes.route('/')
@login_required
def index():
    redis_client = get_redis()
    keys=redis_client.keys("*")
    all_hashes = []
    for key in keys:
        value = get_data_from_cache(key)
        meta = value.get("meta")
        if meta:
            hash = meta.get("hashes")
        else:
            hash = {}
        all_hashes.append({"key": key.decode()}|hash)
    all_hashes_df = pd.DataFrame(all_hashes, columns=['key', 'events', 'drops', 'locs', 'nodes', 'chars', 'other', 'all'])

    msf_api = get_msf_api()
    endpoint = "/player/v1/card"
    response = msf_api.get(endpoint)
    card = response.json()
    current_hashes = card["meta"]["hashes"]
    current_hashes_df = pd.DataFrame([{"key": "current"}|current_hashes])
    all_hashes_df_combined = pd.merge(current_hashes_df, all_hashes_df, how="outer")

    all_hashes_df_combined.sort_values("all", inplace=True)


    def convert_hex(x):
        try:
            x = float(int(x,16))
        except (ValueError, TypeError):
            pass
        return x
    
    hash_gmap = all_hashes_df_combined.applymap(convert_hex)

    def style_current(v, props=''):
        return props if v == "current" else None
    
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    def make_pretty2(styler):
        styler.applymap(style_current, props='background-color:yellow;')
        styler.background_gradient(axis = None, subset=['events', 'drops', 'locs', 'nodes', 'chars', 'other', 'all'], gmap=hash_gmap, cmap="gist_rainbow")
        styler.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'need': "{:,.0f}",
                                          'amount': "{:,.0f}"
                                           } )
        return styler
    all_hashes_html = all_hashes_df_combined.style.pipe(make_pretty2).to_html()

    return render_template('hashes/index.html', html=Markup(all_hashes_html))

@hashes.route('/clear_cache')
@login_required
def clear_cache():
    redis_client = get_redis()
    redis_client.flushdb()
    return "OK", {"Content-Type": "text/plain"}

@hashes.route('/rebuild_cache')
@login_required
def rebuild_cache():
    def generate():
        functions = [get_farming_table, all_teams, get_chars]
        for i in range(len(functions)+1):
            if i>0:
                current_app.logger.info (f'Calling {functions[i-1].__name__}()')
                functions[i-1]()
            if i<len(functions):
                text = f'Calling {functions[i].__name__}()\n'
            if i==0:
                text = "\n" + text
                # https://stackoverflow.com/questions/33464381/safari-render-html-as-received
                text = "." * (1024-len(text)) + text
            if i==len(functions):
                text = "Done"
            yield text
    return stream_with_context(generate()), {"Content-Type": "text/plain"}

@hashes.route('/rebuild_cache_debug')
@login_required
def rebuild_cache_debug():
    def generate():
        functions = [get_farming_table, all_teams, get_chars]
        for i in range(len(functions)+1):
            if i>0:
                current_app.logger.info (f'Calling {functions[i-1].__name__}()')
                functions[i-1]()
            if i<len(functions):
                text = f'Calling {functions[i].__name__}()\n'
            if i==0:
                text = "\n" + text
                # https://stackoverflow.com/questions/33464381/safari-render-html-as-received
                text = "." * (1024-len(text)) + text
            if i==len(functions):
                text = "Done"
            yield text
    return list(generate()), {"Content-Type": "text/plain"}

@hashes.route('/rebuild_cache_plain')
@login_required
def rebuild_cache_plain():    
    get_farming_table() 
    all_teams()
    get_chars()
    return "OK", {"Content-Type": "text/plain"}

# https://flask.palletsprojects.com/en/2.2.x/patterns/javascript/
@hashes.route('/rebuild_cache_log')
@login_required
def rebuild_cache_log():
    return (render_template("hashes/rebuild_cache_log.html"))