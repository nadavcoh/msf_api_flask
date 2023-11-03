from time import time
from flask import session
from flask_login import current_user
from app.msf_api import get_msf_api, API_SERVER
from app.db import get_db
import json

def get_gold_from_api():
    msf_api = get_msf_api()
    endpoint = "/player/v1/events"
    params = {"statsFormat": "csv",
            "itemFormat": "id",
            "traitFormat": "id",
            "type": "milestone",
            "objRewards": "full",
            "pieceInfo": "none"}
    r = msf_api.get(endpoint, params=params)
    events = r.json()
    current_time = time()
    current_gold_milestone = [event for event in events["data"] if (event["name"] == "Golden Dimension" or event["name"] == "Golden Opportunity") and event["startTime"] < current_time and event["endTime"] > current_time][0]["milestone"]
    current_gold_milestone_points = current_gold_milestone["brackets"][0]["objective"]["progress"]["points"]
    current_gold_milestone_goal = current_gold_milestone["brackets"][0]["objective"]["tiers"][str(max([int(x) for x in current_gold_milestone["brackets"][0]["objective"]["tiers"].keys()]))]["goal"]
    return {"current_points": current_gold_milestone_points,
            "goal": current_gold_milestone_goal,
            "updated": current_time}

def update_gold():
    current_gold = get_gold_from_api()
    set_gold_to_db(current_gold)
    return current_gold

def get_gold():
    current_gold = get_gold_from_db()
    if not current_gold:
        current_gold = update_gold()
    return current_gold

def get_gold_from_db():
    db = get_db()
    resp = db.execute(
        "SELECT gold from My_Users WHERE id = %s", (current_user.id,)
    ).fetchone()
    if resp["gold"]:
        resp = json.loads(resp["gold"])
    else:
        resp = resp["gold"]
    return resp

def set_gold_to_db(gold):
    db = get_db()
    db.execute(
        """UPDATE My_Users
        SET gold = %s
        WHERE id = %s;""",
        (json.dumps(gold), current_user.id),
    )
    db.commit()