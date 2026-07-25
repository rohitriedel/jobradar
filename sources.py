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
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "results_per_page": ADZUNA_RESULTS_PER_PAGE,
                # what_or = match ANY of these words/phrases
                "what_or": " ".join(SEARCH_TERMS),
                "content-type": "application/json",
            }
            try:
                r = _get_with_retry(client, url, params, f"adzuna:{country}")
                results = r.json().get("results", [])
            except Exception as e:
                print(f"  [adzuna:{country}] error: {e}")
                continue
            time.sleep(0.5)  # be polite between countries
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
            print(f"  [adzuna:{country}] {len(results)} raw")
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
    query = " OR ".join(f'"{t}"' for t in SEARCH_TERMS)
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
                    "posted": item.get("job_posted_at_datetime_utc")
                              or item.get("job_posted_at", ""),
                    "description": item.get("job_description", ""),
                })
            print(f"  [jsearch:{country}] {len(data)} raw")
    return jobs


def fetch_all():
    return fetch_adzuna() + fetch_jsearch()
