"""JobRadar — Evening 1 pipeline.

    fetch (Adzuna + JSearch)  ->  filter (title + language)  ->
    dedupe (SQLite)  ->  web page + email digest
"""

from dotenv import load_dotenv

import config
import store
import filters
import sources
import digest


def collapse_duplicates(jobs):
    """Adzuna often lists the same role under several IDs. Keep one per
    (title, company, country) so the digest isn't cluttered with repeats."""
    seen, out = set(), []
    for j in jobs:
        key = (
            (j.get("title") or "").strip().lower(),
            (j.get("company") or "").strip().lower(),
            j.get("country", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def main():
    load_dotenv()

    print("1/4  Fetching from job APIs…")
    raw = sources.fetch_all()
    print(f"     {len(raw)} raw postings")

    print("2/4  Filtering by title + language…")
    matched = [j for j in raw if filters.keep(j)]
    matched = collapse_duplicates(matched)
    print(f"     {len(matched)} match Scrum/Coach + EN/DE (near-duplicates collapsed)")

    print("3/4  Removing ones you've already seen…")
    conn = store.connect(config.DB_PATH)
    new = store.filter_new(conn, matched)
    print(f"     {len(new)} are new")

    print("4/4  Building digest…")
    path = digest.write_webpage(new)
    print(f"     web page → {path}")
    digest.send_email(new)

    print("Done.")


if __name__ == "__main__":
    main()
