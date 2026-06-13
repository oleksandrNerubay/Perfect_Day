import mongomock
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_mongo():
    with patch("db.client._client", mongomock.MongoClient()):
        yield


def test_create_and_end_session():
    from db.ops import create_session, end_session
    sid = create_session("user_1", {"locale": "en"})
    assert isinstance(sid, str) and len(sid) == 36

    result = end_session(sid)
    assert "duration_s" in result
    assert result["turn_count"] == 0


def test_end_session_not_found():
    from db.ops import end_session
    result = end_session("nonexistent-id")
    assert result.get("error") == "session_not_found"


def test_save_and_get_history():
    from db.ops import create_session, save_turn, get_history
    sid = create_session("user_2", {})
    save_turn(sid, "user", "Hello", confidence=0.95, words=[])
    save_turn(sid, "agent", "Hi there!", ml_reply="Hi there!")

    history = get_history(sid)
    assert len(history) == 2
    assert history[0]["speaker"] == "user"
    assert history[0]["turn_index"] == 0
    assert history[1]["speaker"] == "agent"
    assert history[1]["turn_index"] == 1
