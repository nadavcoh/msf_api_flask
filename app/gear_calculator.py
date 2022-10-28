from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
)
from flask_login import current_user
from .char import get_chars
from .db import get_db

gear_calculator = Blueprint('gear_Calculator', __name__, url_prefix='/gear-calculator')

@gear_calculator.route('/create_team', methods=('GET', 'POST'))
def create_team():
    if request.method == 'POST':
        chars = list(request.form.keys())
        chars.remove("to_tier")
        to_tier = request.form["to_tier"]
        db = get_db()
        db.execute(
            "INSERT INTO Teams (user_id, char1, char2, char3, char4, char5, to_tier) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (current_user.id, chars[0], chars[1], chars[2], chars[3], chars[4], to_tier),
        )
        db.commit()
        flash ("Team added")
        
    chars = get_chars()
    return render_template('gear-calculator/create_team.html', chars = chars["data"])