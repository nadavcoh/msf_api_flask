from app.nadavcoh_redis import get_data_from_cache, set_data_to_cache
from app.msf_api import get_msf_api, API_SERVER
from flask import session

def get_gear_from_api(gear_id: str) -> dict:
    """Data from api"""
    msf_api = get_msf_api()
    endpoint = "/game/v1/items/" + gear_id
    params = {"statsFormat": "csv",
            #  "pieceInfo": "none",
              "pieceDirectCost": "full",
              "pieceFlatCost": "full",
              "subPieceInfo": "none"}
    r = msf_api.get(API_SERVER + endpoint, params=params, token=session["token"])
    data = r.json()
    # if (current_chars_hash != data["meta"]["hashes"]["chars"]):
    current_chars_hash = data["meta"]["hashes"]["chars"]
    # check_hash() f
    return data

def get_gear(gear: str) -> dict:

    # First it looks for the data in redis cache
    data = get_data_from_cache(key="gear_"+gear)

    # If cache is found then serves the data from cache
    if data is not None:
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        print(f"Calling get_gear_from_api({gear})")
        data = get_gear_from_api(gear)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key="gear_"+gear, value=data)
        return data

