"""
Generate customer-representative training conversations from Yelp reviews.
Each conversation: one user query derived from business metadata + one agent reply
derived from review text. Stored separately for classification reinforcement training.

Run from project root:
    python ml/build_rep_training.py

Output: data/rep_conversations.jsonl
"""
import hashlib
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ml.rep_constants import (
    AGENT_TEMPLATES, OCCASION_PATTERNS, PRICE_PATTERNS,
    PRICE_DESC, RELEVANT_TERMS, USER_TEMPLATES,
)

YELP_DIR    = Path("yelp_dataset")
OUTPUT_PATH = Path("data/rep_conversations.jsonl")
CONV_TARGET = 100_000
SYNTH_EACH  = 400
RANDOM_SEED = 42
KNOWN_REVIEW_COUNT = 6_990_280   # from pretrain run; avoids a full pre-count pass


def load_businesses() -> dict[str, dict]:
    path = YELP_DIR / "yelp_academic_dataset_business.json"
    if not path.exists():
        sys.exit(f"Business file not found: {path}")
    businesses: dict[str, dict] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            cats = row.get("categories") or ""
            if not any(t in cats.lower() for t in RELEVANT_TERMS):
                continue
            cat_list = [c.strip() for c in cats.split(",") if c.strip()]
            display = next(
                (c for c in cat_list if any(t in c.lower() for t in RELEVANT_TERMS)),
                cat_list[0] if cat_list else "Venue",
            )
            price_raw = (row.get("attributes") or {}).get("RestaurantsPriceRange2")
            try:
                price: Optional[int] = int(price_raw) if price_raw else None
            except (ValueError, TypeError):
                price = None
            businesses[row["business_id"]] = {
                "name": row["name"],
                "display_category": display,
                "price_level": price,
                "rating": row.get("stars"),
            }
    print(f"Loaded {len(businesses):,} relevant businesses")
    return businesses


def detect_occasion(text: str) -> Optional[str]:
    low = text.lower()
    for occasion, patterns in OCCASION_PATTERNS.items():
        if any(p in low for p in patterns):
            return occasion
    return None


def detect_price_mention(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in PRICE_PATTERNS)


def extract_highlight(text: str, max_len: int = 180) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    for sent in sentences:
        sent = sent.strip()
        if len(sent) >= 30:
            return sent[:max_len] + ("..." if len(sent) > max_len else "")
    return text[:max_len].strip() + "..."


def assign_intent(stars: float, occasion: Optional[str], has_price: bool) -> str:
    if stars <= 2:
        return "complaint"
    if occasion:
        return "event_venue_search"
    if has_price and stars >= 3:
        return "price_inquiry"
    if stars >= 4:
        return "recommendation_request"
    return "venue_inquiry"


def make_user_turn(
    intent: str,
    occasion: Optional[str],
    category: str,
    name: str,
    rng: random.Random,
) -> str:
    templates = USER_TEMPLATES.get(intent, USER_TEMPLATES["general_inquiry"])
    tmpl = rng.choice(templates)
    return tmpl.format(
        category=category,
        occasion=(occasion or "special event").replace("_", " "),
        name=name,
    )


def make_agent_turn(
    intent: str,
    name: str,
    category: str,
    stars: float,
    price_level: Optional[int],
    highlight: str,
    occasion: Optional[str],
) -> str:
    if intent == "greeting":
        return AGENT_TEMPLATES["greeting"]
    if intent == "general_inquiry":
        return AGENT_TEMPLATES["general"]

    occasion_suffix = (
        f" It would be a great fit for your {occasion.replace('_', ' ')}!"
        if occasion and intent == "event_venue_search" else ""
    )
    price_desc = PRICE_DESC.get(price_level, "reasonably priced") if price_level else "variably priced"

    if intent == "price_inquiry":
        key = "price_positive" if stars >= 4 else "price_negative"
        return AGENT_TEMPLATES[key].format(
            name=name, price_desc=price_desc, stars=int(stars), highlight=highlight,
        )

    sentiment = "positive" if stars >= 4 else ("negative" if stars <= 2 else "neutral")
    return AGENT_TEMPLATES[sentiment].format(
        name=name, category=category, stars=int(stars),
        highlight=highlight, occasion_suffix=occasion_suffix,
    )


