from app.gear import get_gear
from .char import get_char
from .nadavcoh_redis import get_data_from_cache, set_data_to_cache
from .roster import find_char_in_roster
from flask import current_app

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
        current_app.logger.info ("Calling calculate_tier_cost_base_gear", char_name, tier, slots)
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
    for tier in range(from_tier+1,to_tier):
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
        current_app.logger.info ("Calling calculate_multi_tier_cost_base_gear", char_name, from_tier, to_tier, slots)
        data = calculate_multi_tier_cost_base_gear (char_name, from_tier, to_tier, slots)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key=key_name, value=data)
        return data

def get_char_to_tier(char_id, tier):
    char = find_char_in_roster(char_id)
    slots_bool_not = [not x for x in char["slots"]]
    return get_multi_tier_cost_base_gear(char_id,char["tier"],tier,slots_bool_not)

def calculate_tier_cost_crafted_gear (char_name, tier, slots=[True]*6):
    totalDirectCost = {}
    char_data = get_char(char_name)
    tier_data = char_data["data"]["gearTiers"][str(tier)]
    if ("slots" in tier_data):
        for slot_num in [i for i in range(len(slots)) if slots[i]]:
            slot = tier_data["slots"][slot_num]
            if ("flatCost" in slot["piece"]):
                # this is a crafted piece - add it to
                    totalDirectCost = gearset_add(totalDirectCost, slot["piece"]["id"], 1)

    def get_direct_cost(gear: dict, quantity: int):
        recursiveDirectCost = {}
        if "directCost" in gear["item"]:
            recursiveDirectCost = gearset_add(recursiveDirectCost, gear["item"]["id"], gear["quantity"] * quantity)
            for piece in gear["item"]["directCost"]:
                recursiveDirectCost = gearset_merge(recursiveDirectCost, get_direct_cost(piece, gear["quantity"]))
        return recursiveDirectCost

    recursiveDirectCost2 = {}
    for (current_gear_id, quantity) in totalDirectCost.items():
        current_gear = get_gear(current_gear_id)
        for piece in current_gear["data"]["directCost"]:
            recursiveDirectCost2 = gearset_merge(recursiveDirectCost2, get_direct_cost(piece, quantity))
    
    return {"data": gearset_merge(totalDirectCost, recursiveDirectCost2), "meta": current_gear["meta"]}

def get_tier_cost_crafted_gear (char_name, tier, slots=[True]*6):
    key_name = "calc_crafted_" + char_name + "_tier_" + str(tier) + "_slots_" + str(slots)
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key_name)

    # If cache is found then serves the data from cache
    if data is not None:
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        current_app.logger.info (f"Calling calculate_tier_cost_crafted_gear({char_name}, {tier}, {slots}")
        data = calculate_tier_cost_crafted_gear (char_name, tier, slots)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key=key_name, value=data)
        return data

def calculate_multi_tier_cost_crafted_gear (char_name, from_tier, to_tier, slots=[True]*6):
    # Slots are listed in order, top to bottom on the left, then top to bottom on the right.
    totalCost = {}
    current_tier = {"meta": None}
    if to_tier>from_tier:
        current_tier = get_tier_cost_crafted_gear(char_name, from_tier, slots)
        totalCost = gearset_merge(totalCost, current_tier["data"])
    for tier in range(from_tier+1,to_tier):
        current_tier = get_tier_cost_crafted_gear(char_name, tier)
        totalCost = gearset_merge(totalCost, current_tier["data"])
    return {"data": totalCost, "meta": current_tier["meta"]}


def get_multi_tier_cost_crafted_gear (char_name, from_tier, to_tier, slots=[True]*6):
    key_name = "calc_crafted_" + char_name + "_tier_" + str(from_tier) + "_to_" + str(to_tier) + "_slots_" + str(slots)
    # First it looks for the data in redis cache
    data = get_data_from_cache(key=key_name)

    # If cache is found then serves the data from cache
    if data is not None:
        return data

    else:
        # If cache is not found then sends request to the MapBox API
        current_app.logger.info ("Calling calculate_multi_tier_cost_crafted_gear", char_name, from_tier, to_tier, slots)
        data = calculate_multi_tier_cost_crafted_gear (char_name, from_tier, to_tier, slots)
        # This block sets saves the respose to redis and serves it directly
        data["cache"] = False
        state = set_data_to_cache(key=key_name, value=data)
        return data

def get_char_to_tier_crafted(char_id, tier):
    char = find_char_in_roster(char_id)
    slots_bool_not = [not x for x in char["slots"]]
    return get_multi_tier_cost_crafted_gear(char_id, char["tier"], tier, slots_bool_not)

def get_gear_flat_cost (gear_id):
    gear_data = get_gear(gear_id)
    gear_data_gearset = { gear["item"]["id"]: gear["quantity"] for gear in gear_data["data"]["flatCost"] }
    return gear_data_gearset

def multiply_gear_set (gearset, n):
    for gear_id in gearset.keys():
        gearset[gear_id] = gearset[gear_id] * n
    return (gearset)