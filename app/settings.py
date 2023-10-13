from flask_login import current_user
from app.db import get_db

def set_msftools_sheetid(id):
    db = get_db()
    db.execute(
    """UPDATE My_Users
    SET msf_tools_sheetid = %s
    WHERE id = %s;""",
    (id , current_user.id))
    db.commit()

def get_msftools_sheetid():
    db = get_db()
    resp = db.execute(
        "SELECT msf_tools_sheetid from My_Users WHERE id = %s", (current_user.id,)
    ).fetchone()
    return resp[0]