def make_conversation(
    review: dict,
    business: dict,
    rng: random.Random,
) -> Optional[dict]:
    text = (review.get("text") or "").strip()
    if not text:
        return None
    stars     = float(review.get("stars", 3))
    occasion  = detect_occasion(text)
    has_price = detect_price_mention(text)
    highlight = extract_highlight(text)
    intent    = assign_intent(stars, occasion, has_price)
    category  = business["display_category"]
    name      = business["name"]
    sentiment = "positive" if stars >= 4 else ("negative" if stars <= 2 else "neutral")

    return {
        "conversation_id":  f"yelp_{review['review_id']}",
        "source":           "yelp_review",
        "source_review_id": review["review_id"],
        "business_id":      review["business_id"],
        "turns": [
            {"role": "user",  "text": make_user_turn(intent, occasion, category, name, rng)},
            {"role": "agent", "text": make_agent_turn(intent, name, category, stars,
                                                       business.get("price_level"), highlight, occasion)},
        ],
        "labels": {
            "intent":      intent,
            "sentiment":   sentiment,
            "occasion":    occasion,
            "category":    category,
            "stars":       int(stars),
            "price_level": business.get("price_level"),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_synth_conversations(n_each: int = SYNTH_EACH) -> list[dict]:
    synth: list[dict] = []
    for intent in ("greeting", "general_inquiry"):
        agent_text = AGENT_TEMPLATES["greeting" if intent == "greeting" else "general"]
        templates  = USER_TEMPLATES[intent]
        cycle      = (templates * (n_each // len(templates) + 1))[:n_each]
        for i, user_text in enumerate(cycle):
            uid = hashlib.md5(f"synth_{intent}_{i}".encode()).hexdigest()[:8]
            synth.append({
                "conversation_id":  f"synth_{intent}_{uid}",
                "source":           "synthetic",
                "source_review_id": None,
                "business_id":      None,
                "turns": [
                    {"role": "user",  "text": user_text},
                    {"role": "agent", "text": agent_text},
                ],
                "labels": {
                    "intent": intent, "sentiment": "neutral",
                    "occasion": None, "category": None, "stars": None, "price_level": None,
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
    return synth


def _stream_review_convs(
    businesses: dict,
    review_path: Path,
    out_path: Path,
    target: int,
    sample_rate: float,
    rng: random.Random,
) -> int:
    written = 0
    with review_path.open("r", encoding="utf-8") as fh, \
         out_path.open("w", encoding="utf-8") as out:
        for line in fh:
            if written >= target:
                break
            line = line.strip()
            if not line or rng.random() > sample_rate:
                continue
            try:
                review = json.loads(line)
            except json.JSONDecodeError:
                continue
            biz = businesses.get(review.get("business_id", ""))
            if biz is None:
                continue
            conv = make_conversation(review, biz, rng)
            if conv is not None:
                out.write(json.dumps(conv) + "\n")
                written += 1
    return written


def build_training_data() -> None:
    rng = random.Random(RANDOM_SEED)
    businesses = load_businesses()

    sample_rate = min(1.0, (CONV_TARGET * 1.6) / KNOWN_REVIEW_COUNT)
    print(f"Sample rate: {sample_rate:.4f}  (target: {CONV_TARGET:,} conversations)")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    review_path = YELP_DIR / "yelp_academic_dataset_review.json"
    print("Streaming reviews → generating conversations...")
    written = _stream_review_convs(businesses, review_path, OUTPUT_PATH, CONV_TARGET, sample_rate, rng)
    print(f"Review-derived conversations written: {written:,}")

    synth = generate_synth_conversations()
    with OUTPUT_PATH.open("a", encoding="utf-8") as out:
        for conv in synth:
            out.write(json.dumps(conv) + "\n")

    total = written + len(synth)
    print(f"Total conversations (incl. {len(synth)} synthetic): {total:,}")
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    build_training_data()
