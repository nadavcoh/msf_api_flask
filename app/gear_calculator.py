import re
from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
)
from flask_login import current_user, login_required
import pandas as pd
from markupsafe import Markup

from app.gear import get_gear
from app.inventory import find_item_in_inventory
from .char import get_char, get_chars
from .db import get_db
from .gear_calculator_functions import gearset_merge, get_char_to_tier, get_char_to_tier_crafted, get_gear_flat_cost, multiply_gear_set

gear_calculator = Blueprint('gear_calculator', __name__, url_prefix='/gear-calculator')

@gear_calculator.route('/create_team', methods=('GET', 'POST'))
@login_required
def create_team():
    if request.method == 'POST':
        chars = list(request.form.keys())
        chars.remove("to_tier")
        to_tier = request.form["to_tier"]
        chars.remove("name")
        name = request.form["name"]
        db = get_db()
        db.execute(
            "INSERT INTO Teams (user_id, char1, char2, char3, char4, char5, to_tier, name) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (current_user.id, chars[0], chars[1], chars[2], chars[3], chars[4], to_tier, name),
        )
        db.commit()
        flash ("Team added")
        
    chars = get_chars()
    return render_template('gear-calculator/create_team.html', chars = chars["data"])

@gear_calculator.route('/')
@login_required
def index():
    db = get_db()
    teams = db.execute(
        """SELECT team_id, char1, char2, char3, char4, char5, to_tier, name
        FROM Teams
        WHERE "user_id" = %s""", (current_user.id,)
    ).fetchall()
    return render_template('gear-calculator/index.html', teams=teams)

