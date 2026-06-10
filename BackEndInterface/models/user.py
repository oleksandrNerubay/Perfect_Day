from datetime import datetime, timezone


def build_user(email: str, hashed_password: str, age=None, interests=None) -> dict:
    if interests is None:
        interests = []

    now = datetime.now(timezone.utc)
    return {
        "email": email,
        "password": hashed_password,
        "age": age,
        "interests": interests,
        "engagement": {
            "session_count": 0,
            "total_time_spent_sec": 0,
            "avg_session_duration_sec": 0.0,
            "last_active": now,
        },
        "recommendation_profile": {
            "interest_weights": {i: 1.0 for i in interests},
            "last_recommended": [],
            "feedback_scores": {},
        },
        "ml_features": {
            "days_since_signup": 0,
            "churn_risk_score": None,
            "segment": None,
        },
        "created_at": now,
        "updated_at": now,
    }
