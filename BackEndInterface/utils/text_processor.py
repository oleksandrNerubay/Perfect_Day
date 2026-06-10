import re

STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "and",
    "or", "but", "i", "you", "me", "my", "we", "what", "how", "can", "do", "did",
}

WH_WORDS = {"what", "where", "when", "why", "who", "which", "whose", "whom"}
IMPERATIVE_VERBS = {"tell", "show", "open", "play", "turn", "set", "find", "go"}
GREETING_PHRASES = {"good morning", "good evening"}
GREETING_WORDS = {"hello", "hi", "hey"}

POSITIVE_WORDS = {"good", "great", "love", "happy", "nice", "thanks", "thank", "awesome", "please"}
NEGATIVE_WORDS = {"bad", "hate", "terrible", "awful", "wrong", "broken", "stop", "no"}

PROFANITY = {"damn", "crap", "hell", "ass", "bastard", "bitch", "shit", "fuck", "piss"}


def process(raw: str) -> dict:
    words = raw.lower().split()
    word_count = len(words)
    return {
        "text": _clean_text(raw),
        "keywords": _extract_keywords(words),
        "word_count": word_count,
        "intent": _detect_intent(raw.lower().strip()),
        "sentiment": _detect_sentiment(set(words)),
        "flagged": _is_flagged(raw, word_count),
    }


def _clean_text(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r" +", " ", text)
    if not text:
        return text
    text = text[0].upper() + text[1:]
    if text[-1] not in ".?!":
        text += "."
    return text


def _extract_keywords(words: list) -> list:
    seen = set()
    result = []
    for w in words:
        w = re.sub(r"[^a-z0-9]", "", w)
        if w and w not in STOPWORDS and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def _detect_intent(lower: str) -> str:
    first_word = lower.split()[0] if lower.split() else ""

    if first_word in WH_WORDS or lower.endswith("?"):
        return "question"

    if first_word in IMPERATIVE_VERBS:
        return "command"

    for phrase in GREETING_PHRASES:
        if phrase in lower:
            return "greeting"

    if first_word in GREETING_WORDS:
        return "greeting"

    return "statement"


def _detect_sentiment(word_set: set) -> str:
    if word_set & POSITIVE_WORDS:
        return "positive"
    if word_set & NEGATIVE_WORDS:
        return "negative"
    return "neutral"


def _is_flagged(raw: str, word_count: int) -> bool:
    if word_count > 300:
        return True
    return bool(set(raw.lower().split()) & PROFANITY)
