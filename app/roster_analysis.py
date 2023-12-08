

from flask import Blueprint, current_app, render_template
from flask_login import login_required
from markupsafe import Markup
import pandas as pd
from app.gear import get_gear
from app.inventory import find_items_in_inventory

from app.msf_api import API_SERVER, get_msf_api
from app.nadavcoh_redis import get_data_from_cache, set_data_to_cache
from app.roster import get_roster


roster_analysis = Blueprint('roster_analysis', __name__, url_prefix='/roster_analysis')

# curl -X GET "https://api.marvelstrikeforce.com/game/v1/upgradeData/yellowStarTotalShards" \
def get_upgrade_data_from_api():
    # Data from api
    msf_api = get_msf_api()
    endpoint = "/game/v1/upgradeData/yellowStarTotalShards"
    params = {}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_upgrade_data():
    key = "upgrade_data"
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the API
        current_app.logger.info("Calling get_teams_from_api()")
        data = get_upgrade_data_from_api()
        # This block saves the respose to redis and serves it directly
        data["cache"] = False
        set_data_to_cache(key=key, value=data)
        return data

def get_inventory_data (row):
    gear_data = get_gear(row["item"])
    char_id = gear_data["data"].get("characterId")
    return {"item": row["item"],
            "char_id": char_id
            }

def get_rs_num (row):
    rs_num = int(row["item"][-1])
    return {"item": row["item"],
            "rs_num": rs_num
            }

def calculate_shards_rs(row):
    upgrade_data = get_upgrade_data()["data"]

    if row["rs_num"] > row["red"]:
        rs_upgradeable = True
    else:
        rs_upgradeable = False

    yellow = row["yellow"]
    if pd.isna(yellow):
        yellow = 0
        shards_used = 0
    else:
        yellow = int(yellow)
        shards_used = upgrade_data[str(yellow)]

    ys_upgradeable = 0
    for i in upgrade_data.keys():
        if int(i) > yellow:
            if upgrade_data[i]-shards_used < row["quantity_x"]:
                ys_upgradeable = int(i)

    if rs_upgradeable and (ys_upgradeable > yellow):
        rs_potential = min(ys_upgradeable, row["rs_num"])
    else:
        rs_potential = 0

    return {"char_id": row["char_id"],
            "rs_upgradeable": rs_upgradeable,
            "ys_upgradeable": ys_upgradeable,
            "rs_potential": rs_potential}

@roster_analysis.route('/')
@login_required
def index():
    roster = get_roster()
    roster_df = pd.DataFrame(roster)
    roster_df.sort_values(["char_id"], inplace=True)
    roster_df.drop(columns = ["slots"], inplace=True)

    shard_df = pd.DataFrame(find_items_in_inventory("SHARD"))
    shard_df.sort_values(["item"], inplace=True)
    shard_df = pd.merge(shard_df, shard_df.apply(get_inventory_data, result_type ='expand', axis = 1))

    rs_df = pd.DataFrame(find_items_in_inventory("RS"))
    rs_df.sort_values(["item"], inplace=True)
    rs_df = pd.merge(rs_df, rs_df.apply(get_inventory_data, result_type ='expand', axis = 1))
    rs_df = pd.merge(rs_df, rs_df.apply(get_rs_num, result_type="expand", axis = 1))

    roster_df = pd.merge(roster_df, shard_df, how = "outer", on = "char_id")

    roster_df = pd.merge(roster_df, rs_df, how="outer", on = "char_id")

    roster_df.drop(columns = ["item_x", "item_y", "quantity_y"], inplace=True)
    roster_df = pd.merge(roster_df, roster_df.apply(calculate_shards_rs, result_type="expand", axis = 1))

    return render_template('teams_analysis.html', content=Markup(roster_df.style.format(formatter={'quantity': "{:.0f}",
                                                                                                   'tier': "{:.0f}",
                                                                                                   'yellow': "{:.0f}",
                                                                                                   'red': "{:.0f}",
                                                                                                   'quantity_x': "{:.0f}",
                                                                                                   'quantity_y': "{:.0f}",
                                                                                                   'rs_num': "{:.0f}",
                                                                                                   'rs_potential': "{:.0f}"
                                                                                                   }).to_html() +
                                                                 shard_df.style.format(formatter={}).to_html() +
                                                                 rs_df.style.format(formatter={}).to_html())
    )