"""
Stream yelp_academic_dataset_business.json and write a filtered venues seed file.

Run from the project root:
    python data/build_catalog.py

Output: data/venues_seed.json  (one JSON object per line)
"""
import json
import sys
from pathlib import Path
from typing import Optional


YELP_DIR = Path("yelp_dataset")
OUTPUT_PATH = Path("data/venues_seed.json")

# Categories drawn from the Yelp taxonomy that match Perfect Day's event/celebration
# focus (restaurants, venues, entertainment, catering, active experiences).
RELEVANT_TERMS: frozenset[str] = frozenset({
    "restaurants",
    "food",
    "bars",
    "nightlife",
    "bakeries",
    "venues",
    "event planning",
    "event spaces",
    "active life",
    "arts & entertainment",
    "entertainment",
    "caterers",
    "coffee & tea",
    "hotels",
    "breakfast & brunch",
    "specialty food",
    "desserts",
    "fitness & instruction",
    "music venue",
    "comedy",
    "karaoke",
    "brewery",
    "winery",
    "wineries",
    "breweries",
})


def is_relevant(categories: str) -> bool:
    low = categories.lower()
    return any(term in low for term in RELEVANT_TERMS)


def primary_category(categories: str) -> str:
    """Return the first category token that matches a relevant term, else the first token."""
    parts = [c.strip() for c in categories.split(",") if c.strip()]
    for part in parts:
        if any(term in part.lower() for term in RELEVANT_TERMS):
            return part
    return parts[0] if parts else "other"


def parse_price_level(attributes: Optional[dict]) -> Optional[int]:
    if not attributes:
        return None
    raw = attributes.get("RestaurantsPriceRange2")
    if raw is None:
        return None
    try:
        val = int(raw)
        return val if 1 <= val <= 4 else None
    except (ValueError, TypeError):
        return None


def map_business(row: dict) -> Optional[dict]:
    categories = row.get("categories") or ""
    if not is_relevant(categories):
        return None
    lat = row.get("latitude")
    lng = row.get("longitude")
    if lat is None or lng is None:
        return None
    return {
        "business_id": row["business_id"],
        "name": row["name"],
        "category": primary_category(categories),
        "price_level": parse_price_level(row.get("attributes")),
        "rating": row.get("stars"),
        "location": {"lat": lat, "lng": lng},
        "max_capacity": None,
    }


def build_catalog() -> None:
    input_path = YELP_DIR / "yelp_academic_dataset_business.json"
    if not input_path.exists():
        sys.exit(f"Business file not found: {input_path}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    kept = 0
    with input_path.open("r", encoding="utf-8") as fh, \
         OUTPUT_PATH.open("w", encoding="utf-8") as out:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            venue = map_business(row)
            if venue is not None:
                out.write(json.dumps(venue) + "\n")
                kept += 1

    pct = 100 * kept / max(total, 1)
    print(f"Processed {total:,} businesses → kept {kept:,} ({pct:.1f}%)")
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    build_catalog()
