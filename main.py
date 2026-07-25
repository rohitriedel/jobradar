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


def main():
    load_dotenv()

    print("1/4  Fetching from job APIs…")
    raw = sources.fetch_all()
    print(f"     {len(raw)} raw postings")

    print("2/4  Filtering by title + language…")
    matched = [j for j in raw if filters.keep(j)]
    print(f"     {len(matched)} match Scrum/Coach + EN/DE")

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
