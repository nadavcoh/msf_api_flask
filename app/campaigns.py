from app.nadavcoh_redis import get_data_from_cache, set_data_to_cache
from app.msf_api import get_msf_api, API_SERVER
from flask import session

def get_campaigns_from_api() -> dict:
    """Data from api"""
    msf_api = get_msf_api()
    endpoint = "/game/v1/episodics/" + "campaign"
    params = {"statsFormat": "csv",
          "itemFormat": "id",
          "traitFormat": "id"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()

    #if (current_chars_hash != data["meta"]["hashes"]["chars"]):
    current_nodes_hash = data["meta"]["hashes"]["nodes"]
    #check_hash()
    return data

def get_campaigns() -> dict:

    # First it looks for the data in redis cache
    data = get_data_from_cache(key="nodes_campaigns")

    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        data = get_campaigns_from_api()
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key="nodes_campaign", value=data)
        return data

def get_campaign_names() -> dict:

    # First it looks for the data in redis cache
    data = get_data_from_cache(key="nodes_campaign_names")

    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        campaigns = get_campaigns()
        # This block sets saves the respose to redis and serves it directly
        campaign_ids = [current_campaign["id"] for current_campaign in campaigns["data"]]
        data = {"data": campaign_ids, "meta": campaigns["meta"]}
        data["cache"] = False
        state = set_data_to_cache(key="nodes_campaign_names", value=data)
        return data

def get_campaign_from_api(campaign_name: str) -> dict:
    """Data from api"""
    msf_api = get_msf_api()
    endpoint = "/game/v1/episodics/" + "campaign" + "/" + campaign_name
    params = {"statsFormat": "csv",
              "itemFormat": "id",
              "traitFormat": "id",
              "nodeInfo": "part",
              "nodeRewards": "full",
              "pieceInfo": "none"}
    r = msf_api.get(API_SERVER + endpoint, params=params)
    data = r.json()

    #if (current_chars_hash != data["meta"]["hashes"]["chars"]):
    current_nodes_hash = data["meta"]["hashes"]["nodes"]
#    check_hash()
    return data

def get_campaign(campaign_name: str) -> dict:

    # First it looks for the data in redis cache
    data = get_data_from_cache(key="nodes_" + campaign_name)

    # If cache is found then serves the data from cache
    if data is not None:
        return data
    else:
        # If cache is not found then sends request to the MapBox API
        data = get_campaign_from_api(campaign_name)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key="nodes_" + campaign_name, value=data)
        return data