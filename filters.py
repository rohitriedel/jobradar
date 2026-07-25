"""Keep only jobs that (a) look like a Scrum Master / coach role by title and
(b) are written in English or German. We also record WHICH language, so the
digest can put English roles first."""

from langdetect import detect, LangDetectException

from config import TITLE_KEYWORDS, KEEP_LANGUAGES


def title_matches(title):
    t = (title or "").lower()
    return any(kw in t for kw in TITLE_KEYWORDS)


def detect_language(job):
    """Return 'en', 'de', or None (unknown / other language)."""
    sample = f"{job.get('title', '')}. {job.get('description', '')}".strip()
    if not sample:
        return None
    try:
        lang = detect(sample)
    except LangDetectException:
        return None
    return lang if lang in KEEP_LANGUAGES else None


def annotate_and_keep(jobs):
    """Filter to relevant + EN/DE roles, tagging each kept job with its
    language. English roles are returned first."""
    kept = []
    for j in jobs:
        if not title_matches(j.get("title")):
            continue
        lang = detect_language(j)
        if lang is None:
            continue
        j["language"] = lang
        kept.append(j)
    # English first, then German
    kept.sort(key=lambda j: 0 if j["language"] == "en" else 1)
    return kept
