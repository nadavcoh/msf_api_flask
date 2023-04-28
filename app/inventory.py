from time import time
from flask_login import current_user
from app.msf_api import get_msf_api
from app.db import get_db
import json

# Inventory
def get_inventory_from_api(since = None):
    msf_api = get_msf_api()
    r = msf_api.get("/player/v1/inventory", params = {"since": since})
    if r.status_code == 344:
        return None
    else:
        inventory = r.json()
        return inventory

def update_inventory():
    db = get_db()
    resp = db.execute(
        "SELECT inventory FROM user WHERE id = ?", (current_user.id,)
    ).fetchone()
    if resp[0]:
        meta = json.loads(resp[0])
        asOf = meta["asOf"]
    else:
        asOf = resp[0]
    inventory = get_inventory_from_api(asOf)
    # https://stackoverflow.com/questions/33636191/insert-a-list-of-dictionaries-into-an-sql-table-using-python
    # https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders
    # https://stackoverflow.com/questions/4205181/insert-into-a-mysql-table-or-update-if-exists
    if inventory:
        # Clear user inventory
        db.execute("""DELETE FROM Inventory WHERE user_id = ?""", (current_user.id,))
        db.commit()
        db.executemany("REPLACE INTO inventory"
                    "(user_id, item, quantity)"
                    "VALUES (:user_id, :item, :quantity)",
                    [k|{"user_id": current_user.id} for k in inventory["data"]])
        inventory["meta"]["updated"] = time()
        db.execute(
        """UPDATE user
        SET inventory = ?
        WHERE id = ?;""",
        (json.dumps(inventory["meta"]), current_user.id))
        db.commit()
    else:
        meta["updated"] = time()
        db.execute(
        """UPDATE user
        SET inventory = ?
        WHERE id = ?;""",
        (json.dumps(meta), current_user.id))
        db.commit()

def find_item_in_inventory (item):
    get_inventory_update_time()
    db = get_db()
    resp = db.execute("""SELECT quantity 
                        FROM Inventory  
                        WHERE "user_id" = ? AND item = ?;
                        """, (current_user.id, item)).fetchone()
    if resp:
        resp = resp[0]
    else:
        resp = 0
    return resp

def get_inventory_update_time():
    db = get_db()
    resp = db.execute(
        "SELECT inventory FROM user WHERE id = ?", (current_user.id,)
    ).fetchone()
    if resp[0]:
        resp = json.loads(resp[0]).get("updated")
    else:
        # resp = resp[0]
        update_inventory()
        resp = get_inventory_update_time()
    return resp