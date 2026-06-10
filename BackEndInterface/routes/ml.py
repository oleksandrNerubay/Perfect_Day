import traceback
from flask import Blueprint, jsonify
from db import users
from utils.serializer import serialize

ml_bp = Blueprint("ml", __name__)


@ml_bp.route("/ml/export", methods=["GET"])
def export():
    try:
        pipeline = [
            {"$project": {"password": 0, "email": 0}},
            {
                "$lookup": {
                    "from": "events",
                    "localField": "_id",
                    "foreignField": "user_id",
                    "as": "event_docs",
                }
            },
            {
                "$addFields": {
                    "event_stats": {
                        "total_voice_turns": {"$sum": "$event_docs.voice_turns"},
                        "total_words_spoken": {"$sum": "$event_docs.total_words_spoken"},
                        "total_time_spent_sec": {"$sum": "$event_docs.time_spent_sec"},
                        "active_days": {"$size": "$event_docs"},
                    }
                }
            },
            {"$project": {"event_docs": 0}},
        ]

        result = list(users.aggregate(pipeline))
        return jsonify([serialize(doc) for doc in result]), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "internal server error"}), 500
