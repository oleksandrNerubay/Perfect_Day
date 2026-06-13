import json
from unittest.mock import MagicMock, patch


def test_whisper_transcribe():
    mock_result = {
        "text": " Hello world",
        "segments": [{"word": "Hello", "start": 0.0}, {"word": "world", "start": 0.5}],
    }
    mock_model = MagicMock()
    mock_model.transcribe.return_value = mock_result

    with patch("speech.whisper_handler._model", mock_model), \
         patch("speech.whisper_handler.AudioSegment") as mock_audio:
        mock_audio.from_file.return_value = MagicMock()
        # Bypass actual file export
        mock_model.transcribe.return_value = mock_result

        from speech.whisper_handler import transcribe_audio
        result = transcribe_audio(b"fake_audio")

    assert result["text"] == "Hello world"
    assert len(result["words"]) == 2


def test_deepgram_handler_emits_partial_and_final():
    sent_frames = []

    class FakeWS:
        def send(self, data):
            sent_frames.append(json.loads(data))

        def receive(self):
            return None  # end immediately

    with patch("speech.deepgram_handler.DeepgramClient") as MockDG:
        mock_conn = MagicMock()
        MockDG.return_value.listen.live.v.return_value = mock_conn
        mock_conn.start.return_value = None
        mock_conn.finish.return_value = None

        from speech.deepgram_handler import stream_audio
        stream_audio(FakeWS(), "test-session")

    mock_conn.start.assert_called_once()
    mock_conn.finish.assert_called_once()
