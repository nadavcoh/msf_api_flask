from email import charset
from requests_oauthlib import OAuth2Session
import pandas as pd
from time import time
import json
import sys
from datetime import timedelta
import redis

# MSF API v
import config
client_id = config.MSF_API_CLIENT_ID
client_secret = config.MSF_API_CLIENT_SECRET

redirect_uri = 'https://localhost:2705/callback'
api_key = r'17wMKJLRxy3pYDCKG5ciP7VSU45OVumB2biCzzgw'
api_server = 'https://api.marvelstrikeforce.com'

scope = ['m3p.f.pr.pro' ,
        'm3p.f.pr.ros',
        'm3p.f.pr.inv',
        'm3p.f.pr.act',
        'openid', 
        'offline'
        ]
global oauth
global redis_client
global roster
global inventory
global characters



# MSF API v
def connect_msf_api():
    global oauth
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri,
                        scope=scope)
    oauth.headers.update({'x-api-key' : api_key})
    authorization_url, state = oauth.authorization_url(
            'https://hydra-public.prod.m3.scopelypv.com/oauth2/auth')

    print ('Please go to %s and authorize access.' % authorization_url, flush=True)
    authorization_response = input('Enter the full callback URL')

    token = oauth.fetch_token(
            'https://hydra-public.prod.m3.scopelypv.com/oauth2/token',
            authorization_response=authorization_response, client_secret=client_secret)

    endpoint = "/game/v1/languages"
    params = {"page": 1,
            "perPage": 1}
    r = oauth.get(api_server + endpoint, params=params)
    ping = r.json()
    current_chars_hash = ping["meta"]["hashes"]["chars"]
    print("Connected, gear_hash: %s" % current_chars_hash)
    return oauth

# Redis v
def redis_connect() -> redis.client.Redis:
    try:
        global redis_client
        redis_client = redis.Redis(
            host="localhost",
            port=6379,
            #password="ubuntu",
            db=0,
            socket_timeout=5,
        )
        ping = redis_client.ping()
        if ping is True:
            print("Connected to redis")
            
            return redis_client
    except redis.AuthenticationError:
        print("AuthenticationError")
        sys.exit(1)

def get_data_from_cache(key: str) -> str:
    """Data from redis."""
    val = redis_client.get(key)
    if val is not None:
        val = json.loads(val)
        val["cache"] = True
        return val
    else:
        return (val)

def set_data_to_cache(key: str, value: str) -> bool:
    """Data to redis."""
    state = redis_client.set(key, value=json.dumps(value))
    return state

# Gear v
def get_gear_from_api(gear_id: str) -> dict:
    """Data from api"""

    endpoint = "/game/v1/items/" + gear_id
    params = {"statsFormat": "csv",
            #  "pieceInfo": "none",
              "pieceDirectCost": "full",
              "pieceFlatCost": "full",
              "subPieceInfo": "none"}
    r = oauth.get(api_server + endpoint, params=params)
    data = r.json()
    #if (current_chars_hash != data["meta"]["hashes"]["chars"]):
    #current_chars_hash = data["meta"]["hashes"]["chars"]
    #check_hash()
    return data

def get_gear(gear: str) -> dict:
    # First it looks for the data in redis cache
    data = get_data_from_cache(key="gear_"+gear)

    # If cache is found then serves the data from cache
    if data is not None:
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        data = get_gear_from_api(gear)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key="gear_"+gear, value=data)
        return data

# Char v
def get_char_from_api(char_id: str) -> dict:
    """Data from api"""
    
    endpoint = "/game/v1/characters/" + char_id
    params = {"statsFormat": "csv",
            "charInfo": "none",
            "costumes": "none",
            "abilityKits": "none",
            "pieceFlatCost": "full",
            "subPieceInfo": "none"}
    r = oauth.get(api_server + endpoint, params=params)
    data = r.json()
    #if (current_chars_hash != data["meta"]["hashes"]["chars"]):
    #current_chars_hash = data["meta"]["hashes"]["chars"]
    #check_hash()
    return data

def get_char(char_id: str) -> dict:
    # First it looks for the data in redis cache
    data = get_data_from_cache(key="char_" + char_id)

    # If cache is found then serves the data from cache
    if data is not None:
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        data = get_char_from_api(char_id)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key="char_" + char_id, value=data)
        return data

def get_chars_from_api():
    global characters
    r = oauth.get(api_server+"/game/v1/characters", params={"charInfo":"full", 
                                                            "status" : "playable",
                                                            "statsFormat": "csv",
                                                            "itemFormat": "id",
                                                            "traitFormat": "id"})
    characters = r.json()
    return characters

def get_chars() -> dict:
    # First it looks for the data in redis cache
    data = get_data_from_cache(key="char_all")

    # If cache is found then serves the data from cache
    if data is not None:
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        data = get_chars_from_api()
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key="char_all", value=data)
        return data

# Gear_calc v
def gearset_add(gearset, gear_id: str, n: str):
    result = dict(gearset)
    if gear_id in result:
        result[gear_id] += n
    else:
        result[gear_id] = n
    return result

def gearset_merge(gearset1: dict, gearset2: dict):
    # https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression
    result = dict(gearset1)
    for gear_id, n in gearset2.items():
        result = gearset_add(result, gear_id, n)
    return result

