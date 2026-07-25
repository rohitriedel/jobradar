"""Keep only jobs that (a) look like a Scrum Master / coach role by title and
(b) are written in English or German."""

from langdetect import detect, LangDetectException

from config import TITLE_KEYWORDS, KEEP_LANGUAGES


def title_matches(title):
    t = (title or "").lower()
    return any(kw in t for kw in TITLE_KEYWORDS)


def language_ok(job):
    sample = f"{job.get('title', '')}. {job.get('description', '')}".strip()
    if not sample:
        return False
    try:
        return detect(sample) in KEEP_LANGUAGES
    except LangDetectException:
        return False


def keep(job):
    return title_matches(job.get("title")) and language_ok(job)
