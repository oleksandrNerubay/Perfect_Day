import requests
import config


def call_ml(session_id: str, current_text: str, history: list[dict]) -> dict:
    payload = {
        "session_id": session_id,
        "current_text": current_text,
        "history": history,
    }
    resp = requests.post(
        f"{config.ML_SERVICE_URL}/classify",
        json=payload,
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def call_ml_safe(session_id: str, current_text: str, history: list[dict]) -> dict:
    try:
        return call_ml(session_id, current_text, history)
    except Exception:
        return {"intent": "unknown", "confidence": 0.0, "suggested_reply": ""}
