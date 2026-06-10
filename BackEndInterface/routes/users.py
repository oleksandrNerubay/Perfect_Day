import traceback
import json
from flask import Blueprint, request, jsonify
import bcrypt
from db_postgres import get_conn

users_bp = Blueprint("users", __name__)


# ─── helpers ────────────────────────────────────────────────────────────────

def _seed_weights(interests: list[str]) -> dict:
    """Seed interest weights at 1.0 for each selected interest."""
    return {i: 1.0 for i in interests}


def _user_row_to_dict(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "age": row["age"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


def _profile_row_to_dict(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "user_id": str(row["user_id"]),
        "interests": row["interests"] or [],
        "interest_weights": row["interest_weights"] or {},
        "feedback_scores": row["feedback_scores"] or {},
        "session_count": row["session_count"],
        "total_time_spent_sec": row["total_time_spent_sec"],
        "segment": row["segment"],
        "last_active": row["last_active"].isoformat() if row["last_active"] else None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


# ─── /register ──────────────────────────────────────────────────────────────

@users_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "email and password are required"}), 400

        age = data.get("age")
        interests = data.get("interests", [])

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        weights = _seed_weights(interests)

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                # Insert user
                cur.execute(
                    """
                    INSERT INTO users (email, password_hash, age)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (email, hashed, age),
                )
                user_id = cur.fetchone()["id"]

                # Insert sample profile seeded from interests
                cur.execute(
                    """
                    INSERT INTO user_profiles
                        (user_id, interests, interest_weights, feedback_scores, segment)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        interests,
                        json.dumps(weights),
                        json.dumps({}),
                        _assign_segment(interests),
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                return jsonify({"error": "email already exists"}), 409
            raise

        return jsonify({"id": str(user_id)}), 201

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "internal server error"}), 500


def _assign_segment(interests: list[str]) -> str:
    """Naive segment assignment from interests for the sample profile."""
    active = {"Sports", "Fitness", "Nature", "Travel"}
    creative = {"Art", "Music", "Cinema", "Fashion"}
    tech = {"Tech", "Gaming"}
    if any(i in active for i in interests):
        return "active"
    if any(i in creative for i in interests):
        return "creative"
    if any(i in tech for i in interests):
        return "tech"
    return "general"


# ─── /login ─────────────────────────────────────────────────────────────────

@users_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "email and password are required"}), 400

        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
            row = cur.fetchone()

        if not row or not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            return jsonify({"error": "invalid credentials"}), 401

        return jsonify({"id": str(row["id"])}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "internal server error"}), 500


# ─── /user/<id> ─────────────────────────────────────────────────────────────

@users_bp.route("/user/<user_id>", methods=["GET"])
def get_user(user_id):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT id, email, age, created_at FROM users WHERE id = %s::uuid", (user_id,))
            user = cur.fetchone()
            if not user:
                return jsonify({"error": "user not found"}), 404

            cur.execute("SELECT * FROM user_profiles WHERE user_id = %s::uuid", (user_id,))
            profile = cur.fetchone()

        result = _user_row_to_dict(user)
        result["profile"] = _profile_row_to_dict(profile) if profile else None
        return jsonify(result), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "internal server error"}), 500


# ─── /user/<id>/feedback ────────────────────────────────────────────────────

@users_bp.route("/user/<user_id>/feedback", methods=["POST"])
def post_feedback(user_id):
    try:
        data = request.get_json() or {}
        item_id = data.get("item_id")
        score = data.get("score")

        if score not in (1, -1):
            return jsonify({"error": "score must be 1 or -1"}), 400
        if not item_id:
            return jsonify({"error": "item_id is required"}), 400

        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE user_profiles
                SET feedback_scores = feedback_scores || %s::jsonb,
                    updated_at = NOW()
                WHERE user_id = %s::uuid
                """,
                (json.dumps({item_id: score}), user_id),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return jsonify({"error": "user not found"}), 404
        conn.commit()

        return jsonify({"ok": True}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "internal server error"}), 500


# ─── /user/<id>/weights ─────────────────────────────────────────────────────

@users_bp.route("/user/<user_id>/weights", methods=["PATCH"])
def update_weights(user_id):
    try:
        data = request.get_json() or {}
        weights = data.get("interest_weights")

        if not isinstance(weights, dict):
            return jsonify({"error": "interest_weights must be a dict"}), 400

        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE user_profiles
                SET interest_weights = %s::jsonb,
                    updated_at = NOW()
                WHERE user_id = %s::uuid
                """,
                (json.dumps(weights), user_id),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return jsonify({"error": "user not found"}), 404
        conn.commit()

        return jsonify({"ok": True}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "internal server error"}), 500
