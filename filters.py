"""Keep only jobs that (a) look like a Scrum Master / coach / delivery role by
title and (b) are written in English or German. We also tag each kept job with
its language, designation category, and work mode (remote/hybrid/onsite), which
the page uses for its filters."""

from langdetect import detect, LangDetectException

from config import (TITLE_KEYWORDS, EXCLUDE_KEYWORDS, KEEP_LANGUAGES,
                    DESIGNATION_CATEGORIES)


def title_matches(title):
    t = (title or "").lower()
    if any(bad in t for bad in EXCLUDE_KEYWORDS):
        return False
    return any(kw in t for kw in TITLE_KEYWORDS)


def categorize(title):
    """Bucket a title into one designation family (first match wins)."""
    t = (title or "").lower()
    for category, keywords in DESIGNATION_CATEGORIES.items():
        if any(kw in t for kw in keywords):
            return category
    return "Other"


# Order matters: check hybrid before remote (a "hybrid remote" role is hybrid),
# and only fall back to onsite / unknown.
_HYBRID = ["hybrid", "hybrides", "teilweise remote", "partly remote", "flexible working"]
_REMOTE = ["fully remote", "100% remote", "remote-first", "remote first",
           "work from home", "home office", "homeoffice", "remote", "telework",
           "ortsunabhängig", "vollständig remote"]
_ONSITE = ["on-site", "on site", "onsite", "vor ort", "office-based",
           "in-office", "präsenz", "no remote", "kein homeoffice"]


def work_mode(job):
    """Return 'remote', 'hybrid', 'onsite', or 'unknown'."""
    # Explicit flags from sources that provide them
    if job.get("is_remote") is True:
        return "remote"
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    if any(k in text for k in _HYBRID):
        return "hybrid"
    if any(k in text for k in _REMOTE):
        return "remote"
    if any(k in text for k in _ONSITE):
        return "onsite"
    return "unknown"


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
    """Filter to relevant + EN/DE roles, tagging each with language, category,
    and work mode. English roles are returned first."""
    kept = []
    for j in jobs:
        if not title_matches(j.get("title")):
            continue
        lang = detect_language(j)
        if lang is None:
            continue
        j["language"] = lang
        j["category"] = categorize(j.get("title"))
        j["work_mode"] = work_mode(j)
        kept.append(j)
    kept.sort(key=lambda j: 0 if j["language"] == "en" else 1)
    return kept
