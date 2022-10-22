import json
from app.gear import get_gear
from app.campaigns import get_campaign
from flask import url_for
import pandas as pd
from app.inventory import find_item_in_inventory
from app.roster import find_char_in_roster

def get_farming() -> str:
    with open('app/all_rewards_by_id.json', 'r') as f:
        all_rewards_by_id = json.load(f)
    resp: str = """<html><head>
<link rel="stylesheet" href="{}"/>
</head><body>""".format(url_for('static', filename='style.css'))
    resp += "<ul class='rewards'>"
    for mat, locations in all_rewards_by_id.items():
        resp += "<li class='reward'>"
        gear_data = get_gear(mat)
        resp += "<img class='reward_icon' src='{}' alt='{}'/>".format(gear_data["data"]["icon"], gear_data["data"]["name"])
        resp += "<span class='mat_id'>{}</span>".format(mat)
        resp += "<span class='mat_name'>{}</span>".format(gear_data["data"]["name"])
        resp += "<ul class='locations'>"
        for location in locations:
            resp += "<li>"
            campaign_data = get_campaign (location["campaign_id"])
            resp += "{} {}-{}".format(campaign_data["data"]["name"], location["chapter"], location["tier"])
            resp += "</li>"
        resp += "</ul></li>"
    resp += "</ul>"
    resp += "</body></html>"
    return (resp)
    
def get_gear_data (row):
    gear_data = get_gear(row["id"])
    explode = row["id"].split("_")
    # if explode[0] == "SHARD":
    #     a
    char = find_char_in_roster(gear_data["data"].get("characterId"))
    return {"id": row["id"],
            "name": gear_data["data"]["name"],
            "icon": gear_data["data"]["icon"],
            "tier": gear_data["data"].get("tier") ,
            "characterId": gear_data["data"].get("characterId"),
            "explode1": explode[0],
            "explode2": (explode[1] if len(explode)>1 else ""),
            "inventory": find_item_in_inventory(row["id"]),
            "yellow": char.get("yellow")  }

def get_farming_locations (row):
    result = ""
    for location in row["locations"]:
        campaign_data = get_campaign (location["campaign_id"])
        result += "{} {}-{}<br>".format(campaign_data["data"]["name"], location["chapter"], location["tier"])
    return result

def get_farming_table() -> pd.DataFrame.style:
    with open('app/all_rewards_by_id.json', 'r') as f:
        all_rewards_by_id = json.load(f)
    farming: pd.DataFrame = pd.DataFrame({"id": all_rewards_by_id.keys(), "locations": all_rewards_by_id.values()} )
    # gear_data = [get_gear_data(id) for id in farming["id"]]
    gear_data = farming.apply (get_gear_data, result_type ='expand', axis = 1)
    # resp += "<ul class='locations'>"

    
    result: pd.DataFrame = pd.merge(farming, gear_data)
    result["locations_pretty"] = farming.apply (get_farming_locations, axis = 1)
    # result.sort_values(["explode1", "tier", "name"], inplace=True)
    result.sort_values(["inventory"], inplace=True)
    return result
    # return gear_data

def get_farming_table_html():
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    farming: str = get_farming_table()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["yellow"]!=7) & (farming["explode1"]=="SHARD")]
    farming = farming.loc[(farming["yellow"]!=6) | (farming["inventory"]<300)]
    farming = farming.loc[(farming["yellow"]!=5) | (farming["inventory"]<500)]
    farming.drop(columns = ["id", "characterId", "explode1", "explode2", "tier"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()

def get_farming_table_html2():
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    farming: str = get_farming_table()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["explode1"]=="GEAR")]
    farming = farming.loc[(farming["tier"]>=12)]
    # farming = farming.loc[(farming["yellow"]!=5) | (farming["inventory"]<500)]
    farming.drop(columns = ["id", "characterId", "explode1", "explode2", "tier", "yellow"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()