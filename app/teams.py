import json
from flask import Blueprint, current_app, render_template
from flask_login import login_required
from markupsafe import Markup
import pandas as pd

from app.char import get_char
from app.msf_api import API_SERVER, get_msf_api
from app.nadavcoh_redis import get_data_from_cache, set_data_to_cache


teams = Blueprint('teams', __name__, url_prefix='/teams')


# curl -X GET "https://api.marvelstrikeforce.com/game/v1/analysis/teamOrder/roster" \
def get_teams_from_api(tab):
    # Data from api
    msf_api = get_msf_api()
    endpoint = "/game/v1/analysis/teamOrder/" + tab
    params = {}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_teams(tab):
    key = "teams_" + tab
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the API
        current_app.logger.info("Calling get_teams_from_api(" + tab + ")")
        data = get_teams_from_api(tab)
        # This block saves the respose to redis and serves it directly
        data["cache"] = False
        set_data_to_cache(key=key, value=data)
        return data

@teams.route('/')
@login_required
def index():
    return render_template('teams.html', 
                           tabs = ["roster", "blitz", "tower", "raids", "arena", "war", "crucible"],
                           get_teams = get_teams,
                           get_char = get_char)

def format_char(char):
    if type(char) is list:
        char = char[0]
        data = f"""<img class='reward_icon' src='{char['portrait']}'><br>
                <b>{char["name"]}</b><br>"""
        for trait in char["traits"]:
            if trait[1]:
                data+=trait[1].capitalize()
            else:
                data+=trait[0].capitalize()
            data+="<br>"
    else:
        data = ""
    return data

def format_traits(traits):
    data = ""
    for trait in traits:
        data+=trait[1].capitalize()
        data+="<br>"
    return data


@teams.route('/analysis')
@login_required
def analysis():
    teams_analysis = get_team_analysis()["data"]
    
    return render_template('teams_analysis.html', content=Markup(teams_analysis.style.format(
        formatter={'total': "{:.0f}",
                   'tab_order': "{:.0f}",
                   'char0': format_char,
                   'char1': format_char,
                   'char2': format_char,
                   'char3': format_char,
                   'char4': format_char,
                   "intersection": format_traits}
    ).to_html()))

def calculate_team_analysis():
    tabs = ["roster", "blitz", "tower", "raids", "arena", "war", "crucible"]
    # tabs = ["blitz"]
    teams_analysis = pd.DataFrame({"tab": ["test"],
                                   "tab_order": [1],
                                   "total": [1],
                                   "char0": [{"test1": "test2", "test3": "test4"}],
                                   "char1": [{"test": "test"}],
                                   "char2": [{"test": "test"}],
                                   "char3": [{"test": "test"}],
                                   "char4": [{"test": "test"}],
                                   "intersection": [{"a": "b"}]
                                   })
    team_id = 0
    for tab in tabs:
        tab_order = 0
        teams = get_teams(tab)
        for team in teams["data"]:
            teams_analysis.loc[team_id, "tab"] = tab
            teams_analysis.loc[team_id, "tab_order"] = tab_order
            teams_analysis.loc[team_id, "total"] = team["total"]
            char_num = 0
            traits_intersect = set()
            for char in team["squad"]:
                if char:
                    char_data = get_char(char)["data"]
                    traits = set([(trait["id"], trait.get("name")) for trait in char_data["traits"]])
                    teams_analysis.loc[team_id, "char"+str(char_num)] = [
                    {
                        "id": char
                        , "name": char_data["name"]
                        , "portrait": char_data["portrait"]
                        , "traits": traits
                        }]
                    if traits_intersect:
                        traits_intersect = traits_intersect.intersection(traits)
                    else:
                        traits_intersect = traits
                char_num = char_num + 1
            teams_analysis.at[team_id, "intersection"] = traits_intersect
            team_id = team_id + 1
            tab_order = tab_order + 1
    data = {}
    data["data"] = teams_analysis
    data["meta"] = teams["meta"]
    return data      
# thousands=",",
#                                 formatter={,
#                                           'tier': "{:.0f}",
#                                           'yellow': "{:.0f}" 

def get_team_analysis():
    key_name = "calc_team_analysis"
    data = get_data_from_cache(key=key_name)
    if data is not None:
        data["data"] = pd.DataFrame(json.loads(data["data"]))
        return data
    else:
        current_app.logger.info ("Calling calculate_team_analysis()")
        data = calculate_team_analysis()
        data["cache"] = False
        data["data"] = data["data"].to_json()
        set_data_to_cache(key=key_name, value=data)
        data["data"] = pd.DataFrame(json.loads(data["data"]))
        return data