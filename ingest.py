"""
Ingest seed data into MongoDB.

Commands (run from project root):
    python ingest.py venues  [--seed data/venues_seed.json] [--dry-run] [--batch-size 500]
    python ingest.py convs   [--src  data/rep_conversations.jsonl] [--dry-run] [--batch-size 500]

Exits non-zero if skip rate exceeds 20% of input.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import os
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "perfectday")

SKIP_RATE_THRESHOLD = 0.20

REQUIRED_VENUE = {"business_id", "name", "category", "rating", "location"}
REQUIRED_CONV  = {"conversation_id", "turns", "labels"}


def get_db() -> "pymongo.database.Database":
    return MongoClient(MONGO_URI)[MONGO_DB]


def ensure_indexes(db) -> None:
    db.venues.create_index("business_id", unique=True)
    db.venues.create_index([("location.lat", 1), ("location.lng", 1)])
    db.venues.create_index("category")
    db.rep_conversations.create_index("conversation_id", unique=True)
    db.rep_conversations.create_index("labels.intent")
    db.rep_conversations.create_index("source_review_id")


def iter_jsonl(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    pass


def validate_venue(doc: dict) -> tuple[bool, str]:
    missing = REQUIRED_VENUE - doc.keys()
    if missing:
        return False, f"missing: {missing}"
    loc = doc.get("location") or {}
    if "lat" not in loc or "lng" not in loc:
        return False, "location.lat/lng missing"
    if not isinstance(doc.get("rating"), (int, float)):
        return False, "rating not numeric"
    return True, ""


def validate_conv(doc: dict) -> tuple[bool, str]:
    missing = REQUIRED_CONV - doc.keys()
    if missing:
        return False, f"missing: {missing}"
    turns = doc.get("turns") or []
    if len(turns) < 1:
        return False, "turns is empty"
    return True, ""


def _flush_batch(db, collection: str, batch: list[UpdateOne], key: str) -> int:
    if not batch:
        return 0
    try:
        result = getattr(db, collection).bulk_write(batch, ordered=False)
        return result.upserted_count + result.modified_count
    except BulkWriteError as exc:
        d = exc.details
        return d.get("nUpserted", 0) + d.get("nModified", 0)


def ingest_venues(seed: Path, dry_run: bool, batch_size: int) -> None:
    valid = skipped = upserted = 0
    batch: list[UpdateOne] = []
    db = None if dry_run else get_db()

    for doc in iter_jsonl(seed):
        ok, _ = validate_venue(doc)
        if not ok:
            skipped += 1
            continue
        valid += 1
        if not dry_run:
            doc["ingested_at"] = datetime.now(timezone.utc).isoformat()
            batch.append(UpdateOne({"business_id": doc["business_id"]}, {"$set": doc}, upsert=True))
            if len(batch) >= batch_size:
                upserted += _flush_batch(db, "venues", batch, "business_id")
                batch = []

    if not dry_run:
        upserted += _flush_batch(db, "venues", batch, "business_id")

    _report("venues", valid, skipped, upserted, dry_run)


def ingest_convs(src: Path, dry_run: bool, batch_size: int) -> None:
    valid = skipped = upserted = 0
    batch: list[UpdateOne] = []
    db = None if dry_run else get_db()

    for doc in iter_jsonl(src):
        ok, _ = validate_conv(doc)
        if not ok:
            skipped += 1
            continue
        valid += 1
        if not dry_run:
            doc["ingested_at"] = datetime.now(timezone.utc).isoformat()
            batch.append(UpdateOne(
                {"conversation_id": doc["conversation_id"]}, {"$set": doc}, upsert=True,
            ))
            if len(batch) >= batch_size:
                upserted += _flush_batch(db, "rep_conversations", batch, "conversation_id")
                batch = []

    if not dry_run:
        upserted += _flush_batch(db, "rep_conversations", batch, "conversation_id")

    _report("conversations", valid, skipped, upserted, dry_run)


def _report(label: str, valid: int, skipped: int, upserted: int, dry_run: bool) -> None:
    total = valid + skipped
    pct = 100 * skipped / max(total, 1)
    print(f"{label:15s}  valid={valid:,}  skipped={skipped:,} ({pct:.1f}%)", end="")
    if dry_run:
        print("  [dry-run — no writes]")
    else:
        print(f"  upserted/modified={upserted:,}")
    if pct > SKIP_RATE_THRESHOLD * 100:
        print(f"WARNING: skip rate {pct:.1f}% > {SKIP_RATE_THRESHOLD*100:.0f}% threshold.")
        if dry_run:
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_v = sub.add_parser("venues")
    p_v.add_argument("--seed", default="data/venues_seed.json", type=Path)
    p_v.add_argument("--dry-run", action="store_true")
    p_v.add_argument("--batch-size", type=int, default=500)

    p_c = sub.add_parser("convs")
    p_c.add_argument("--src", default="data/rep_conversations.jsonl", type=Path)
    p_c.add_argument("--dry-run", action="store_true")
    p_c.add_argument("--batch-size", type=int, default=500)

    args = parser.parse_args()
    src = args.seed if args.cmd == "venues" else args.src
    if not src.exists():
        sys.exit(f"File not found: {src}")

    if not args.dry_run:
        db = get_db()
        ensure_indexes(db)
        print(f"Connected: {MONGO_DB} @ {MONGO_URI}\n")

    if args.cmd == "venues":
        ingest_venues(args.seed, args.dry_run, args.batch_size)
    else:
        ingest_convs(args.src, args.dry_run, args.batch_size)


if __name__ == "__main__":
    main()
