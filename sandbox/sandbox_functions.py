from requests_oauthlib import OAuth2Session
import pandas as pd
from time import time
import json
import sys
from datetime import timedelta
import redis

# MSF API 
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



def gearset_add(gearset, gear_id: str, n: str):
    result = dict(gearset)
    if gear_id in result:
        result[gear_id] += n
    else:
        result[gear_id] = n
    return result

def gearset_merge(gearset1: dict, gearset2: dict):
    result = dict(gearset1)
    for gear_id, n in gearset2.items():
        result = gearset_add(result, gear_id, n)
    return result

def get_tier_cost_base_gear (char_name, tier, slots=[True]*6):
    # Slots are listed in order, top to bottom on the left, then top to bottom on the right.
    totalCost = {}
    char_data = get_char(char_name)
    tier_data = char_data["data"]["gearTiers"][str(tier)]
    if ("slots" in tier_data):
        for slot in tier_data["slots"]:
            if ("flatCost" in slot["piece"]):
            # this is a crafted piece - add its flatcost
                for item in slot["piece"]["flatCost"]:
                    totalCost = gearset_add(totalCost, item["item"]["id"], item["quantity"])
            else:
            # this is a base piece - add it
                totalCost = gearset_add(totalCost, slot["piece"]["id"], 1)
    return totalCost
