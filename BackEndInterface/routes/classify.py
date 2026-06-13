from flask import Blueprint, request, jsonify
from ml.client import call_ml_safe

bp = Blueprint("classify", __name__)


@bp.post("/ml/classify")
def classify():
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id", "")
    text = body.get("text", "")
    history = body.get("history", [])
    result = call_ml_safe(session_id, text, history)
    return jsonify(result)
