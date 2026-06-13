from pymongo import ASCENDING
from db.client import get_db


def ensure_indexes() -> None:
    db = get_db()
    db.sessions.create_index("session_id", unique=True)
    db.conversations.create_index(
        [("session_id", ASCENDING), ("turn_index", ASCENDING)]
    )
