import traceback
from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from db import users, voice_entries, events
from models.voice_entry import build_voice_entry
from utils.text_processor import process
from utils.serializer import serialize

voice_bp = Blueprint("voice", __name__)


@voice_bp.route("/voice", methods=["POST"])
def handle_voice():
    try:
        data = request.get_json() or {}
        user_id_str = data.get("user_id")
        session_id = data.get("session_id")
        raw_input = data.get("raw_input")

        if not user_id_str or not session_id or not raw_input:
            return jsonify({"error": "user_id, session_id, and raw_input are required"}), 400

        try:
            user_oid = ObjectId(user_id_str)
        except (InvalidId, Exception):
            return jsonify({"error": "invalid user_id"}), 400

        if not users.find_one({"_id": user_oid}):
            return jsonify({"error": "user not found"}), 404

        language = data.get("language", "en")
        turn_index = data.get("turn_index", 0)

        received_at = datetime.now(timezone.utc)
        processed = process(raw_input)
        generated_at = datetime.now(timezone.utc)
        processing_ms = int((generated_at - received_at).total_seconds() * 1000)

        entry_doc = build_voice_entry(
            user_id=user_oid,
            session_id=session_id,
            raw_input=raw_input,
            language=language,
            turn_index=turn_index,
            processed=processed,
            received_at=received_at,
            generated_at=generated_at,
            processing_ms=processing_ms,
        )

        result = voice_entries.insert_one(entry_doc)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        events.update_one(
            {"user_id": user_oid, "date": today},
            {
                "$inc": {
                    "voice_turns": 1,
                    "total_words_spoken": processed["word_count"],
                }
            },
            upsert=True,
        )

        users.update_one(
            {"_id": user_oid},
            {
                "$inc": {"engagement.session_count": 1},
                "$set": {"engagement.last_active": generated_at, "updated_at": generated_at},
            },
        )

        return jsonify({
            "output_text": processed["text"],
            "entry_id": str(result.inserted_id),
            "processing_ms": processing_ms,
        }), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "internal server error"}), 500
