from .nadavcoh_redis import get_data_from_cache, set_data_to_cache
from .msf_api import get_msf_api

def get_char_from_api(char_id: str) -> dict:
    msf_api = get_msf_api()
    endpoint = "/game/v1/characters/" + char_id
    params = {"statsFormat": "csv",
            "charInfo": "full",
            "costumes": "none",
            "abilityKits": "none",
            "pieceFlatCost": "full",
            "subPieceInfo": "none"}
    r = msf_api.get(endpoint, params=params)
    data = r.json()
    return data

def get_char(char_id: str) -> dict:
    data = get_data_from_cache(key="char_" + char_id)
    if data is not None:
        return data
    else:
        data = get_char_from_api(char_id)
        data["cache"] = False
        state = set_data_to_cache(key="char_" + char_id, value=data)
        return data

def get_chars_from_api():
    msf_api = get_msf_api()
    r = msf_api.get("/game/v1/characters", params={"charInfo":"full", 
                                                            "status" : "playable",
                                                            "statsFormat": "csv",
                                                            "itemFormat": "id",
                                                            "traitFormat": "id"})
    characters = r.json()
    return characters

def get_chars() -> dict:
    data = get_data_from_cache(key="char_all")
    if data is not None:
        return data
    else:
        print ("Calling get_chars_from_api()")
        data = get_chars_from_api()
        data["cache"] = False
        state = set_data_to_cache(key="char_all", value=data)
        return data