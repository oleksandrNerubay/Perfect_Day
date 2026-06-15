"""
CustomerRepresentative — the three-stage pipeline:
  1. identify(text)  → intent + entities
  2. process(intent, entities, user_id) → ranked venue candidates from MongoDB
  3. respond(intent, entities, candidates) → reply string

Load once, call per request. Designed to be imported by Flask routes.

Usage:
    import sys; sys.path.insert(0, "/path/to/perfectDay")  # if needed
    from ml.representative import CustomerRepresentative
    rep = CustomerRepresentative()
    intent_data = rep.identify("I need a bar for my birthday party")
    candidates  = rep.process(**intent_data)
    reply       = rep.respond(**intent_data, candidates=candidates)
"""
import re
import sys
from pathlib import Path
from typing import Optional

import joblib
from pymongo import MongoClient

from ml.rep_constants import (
    AGENT_TEMPLATES, OCCASION_PATTERNS, PRICE_PATTERNS,
    PRICE_DESC, RELEVANT_TERMS,
)

_PROJECT_ROOT = Path(__file__).parent.parent
_MODEL_CLF    = _PROJECT_ROOT / "models" / "rep_intent_clf.joblib"
_MODEL_AFF    = _PROJECT_ROOT / "models" / "affinity_warmstart.joblib"

_CATEGORY_KEYWORDS: dict[str, str] = {
    "restaurant":   "Restaurants", "food":    "Food",
    "bar":          "Bars",        "bars":    "Bars",
    "cafe":         "Coffee & Tea","coffee":  "Coffee & Tea",
    "venue":        "Venues & Event Spaces",
    "event space":  "Venues & Event Spaces",
    "bakery":       "Bakeries",    "bakeries":"Bakeries",
    "catering":     "Caterers",    "caterer": "Caterers",
    "hotel":        "Hotels",
    "entertainment":"Arts & Entertainment",
    "nightclub":    "Nightlife",   "nightlife":"Nightlife",
    "brewery":      "Breweries",   "winery":  "Wineries",
}

_GROUP_RE = re.compile(r"(?:party|group|table) of (\d+)|(\d+) (?:people|guests|persons)", re.I)

# Matches "about X", "at X", "is X", "called X" where X starts with a capital — venue name hint.
_VENUE_NAME_RE = re.compile(
    r"\b(?:about|at|is|called|named|review(?:s)? of)\s+([A-Z][A-Za-z0-9 &'.]+?)(?=[?,!.]|\s+(?:good|bad|worth|like|open|affordable|expensive|a\b|the\b)|$)",
)

# Rule-based negative sentiment — overrides a low-confidence classifier label to "complaint".
_NEGATIVE_TERMS: frozenset[str] = frozenset({
    "terrible", "awful", "horrible", "worst", "disgusting", "disappointing",
    "never again", "1 star", "one star", "zero stars", "wasted my",
    "do not go", "stay away", "rip off", "ripped off", "waste of money",
    "dreadful", "abysmal", "pathetic", "unacceptable", "poor service",
})


