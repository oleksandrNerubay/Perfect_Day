import sys
from pathlib import Path
from typing import Optional

from flask import Blueprint, request, jsonify

import config

# Resolved once at import time but NOT inserted into sys.path yet — that happens
# lazily inside _get_rep() so module-level imports in the rest of the app are
# never shadowed by the project-root ml/ package.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

bp = Blueprint("recommend", __name__)

# Module-level singleton — loaded once on first request, reused across all subsequent calls.
_rep = None


def _get_rep():
    global _rep
    if _rep is None:
        if str(_PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(_PROJECT_ROOT))
        from ml.representative import CustomerRepresentative
        _rep = CustomerRepresentative(mongo_uri=config.MONGO_URI, mongo_db=config.MONGO_DB)
    return _rep


def _clean_candidate(doc: dict) -> dict:
    return {k: doc[k] for k in ("business_id", "name", "category", "price_level", "rating", "location") if k in doc}


def _recommend_safe(text: str, user_id: Optional[str]) -> dict:
    try:
        rep         = _get_rep()
        intent_data = rep.identify(text)
        candidates  = rep.process(**intent_data, user_id=user_id)
        reply       = rep.respond(**intent_data, candidates=candidates)
        return {
            "intent":     intent_data["intent"],
            "confidence": round(intent_data["confidence"], 4),
            "entities":   intent_data["entities"],
            "candidates": [_clean_candidate(c) for c in candidates],
            "reply":      reply,
        }
    except Exception as exc:
        return {"error": str(exc), "code": "representative_error"}


@bp.post("/recommend")
def recommend() -> tuple:
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required", "code": "missing_text"}), 400
    if len(text) > 2000:
        return jsonify({"error": "text exceeds 2000-character limit", "code": "text_too_long"}), 400

    result = _recommend_safe(text, body.get("user_id"))
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200
