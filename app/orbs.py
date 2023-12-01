
from flask import Blueprint, current_app, render_template
from flask_login import login_required
from app.campaigns import get_campaign
from app.gear import get_gear

from app.msf_api import API_SERVER, get_msf_api
from app.nadavcoh_redis import get_data_from_cache, set_data_to_cache

orbs = Blueprint('orbs', __name__, url_prefix='/orbs')

# def find_key2_in_key1_generator(data, key1, key2):
#     if isinstance(data, dict):
#         if key1 in data and key2 in data[key1]:
#             yield data[key1][key2]
        
#         for key, value in data.items():
#             if isinstance(value, (dict, list)):
#                 yield from find_key2_in_key1_generator(value, key1, key2)

#     elif isinstance(data, list):
#         for item in data:
#             yield from find_key2_in_key1_generator(item, key1, key2)

def find_key_in_data_generator(data, key):
    if isinstance(data, dict):
        if key in data:
            yield data[key]
        
        for _, value in data.items():
            if isinstance(value, (dict, list)):
                yield from find_key_in_data_generator(value, key)

    elif isinstance(data, list):
        for item in data:
            yield from find_key_in_data_generator(item, key)

def get_events_from_api():
    # Data from api
    msf_api = get_msf_api()
    # curl -X GET "https://api.marvelstrikeforce.com/game/v1/events?statsFormat=csv&itemFormat=id&traitFormat=id&eventInfo=none&pieceInfo=none&quantityFormat=int"

    endpoint = "/game/v1/events"
    params = {"statsFormat": "csv",
          "itemFormat": "id",
          "traitFormat": "id",
          "eventInfo": "none",
          "pieceInfo": "none",
          "quantityFormat": "int"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_events():
    key = "nodes_events"
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the API
        current_app.logger.info("Calling get_eventss_from_api()")
        data = get_events_from_api()
        # This block saves the respose to redis and serves it directly
        data["cache"] = False
        set_data_to_cache(key=key, value=data)
        return data

def get_event_from_api(event):
    # Data from api
    msf_api = get_msf_api()
    # curl -X GET "https://api.marvelstrikeforce.com/game/v1/events/event?statsFormat=csv&itemFormat=id&traitFormat=id&
    #   objRewards=none&pieceInfo=none"
    # curl -X GET "https://api.marvelstrikeforce.com/game/v1/events/654802508dde86add8789766?statsFormat=csv&itemFormat=id&
    # traitFormat=id&eventInfo=full&objRewards=full&pieceInfo=none&quantityFormat=int" \

    endpoint = "/game/v1/events/" + event
    params = {"statsFormat": "csv",
          "itemFormat": "id",
          "traitFormat": "id",
          "pieceInfo": "none"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_event(event):
    key = "nodes_event_" + event
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the API
        current_app.logger.info("Calling get_event_from_api(" + event + ")")
        data = get_event_from_api(event)
        # This block saves the respose to redis and serves it directly
        data["cache"] = False
        set_data_to_cache(key=key, value=data)
        return data

def get_orb_from_api(orb):
    # Data from api
    msf_api = get_msf_api()
    # curl -X GET "https://api.marvelstrikeforce.com/game/v1/orbRewards/orb?itemFormat=id&statsFormat=csv&pieceInfo=none&subPieceInfo=none" \

    endpoint = "/game/v1/orbRewards/" + orb
    params = {"statsFormat": "csv",
          "itemFormat": "id",
          "subPieceInfo": "none",
          "pieceInfo": "none" }
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_orb(orb):
    key = "nodes_orb_" + orb
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the API
        current_app.logger.info("Calling get_orb_from_api(" + orb + ")")
        data = get_orb_from_api(orb)
        # This block saves the respose to redis and serves it directly
        data["cache"] = False
        set_data_to_cache(key=key, value=data)
        return data

def get_episodics_from_api(type):
    # Data from api
    msf_api = get_msf_api()
    endpoint = "/game/v1/episodics/" + type
    params = {"statsFormat": "csv",
          "itemFormat": "id",
          "traitFormat": "id"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_episodics(type) -> dict:
    key = "nodes_" + type
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        current_app.logger.info("Calling get_episodics_from_api(" + type + ")")
        data = get_episodics_from_api(type)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key=key, value=data)
        return data

def get_episodics_names(type) -> dict:
    key="nodes_" + type + "_names"
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)

    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        current_app.logger.info ("Calling get_episodic(" + type + ")")
        campaigns = get_episodics(type)
        # This block sets saves the respose to redis and serves it directly
        campaign_ids = [current_campaign["id"] for current_campaign in campaigns["data"]]
        data = {"data": campaign_ids, "meta": campaigns["meta"]}
        data["cache"] = False
        state = set_data_to_cache(key=key, value=data)
        return data

def get_episodic_from_api(episodic_type, episodic_name):
    # Data from api
    msf_api = get_msf_api()
    endpoint = "/game/v1/episodics/" + episodic_type + "/" + episodic_name
    params = {"statsFormat": "csv",
              "itemFormat": "id",
              "traitFormat": "id",
              "nodeInfo": "full",
              "nodeRewards": "full",
              "pieceInfo": "none"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_episodic(episodic_type, episodic_name):
    key = "nodes_episodic_" + episodic_type + "_" + episodic_name
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        current_app.logger.info (f"Calling get_episodic_from_api({episodic_type}, {episodic_name})")
        data = get_episodic_from_api(episodic_type, episodic_name)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key=key, value=data)
        return data


# curl -X GET "https://api.marvelstrikeforce.com/game/v1/dds?itemFormat=id&nodeInfo=full&nodeRewards=full&
# pieceInfo=none&raidRewards=full" \
def get_dds_from_api():
    # Data from api
    msf_api = get_msf_api()
    endpoint = "/game/v1/dds"
    params = {"itemFormat": "id",
              "nodeInfo": "full",
              "nodeRewards": "full",
              "pieceInfo": "none",
              "raidRewards": "full"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_dds():
    key = "nodes_dds"
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        current_app.logger.info ("Calling get_dds_from_api()")
        data = get_dds_from_api()
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        set_data_to_cache(key=key, value=data)
        return data

# curl -X GET "https://api.marvelstrikeforce.com/game/v1/raids?itemFormat=id&nodeInfo=part&nodeReqs=none&nodeRewards=full&
# pieceInfo=none&raidRewards=full" \
def get_raids_from_api():
    # Data from api
    msf_api = get_msf_api()
    endpoint = "/game/v1/raids"
    params = {"itemFormat": "id",
              "nodeInfo": "part",
              "nodeReqs": "none",
              "nodeRewards": "full",
              "pieceInfo": "none",
              "raidRewards": "full"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_raids():
    key = "nodes_raids"
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        current_app.logger.info ("Calling get_raids_from_api()")
        data = get_raids_from_api()
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        set_data_to_cache(key=key, value=data)
        return data

# curl -X GET "https://api.marvelstrikeforce.com/player/v1/events?itemFormat=id&objRewards=full" \
def get_user_events_from_api():
    # Data from api
    msf_api = get_msf_api()
    endpoint = "/player/v1/events"
    params = {"itemFormat": "id",
              "objRewards": "full"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()
    return data

def get_user_events():
    key = "nodes_user_events"
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key)
    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        current_app.logger.info ("Calling get_user_events_from_api()")
        data = get_user_events_from_api()
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        set_data_to_cache(key=key, value=data)
        return data

def add_to_results(results_array, result):
    if result not in results_array:
        results_array.append(result)
    return results_array

@orbs.route('/')
@login_required
def index():
    orbs_results = []
    for event in get_events()["data"]:
        result_generator = find_key_in_data_generator(get_event(event["id"]), 'item')
        for result in result_generator:
            data = get_orb(result)
            if "error" in data:
                if data["error"]["code"] != 404:
                    current_app.logger.info(result + " - " + str(data["error"]["code"]))
            else:
                current_app.logger.info(result)
                orbs_results = add_to_results(orbs_results, result)
    
    episodics = ["campaign", "eventCampaign", "challenge", "flashEvent", "unlockEvent", "otherEvent"]
    for episodicType in episodics:
        for episodic in get_episodics_names(episodicType)["data"]:
            result_generator = find_key_in_data_generator(get_episodic(episodicType, episodic), 'item')
            for result in result_generator:
                data = get_orb(result)
                if "error" in data:
                    if data["error"]["code"] != 404:
                        current_app.logger.info(result + " - " + str(data["error"]["code"]))
                else:
                    current_app.logger.info(result)
                    orbs_results = add_to_results(orbs_results, result)
    
    result_generator = find_key_in_data_generator(get_dds(), 'item')
    for result in result_generator:
        data = get_orb(result)
        if "error" in data:
            if data["error"]["code"] != 404:
                current_app.logger.info(result + " - " + str(data["error"]["code"]))
        else:
            current_app.logger.info(result)
            orbs_results = add_to_results(orbs_results, result)
    
    result_generator = find_key_in_data_generator(get_raids(), 'item')
    for result in result_generator:
        data = get_orb(result)
        if "error" in data:
            if data["error"]["code"] != 404:
                current_app.logger.info(result + " - " + str(data["error"]["code"]))
        else:
            current_app.logger.info(result)
            orbs_results = add_to_results(orbs_results, result)

    result_generator = find_key_in_data_generator(get_user_events(), 'item')
    for result in result_generator:
        data = get_orb(result)
        if "error" in data:
            if data["error"]["code"] != 404:
                current_app.logger.info(result + " - " + str(data["error"]["code"]))
        else:
            current_app.logger.info(result)
            orbs_results = add_to_results(orbs_results, result)

    current_app.logger.info("Done")
    return render_template('orbs.html', orbs_results = orbs_results, get_gear = get_gear, get_otb = get_orb)