class CustomerRepresentative:

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017",
        mongo_db:  str = "perfectday",
    ) -> None:
        if not _MODEL_CLF.exists():
            sys.exit(f"Intent classifier not found: {_MODEL_CLF} — run rep_classifier.py first")
        clf_bundle  = joblib.load(_MODEL_CLF)
        self._pipe  = clf_bundle["pipeline"]

        self._aff_model = None
        self._aff_features: list[str] = []
        if _MODEL_AFF.exists():
            aff = joblib.load(_MODEL_AFF)
            self._aff_model    = aff.get("model")
            self._aff_features = aff.get("feature_names", [])

        self._db = MongoClient(mongo_uri)[mongo_db]

    def identify(self, text: str) -> dict:
        """Stage 1 — classify intent and extract entities from raw user input."""
        proba      = self._pipe.predict_proba([text])[0]
        classes    = self._pipe.classes_
        intent     = classes[proba.argmax()]
        confidence = float(proba.max())

        # Rule-based override: strongly negative language at low classifier confidence
        # signals a complaint the template-trained model hasn't seen in this phrasing.
        if confidence < 0.70 and self._has_negative_sentiment(text):
            intent     = "complaint"
            confidence = min(confidence + 0.25, 0.88)

        entities = self._extract_entities(text)
        return {"intent": intent, "confidence": confidence, "entities": entities, "text": text}

    def _has_negative_sentiment(self, text: str) -> bool:
        low = text.lower()
        return any(term in low for term in _NEGATIVE_TERMS)

    def process(
        self,
        intent: str,
        entities: dict,
        user_id: Optional[str] = None,
        **_kwargs,
    ) -> list[dict]:
        """Stage 2 — query MongoDB venues filtered by entities, ranked by rating + affinity."""
        if intent in ("greeting", "general_inquiry"):
            return []
        candidates = self._query_venues(entities)
        return self._rank(candidates, entities)

    def respond(
        self,
        intent: str,
        entities: dict,
        candidates: list[dict],
        **_kwargs,
    ) -> str:
        """Stage 3 — generate a natural-language reply."""
        if intent == "greeting":
            return AGENT_TEMPLATES["greeting"]
        if intent == "general_inquiry":
            return AGENT_TEMPLATES["general"]
        if not candidates:
            return self._no_results_reply(intent, entities)
        top = candidates[0]
        return self._format_reply(intent, entities, top, candidates)

    def _extract_entities(self, text: str) -> dict:
        low = text.lower()
        occasion = next(
            (occ for occ, patterns in OCCASION_PATTERNS.items() if any(p in low for p in patterns)),
            None,
        )
        category = next(
            (_CATEGORY_KEYWORDS[kw] for kw in _CATEGORY_KEYWORDS if kw in low),
            None,
        )
        has_price  = any(p in low for p in PRICE_PATTERNS)
        mg         = _GROUP_RE.search(text)
        group_size = int(mg.group(1) or mg.group(2)) if mg else None
        mn         = _VENUE_NAME_RE.search(text)
        venue_name = mn.group(1).strip() if mn else None
        return {
            "occasion":   occasion,
            "category":   category,
            "has_price":  has_price,
            "group_size": group_size,
            "venue_name": venue_name,
        }

    def _query_venues(self, entities: dict) -> list[dict]:
        q: dict = {}
        if entities.get("venue_name"):
            q["name"] = {"$regex": entities["venue_name"], "$options": "i"}
        elif entities.get("category"):
            q["category"] = {"$regex": entities["category"], "$options": "i"}
        limit  = 5 if entities.get("venue_name") else 20
        cursor = self._db.venues.find(q, {"_id": 0}).sort("rating", -1).limit(limit)
        return list(cursor)

    def _rank(self, venues: list[dict], entities: dict) -> list[dict]:
        if not venues or self._aff_model is None:
            return venues[:5]
        import numpy as np
        rows = []
        for v in venues:
            row = {
                "cat_in_history": 1.0,  # unknown at rank time; assume relevant since category-filtered
                "offer_rating":   float(v.get("rating") or 3.0),
                "price_level":    float(v.get("price_level") or float("nan")),
            }
            rows.append([row.get(f, float("nan")) for f in self._aff_features])
        X = np.array(rows, dtype=float)
        scores = self._aff_model.predict_proba(X)[:, 1]
        ranked = sorted(zip(scores, venues), key=lambda t: t[0], reverse=True)
        return [v for _, v in ranked[:5]]

    def _format_reply(
        self,
        intent: str,
        entities: dict,
        top: dict,
        all_candidates: list[dict],
    ) -> str:
        name      = top.get("name", "this venue")
        category  = top.get("category", "venue")
        stars     = top.get("rating", 0.0)
        pl        = top.get("price_level")
        occasion  = entities.get("occasion")
        price_desc = PRICE_DESC.get(pl, "variably priced") if pl else "variably priced"

        occasion_suffix = (
            f" It would be a great fit for your {occasion.replace('_', ' ')}!"
            if occasion and intent == "event_venue_search" else ""
        )
        sentiment = "positive" if stars >= 4 else ("negative" if stars <= 2 else "neutral")

        others_str = (
            " Other options include: "
            + ", ".join(v["name"] for v in all_candidates[1:4] if "name" in v)
            + "."
            if len(all_candidates) > 1 else ""
        )

        if intent == "complaint":
            return AGENT_TEMPLATES["complaint"].format(
                name=name, category=category, stars=int(stars), other_options=others_str,
            ).strip()

        if intent == "price_inquiry":
            key = "price_positive" if stars >= 4 else "price_negative"
            return (AGENT_TEMPLATES[key].format(
                name=name, price_desc=price_desc, stars=int(stars), highlight="",
            ) + others_str).strip()

        reply = AGENT_TEMPLATES[sentiment].format(
            name=name, category=category, stars=int(stars),
            highlight="", occasion_suffix=occasion_suffix,
        ).strip()
        return reply + others_str

    def _no_results_reply(self, intent: str, entities: dict) -> str:
        cat     = entities.get("category", "venue")
        occ     = entities.get("occasion", "")
        tail    = f" for your {occ.replace('_', ' ')}" if occ else ""
        return (
            f"I couldn't find a matching {cat}{tail} right now. "
            "Try broadening your search or let me know a different type of venue."
        )