@gear_calculator.route('/team/<int:id>')
@login_required
def team(id):
    db = get_db()
    team = db.execute(
        """SELECT team_id, char1, char2, char3, char4, char5, to_tier, name
        FROM Teams
        WHERE "user_id" = %s and "team_id" = %s""", (current_user.id, id)
    ).fetchone()

    result = pd.DataFrame(columns=["gear_id"], dtype = str)
    for char_num in range(1,6):
        char_data = get_char_to_tier(team["char"+str(char_num)], team["to_tier"])
        char_df = pd.DataFrame(data={"gear_id": char_data["data"].keys(), "char"+str(char_num): char_data["data"].values()} )
        char_df = char_df.astype({'gear_id':str})
        result = pd.merge(result, char_df, how="outer")
    
    result.fillna(0, inplace=True)
    result.drop(index=result.loc[result["gear_id"]=="SC"].index, inplace=True)
    result["need"] = result.sum(axis="columns", numeric_only=True)
    def get_inventory_data (row):
        return find_item_in_inventory(row["gear_id"])
    result["have"] = result.apply(get_inventory_data, axis=1)
    result["remaining"] = result["need"] - result["have"]
    result["remaining"] = [0 if x<0 else x for x in result["remaining"]]

    crafted = pd.DataFrame(columns=["gear_id"], dtype = str)
    for char_num in range(1,6):
        char_data2 = get_char_to_tier_crafted(team["char"+str(char_num)], team["to_tier"])
        char_df2 = pd.DataFrame(data={"gear_id": char_data2["data"].keys(), "char"+str(char_num): char_data2["data"].values()} )
        char_df2 = char_df2.astype({'gear_id':str})
        crafted = pd.merge(crafted, char_df2, how="outer")
    
    crafted.fillna(0, inplace=True)
    # crafted.drop(index=result.loc[result["gear_id"]=="SC"].index, inplace=True)
    crafted["need"] = crafted.sum(axis="columns", numeric_only=True)
    crafted["have"] = crafted.apply(get_inventory_data, axis=1)
    crafted.drop(index=crafted.loc[crafted["have"]==0].index, inplace=True)
    crafted["amount"] = crafted.apply(lambda x: min(x["need"], x["have"]), axis=1)
    crafted_to_dict = crafted.drop(columns = ["char1", "char2", "char3", "char4", "char5", "need", "have"])
    crafted_dict = crafted_to_dict.to_dict('records')
    
    crafted_gearset_cost = {}
    for gear in crafted_dict:
        flat_cost = get_gear_flat_cost(gear["gear_id"])
        multiple_flat_cost = multiply_gear_set(flat_cost, gear["amount"])
        crafted_gearset_cost = gearset_merge(crafted_gearset_cost, multiple_flat_cost)

    crafted_df = pd.DataFrame(data={"gear_id": crafted_gearset_cost.keys(), "from_crafted": crafted_gearset_cost.values()})
    crafted_df.drop(index=crafted_df.loc[crafted_df["gear_id"]=="SC"].index, inplace=True)
    
    result = pd.merge(result, crafted_df, how = "outer")
    result.fillna(0, inplace=True)

    result["remaining_adjusted"] = result["remaining"] - result["from_crafted"]
    result["remaining_adjusted"] = [0 if x<0 else x for x in result["remaining_adjusted"]]

    def get_gear_data (row):
        gear_data = get_gear(row["gear_id"])
        return {"gear_id": row["gear_id"],
                "name": gear_data["data"]["name"],
                "icon": gear_data["data"]["icon"],
                "tier": gear_data["data"].get("tier") ,
                }
    gear_data = result.apply (get_gear_data, result_type ='expand', axis = 1)
    result = pd.merge(result, gear_data)
    result.sort_values(["remaining_adjusted", "tier", "name"], ascending=[False, False, True], inplace=True)
    result.drop(columns = ["gear_id", "tier"], inplace=True)
    # https://stackoverflow.com/questions/52475458/how-to-sort-pandas-dataframe-with-a-key
    rule = {
    "name": 1,
    "icon": 2,
    "char1": 11,
    "char2": 12,
    "char3": 13,
    "char4": 14,
    "char5": 15,
    "need": 5,
    "have": 4,
    "remaining": 3,
    "remaining_adjusted": 2.1,
    "from_crafted": 2.2
    }
    result.sort_index(axis="columns", inplace = True, key=lambda x: pd.Series(x).apply(lambda y: rule.get(y, 1000)))
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    def make_index(x):
        if x.startswith("char"):
            char_name = team[x]
            char_data = get_char(char_name)
            x = "<img class='mid' src='{}'><br>".format(char_data["data"]["portrait"])
            x += char_data["data"]["name"]
        else:
            match x:
                case "name":
                    x = "Name"
                case _:
                    x = x.replace("_"," ")
                    x = x.title()
        return x
    def make_pretty(styler):
        styler.highlight_min(subset="remaining_adjusted", color="palegreen")
        styler.highlight_between(subset="remaining_adjusted", left=1)
        styler.format_index(formatter=make_index, axis="columns")
        styler.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'char1': "{:,.0f}",
                                          'char2': "{:,.0f}",
                                          'char3': "{:,.0f}",
                                          'char4': "{:,.0f}",
                                          'char5': "{:,.0f}",
                                          'need': "{:,.0f}",
                                          'remaining': "{:,.0f}",
                                          'have': "{:,.0f}",
                                          'from_crafted': "{:,.0f}",
                                          'remaining_adjusted': "{:,.0f}"
                                           } )
        return styler
    df_html = result.style.pipe(make_pretty).to_html()

    if len(crafted):
        gear_data = crafted.apply (get_gear_data, result_type ='expand', axis = 1)
        crafted = pd.merge(crafted, gear_data)
    else:
        crafted.insert(len(crafted.columns), "name", None)
        crafted.insert(len(crafted.columns), "icon", None)
        crafted.insert(len(crafted.columns), "tier", None)
    crafted.sort_values(["tier", "name"], ascending=[False, True], inplace=True)
    crafted.drop(columns = ["gear_id", "tier"], inplace=True)
    
    # https://stackoverflow.com/questions/52475458/how-to-sort-pandas-dataframe-with-a-key
    rule = {
    "name": 1,
    "icon": 2,
    "char1": 11,
    "char2": 12,
    "char3": 13,
    "char4": 14,
    "char5": 15,
    "need": 5,
    "have": 4,
    "remaining": 3
    }
    crafted.sort_index(axis="columns", inplace = True, key=lambda x: pd.Series(x).apply(lambda y: rule.get(y, 1000)))
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    def make_pretty2(styler):
        # styler.highlight_min(subset="remaining", color="palegreen")
        styler.highlight_between(subset="have", left=1)
        styler.format_index(formatter=make_index, axis="columns")
        styler.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'char1': "{:,.0f}",
                                          'char2': "{:,.0f}",
                                          'char3': "{:,.0f}",
                                          'char4': "{:,.0f}",
                                          'char5': "{:,.0f}",
                                          'need': "{:,.0f}",
                                          'amount': "{:,.0f}"
                                           } )
        return styler
    crafted_html = crafted.style.pipe(make_pretty2).to_html()

    return render_template('gear-calculator/team.html', team=team, df_html=Markup(df_html) + Markup(crafted_html))

