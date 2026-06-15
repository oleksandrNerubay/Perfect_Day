"""
Train the intent classifier for the customer representative pipeline.

Reads data/rep_conversations.jsonl → trains TF-IDF + LogisticRegression
on the user turn text → intent label mapping.

Run from project root:
    python ml/rep_classifier.py

Output: models/rep_intent_clf.joblib
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from ml.rep_constants import INTENT_LABELS

CONV_PATH  = Path("data/rep_conversations.jsonl")
MODEL_PATH = Path("models/rep_intent_clf.joblib")
RANDOM_SEED = 42


def load_training_data() -> tuple[list[str], list[str]]:
    if not CONV_PATH.exists():
        sys.exit(f"Conversations file not found: {CONV_PATH}  — run build_rep_training.py first")
    texts:  list[str] = []
    labels: list[str] = []
    with CONV_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            turns = doc.get("turns") or []
            intent = (doc.get("labels") or {}).get("intent", "")
            if not turns or not intent:
                continue
            user_text = next((t["text"] for t in turns if t.get("role") == "user"), "")
            if user_text and intent in INTENT_LABELS:
                texts.append(user_text)
                labels.append(intent)
    return texts, labels


def print_class_balance(labels: list[str]) -> None:
    from collections import Counter
    counts = Counter(labels)
    total  = len(labels)
    print("\n--- Class balance ---")
    for intent in INTENT_LABELS:
        n = counts.get(intent, 0)
        print(f"  {intent:<25s} {n:>7,}  ({100*n/total:.1f}%)")
    print(f"  {'TOTAL':<25s} {total:>7,}")


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=60_000,
            sublinear_tf=True,
            min_df=2,
        )),
        ("clf", LogisticRegression(
            C=4.0,
            max_iter=500,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )),
    ])


def evaluate(pipe: Pipeline, X_val: list[str], y_val: list[str]) -> None:
    y_pred = pipe.predict(X_val)
    print("\n--- Classification report (holdout) ---")
    print(classification_report(y_val, y_pred, target_names=sorted(set(y_val)), digits=3))


def save_model(pipe: Pipeline, le: LabelEncoder) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipe, "label_encoder": le, "intent_labels": INTENT_LABELS}, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


def train() -> None:
    print("Loading training data...")
    texts, labels = load_training_data()
    print(f"Loaded {len(texts):,} samples across {len(set(labels))} intent classes")
    print_class_balance(labels)

    le = LabelEncoder().fit(labels)

    X_train, X_val, y_train, y_val = train_test_split(
        texts, labels, test_size=0.15, random_state=RANDOM_SEED, stratify=labels,
    )
    print(f"\nTrain: {len(X_train):,}  Val: {len(X_val):,}")

    print("Training TF-IDF + LogisticRegression...")
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    evaluate(pipe, X_val, y_val)
    save_model(pipe, le)


if __name__ == "__main__":
    train()
