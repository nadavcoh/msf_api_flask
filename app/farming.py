import json
from app.gear import get_gear
from app.campaigns import get_campaign, get_campaign_names
from flask import url_for, current_app
import pandas as pd
from app.inventory import find_item_in_inventory
from app.nadavcoh_redis import get_data_from_cache, set_data_to_cache
from app.roster import find_char_in_roster
    
def calculate_all_rewards_by_id(): 
    all_rewards_by_id = {}
    for current_campaign_name in get_campaign_names()["data"]:
        current_campaign = get_campaign(current_campaign_name)
        for current_chapter_num, current_chapter_data in current_campaign["data"]["chapters"].items():
            for current_tier_num, current_tier_data in current_chapter_data["tiers"].items():
                if current_tier_data:
                    for current_reward_group in current_tier_data["rewards"]["allOf"]:
                        for current_reward_group_key, current_reward_group_value in current_reward_group.items():
                            match current_reward_group_key:
                                case "item":
                                    if (current_reward_group_value != "SC" and current_reward_group_value != "XP"):
                                        #print (current_reward_group_value)
                                        reward = {"campaign_id": current_campaign_name, "chapter": current_chapter_num, "tier": current_tier_num}
                                        if (current_reward_group_value not in all_rewards_by_id):
                                            all_rewards_by_id[current_reward_group_value] = [reward]
                                        else:
                                            all_rewards_by_id[current_reward_group_value].append(reward)
                                    pass
                                case "chanceOf":
                                    for current_reward_group_key_chahnceof, current_reward_group_value_chanceof in current_reward_group_value.items():
                                        match current_reward_group_key_chahnceof:
                                            case "item":
                                                if (current_reward_group_value_chanceof != "SC" and current_reward_group_value_chanceof != "XP"):
                                                    #print (current_reward_group_value_chanceof)
                                                    reward = {"campaign_id": current_campaign_name, "chapter": current_chapter_num, "tier": current_tier_num}
                                                    if (current_reward_group_value_chanceof not in all_rewards_by_id):
                                                        all_rewards_by_id[current_reward_group_value_chanceof] = [reward]
                                                    else:
                                                        all_rewards_by_id[current_reward_group_value_chanceof].append(reward)
                                                pass
                                            case "quantity":
                                                pass
                                            case "oneOf":
                                                for oneof_arrayitem in current_reward_group_value_chanceof:
                                                    for oneof_key, oneof_value in oneof_arrayitem.items():
                                                        match oneof_key:
                                                            case "item":
                                                                if (oneof_value != "SC" and oneof_value != "XP"):
                                                                    reward = {"campaign_id": current_campaign_name, "chapter": current_chapter_num, "tier": current_tier_num}
                                                                    if (oneof_value not in all_rewards_by_id):
                                                                        all_rewards_by_id[oneof_value] = [reward]
                                                                    else:
                                                                        all_rewards_by_id[oneof_value].append(reward)
                                                                pass
                                                            case "quantity":
                                                                pass
                                                            case "weight":
                                                                pass
                                                            case _:
                                                                current_app.logger.info("Unmatched3: "+oneof_key)
                                            case _:
                                                current_app.logger.info ("Unmatched2: "+current_reward_group_key_chahnceof)
                                case "oneOf":
                                    for oneof_arrayitem in current_reward_group_value:
                                        for oneof_key, oneof_value in oneof_arrayitem.items():
                                            match oneof_key:
                                                case "item":
                                                    if (oneof_value != "SC" and oneof_value != "XP"):
                                                        reward = {"campaign_id": current_campaign_name, "chapter": current_chapter_num, "tier": current_tier_num}
                                                        if (oneof_value not in all_rewards_by_id):
                                                            all_rewards_by_id[oneof_value] = [reward]
                                                        else:
                                                            all_rewards_by_id[oneof_value].append(reward)
                                                    pass
                                                case "quantity":
                                                    pass
                                                case "weight":
                                                    pass
                                                case "maxQuantity":
                                                    pass
                                                case _:
                                                    current_app.logger.info("Unmatched4: "+oneof_key)
                                case "quantity":
                                    pass
                                case _:
                                    current_app.logger.info ("Unmatched1: "+current_reward_group_key)
    farming: pd.DataFrame = pd.DataFrame({"id": all_rewards_by_id.keys(), "locations": all_rewards_by_id.values()} )
    gear_data = farming.apply (get_gear_data, result_type ='expand', axis = 1)
    result: pd.DataFrame = pd.merge(farming, gear_data)
    result["locations_pretty"] = farming.apply (get_farming_locations, axis = 1)
    data = {}
    data["data"] = result
    data["meta"] = current_campaign["meta"]
    return data       
    
def get_gear_data (row):
    gear_data = get_gear(row["id"])
    explode = row["id"].split("_")
    return {"id": row["id"],
            "name": gear_data["data"]["name"],
            "icon": gear_data["data"]["icon"],
            "tier": gear_data["data"].get("tier") ,
            "characterId": gear_data["data"].get("characterId"),
            "explode1": explode[0],
            "explode2": (explode[1] if len(explode)>1 else ""),
            "explode3": (explode[2] if len(explode)>2 else ""),
            "explode4": (explode[3] if len(explode)>3 else ""),
            "rs": (explode[3] if len(explode)>3 else (explode[2] if len(explode)>2 else ""))
            }

