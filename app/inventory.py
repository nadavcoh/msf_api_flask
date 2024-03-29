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
        "SELECT inventory from My_Users WHERE id = %s", (current_user.id,)
    ).fetchone()
    if resp["inventory"]:
        meta = json.loads(resp["inventory"])
        asOf = meta["asOf"]
    else:
        asOf = resp["inventory"]
    inventory = get_inventory_from_api(asOf)
    # https://stackoverflow.com/questions/33636191/insert-a-list-of-dictionaries-into-an-sql-table-using-python
    # https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders
    # https://stackoverflow.com/questions/4205181/insert-into-a-mysql-table-or-update-if-exists
    if inventory:
        # Clear user inventory
        db.execute("""DELETE FROM Inventory WHERE user_id = %s""", (current_user.id,))
        db.commit()
        db.cursor().executemany("INSERT INTO inventory "
                    "(user_id, item, quantity) "
                    "VALUES (%(user_id)s, %(item)s, %(quantity)s) "
                    "ON CONFLICT DO NOTHING;",
                    [k|{"user_id": current_user.id} for k in inventory["data"]])
        inventory["meta"]["updated"] = time()
        db.execute(
        """UPDATE My_Users
        SET inventory = %s
        WHERE id = %s;""",
        (json.dumps(inventory["meta"]), current_user.id))
        db.commit()
    else:
        meta["updated"] = time()
        db.execute(
        """UPDATE My_Users
        SET inventory = %s
        WHERE id = %s;""",
        (json.dumps(meta), current_user.id))
        db.commit()

def find_item_in_inventory (item):
    get_inventory_update_time()
    db = get_db()
    resp = db.execute("""SELECT quantity 
                        FROM Inventory  
                        WHERE "user_id" = %s AND item = %s;
                        """, (current_user.id, item)).fetchone()
    if resp:
        resp = resp["quantity"]
    else:
        resp = 0
    return resp

def get_inventory_update_time():
    db = get_db()
    resp = db.execute(
        "SELECT inventory from My_Users WHERE id = %s", (current_user.id,)
    ).fetchone()
    if resp["inventory"]:
        resp = json.loads(resp["inventory"]).get("updated")
    else:
        # resp = resp[0]
        update_inventory()
        resp = get_inventory_update_time()
    return resp

def find_items_in_inventory (item):
    get_inventory_update_time()
    db = get_db()
    resp = db.execute("""SELECT item, quantity 
                        FROM Inventory  
                        WHERE "user_id" = %s AND item like %s;
                        """, (current_user.id, item+"%")).fetchall()
    return resp