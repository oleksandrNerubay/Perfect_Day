"""
Build a warm-start affinity model from Yelp review + business data.

This is a transfer warm-start, to be fine-tuned on real impression logs,
not the production engagement model.

Run from the project root:
    python ml/pretrain_affinity.py

Output: models/affinity_warmstart.joblib
"""
import json
import random
import sys
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


YELP_DIR = Path("yelp_dataset")
MODEL_PATH = Path("models/affinity_warmstart.joblib")
SAMPLE_TARGET = 500_000
RANDOM_SEED = 42

RELEVANT_TERMS: frozenset[str] = frozenset({
    "restaurants", "food", "bars", "nightlife", "bakeries",
    "venues", "event planning", "event spaces", "active life",
    "arts & entertainment", "entertainment", "caterers",
    "coffee & tea", "hotels", "breakfast & brunch", "specialty food",
    "desserts", "fitness & instruction", "music venue", "comedy",
    "karaoke", "brewery", "winery", "wineries", "breweries",
})

# Feature names must stay in sync with recommender._featurize.
FEATURE_NAMES: list[str] = ["cat_in_history", "offer_rating", "price_level", "distance_km"]


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
            price_raw = (row.get("attributes") or {}).get("RestaurantsPriceRange2")
            try:
                price: Optional[int] = int(price_raw) if price_raw else None
            except (ValueError, TypeError):
                price = None
            businesses[row["business_id"]] = {
                "categories": frozenset(c.strip().lower() for c in cats.split(",") if c.strip()),
                "price_level": price,
                "rating": row.get("stars"),
            }

    print(f"Loaded {len(businesses):,} relevant businesses")
    return businesses


def build_user_histories_and_count(
    businesses: dict[str, dict],
) -> tuple[dict[str, dict[str, int]], int]:
    """Single pass: build per-user category->count maps and total review line count.

    Counts how many distinct businesses each user reviewed per category.
    count > 1 for a category means the user has OTHER reviews in that category
    beyond the current one being evaluated, giving a leakage-free cat_in_history.
    """
    path = YELP_DIR / "yelp_academic_dataset_review.json"
    if not path.exists():
        sys.exit(f"Review file not found: {path}")

    user_cats: dict[str, dict[str, int]] = {}
    total = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            biz = businesses.get(row.get("business_id", ""))
            if biz is None:
                continue
            uid = row["user_id"]
            if uid not in user_cats:
                user_cats[uid] = {}
            for cat in biz["categories"]:
                user_cats[uid][cat] = user_cats[uid].get(cat, 0) + 1

    print(f"Scanned {total:,} reviews → built history for {len(user_cats):,} users")
    return user_cats, total


def sample_training_rows(
    businesses: dict[str, dict],
    user_histories: dict[str, dict[str, int]],
    sample_rate: float,
    rng: random.Random,
) -> list[dict]:
    """Second pass: probabilistic sample; build one feature dict per row."""
    path = YELP_DIR / "yelp_academic_dataset_review.json"
    rows: list[dict] = []

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if rng.random() > sample_rate:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            biz = businesses.get(row.get("business_id", ""))
            if biz is None:
                continue
            # count > 1 means the user reviewed at least one OTHER business in that category,
            # so the category genuinely appears in their prior history (no leakage).
            cat_counts = user_histories.get(row["user_id"], {})
            cat_in_hist = int(any(cat_counts.get(cat, 0) > 1 for cat in biz["categories"]))
            rows.append({
                "cat_in_history": cat_in_hist,
                "offer_rating": biz["rating"],
                "price_level": biz["price_level"],
                "distance_km": float("nan"),  # no user location available in Yelp data
                "label": int(row["stars"] >= 4),
            })

    return rows


def print_summary(X: np.ndarray, y: np.ndarray) -> None:
    pos = int(y.sum())
    total = len(y)
    print("\n--- Class balance ---")
    print(f"  positive (>=4 stars): {pos:,} ({100*pos/total:.1f}%)")
    print(f"  negative (<4 stars):  {total-pos:,} ({100*(total-pos)/total:.1f}%)")
    print("\n--- Feature ranges (non-NaN values, after all-NaN columns dropped) ---")
    for i in range(X.shape[1]):
        col = X[:, i]
        valid = col[~np.isnan(col)]
        if len(valid) == 0:
            print(f"  col[{i}]: all NaN")
        else:
            print(f"  col[{i}]: min={valid.min():.3f}  max={valid.max():.3f}  mean={valid.mean():.3f}")


def build_feature_matrix(records: list[dict]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    X_full = np.array(
        [
            [
                r["cat_in_history"],
                r["offer_rating"] if r["offer_rating"] is not None else float("nan"),
                r["price_level"] if r["price_level"] is not None else float("nan"),
                r["distance_km"],
            ]
            for r in records
        ],
        dtype=float,
    )
    y = np.array([r["label"] for r in records], dtype=np.int8)

    # sklearn HistGBT (tested on 1.9.0) crashes when binning an all-NaN column
    # because sliding_window_view needs at least 2 distinct values.
    # distance_km is all NaN for warmstart (no user location in Yelp data).
    # Drop such columns; fine-tune with real distances on live impression logs.
    valid_cols = [i for i in range(X_full.shape[1]) if not np.all(np.isnan(X_full[:, i]))]
    active_features = [FEATURE_NAMES[i] for i in valid_cols]
    if len(valid_cols) < len(FEATURE_NAMES):
        dropped = [FEATURE_NAMES[i] for i in range(len(FEATURE_NAMES)) if i not in valid_cols]
        print(f"  Dropped all-NaN features (add at fine-tune time): {dropped}")
    return X_full[:, valid_cols], y, active_features


def fit_and_save(X: np.ndarray, y: np.ndarray, active_features: list[str]) -> None:
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    clf = HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.05,
        max_depth=4,
        min_samples_leaf=50,
        random_state=RANDOM_SEED,
    )
    clf.fit(X_train, y_train)
    val_proba = clf.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, val_proba)
    print(f"\nHoldout AUC: {auc:.4f}  (n_val={len(y_val):,})")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": clf, "feature_names": active_features, "all_features": FEATURE_NAMES}, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}  (features used: {active_features})")


def train() -> None:
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    rng = random.Random(RANDOM_SEED)

    print("Step 1/4 — loading relevant businesses...")
    businesses = load_businesses()

    print("Step 2/4 — building user category histories (pass 1 of reviews)...")
    user_histories, total_reviews = build_user_histories_and_count(businesses)

    sample_rate = min(1.0, SAMPLE_TARGET / max(total_reviews, 1))
    print(f"\nTotal review lines: {total_reviews:,} → sample rate: {sample_rate:.4f}")

    print("Step 3/4 — sampling training rows (pass 2 of reviews)...")
    records = sample_training_rows(businesses, user_histories, sample_rate, rng)
    print(f"Sampled {len(records):,} training rows")

    print("Step 4/4 — training HistGradientBoostingClassifier...")
    X, y, active_features = build_feature_matrix(records)
    print_summary(X, y)
    fit_and_save(X, y, active_features)


if __name__ == "__main__":
    train()
