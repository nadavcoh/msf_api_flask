from flask_login import UserMixin

from app.db import get_db

class User(UserMixin):
    def __init__(self, id_, name, icon, frame):
        self.id = id_
        self.name = name
        self.icon = icon
        self.frame = frame

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM My_Users WHERE id = %s", (user_id,)
        ).fetchone()
        if not user:
            return None

        user = User(
            id_=user["id"], name=user["name"], icon=user["icon"], frame=user["frame"]
        )
        return user

    @staticmethod
    def create(id_, name, icon, frame):
        db = get_db()
        db.execute(
            "INSERT INTO My_Users (id, name, icon, frame) "
            "VALUES (%s, %s, %s, %s)",
            (id_, name, icon, frame),
        )
        db.commit()