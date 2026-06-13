import io
import tempfile

import whisper
from pydub import AudioSegment
import config

# Pre-load at startup to avoid per-request cost (~140 MB for base model)
_model = whisper.load_model(config.WHISPER_MODEL)


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> dict:
    """Transcribe raw audio bytes. Converts WebM → WAV before passing to Whisper."""
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio.export(tmp.name, format="wav")
        result = _model.transcribe(tmp.name)

    words = [
        {"word": w["word"], "start_s": w["start"]}
        for w in result.get("segments", [])
    ]
    return {
        "text": result["text"].strip(),
        "confidence": None,  # Whisper does not expose per-utterance confidence
        "words": words,
    }
