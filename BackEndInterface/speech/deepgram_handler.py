import json
from datetime import datetime, timezone

from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import config


def stream_audio(ws, session_id: str) -> None:
    """Handle a Flask-Sock WebSocket: receive binary WebM frames, emit JSON transcript events."""
    dg = DeepgramClient(config.DEEPGRAM_API_KEY)
    connection = dg.listen.live.v("1")

    def on_message(self, result, **kwargs):
        alt = result.channel.alternatives[0]
        text = alt.transcript
        if not text:
            return
        frame_type = "final" if result.is_final else "partial"
        ws.send(json.dumps({
            "type": frame_type,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

    connection.on(LiveTranscriptionEvents.Transcript, on_message)

    options = LiveOptions(
        model="nova-2",
        language="en-US",
        encoding="webm-opus",
        interim_results=True,
    )
    connection.start(options)

    try:
        while True:
            data = ws.receive()
            if data is None:
                break
            connection.send(data)
    finally:
        connection.finish()
