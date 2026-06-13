import responses as resp_lib
import pytest
from ml.client import call_ml, call_ml_safe
import config


@resp_lib.activate
def test_call_ml_success():
    resp_lib.add(
        resp_lib.POST,
        f"{config.ML_SERVICE_URL}/classify",
        json={"intent": "event_inquiry", "confidence": 0.91, "suggested_reply": "What city?"},
        status=200,
    )
    result = call_ml("sid", "I need a venue", [])
    assert result["intent"] == "event_inquiry"
    assert result["confidence"] == 0.91


@resp_lib.activate
def test_call_ml_safe_on_timeout():
    resp_lib.add(
        resp_lib.POST,
        f"{config.ML_SERVICE_URL}/classify",
        body=Exception("timeout"),
    )
    result = call_ml_safe("sid", "some text", [])
    assert result["intent"] == "unknown"
    assert result["confidence"] == 0.0
    assert result["suggested_reply"] == ""


@resp_lib.activate
def test_call_ml_safe_on_http_error():
    resp_lib.add(
        resp_lib.POST,
        f"{config.ML_SERVICE_URL}/classify",
        status=500,
    )
    result = call_ml_safe("sid", "text", [])
    assert result["intent"] == "unknown"
