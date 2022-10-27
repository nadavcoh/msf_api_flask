from time import time
from flask_login import current_user
from app.msf_api import get_msf_api
from app.db import get_db
import pandas as pd
from app.settings import get_msftools_sheetid
import json

# Roster
def get_roster_from_api(since = None):
    msf_api = get_msf_api()
    r = msf_api.get("/player/v1/roster", params = {"since": since})
    if r.status_code == 344:
        return None
    else:
        roster = r.json()
        return roster

def update_roster():
    db = get_db()
    resp = db.execute(
        "SELECT roster FROM user WHERE id = ?", (current_user.id,)
    ).fetchone()
    if resp[0]:
        meta = json.loads(resp[0])
        asOf = meta["asOf"]
    else:
        asOf = resp[0]
    roster = get_roster_from_api(asOf)
    
    # https://stackoverflow.com/questions/33636191/insert-a-list-of-dictionaries-into-an-sql-table-using-python
    # https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders
    # https://stackoverflow.com/questions/4205181/insert-into-a-mysql-table-or-update-if-exists
    if roster:
        # Clear current roster    
        db.execute("DELETE FROM Roster WHERE 'user_id' = ?;", (current_user.id,))
        def dump_slots(char):
            char["gearSlots"] = json.dumps(char["gearSlots"])
            return char
        roster["data"] = [dump_slots(k) for k in roster["data"]]
        db.executemany("REPLACE INTO Roster"
                    "(user_id, char_id, tier, slots, yellow)"
                    "VALUES (:user_id, :id, :gearTier, :gearSlots, :activeYellow)",
                    [k|{"user_id": current_user.id} for k in roster["data"]])
        roster["meta"]["updated"] = time()
        db.execute(
        """UPDATE user
        SET roster = ?
        WHERE id = ?;""",
        (json.dumps(roster["meta"]), current_user.id))
        db.commit()
    else:
        meta["updated"] = time()
        db.execute(
        """UPDATE user
        SET roster = ?
        WHERE id = ?;""",
        (json.dumps(meta), current_user.id))
        db.commit()

def find_char_in_roster (id):
    db = get_db()
    resp = db.execute("""SELECT char_id, tier, slots, yellow 
                        FROM Roster  
                        WHERE "user_id" = ? AND char_id = ?;
                        """, (current_user.id, id)).fetchone()
    if resp:
        char = dict(resp)
        char["slots"] = json.loads(char["slots"])
    else:
        char = {}
    return char


    # Slots are listed in order, top to bottom on the left, then top to bottom on the right.

def get_roster_update_time():
    db = get_db()
    resp = db.execute(
        "SELECT roster FROM user WHERE id = ?", (current_user.id,)
    ).fetchone()
    if resp[0]:
        resp = json.loads(resp[0]).get("updated")
    else:
        resp = resp[0]
    return resp