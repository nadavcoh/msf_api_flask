from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for, Markup
)
from flask_login import current_user, login_required
import pandas as pd
from app.gear import get_gear

from app.inventory import find_item_in_inventory
from .char import get_char, get_chars
from .db import get_db
from .gear_calculator_functions import get_char_to_tier

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
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
        WHERE "user_id" = ?""", (current_user.id,)
    ).fetchall()
    return render_template('gear-calculator/index.html', teams=teams)

@gear_calculator.route('/team/<int:id>')
@login_required
def team(id):
    db = get_db()
    team = db.execute(
        """SELECT team_id, char1, char2, char3, char4, char5, to_tier, name
        FROM Teams
        WHERE "user_id" = ? and "team_id" = ?""", (current_user.id, id)
    ).fetchone()

    result = pd.DataFrame(columns=["gear_id"], dtype = str)
    for char_num in range(1,6):
        char_data = get_char_to_tier(team["char"+str(char_num)], team["to_tier"])
        char_df = pd.DataFrame(data={"gear_id": char_data["data"].keys(), "char"+str(char_num): char_data["data"].values()} )
        char_df = char_df.astype({'gear_id':str})
        result = pd.merge(result, char_df, how="outer")
    
    
    result.fillna(0, inplace=True)
    result.drop(index=result.loc[result["gear_id"]=="SC"].index, inplace=True)
    result["need"] = result.sum(axis="columns")
    def get_inventory_data (row):
        return find_item_in_inventory(row["gear_id"])
    result["have"] = result.apply(get_inventory_data, axis=1)
    result["remaining"] = result["need"] - result["have"]
    result["remaining"] = [0 if x<0 else x for x in result["remaining"]]
    def get_gear_data (row):
        gear_data = get_gear(row["gear_id"])
        return {"gear_id": row["gear_id"],
                "name": gear_data["data"]["name"],
                "icon": gear_data["data"]["icon"],
                "tier": gear_data["data"].get("tier") ,
                }
    gear_data = result.apply (get_gear_data, result_type ='expand', axis = 1)
    result = pd.merge(result, gear_data)
    result.sort_values(["remaining", "tier", "name"], ascending=[False, False, True], inplace=True)
    result.drop(columns = ["gear_id", "tier"], inplace=True)
    # https://stackoverflow.com/questions/52475458/how-to-sort-pandas-dataframe-with-a-key
    rule = {
    "name": 1,
    "icon": 2,
    "char1": 3,
    "char2": 4,
    "char3": 5,
    "char4": 6,
    "char5": 7,
    "need": 8,
    "have": 9,
    "remaining": 10
    }
    result.sort_index(axis="columns", inplace = True, key=lambda x: pd.Series(x).apply(lambda y: rule.get(y, 1000)))
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html#Other-Fun-and-Useful-Stuff
    def make_index(x):
        if x.startswith("char"):
            char_name = team[x]
            char_data = get_char(char_name)
            x = "<img src='{}'>".format(char_data["data"]["portrait"])
            x += char_data["data"]["name"]

        else:
            match x:
                case "name":
                    x = "Name"
                case _:
                    x = x.capitalize()
        return x
    def make_pretty(styler):
        styler.highlight_min(subset="remaining", color="palegreen")
        styler.highlight_between(subset="remaining", left=1)
        styler.format_index(formatter=make_index, axis="columns")
        styler.format(thousands=",",
                                formatter={'icon': lambda x: "<img class='reward_icon' src='{}'>".format(x),
                                          'char1': "{:,.0f}",
                                          'char2': "{:,.0f}",
                                          'char3': "{:,.0f}",
                                          'char4': "{:,.0f}",
                                          'char5': "{:,.0f}",
                                          'need': "{:,.0f}",
                                          'remaining': "{:,.0f}"
                                           } )
        return styler
    df_html = result.style.pipe(make_pretty).to_html()
    return render_template('gear-calculator/team.html', team=team, df_html=Markup(df_html))