def calculate_tier_cost_base_gear (char_name, tier, slots=[True]*6):
    # Slots are listed in order, top to bottom on the left, then top to bottom on the right.
    totalCost = {}
    char_data = get_char(char_name)
    tier_data = char_data["data"]["gearTiers"][str(tier)]
    if ("slots" in tier_data):
        for slot_num in [i for i in range(len(slots)) if slots[i]]:
            slot = tier_data["slots"][slot_num]
            if ("flatCost" in slot["piece"]):
            # this is a crafted piece - add its flatcost
                for item in slot["piece"]["flatCost"]:
                    totalCost = gearset_add(totalCost, item["item"]["id"], item["quantity"])
            else:
            # this is a base piece - add it
                totalCost = gearset_add(totalCost, slot["piece"]["id"], 1)
    return {"data": totalCost, "meta": char_data["meta"]}

def get_tier_cost_base_gear (char_name, tier, slots=[True]*6):
    key_name = "calc_" + char_name + "_tier_" + str(tier) + "_slots_" + str(slots)
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key_name)

    # If cache is found then serves the data from cache
    if data is not None:
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        data = calculate_tier_cost_base_gear (char_name, tier, slots)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key=key_name, value=data)
        return data

def calculate_multi_tier_cost_base_gear (char_name, from_tier, to_tier, slots=[True]*6):
    # Slots are listed in order, top to bottom on the left, then top to bottom on the right.
    totalCost = {}
    current_tier = get_tier_cost_base_gear(char_name, from_tier, slots)
    if to_tier>from_tier:
        totalCost = gearset_merge(totalCost, current_tier["data"])
    for tier in range(from_tier+1,to_tier-1):
        current_tier = get_tier_cost_base_gear(char_name, tier)
        totalCost = gearset_merge(totalCost, current_tier["data"])
    return {"data": totalCost, "meta": current_tier["meta"]}

def get_multi_tier_cost_base_gear (char_name, from_tier, to_tier, slots=[True]*6):
    key_name = "calc_" + char_name + "_tier_" + str(from_tier) + "_to_" + str(to_tier) + "_slots_" + str(slots)
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key_name)

    # If cache is found then serves the data from cache
    if data is not None:
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        data = calculate_multi_tier_cost_base_gear (char_name, from_tier, to_tier, slots)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key=key_name, value=data)
        return data

def get_char_to_tier(char_id, tier):
    char = get_char_from_roster(char_id)
    slots_bool_not = [not x for x in char["slots"]]
    return get_multi_tier_cost_base_gear(char_id,char["tier"],tier,slots_bool_not)

# Roster v
import pandas as pd
import config
SHEET_ID = config.MSFTOOLS_SHEETID
SHEET_NAME = 'Roster'

# Roster v
def get_roster():
    # https://medium.com/geekculture/2-easy-ways-to-read-google-sheets-data-using-python-9e7ef366c775
    # https://stackoverflow.com/questions/33713084/download-link-for-google-spreadsheets-csv-export-with-multiple-sheets
    global roster
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'
    roster = pd.read_csv(url)
    roster.drop(columns = ['StarkHealth', 'StarkDamage','StarkArmor','StarkFocus', 'StarkResist', 'SaveTime', 'Power', 'Yellow', 'Red', 'Level', 'Basic', 'Special', 'Ultimate', 'Passive', 'IsoClass', 'IsoPips', 'Fragments', 'UnclaimedRed'], inplace=True)
    # roster = df[['ID','Tier','TopLeft', 'MidLeft', 'BottomLeft', 'TopRight', 'MidRight', 'BottomRight']]
    roster.fillna(0, inplace=True)
    roster["Tier"] = pd.to_numeric(roster["Tier"], downcast="integer")
    slots_y_n = roster[['TopLeft', 'MidLeft', 'BottomLeft', 'TopRight', 'MidRight', 'BottomRight']].values.tolist()   
    slots_bool = [[x=="Y" for x in k] for k in slots_y_n]
    roster.insert(2,"slots",slots_bool)
    roster.drop(columns=['TopLeft', 'MidLeft', 'BottomLeft', 'TopRight', 'MidRight', 'BottomRight'], inplace=True)
    return (roster)

def get_char_from_roster(char_id):
    # Slots are listed in order, top to bottom on the left, then top to bottom on the right.
    char = roster.loc[roster["ID"]==char_id]
    slots_y_n = char[['TopLeft', 'MidLeft', 'BottomLeft', 'TopRight', 'MidRight', 'BottomRight']].values.tolist()[0]
    slots_bool = [x=="Y" for x in slots_y_n]
    return {"id": char_id,
            "tier": int(char["Tier"].values[0]),
            "slots": slots_bool}

# Inventory v
def get_inventory():
    global inventory
    r = oauth.get(api_server+"/player/v1/inventory")
    r.json()
    inventory=r.json()
    return inventory

def find_in_inventory(cost: dict) -> list:
    costInv = []
    for currentItem in cost["data"]:
        currentCost = [inventoryItem["quantity"] for inventoryItem in inventory["data"] if currentItem == inventoryItem["item"]]
        if (len(currentCost) == 0):
            currentCost = [0]
        costInv.extend(currentCost)
    cost_array = pd.DataFrame(list(cost["data"].items()))
    cost_array.columns = ["Name", "Needed"]
    cost_array.insert(2, "Inventory", costInv)
    return cost_array