def get_inventory_data (row):
    gear_data = get_gear(row["id"])
    char = find_char_in_roster(gear_data["data"].get("characterId"))
    return {"id": row["id"],
            "inventory": find_item_in_inventory(row["id"]),
            "inventory_char": find_item_in_inventory(gear_data["data"].get("characterId"))
            "yellow": char.get("yellow"),
            "red": char.get("red"),
            "red_delta": (char.get("yellow") - char.get("red")) if char else ""}

def get_farming_locations(row):
    result = "<div class='reward'><ul class='locations'>"
    for location in row["locations"]:
        campaign_data = get_campaign (location["campaign_id"])
        result += "<li class='location'>{} {} {}-{}</li>".format(campaign_data["data"]["name"], campaign_data["data"].get("subName", ""), location["chapter"], location["tier"])
    result += "</ul></div>"
    return result

def get_farming_table() -> pd.DataFrame.style:
    key_name = "calc_farming_table"
    data = get_data_from_cache(key=key_name)
    if data is not None:
        data["data"] = pd.DataFrame(json.loads(data["data"]))
        return data
    else:
        current_app.logger.info ("Calling calculate_all_rewards_by_id()")
        data = calculate_all_rewards_by_id()
        data["cache"] = False
        data["data"] = data["data"].to_json()
        state = set_data_to_cache(key=key_name, value=data)
        data["data"] = pd.DataFrame(json.loads(data["data"]))
        return data

def get_farming_inventory():
    farming = get_farming_table()["data"]
    inventory_data = farming.apply (get_inventory_data, result_type ='expand', axis = 1)
    result: pd.DataFrame = pd.merge(farming, inventory_data)
    result.sort_values(["inventory"], inplace=True)
    return result

def get_farming_table_html_char_shards():
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    farming = get_farming_inventory()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["yellow"]!=7) & (farming["explode1"]=="SHARD")]
    farming = farming.loc[(farming["yellow"]!=6) | (farming["inventory"]<300)]
    farming = farming.loc[(farming["yellow"]!=5) | (farming["inventory"]<500)]
    farming = farming.loc[(farming["yellow"]!=4) | (farming["inventory"]<630)]
    farming.drop(columns = ["id", "characterId", "explode1", "explode2", "tier"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()

def get_farming_table_html_gear_gold_teal():
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    farming: str = get_farming_inventory()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["explode1"]=="GEAR")]
    farming = farming.loc[(farming["tier"]>=12)]
    farming.drop(columns = ["id", "characterId", "explode1", "explode2", "tier", "yellow"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()

def get_farming_table_html_gear_purple_blue_green():
    farming: str = get_farming_inventory()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["explode1"]=="GEAR")]
    farming = farming.loc[(farming["tier"]<12)]
    farming.drop(columns = ["id", "characterId", "explode1", "explode2", "tier", "yellow"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()

def get_farming_table_html_iso8():
    farming: str = get_farming_inventory()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["explode1"]=="ISOITEM")]
    farming.drop(columns = ["id", "characterId", "explode1", "explode2", "tier", "yellow"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()

def get_farming_table_html_rs():
    farming = get_farming_inventory()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["explode1"]=="RS")]
    farming.sort_values(["red", "red_delta"], ascending=[False, Fales] , inplace=True)
    farming.drop(columns = ["id", "explode1", "explode2", "explode3", "explode4"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}",
                                          'red': "{:.0f}" } ).to_html()

def get_farming_table_html_char_all():
    farming: str = get_farming_inventory()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["explode1"]=="SHARD")]
    farming.drop(columns = ["id", "characterId", "explode1", "explode2", "tier"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()

def get_farming_table_html_misc():
    farming: str = get_farming_inventory()
    farming.drop(columns="locations", inplace = True)
    farming = farming.loc[(farming["explode1"]!="GEAR")]
    farming = farming.loc[(farming["explode1"]!="ISOITEM")]
    farming = farming.loc[(farming["explode1"]!="SHARD")]
    farming = farming.loc[(farming["explode1"]!="RS")]
    farming.drop(columns = ["characterId", "explode2", "tier", "yellow"], inplace=True)
    farming.sort_values(["id"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()

def get_farming_table_html_all():
    farming: str = get_farming_inventory()
    farming.drop(columns="locations", inplace = True)
    # farming = farming.loc[(farming["explode1"]!="GEAR")]
    # farming = farming.loc[(farming["explode1"]!="ISOITEM")]
    # farming = farming.loc[(farming["explode1"]!="SHARD")]
    farming.drop(columns = ["characterId", "explode2", "tier", "yellow"], inplace=True)
    farming.sort_values(["id"], inplace=True)
    return farming.style.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'tier': "{:.0f}",
                                          'yellow': "{:.0f}" } ).to_html()
