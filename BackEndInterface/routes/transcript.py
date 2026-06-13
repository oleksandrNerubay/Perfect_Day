from flask import Blueprint, jsonify
from db.ops import get_history
from db.client import get_db

bp = Blueprint("transcript", __name__)


@bp.get("/session/<session_id>/transcript")
def get_transcript(session_id: str):
    if not get_db().sessions.find_one({"session_id": session_id}):
        return jsonify({"error": "session not found", "code": "session_not_found"}), 404
    turns = get_history(session_id)
    return jsonify({"turns": turns})
