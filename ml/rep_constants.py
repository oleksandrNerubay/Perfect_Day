"""
Shared constants for the customer representative pipeline.
Imported by build_rep_training.py, rep_classifier.py, and representative.py.
"""
from __future__ import annotations

INTENT_LABELS: list[str] = [
    "event_venue_search",     # "I need a place for my birthday party"
    "recommendation_request", # "What's a good bar nearby?"
    "price_inquiry",          # "How expensive is XYZ?"
    "venue_inquiry",          # "Tell me about ABC place"
    "complaint",              # "I had a bad experience"
    "greeting",               # "Hi / Hello"
    "general_inquiry",        # "What can you help me with?"
]

# Ordered most-specific first so the first match wins.
OCCASION_PATTERNS: dict[str, list[str]] = {
    "wedding":       ["wedding", "bridal", "bachelorette", "bachelor", "rehearsal dinner"],
    "graduation":    ["graduation", "graduate", "grad party", "grad dinner"],
    "corporate":     ["corporate event", "company event", "work event", "office party",
                      "team outing", "work lunch", "business meeting", "company party"],
    "anniversary":   ["anniversary", "date night"],
    "baby_shower":   ["baby shower", "gender reveal"],
    "holiday_party": ["holiday party", "christmas party", "new year's eve", "halloween party"],
    "birthday":      ["birthday", "bday", "b-day", "turning "],
    "general_party": ["party", "celebration", "get together", "gathering", "group dinner"],
}

PRICE_PATTERNS: list[str] = [
    "expensive", "pricey", "overpriced", "cheap", "affordable",
    "reasonable", "great value", "budget", "per person", "pricing",
]

PRICE_DESC: dict[int, str] = {
    1: "budget-friendly (under $10/person)",
    2: "moderately priced ($11–$30/person)",
    3: "upscale ($31–$60/person)",
    4: "fine dining ($60+/person)",
}

RELEVANT_TERMS: frozenset[str] = frozenset({
    "restaurants", "food", "bars", "nightlife", "bakeries",
    "venues", "event planning", "event spaces", "active life",
    "arts & entertainment", "entertainment", "caterers",
    "coffee & tea", "hotels", "breakfast & brunch", "specialty food",
    "desserts", "fitness & instruction", "music venue", "comedy",
    "karaoke", "brewery", "winery", "wineries", "breweries",
})

# {category}, {occasion}, {name} are filled at generation time.
USER_TEMPLATES: dict[str, list[str]] = {
    "event_venue_search": [
        "I'm looking for a {category} for a {occasion}. Any recommendations?",
        "Can you suggest a good {category} for a {occasion} celebration?",
        "We're planning a {occasion} and need a great {category}.",
        "Help me find a {category} suitable for a {occasion}.",
        "What {category} would you recommend for a {occasion}?",
    ],
    "recommendation_request": [
        "What's a good {category} around here?",
        "Can you recommend a top-rated {category}?",
        "I'm looking for a great {category} — what do you suggest?",
        "What {category} is worth visiting?",
        "Suggest a quality {category} for me.",
    ],
    "price_inquiry": [
        "How expensive is {name}? Is it worth it?",
        "What's the price range at {name}?",
        "Is {name} affordable for a group?",
        "Tell me about the pricing at {name}.",
        "Is {name} budget-friendly?",
    ],
    "venue_inquiry": [
        "What can you tell me about {name}?",
        "Is {name} a good place to visit?",
        "What do customers say about {name}?",
        "Tell me more about {name}.",
        "What's {name} like?",
    ],
    "complaint": [
        "I had a disappointing experience at {name}. Can you help?",
        "What should I know about issues at {name}?",
        "I'm hearing bad things about {name} — is that accurate?",
        "Why did {name} let people down?",
    ],
    "greeting": [
        "Hi! I need help planning an event.",
        "Hello, can you assist me with event planning?",
        "Hey there, I'm looking for venue recommendations.",
        "Hi, I'd like help finding a good place for my group.",
        "Hello! What can Perfect Day help me with?",
    ],
    "general_inquiry": [
        "What services do you offer for event planning?",
        "How can you help me plan my day?",
        "I need help planning an outing — where do I start?",
        "Can you walk me through what Perfect Day does?",
        "What kinds of venues can you help me find?",
    ],
}

# {name}, {category}, {stars}, {price_desc}, {highlight}, {occasion_suffix}
AGENT_TEMPLATES: dict[str, str] = {
    "positive": (
        "{name} is an excellent choice! It's a highly-rated {category} with {stars} stars. "
        "{highlight}{occasion_suffix}"
    ),
    "neutral": (
        "{name} is a solid option — a {category} rated {stars} stars. {highlight}"
    ),
    "negative": (
        "Based on customer feedback, {name} has a {stars}-star rating and may not be the best "
        "choice. {highlight} I can suggest better alternatives if you'd like."
    ),
    "price_positive": (
        "{name} is {price_desc} and well regarded, with a {stars}-star rating. {highlight}"
    ),
    "price_negative": (
        "{name} is {price_desc}, but its {stars}-star rating suggests it may not justify "
        "the cost. {highlight}"
    ),
    "complaint": (
        "I'm sorry you had a disappointing experience! Let me suggest some better-rated options. "
        "{name} is a {stars}-star {category} that customers consistently recommend. "
        "{other_options}"
    ),
    "greeting": (
        "Hello! I'm your Perfect Day assistant. I can help you discover venues, restaurants, "
        "and event spaces tailored to your occasion and budget. What are you planning today?"
    ),
    "general": (
        "I can help you find and book venues for any occasion — birthdays, weddings, corporate "
        "events, and more. I match recommendations to your preferences and connect you with "
        "exclusive deals. What kind of event are you planning?"
    ),
}
