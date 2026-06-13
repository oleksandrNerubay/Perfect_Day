import uuid
from datetime import datetime, timezone
from typing import Any

from db.client import get_db


def create_session(user_id: str, metadata: dict) -> str:
    session_id = str(uuid.uuid4())
    get_db().sessions.insert_one({
        "session_id": session_id,
        "user_id": user_id,
        "started_at": datetime.now(timezone.utc),
        "ended_at": None,
        "metadata": metadata,
    })
    return session_id


def end_session(session_id: str) -> dict[str, Any]:
    db = get_db()
    session = db.sessions.find_one({"session_id": session_id})
    if not session:
        return {"error": "session_not_found"}
    now = datetime.now(timezone.utc)
    db.sessions.update_one(
        {"session_id": session_id},
        {"$set": {"ended_at": now}},
    )
    started_at = session["started_at"]
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    duration_s = (now - started_at).total_seconds()
    turn_count = db.conversations.count_documents({"session_id": session_id})
    return {"duration_s": duration_s, "turn_count": turn_count}


def save_turn(
    session_id: str,
    speaker: str,
    text: str,
    confidence: float | None = None,
    words: list | None = None,
    ml_intent: str | None = None,
    ml_reply: str | None = None,
) -> None:
    db = get_db()
    turn_index = db.conversations.count_documents({"session_id": session_id})
    db.conversations.insert_one({
        "session_id": session_id,
        "turn_index": turn_index,
        "speaker": speaker,
        "text": text,
        "confidence": confidence,
        "words": words or [],
        "ml_intent": ml_intent,
        "ml_reply": ml_reply,
        "created_at": datetime.now(timezone.utc),
    })


def get_history(session_id: str) -> list[dict]:
    cursor = get_db().conversations.find(
        {"session_id": session_id},
        {"_id": 0},
    ).sort("turn_index", 1)
    return list(cursor)
