"""Render the new jobs as a web page and (optionally) email them to you."""

import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

from config import WEBPAGE_PATH


def _card(job):
    company = job["company"] or "—"
    location = job["location"] or job["country"]
    lang = (job.get("language") or "").upper()
    badge = f'<span class="lang lang-{lang.lower()}">{lang}</span>' if lang else ""
    return f"""
    <div class="card">
      <div class="title-row">{badge}<a class="title" href="{job['url']}" target="_blank" rel="noopener">{job['title']}</a></div>
      <div class="meta">{company} · {location} · <span class="src">{job['source']}</span></div>
      <a class="apply" href="{job['url']}" target="_blank" rel="noopener">Open &amp; apply →</a>
    </div>"""


def render_html(jobs):
    stamp = datetime.now().strftime("%a %d %b %Y, %H:%M")
    cards = "\n".join(_card(j) for j in jobs) if jobs else \
        '<p class="empty">No new matches this run.</p>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JobRadar — Scrum Master / Coach</title>
<style>
  body {{ font: 16px/1.5 -apple-system, system-ui, sans-serif; max-width: 760px;
         margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; margin-bottom: .2rem; }}
  .sub {{ color: #666; margin-bottom: 1.5rem; }}
  .card {{ border: 1px solid #e3e3e3; border-radius: 12px; padding: 1rem 1.2rem;
           margin-bottom: .9rem; }}
  .title {{ font-weight: 600; font-size: 1.05rem; color: #0b5; text-decoration: none; }}
  .title:hover {{ text-decoration: underline; }}
  .meta {{ color: #555; font-size: .9rem; margin: .3rem 0 .6rem; }}
  .src {{ color: #999; }}
  .apply {{ font-size: .9rem; text-decoration: none; color: #0366d6; }}
  .title-row {{ display: flex; align-items: baseline; gap: .5rem; }}
  .lang {{ font-size: .7rem; font-weight: 700; padding: .1rem .4rem; border-radius: 5px;
           letter-spacing: .03em; flex: none; }}
  .lang-en {{ background: #d8f5df; color: #0a6b2b; }}
  .lang-de {{ background: #ffe9c7; color: #8a5a00; }}
  .empty {{ color: #888; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #141414; color: #eee; }}
    .card {{ border-color: #333; }}
    .meta {{ color: #aaa; }} .sub {{ color: #999; }}
  }}
</style></head><body>
<h1>JobRadar — Scrum Master / Agile Coach</h1>
<div class="sub">{len(jobs)} new match(es) · {stamp}</div>
{cards}
</body></html>"""


def write_webpage(jobs, path=WEBPAGE_PATH):
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_html(jobs))
    return path


def send_email(jobs):
    user = os.getenv("SMTP_USER")
    pw = os.getenv("SMTP_APP_PASSWORD")
    to = os.getenv("DIGEST_TO")
    if not (user and pw and to):
        print("  [email] SMTP not configured — skipping send")
        return False
    if not jobs:
        print("  [email] no new jobs — not sending")
        return False

    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    msg = MIMEText(render_html(jobs), "html", "utf-8")
    msg["Subject"] = f"JobRadar: {len(jobs)} new Scrum Master / Coach role(s)"
    msg["From"] = user
    msg["To"] = to
    try:
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(user, pw)
            s.send_message(msg)
        print(f"  [email] sent to {to}")
        return True
    except Exception as e:
        print(f"  [email] error: {e}")
        return False
