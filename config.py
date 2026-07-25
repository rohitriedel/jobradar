"""All the knobs for JobRadar in one place. Edit here, not in the code."""

# ---------------------------------------------------------------------------
# DESIGNATIONS — the Scrum Master role fragmented in 2026. These are the title
# families that do (broadly) the same work. Each job is bucketed into the first
# category whose keyword its title contains. Order = priority when a title
# could fit more than one bucket (most specific first).
# ---------------------------------------------------------------------------
DESIGNATION_CATEGORIES = {
    "Release Train Engineer": [
        "release train engineer", "solution train engineer", "train engineer",
    ],
    "Delivery Manager": [
        "agile delivery manager", "delivery manager", "delivery lead",
        "agile delivery lead", "delivery coach", "flow manager", "flow lead",
    ],
    "Agile Coach": [
        "agile coach", "agility lead", "agile lead", "ways of working",
        "enterprise coach", "transformation coach", "agile transformation",
        "kanban coach",
    ],
    "Team Facilitator": [
        "agile team facilitator", "team facilitator", "iteration manager",
        "team coach",
    ],
    "Agile PM": [
        "agile project manager", "agile programme manager", "agile program manager",
    ],
    "Scrum Master": [
        "scrum master", "scrum-master", "agile master", "scrum coach",
    ],
}

# Flattened keyword list — a title is kept if it contains ANY of these.
TITLE_KEYWORDS = [kw for kws in DESIGNATION_CATEGORIES.values() for kw in kws]

# ...but rejected if the title also contains one of these — kills non-tech
# "delivery manager" noise (logistics, procurement, food, etc.) without
# dropping real agile-delivery roles.
EXCLUDE_KEYWORDS = [
    "procurement", "logistics", "supply chain", "courier", "warehouse",
    "food delivery", "transport", "fleet", "catering", "driver",
]

# Broad phrases sent to the APIs. Adzuna ORs these; the title filter then trims.
SEARCH_TERMS = [
    "scrum master", "agile coach", "agile delivery manager", "delivery manager",
    "delivery lead", "release train engineer", "iteration manager",
    "agile team facilitator", "team coach", "agile master", "scrum coach",
    "agile project manager", "agile program manager", "agile lead",
    "ways of working",
]

# Smaller curated set for the free government APIs (looped one query each).
GOV_SEARCH_TERMS = [
    "scrum master", "agile coach", "agile delivery manager",
    "release train engineer", "iteration manager", "team coach",
]

# Languages to keep, detected from title + description. English first on page.
KEEP_LANGUAGES = {"en", "de"}

# Adzuna country endpoints across Europe (their supported EU markets).
ADZUNA_COUNTRIES = ["gb", "de", "at", "ch", "nl", "be", "fr", "it", "es", "pl"]
ADZUNA_RESULTS_PER_PAGE = 50
ADZUNA_MAX_PAGES = 3  # depth per country, so we don't miss jobs

# JSearch = the Google-for-Jobs feed (catches LinkedIn/Glassdoor/Indeed/StepStone
# postings). Tested 2026-07-26: these 6 return data (gb/ie/se/pl/be come back empty
# on the free tier; se/no are covered by the gov APIs anyway).
# BUDGET: free tier is a hard 200 requests/month. 6 countries × ONCE daily = 180/mo,
# which fits. So JSearch runs only on the MORNING cloud sweep (see sources.py gate);
# Adzuna/EURES/gov APIs are free and still run twice daily.
JSEARCH_COUNTRIES = ["de", "at", "ch", "nl", "fr", "es"]
JSEARCH_PAGES = 1

# EURES — the EU Commission's pan-European job portal (open, no key). This is
# the wide net: covers every EU country, incl. the ones Adzuna/JSearch miss
# (Ireland, Finland, Portugal, Greece, Eastern EU…). BEST_MATCH ranks relevant
# roles first; the title filter trims the tail.
EURES_MAX_PAGES = 2
EURES_RESULTS_PER_PAGE = 50

# ---------------------------------------------------------------------------
# WATCHED COMPANIES — polled DIRECTLY from their careers portal (open ATS APIs,
# no key). Straight from the source, so fresher/more complete than aggregators.
# Format: (ats, slug, "Display Name").  ats ∈ greenhouse|lever|ashby|smartrecruiters.
# All slugs below were verified working 2026-07-26. Add a company = add a line.
# To find a slug: check the careers-page URL, e.g. boards.greenhouse.io/<slug>,
# jobs.lever.co/<slug>, jobs.ashbyhq.com/<slug>, jobs.smartrecruiters.com/<Slug>.
# ---------------------------------------------------------------------------
WATCHED_COMPANIES = [
    ("greenhouse", "celonis", "Celonis"),
    ("greenhouse", "getyourguide", "GetYourGuide"),
    ("greenhouse", "n26", "N26"),
    ("greenhouse", "hellofresh", "HelloFresh"),
    ("greenhouse", "trivago", "trivago"),
    ("greenhouse", "contentful", "Contentful"),
    ("greenhouse", "gitlab", "GitLab"),
    ("greenhouse", "thoughtworks", "Thoughtworks"),
    ("greenhouse", "doctolib", "Doctolib"),
    ("greenhouse", "typeform", "Typeform"),
    ("greenhouse", "sumup", "SumUp"),
    ("greenhouse", "raisin", "Raisin"),
    ("greenhouse", "solarisbank", "Solaris"),
    ("greenhouse", "mirakl", "Mirakl"),
    ("lever", "spotify", "Spotify"),
    ("ashby", "pennylane", "Pennylane"),
    ("smartrecruiters", "Continental", "Continental"),
    ("smartrecruiters", "Visa", "Visa"),
]

# Where the SQLite "already seen" database and the web page get written.
DB_PATH = "jobradar.db"
WEBPAGE_PATH = "index.html"
