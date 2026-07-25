"""Watched-companies source.

Some employers expose their careers page as an OPEN, no-key JSON API (their
Applicant Tracking System). For those we can poll the portal DIRECTLY — fresher
and more complete than any aggregator, because it's straight from the source.

Four ATSs cover most of them: Greenhouse, Lever, Ashby, SmartRecruiters.
Add a company by putting one line in config.WATCHED_COMPANIES — no code change.

NOTE: the giants that hire the MOST Scrum Masters (Accenture, Capgemini, TCS,
banks…) run Workday / SuccessFactors, which are NOT openly pollable. Those stay
covered by the aggregators (Adzuna/JSearch/EURES) + native LinkedIn/Xing alerts.
"""

import time
import httpx

from config import WATCHED_COMPANIES, TITLE_KEYWORDS, EXCLUDE_KEYWORDS

TIMEOUT = httpx.Timeout(20.0)

# Best-effort country code from a free-text location, for the page's filter.
_COUNTRY = {
    "germany": "DE", "deutschland": "DE", "austria": "AT", "österreich": "AT",
    "switzerland": "CH", "schweiz": "CH", "netherlands": "NL", "nederland": "NL",
    "france": "FR", "spain": "ES", "españa": "ES", "italy": "IT", "italia": "IT",
    "belgium": "BE", "poland": "PL", "polska": "PL", "ireland": "IE",
    "portugal": "PT", "sweden": "SE", "norway": "NO", "denmark": "DK",
    "finland": "FI", "united kingdom": "GB", "uk": "GB", "england": "GB",
    "czech": "CZ", "romania": "RO", "greece": "GR", "hungary": "HU",
    "luxembourg": "LU", "remote": "", "europe": "",
}


def _country(loc):
    t = (loc or "").lower()
    for name, code in _COUNTRY.items():
        if name in t:
            return code
    return ""


def _title_ok(title):
    t = (title or "").lower()
    if any(b in t for b in EXCLUDE_KEYWORDS):
        return False
    return any(k in t for k in TITLE_KEYWORDS)


# --------------------------------------------------------------------------- #
# Per-ATS pollers — each returns a list of normalised job dicts (title-filtered)
# --------------------------------------------------------------------------- #
def _greenhouse(client, slug, name):
    r = client.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        if not _title_ok(j.get("title")):
            continue
        loc = (j.get("location") or {}).get("name", "")
        out.append({
            "id": f"gh:{slug}:{j.get('id')}", "source": f"{name} (careers)",
            "title": j.get("title", ""), "company": name, "location": loc,
            "country": _country(loc), "url": j.get("absolute_url", ""),
            "posted": j.get("updated_at", ""),
            "description": f"{j.get('title','')} at {name}. {loc}",
        })
    return out


def _lever(client, slug, name):
    r = client.get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    r.raise_for_status()
    out = []
    for j in r.json():
        if not _title_ok(j.get("text")):
            continue
        loc = (j.get("categories") or {}).get("location", "")
        out.append({
            "id": f"lever:{slug}:{j.get('id')}", "source": f"{name} (careers)",
            "title": j.get("text", ""), "company": name, "location": loc,
            "country": _country(loc), "url": j.get("hostedUrl", ""),
            "posted": j.get("createdAt", ""),
            "description": j.get("descriptionPlain") or f"{j.get('text','')} {loc}",
        })
    return out


def _ashby(client, slug, name):
    r = client.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        if not _title_ok(j.get("title")):
            continue
        loc = j.get("location", "")
        out.append({
            "id": f"ashby:{slug}:{j.get('id')}", "source": f"{name} (careers)",
            "title": j.get("title", ""), "company": name, "location": loc,
            "country": _country(loc), "url": j.get("jobUrl", ""),
            "posted": j.get("publishedAt", ""),
            "description": j.get("descriptionPlain") or f"{j.get('title','')} {loc}",
        })
    return out


def _smartrecruiters(client, slug, name):
    out = []
    postings = []
    for offset in range(0, 1000, 100):  # paginate; big boards hide SM roles deep
        r = client.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
                       params={"limit": 100, "offset": offset})
        r.raise_for_status()
        chunk = r.json().get("content", [])
        postings.extend(chunk)
        if len(chunk) < 100:
            break
        time.sleep(0.15)
    for j in postings:
        if not _title_ok(j.get("name")):
            continue
        loc = ", ".join(x for x in [
            (j.get("location") or {}).get("city"),
            (j.get("location") or {}).get("country"),
        ] if x)
        out.append({
            "id": f"sr:{slug}:{j.get('id')}", "source": f"{name} (careers)",
            "title": j.get("name", ""), "company": name, "location": loc,
            "country": ((j.get("location") or {}).get("country") or "").upper()[:2],
            "url": (j.get("ref") or "").replace("api.smartrecruiters.com/v1",
                                                "jobs.smartrecruiters.com")
                   or f"https://jobs.smartrecruiters.com/{slug}",
            "posted": j.get("releasedDate", ""),
            "description": f"{j.get('name','')} at {name}. {loc}",
        })
    return out


_POLLERS = {
    "greenhouse": _greenhouse, "lever": _lever,
    "ashby": _ashby, "smartrecruiters": _smartrecruiters,
}


def fetch_watched():
    jobs = []
    with httpx.Client(timeout=TIMEOUT, headers={"accept": "application/json"},
                      follow_redirects=True) as client:
        for ats, slug, name in WATCHED_COMPANIES:
            poll = _POLLERS.get(ats)
            if not poll:
                continue
            try:
                got = poll(client, slug, name)
                jobs.extend(got)
            except Exception as e:
                print(f"  [watch:{name}] error: {e}")
            time.sleep(0.2)
    print(f"  [watch] {len(jobs)} matching roles across {len(WATCHED_COMPANIES)} companies")
    return jobs
