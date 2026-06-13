from flask import Blueprint, request, jsonify
from db.ops import create_session, end_session

bp = Blueprint("session", __name__)


@bp.post("/session/start")
def start():
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required", "code": "missing_user_id"}), 400
    session_id = create_session(user_id, body.get("metadata", {}))
    return jsonify({"session_id": session_id}), 201


@bp.post("/session/end")
def end():
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required", "code": "missing_session_id"}), 400
    result = end_session(session_id)
    if "error" in result:
        return jsonify({"error": "session not found", "code": result["error"]}), 404
    return jsonify(result)
