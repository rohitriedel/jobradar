"""All the knobs for JobRadar in one place. Edit here, not in the code."""

# Job titles we care about. A posting is kept only if its title matches one of
# these (case-insensitive substring). Add/remove freely.
TITLE_KEYWORDS = [
    "scrum master",
    "agile coach",
    "team coach",
    "agile team coach",
    "agile coach",
    "agile master",
    "iteration manager",
    "agile team facilitator",
    "delivery coach",
]

# Search phrases we send to the job APIs (broader than the title filter above;
# the title filter then trims the noise).
SEARCH_TERMS = ["scrum master", "agile coach", "team coach"]

# Languages to keep. Detected from the job title + description.
KEEP_LANGUAGES = {"en", "de"}

# Adzuna country endpoints across Europe (their supported EU markets).
ADZUNA_COUNTRIES = ["gb", "de", "at", "ch", "nl", "be", "fr", "it", "es", "pl"]

# How many results per Adzuna page/query (max 50 on the free tier).
ADZUNA_RESULTS_PER_PAGE = 50

# JSearch: which country codes to sweep and how many result-pages each.
# Deliberately aimed at gaps Adzuna can't see: Scandinavia (se/dk/no) + Ireland
# (English-native), plus Germany where JSearch catches StepStone/Indeed roles.
JSEARCH_COUNTRIES = ["se", "dk", "no", "ie", "de"]
JSEARCH_PAGES = 1

# Where the SQLite "already seen" database and the web page get written.
DB_PATH = "jobradar.db"
WEBPAGE_PATH = "index.html"
