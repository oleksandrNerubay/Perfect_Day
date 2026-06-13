import json

from flask import Blueprint, request, jsonify
from flask_sock import Sock

from db.ops import save_turn, get_history
from ml.client import call_ml_safe
import config

bp = Blueprint("transcribe", __name__)
sock = Sock()


@bp.post("/transcribe")
def transcribe_batch():
    if "audio" not in request.files:
        return jsonify({"error": "audio file required", "code": "missing_audio"}), 400
    audio_bytes = request.files["audio"].read()
    from speech.whisper_handler import transcribe_audio
    result = transcribe_audio(audio_bytes)
    return jsonify(result)


@sock.route("/stream")
def stream(ws):
    session_id = request.args.get("session_id", "")

    if config.ASR_PROVIDER == "deepgram":
        from speech.deepgram_handler import stream_audio

        # Wrap ws so deepgram_handler can also forward ml_response frames
        class _WSProxy:
            def receive(self):
                return ws.receive()

            def send(self, data: str):
                ws.send(data)
                # After each final frame, dispatch to ML
                frame = json.loads(data)
                if frame.get("type") == "final" and session_id:
                    text = frame["text"]
                    history = [
                        {"speaker": t["speaker"], "text": t["text"], "turn": t["turn_index"]}
                        for t in get_history(session_id)
                    ]
                    save_turn(session_id, "user", text)
                    ml = call_ml_safe(session_id, text, history)
                    ws.send(json.dumps({
                        "type": "ml_response",
                        "intent": ml["intent"],
                        "suggested_reply": ml["suggested_reply"],
                    }))

        stream_audio(_WSProxy(), session_id)
    else:
        # Whisper batch mode over WebSocket: accumulate all frames then transcribe
        from speech.whisper_handler import transcribe_audio
        chunks = []
        while True:
            data = ws.receive()
            if data is None:
                break
            chunks.append(data if isinstance(data, bytes) else data.encode())
        if chunks:
            result = transcribe_audio(b"".join(chunks))
            ws.send(json.dumps({"type": "final", **result}))
            if session_id:
                history = [
                    {"speaker": t["speaker"], "text": t["text"], "turn": t["turn_index"]}
                    for t in get_history(session_id)
                ]
                save_turn(session_id, "user", result["text"], result["confidence"], result["words"])
                ml = call_ml_safe(session_id, result["text"], history)
                ws.send(json.dumps({
                    "type": "ml_response",
                    "intent": ml["intent"],
                    "suggested_reply": ml["suggested_reply"],
                }))
