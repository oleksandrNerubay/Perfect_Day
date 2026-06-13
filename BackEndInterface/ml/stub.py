# DEV ONLY — do not use in production. Set ML_SERVICE_URL to the real service before any demo.
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.post("/classify")
def classify():
    return jsonify({
        "intent": "event_inquiry",
        "confidence": 0.9,
        "suggested_reply": "I can help with that! What city are you in?",
    })


if __name__ == "__main__":
    app.run(port=8001)
