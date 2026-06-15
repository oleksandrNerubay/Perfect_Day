from unittest.mock import MagicMock, patch
import json
import pytest


def _make_mock_rep() -> MagicMock:
    mock_rep = MagicMock()
    mock_rep.identify.return_value = {
        "intent": "event_venue_search",
        "confidence": 0.94,
        "entities": {"occasion": "birthday", "category": "Bars",
                     "has_price": False, "group_size": None, "venue_name": None},
        "text": "I need a bar for my birthday party",
    }
    mock_rep.process.return_value = [
        {"business_id": "abc1", "name": "The Rooftop Bar", "category": "Bars",
         "price_level": 2, "rating": 4.5, "location": {"lat": 34.05, "lng": -118.24}},
    ]
    mock_rep.respond.return_value = "The Rooftop Bar is an excellent choice for your birthday!"
    return mock_rep


@pytest.fixture()
def client():
    # Import create_app before _get_rep is ever called so the project-root ml/
    # package never enters sys.path during the test run.
    from app import create_app
    with patch("routes.recommend._get_rep", return_value=_make_mock_rep()):
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c


def test_recommend_happy_path(client):
    resp = client.post(
        "/recommend",
        data=json.dumps({"text": "I need a bar for my birthday party", "user_id": "u1"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["intent"] == "event_venue_search"
    assert body["confidence"] == 0.94
    assert body["reply"] == "The Rooftop Bar is an excellent choice for your birthday!"
    assert len(body["candidates"]) == 1
    assert body["candidates"][0]["name"] == "The Rooftop Bar"


def test_recommend_missing_text(client):
    resp = client.post("/recommend", data=json.dumps({}), content_type="application/json")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code"] == "missing_text"


def test_recommend_text_too_long(client):
    resp = client.post(
        "/recommend",
        data=json.dumps({"text": "x" * 2001}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "text_too_long"


def test_recommend_representative_error(client):
    with patch("routes.recommend._recommend_safe", return_value={"error": "model exploded", "code": "representative_error"}):
        resp = client.post(
            "/recommend",
            data=json.dumps({"text": "find me a venue"}),
            content_type="application/json",
        )
    assert resp.status_code == 500
    assert resp.get_json()["code"] == "representative_error"