@gear_calculator.route('/team/<int:id>/delete')
@login_required
def delete_team(id):
    db = get_db()
    db.execute('DELETE FROM Teams WHERE team_id = %s and "user_id" = %s', (id, current_user.id))
    db.commit()
    return redirect(url_for('gear_calculator.index'))

@gear_calculator.route('/all-teams')
@login_required
def all_teams():
    db = get_db()
    teams = db.execute(
        """SELECT team_id, char1, char2, char3, char4, char5, to_tier, name
        FROM Teams
        WHERE "user_id" = %s""", (current_user.id,)
    ).fetchall()
    result = pd.DataFrame(columns=["gear_id"], dtype = str)
    for team in teams:
        team_gearset = {}
        for char_num in range(1,6):
            char_gearset = get_char_to_tier(team["char"+str(char_num)], team["to_tier"])
            team_gearset = gearset_merge(team_gearset, char_gearset["data"])
        team_df = pd.DataFrame(data={"gear_id": team_gearset.keys(), "team"+str(team["team_id"]): team_gearset.values()} )
        team_df = team_df.astype({'gear_id':str})
        result = pd.merge(result, team_df, how="outer")
    
    result.fillna(0, inplace=True)
    result.drop(index=result.loc[result["gear_id"]=="SC"].index, inplace=True)
    result["need"] = result.sum(axis="columns", numeric_only=True)
    def get_inventory_data (row):
        return find_item_in_inventory(row["gear_id"])
    result["have"] = result.apply(get_inventory_data, axis=1)
    result["remaining"] = result["need"] - result["have"]
    result["remaining"] = [0 if x<0 else x for x in result["remaining"]]

    crafted = pd.DataFrame(columns=["gear_id"], dtype = str)
    for team in teams:
        team_gearset_crafted = {}
        for char_num in range(1,6):
            char_gearset_crafted = get_char_to_tier_crafted(team["char"+str(char_num)], team["to_tier"])
            team_gearset_crafted = gearset_merge(team_gearset_crafted, char_gearset_crafted["data"])
        team_df_crafted = pd.DataFrame(data={"gear_id": team_gearset_crafted.keys(), "team"+str(team["team_id"]): team_gearset_crafted.values()} )
        team_df_crafted = team_df_crafted.astype({'gear_id':str})
        crafted = pd.merge(crafted, team_df_crafted, how="outer")

    crafted.fillna(0, inplace=True)
    # crafted.drop(index=result.loc[result["gear_id"]=="SC"].index, inplace=True)
    crafted["need"] = crafted.sum(axis="columns", numeric_only=True)
    crafted["have"] = crafted.apply(get_inventory_data, axis=1)
    crafted.drop(index=crafted.loc[crafted["have"]==0].index, inplace=True)
    crafted["amount"] = crafted.apply(lambda x: min(x["need"], x["have"]), axis=1)
    crafted_to_dict = crafted.drop(columns = ["need", "have"])
    crafted_dict = crafted_to_dict.to_dict('records')
    
    crafted_gearset_cost = {}
    for gear in crafted_dict:
        flat_cost = get_gear_flat_cost(gear["gear_id"])
        multiple_flat_cost = multiply_gear_set(flat_cost, gear["amount"])
        crafted_gearset_cost = gearset_merge(crafted_gearset_cost, multiple_flat_cost)

    crafted_df = pd.DataFrame(data={"gear_id": crafted_gearset_cost.keys(), "from_crafted": crafted_gearset_cost.values()})
    crafted_df.drop(index=crafted_df.loc[crafted_df["gear_id"]=="SC"].index, inplace=True)
    
    result = pd.merge(result, crafted_df, how = "outer")
    result.fillna(0, inplace=True)

    result["remaining_adjusted"] = result["remaining"] - result["from_crafted"]
    result["remaining_adjusted"] = [0 if x<0 else x for x in result["remaining_adjusted"]]

    def get_gear_data (row):
        gear_data = get_gear(row["gear_id"])
        return {"gear_id": row["gear_id"],
                "name": gear_data["data"]["name"],
                "icon": gear_data["data"]["icon"],
                "tier": gear_data["data"].get("tier") ,
                }
    gear_data = result.apply (get_gear_data, result_type ='expand', axis = 1)
    result = pd.merge(result, gear_data)
    result.sort_values(["remaining_adjusted", "tier", "name"], ascending=[False, False, True], inplace=True)
    result.drop(columns = ["gear_id", "tier"], inplace=True)
    # https://stackoverflow.com/questions/52475458/how-to-sort-pandas-dataframe-with-a-key
    rule = {
    "name": 1,
    "icon": 2,
    "need": 5,
    "have": 4,
    "remaining": 3,
    "remaining_adjusted": 2.1,
    "from_crafted": 2.2
    }
    result.sort_index(axis="columns", inplace = True, key=lambda x: pd.Series(x).apply(lambda y: rule.get(y, 1000)))
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    def make_index(x):
        if x.startswith("team"):
            team_id = int(re.match(r'team(.*)', x).group(1))
            team_row = [team for team in teams if team["team_id"] == team_id][0]
            x = team_row["name"]
            for char_num in range(1,6):
                char_name = team_row["char"+str(char_num)]
                char_data = get_char(char_name)
                x += "<br><img class='tiny' src='{}'>".format(char_data["data"]["portrait"])
                # x += char_data["data"]["name"]
        else:
            x = x.replace("_"," ")
            x = x.title()
        return x
    teams_list = ["team"+str(team["team_id"]) for team in teams]
    teams_formatter = {team_name: "{:,.0f}" for team_name in teams_list}
    def make_pretty(styler):
        styler.highlight_min(subset="remaining_adjusted", color="palegreen")
        styler.highlight_between(subset="remaining_adjusted", left=1)
        styler.format_index(formatter=make_index, axis="columns")
        styler.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'need': "{:,.0f}",
                                          'remaining': "{:,.0f}",
                                          'have': "{:,.0f}",
                                          'from_crafted': "{:,.0f}",
                                          'remaining_adjusted': "{:,.0f}"
                                           }|teams_formatter )
        return styler
    df_html = result.style.pipe(make_pretty).to_html()

    if len(crafted):
        gear_data = crafted.apply (get_gear_data, result_type ='expand', axis = 1)
        crafted = pd.merge(crafted, gear_data)
    else:
        crafted.insert(len(crafted.columns), "name", None)
        crafted.insert(len(crafted.columns), "icon", None)
        crafted.insert(len(crafted.columns), "tier", None)
    crafted.sort_values(["tier", "name"], ascending=[False, True], inplace=True)
    crafted.drop(columns = ["gear_id", "tier"], inplace=True)
    
    # https://stackoverflow.com/questions/52475458/how-to-sort-pandas-dataframe-with-a-key
    rule = {
    "name": 1,
    "icon": 2,
    "need": 5,
    "have": 4,
    "remaining": 3
    }
    crafted.sort_index(axis="columns", inplace = True, key=lambda x: pd.Series(x).apply(lambda y: rule.get(y, 1000)))
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    def make_pretty2(styler):
        # styler.highlight_min(subset="remaining", color="palegreen")
        styler.highlight_between(subset="have", left=1)
        styler.format_index(formatter=make_index, axis="columns")
        styler.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'need': "{:,.0f}",
                                          'amount': "{:,.0f}"
                                           } |teams_formatter)
        return styler
    crafted_html = crafted.style.pipe(make_pretty2).to_html()

    return render_template('gear-calculator/all_teams.html', df_html=Markup(df_html) + Markup(crafted_html))