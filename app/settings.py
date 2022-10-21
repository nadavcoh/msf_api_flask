from flask_login import current_user
from app.db import get_db

def set_msftools_sheetid(id):
    db = get_db()
    db.execute(
    """UPDATE user
    SET msf_tools_sheetid = ?
    WHERE id = ?;""",
    (id , current_user.id))
    db.commit()

def get_msftools_sheetid():
    db = get_db()
    resp = db.execute(
        "SELECT msf_tools_sheetid FROM user WHERE id = ?", (current_user.id,)
    ).fetchone()
    return resp[0]