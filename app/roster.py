from flask_login import current_user
from app.db import get_db
import pandas as pd
from app.settings import get_msftools_sheetid
import json

SHEET_NAME = 'Roster'

# Roster
def get_roster_from_msftools(SHEET_ID):
    # https://medium.com/geekculture/2-easy-ways-to-read-google-sheets-data-using-python-9e7ef366c775
    # https://stackoverflow.com/questions/33713084/download-link-for-google-spreadsheets-csv-export-with-multiple-sheets
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'
    roster = pd.read_csv(url)
    roster.drop(columns = ['StarkHealth', 'StarkDamage','StarkArmor','StarkFocus', 'StarkResist', 'SaveTime', 'Power', 'Yellow', 'Red', 'Level', 'Basic', 'Special', 'Ultimate', 'Passive', 'IsoClass', 'IsoPips', 'Fragments', 'UnclaimedRed'], inplace=True)
    # roster = df[['ID','Tier','TopLeft', 'MidLeft', 'BottomLeft', 'TopRight', 'MidRight', 'BottomRight']]
    roster.fillna(0, inplace=True)
    roster["Tier"] = pd.to_numeric(roster["Tier"], downcast="integer")
    slots_y_n = roster[['TopLeft', 'MidLeft', 'BottomLeft', 'TopRight', 'MidRight', 'BottomRight']].values.tolist()   
    slots_bool = [json.dumps([x=="Y" for x in k]) for k in slots_y_n]
    roster.insert(2,"slots",slots_bool)
    roster.drop(columns=['TopLeft', 'MidLeft', 'BottomLeft', 'TopRight', 'MidRight', 'BottomRight'], inplace=True)
    return (roster)

def update_roster():
    db = get_db()
    msf_tools_sheetid = get_msftools_sheetid()
    roster = get_roster_from_msftools(msf_tools_sheetid)
    # https://stackoverflow.com/questions/33636191/insert-a-list-of-dictionaries-into-an-sql-table-using-python
    # https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders
    # https://stackoverflow.com/questions/4205181/insert-into-a-mysql-table-or-update-if-exists
    # Clear current roster
    db.execute("DELETE FROM Roster WHERE 'user_id' = ?;", (current_user.id,))
    db.executemany("REPLACE INTO Roster"
                "(user_id, char_id, tier, slots)"
                "VALUES (:user_id, :ID, :Tier, :slots)",
                [k|{"user_id": current_user.id} for k in roster.to_dict('records')])
    db.commit()

# def find_item_in_inventory (item):
#     db = get_db()
#     resp = db.execute("""SELECT quantity 
#                         FROM Inventory  
#                         WHERE "user_id" = ? AND item = ?;
#                         """, (current_user.id, item)).fetchone()
#     if resp:
#         resp = resp[0]
#     else:
#         resp = 0
#     return resp

# def get_char_from_roster(char_id):
#     # Slots are listed in order, top to bottom on the left, then top to bottom on the right.
#     char = roster.loc[roster["ID"]==char_id]
#     slots_y_n = char[['TopLeft', 'MidLeft', 'BottomLeft', 'TopRight', 'MidRight', 'BottomRight']].values.tolist()[0]
#     slots_bool = [x=="Y" for x in slots_y_n]
#     return {"id": char_id,
#             "tier": int(char["Tier"].values[0]),
#             "slots": slots_bool}