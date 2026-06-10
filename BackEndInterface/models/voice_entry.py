from datetime import datetime
from bson import ObjectId


def build_voice_entry(
    user_id: ObjectId,
    session_id: str,
    raw_input: str,
    language: str,
    turn_index: int,
    processed: dict,
    received_at: datetime,
    generated_at: datetime,
    processing_ms: int,
) -> dict:
    return {
        "user_id": user_id,
        "session_id": session_id,
        "input": {
            "raw": raw_input,
            "language": language,
            "word_count": processed["word_count"],
            "received_at": received_at,
        },
        "output": {
            "text": processed["text"],
            "generated_at": generated_at,
            "processing_ms": processing_ms,
        },
        "metadata": {
            "intent": processed["intent"],
            "keywords": processed["keywords"],
            "sentiment": processed["sentiment"],
            "flagged": processed["flagged"],
            "turn_index": turn_index,
        },
        "created_at": generated_at,
    }
