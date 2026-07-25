"""Fetch jobs from the two aggregator APIs and normalise them into one shape:

    {id, source, title, company, location, country, url, posted, description}
"""

import os
import time
import httpx

from config import (
    SEARCH_TERMS,
    ADZUNA_COUNTRIES,
    ADZUNA_RESULTS_PER_PAGE,
    ADZUNA_MAX_PAGES,
    JSEARCH_COUNTRIES,
    JSEARCH_PAGES,
)

TIMEOUT = httpx.Timeout(30.0)


def _get_with_retry(client, url, params, label, tries=3):
    """GET with retry+backoff for transient throttling (503/429)."""
    for attempt in range(1, tries + 1):
        try:
            r = client.get(url, params=params)
            if r.status_code in (429, 503) and attempt < tries:
                wait = 2 * attempt
                print(f"  [{label}] {r.status_code}, retrying in {wait}s…")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            if attempt < tries:
                time.sleep(2 * attempt)
                continue
            raise e
    return None


# --------------------------------------------------------------------------- #
# Adzuna
# --------------------------------------------------------------------------- #
def fetch_adzuna():
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        print("  [adzuna] no key set — skipping")
        return []

    jobs = []
    with httpx.Client(timeout=TIMEOUT) as client:
        for country in ADZUNA_COUNTRIES:
            got = 0
            for page in range(1, ADZUNA_MAX_PAGES + 1):
                url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
                params = {
                    "app_id": app_id,
                    "app_key": app_key,
                    "results_per_page": ADZUNA_RESULTS_PER_PAGE,
                    # what_or = match ANY of these words/phrases
                    "what_or": " ".join(SEARCH_TERMS),
                    "content-type": "application/json",
                }
                try:
                    r = _get_with_retry(client, url, params, f"adzuna:{country}:{page}")
                    results = r.json().get("results", [])
                except Exception as e:
                    print(f"  [adzuna:{country}:{page}] error: {e}")
                    break
                time.sleep(0.5)  # be polite between pages/countries
                for item in results:
                    jobs.append({
                        "id": f"adzuna:{item.get('id')}",
                        "source": "Adzuna",
                        "title": item.get("title", ""),
                        "company": (item.get("company") or {}).get("display_name", ""),
                        "location": (item.get("location") or {}).get("display_name", ""),
                        "country": country.upper(),
                        "url": item.get("redirect_url", ""),
                        "posted": item.get("created", ""),
                        "description": item.get("description", ""),
                    })
                got += len(results)
                if len(results) < ADZUNA_RESULTS_PER_PAGE:
                    break  # last page reached
            print(f"  [adzuna:{country}] {got} raw")
    return jobs


