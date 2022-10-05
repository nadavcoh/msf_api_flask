import json
from app.gear import get_gear
from app.campaigns import get_campaign
from flask import url_for

def get_farming():
    with open('app/all_rewards_by_id.json', 'r') as f:
        all_rewards_by_id = json.load(f)
    resp = """<html><head>
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