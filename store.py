"""Tiny SQLite layer that remembers which jobs we've already shown you,
so the same posting never turns up in two digests."""

import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id         TEXT PRIMARY KEY,   -- stable per source, e.g. "adzuna:12345"
    source     TEXT,
    title      TEXT,
    company    TEXT,
    location   TEXT,
    country    TEXT,
    url        TEXT,
    posted     TEXT,
    description TEXT,
    first_seen TEXT
);
"""


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def filter_new(conn, jobs):
    """Return only the jobs whose id we've never stored before, and store them."""
    new = []
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    for j in jobs:
        exists = cur.execute("SELECT 1 FROM jobs WHERE id = ?", (j["id"],)).fetchone()
        if exists:
            continue
        cur.execute(
            """INSERT INTO jobs
               (id, source, title, company, location, country, url, posted, description, first_seen)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                j["id"], j["source"], j["title"], j["company"], j["location"],
                j["country"], j["url"], j["posted"], j["description"], now,
            ),
        )
        new.append(j)
    conn.commit()
    return new