# --------------------------------------------------------------------------- #
# JSearch (Google for Jobs, via RapidAPI)
# --------------------------------------------------------------------------- #
def fetch_jsearch():
    key = os.getenv("RAPIDAPI_KEY")
    if not key:
        print("  [jsearch] no key set — skipping")
        return []

    headers = {
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    # Google-for-Jobs chokes on very long OR chains — keep this compact.
    query = ('"scrum master" OR "agile coach" OR "delivery manager" '
             'OR "release train engineer" OR "agile delivery manager"')
    jobs = []
    with httpx.Client(timeout=TIMEOUT, headers=headers) as client:
        for country in JSEARCH_COUNTRIES:
            params = {
                "query": query,
                "page": "1",
                "num_pages": str(JSEARCH_PAGES),
                "country": country,
                "date_posted": "week",
            }
            try:
                r = _get_with_retry(
                    client, "https://jsearch.p.rapidapi.com/search-v2", params,
                    f"jsearch:{country}")
                # search-v2 nests results under data.jobs
                data = (r.json().get("data") or {}).get("jobs", []) or []
            except Exception as e:
                print(f"  [jsearch:{country}] error: {e}")
                continue
            time.sleep(0.5)
            for item in data:
                jobs.append({
                    "id": f"jsearch:{item.get('job_id')}",
                    "source": "JSearch",
                    "title": item.get("job_title", ""),
                    "company": item.get("employer_name", ""),
                    "location": ", ".join(
                        x for x in [item.get("job_city"), item.get("job_country")] if x
                    ),
                    "country": (item.get("job_country") or country).upper(),
                    "url": item.get("job_apply_link", ""),
                    "is_remote": item.get("job_is_remote"),
                    "posted": item.get("job_posted_at_datetime_utc")
                              or item.get("job_posted_at", ""),
                    "description": item.get("job_description", ""),
                })
            print(f"  [jsearch:{country}] {len(data)} raw")
    return jobs


# --------------------------------------------------------------------------- #
# Sweden — JobTech / Platsbanken (open government API, no key)
# --------------------------------------------------------------------------- #
def fetch_jobtech_se():
    from config import GOV_SEARCH_TERMS
    jobs, seen = [], set()
    with httpx.Client(timeout=TIMEOUT) as client:
        for term in GOV_SEARCH_TERMS:
            try:
                r = _get_with_retry(
                    client, "https://jobsearch.api.jobtechdev.se/search",
                    {"q": term, "limit": 50}, f"jobtech:{term}")
                hits = r.json().get("hits", []) or []
            except Exception as e:
                print(f"  [jobtech:{term}] error: {e}")
                continue
            for h in hits:
                jid = f"jobtech:{h.get('id')}"
                if jid in seen:
                    continue
                seen.add(jid)
                addr = h.get("workplace_address") or {}
                desc = h.get("description") or {}
                jobs.append({
                    "id": jid,
                    "source": "Platsbanken (SE)",
                    "title": h.get("headline", ""),
                    "company": (h.get("employer") or {}).get("name", ""),
                    "location": ", ".join(
                        x for x in [addr.get("municipality"), "Sweden"] if x),
                    "country": "SE",
                    "url": h.get("webpage_url")
                           or (h.get("application_details") or {}).get("url", ""),
                    "posted": h.get("publication_date", ""),
                    "description": desc.get("text", "") if isinstance(desc, dict) else "",
                })
            time.sleep(0.3)
    print(f"  [jobtech:SE] {len(jobs)} raw")
    return jobs


# --------------------------------------------------------------------------- #
# Norway — NAV Arbeidsplassen search (open endpoint their own site uses, no key)
# --------------------------------------------------------------------------- #
def fetch_navno_no():
    from config import GOV_SEARCH_TERMS
    jobs, seen = [], set()
    with httpx.Client(timeout=TIMEOUT, headers={"accept": "application/json"}) as client:
        for term in GOV_SEARCH_TERMS:
            try:
                r = _get_with_retry(
                    client, "https://arbeidsplassen.nav.no/stillinger/api/search",
                    {"q": term, "size": 100}, f"navno:{term}")
                hits = ((r.json().get("hits") or {}).get("hits")) or []
            except Exception as e:
                print(f"  [navno:{term}] error: {e}")
                continue
            for hit in hits:
                src = hit.get("_source") or {}
                uuid = src.get("uuid")
                if not uuid or uuid in seen:
                    continue
                seen.add(uuid)
                props = src.get("properties") or {}
                loc = (src.get("locationList") or [{}])[0]
                # The search hit has no ad body; build a text sample from the
                # fields it does return, so language detection has something.
                sample = " ".join(str(x) for x in [
                    src.get("title"), props.get("jobtitle"),
                    props.get("keywords"), props.get("searchtags"),
                    props.get("remote"),
                ] if x)
                jobs.append({
                    "id": f"navno:{uuid}",
                    "source": "NAV (NO)",
                    "title": src.get("title", ""),
                    "company": (src.get("employer") or {}).get("name")
                               or src.get("businessName", ""),
                    "location": ", ".join(
                        x for x in [(loc.get("city") or "").title(), "Norway"] if x),
                    "country": "NO",
                    "url": f"https://arbeidsplassen.nav.no/stillinger/stilling/{uuid}",
                    "posted": src.get("published", ""),
                    "description": sample,
                })
            time.sleep(0.3)
    print(f"  [navno:NO] {len(jobs)} raw")
    return jobs


# --------------------------------------------------------------------------- #
# EURES — EU Commission pan-European job portal (open, no key). Wide EU net.
# --------------------------------------------------------------------------- #
def fetch_eures():
    from urllib.parse import quote
    from config import GOV_SEARCH_TERMS, EURES_MAX_PAGES, EURES_RESULTS_PER_PAGE
    url = ("https://europa.eu/eures/api/jv-searchengine/public/jv-search/search")
    jobs, seen = [], set()
    with httpx.Client(timeout=httpx.Timeout(45.0),
                      headers={"accept": "application/json"}) as client:
        for term in GOV_SEARCH_TERMS:
            for page in range(1, EURES_MAX_PAGES + 1):
                body = {
                    "resultsPerPage": EURES_RESULTS_PER_PAGE, "page": page,
                    "sortSearch": "BEST_MATCH",  # relevant roles first
                    "keywords": [{"keyword": term, "specificSearchCode": "TITLE"}],
                    "publicationPeriod": "LAST_WEEK",
                    "occupationUris": [], "skillUris": [], "requiredExperienceCodes": [],
                    "positionScheduleCodes": [], "sectorCodes": [],
                    "educationAndQualificationLevelCodes": [], "positionOfferingCodes": [],
                    "locationCodes": [], "euresFlagCodes": [], "otherBenefitsCodes": [],
                    "requiredLanguages": [], "minNumberPost": None,
                    "sessionId": "jobradar", "userPreferredLanguage": None,
                    "requestLanguage": "en",
                }
                try:
                    r = client.post(url, json=body)
                    r.raise_for_status()
                    jvs = r.json().get("jvs", []) or []
                except Exception as e:
                    print(f"  [eures:{term}:{page}] error: {e}")
                    break
                for jv in jvs:
                    jid = jv.get("id")
                    if not jid or jid in seen:
                        continue
                    seen.add(jid)
                    country = next(iter((jv.get("locationMap") or {}).keys()), "")
                    posted = ""
                    ms = jv.get("lastModificationDate")
                    if isinstance(ms, (int, float)):
                        from datetime import datetime, timezone
                        posted = datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()
                    jobs.append({
                        "id": f"eures:{jid}",
                        "source": "EURES (EU)",
                        "title": jv.get("title", ""),
                        "company": (jv.get("employer") or {}).get("name", ""),
                        "location": country,
                        "country": country.upper(),
                        "url": f"https://europa.eu/eures/portal/jv-se/jv-details/{quote(jid, safe='')}?lang=en",
                        "posted": posted,
                        "description": jv.get("description", ""),
                    })
                if len(jvs) < EURES_RESULTS_PER_PAGE:
                    break
                time.sleep(0.4)
    print(f"  [eures:EU] {len(jobs)} raw")
    return jobs


def fetch_all():
    return (fetch_adzuna() + fetch_jsearch() + fetch_eures()
            + fetch_jobtech_se() + fetch_navno_no())
