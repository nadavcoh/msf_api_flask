from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for, Markup
)
from flask_login import current_user, login_required
import pandas as pd
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
    all_hashes_df = pd.DataFrame(all_hashes)
    
    # all_hashes_df.sort_values("all", inplace=True)

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
    # all_hashes_df_combined.drop(columns=["key"], inplace=True)


    def style_current(v, props=''):
        return props if v == "current" else None
    
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    def make_pretty2(styler):
        # styler.highlight_min(subset="remaining", color="palegreen")
        #styler.highlight_between(subset="have", left=1)
        #styler.format_index(formatter=make_index, axis="columns")
        styler.applymap(style_current, props='background-color:yellow;')
        styler.background_gradient(axis = None, subset=['events', 'drops', 'locs', 'nodes', 'chars', 'other', 'all'], gmap=hash_gmap, cmap="gist_rainbow")
        styler.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'need': "{:,.0f}",
                                          'amount': "{:,.0f}"
                                           } )
        return styler
    all_hashes_html = all_hashes_df_combined.style.pipe(make_pretty2).to_html()


    df = pd.DataFrame(columns=["City", "Temp (c)", "Rain (mm)", "Wind (m/s)"],
                  data=[["Stockholm", 21.6, 5.0, 3.2],
                        ["Oslo", 22.4, 13.3, 3.1],
                        ["Copenhagen", 24.5, 0.0, 6.7]])
    test_html = hash_gmap.style.background_gradient().to_html()

    return render_template('hashes/index.html', html=Markup(all_hashes_html))