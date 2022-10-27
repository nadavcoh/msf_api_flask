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
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None

        user = User(
            id_=user[0], name=user[1], icon=user[2], frame=user[3]
        )
        return user

    @staticmethod
    def create(id_, name, icon, frame):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, icon, frame) "
            "VALUES (?, ?, ?, ?)",
            (id_, name, icon, frame),
        )
        db.commit()