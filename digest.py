"""Render jobs two ways:
  - render_page(jobs): the interactive, filterable web page (all current jobs)
  - render_email(jobs): a simple static list for the email digest (new jobs)
"""

import os
import html
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

from config import WEBPAGE_PATH

MODE_LABEL = {"remote": "Remote", "hybrid": "Hybrid",
              "onsite": "Onsite", "unknown": "Unspecified"}
LANG_LABEL = {"en": "English", "de": "German"}


def _esc(s):
    return html.escape(s or "")


# --------------------------------------------------------------------------- #
# Interactive web page
# --------------------------------------------------------------------------- #
def _card(job):
    lang = (job.get("language") or "").lower()
    mode = (job.get("work_mode") or "unknown").lower()
    cat = job.get("category") or "Other"
    country = job.get("country") or ""
    company = _esc(job.get("company")) or "—"
    location = _esc(job.get("location")) or country
    search = _esc(f"{job.get('title','')} {job.get('company','')}").lower()
    return f"""
    <div class="card" data-lang="{lang}" data-mode="{mode}" data-cat="{_esc(cat)}"
         data-country="{country}" data-search="{search}">
      <div class="title-row">
        <span class="lang lang-{lang}">{lang.upper()}</span>
        <a class="title" href="{_esc(job.get('url'))}" target="_blank" rel="noopener">{_esc(job.get('title'))}</a>
      </div>
      <div class="meta">{company} · {location}</div>
      <div class="chips">
        <span class="chip cat">{_esc(cat)}</span>
        <span class="chip mode-{mode}">{MODE_LABEL.get(mode, 'Unspecified')}</span>
        <span class="chip">{country}</span>
        <span class="chip src">{_esc(job.get('source'))}</span>
      </div>
      <a class="apply" href="{_esc(job.get('url'))}" target="_blank" rel="noopener">Open &amp; apply →</a>
    </div>"""


def _pill_group(name, label, options, active="all"):
    """options = list of (value, text). 'all' pill added first. `active` = which
    value starts selected (default 'all')."""
    def cls(v):
        return "pill active" if v == active else "pill"
    pills = [f'<button class="{cls("all")}" data-group="{name}" data-value="all">All</button>']
    for value, text in options:
        pills.append(
            f'<button class="{cls(value)}" data-group="{name}" data-value="{_esc(value)}">{_esc(text)}</button>')
    return f'<div class="fgroup"><span class="flabel">{label}</span>{"".join(pills)}</div>'


def render_page(jobs):
    stamp = datetime.now().strftime("%a %d %b %Y, %H:%M")
    n_en = sum(1 for j in jobs if (j.get("language") or "") == "en")

    cats = sorted({j.get("category") or "Other" for j in jobs})
    countries = sorted({j.get("country") or "" for j in jobs if j.get("country")})
    modes = [m for m in ["remote", "hybrid", "onsite", "unknown"]
             if any((j.get("work_mode") or "unknown") == m for j in jobs)]

    filters_html = "".join([
        _pill_group("lang", "Language", [("en", "English"), ("de", "German")], active="en"),
        _pill_group("mode", "Work mode", [(m, MODE_LABEL[m]) for m in modes]),
        _pill_group("cat", "Designation", [(c, c) for c in cats]),
        _pill_group("country", "Country", [(c, c) for c in countries]),
    ])
    cards = "\n".join(_card(j) for j in jobs) if jobs else \
        '<p class="empty">No jobs yet — run the sweep.</p>'

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JobRadar — Scrum Master / Agile / Delivery roles</title>
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#0a7f3f">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="JobRadar">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<style>
  :root {{ --bg:#fff; --fg:#1a1a1a; --muted:#666; --card:#fff; --border:#e3e3e3;
           --chip:#f0f2f5; --chipfg:#444; --accent:#0a7f3f; --link:#0366d6; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#141414; --fg:#eee; --muted:#aaa; --card:#1c1c1c; --border:#333;
             --chip:#262626; --chipfg:#ccc; --accent:#3fbf6f; --link:#5aa2ff; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ font:16px/1.5 -apple-system, system-ui, sans-serif; max-width:840px;
         margin:0 auto; padding:1.5rem 1rem 3rem; color:var(--fg); background:var(--bg); }}
  h1 {{ font-size:1.4rem; margin:0 0 .2rem; }}
  .sub {{ color:var(--muted); margin-bottom:1rem; }}
  .bar {{ position:sticky; top:0; background:var(--bg); padding:.6rem 0;
          border-bottom:1px solid var(--border); z-index:5; }}
  .search {{ width:100%; padding:.55rem .7rem; font-size:1rem; border:1px solid var(--border);
             border-radius:9px; background:var(--card); color:var(--fg); margin-bottom:.6rem; }}
  .fgroup {{ display:flex; flex-wrap:wrap; align-items:center; gap:.3rem; margin:.25rem 0; }}
  .flabel {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.05em;
             color:var(--muted); width:5.2rem; flex:none; }}
  .pill {{ font:inherit; font-size:.82rem; padding:.22rem .6rem; border-radius:999px;
           border:1px solid var(--border); background:var(--card); color:var(--fg);
           cursor:pointer; }}
  .pill.active {{ background:var(--accent); border-color:var(--accent); color:#fff; }}
  .count {{ margin:.9rem 0 .4rem; color:var(--muted); font-size:.9rem; }}
  .card {{ border:1px solid var(--border); border-radius:12px; padding:.9rem 1.1rem;
           margin-bottom:.8rem; background:var(--card); }}
  .title-row {{ display:flex; align-items:baseline; gap:.5rem; }}
  .title {{ font-weight:600; font-size:1.05rem; color:var(--accent); text-decoration:none; }}
  .title:hover {{ text-decoration:underline; }}
  .meta {{ color:var(--muted); font-size:.9rem; margin:.3rem 0 .5rem; }}
  .lang {{ font-size:.68rem; font-weight:700; padding:.1rem .38rem; border-radius:5px; flex:none; }}
  .lang-en {{ background:#d8f5df; color:#0a6b2b; }}
  .lang-de {{ background:#ffe9c7; color:#8a5a00; }}
  .chips {{ display:flex; flex-wrap:wrap; gap:.35rem; margin-bottom:.55rem; }}
  .chip {{ font-size:.72rem; padding:.12rem .5rem; border-radius:6px;
           background:var(--chip); color:var(--chipfg); }}
  .chip.cat {{ font-weight:600; }}
  .mode-remote {{ background:#dbeafe; color:#1e4fa3; }}
  .mode-hybrid {{ background:#ede0ff; color:#5b2ea6; }}
  .mode-onsite {{ background:#ffe0e0; color:#a33; }}
  .apply {{ font-size:.9rem; text-decoration:none; color:var(--link); }}
  .empty {{ color:var(--muted); }}
</style></head><body>
<h1>JobRadar</h1>
<div class="sub">Scrum Master · Agile Coach · Delivery Manager &amp; related — {len(jobs)} roles ({n_en} English) · updated {stamp}</div>
<div class="bar">
  <input id="q" class="search" type="search" placeholder="Search title or company…">
  {filters_html}
</div>
<div class="count" id="count"></div>
<div id="list">
{cards}
</div>
<script>
  const state = {{lang:'en', mode:'all', cat:'all', country:'all', q:''}};
  const cards = Array.from(document.querySelectorAll('.card'));
  const countEl = document.getElementById('count');

  function apply() {{
    let shown = 0;
    for (const c of cards) {{
      const ok =
        (state.lang==='all'    || c.dataset.lang===state.lang) &&
        (state.mode==='all'    || c.dataset.mode===state.mode) &&
        (state.cat==='all'     || c.dataset.cat===state.cat) &&
        (state.country==='all' || c.dataset.country===state.country) &&
        (state.q===''          || c.dataset.search.includes(state.q));
      c.style.display = ok ? '' : 'none';
      if (ok) shown++;
    }}
    countEl.textContent = shown + ' of ' + cards.length + ' roles shown';
  }}

  document.querySelectorAll('.pill').forEach(p => p.addEventListener('click', () => {{
    const g = p.dataset.group;
    document.querySelectorAll('.pill[data-group="'+g+'"]').forEach(x => x.classList.remove('active'));
    p.classList.add('active');
    state[g] = p.dataset.value;
    apply();
  }}));
  document.getElementById('q').addEventListener('input', e => {{
    state.q = e.target.value.trim().toLowerCase(); apply();
  }});
  apply();
  if ('serviceWorker' in navigator) {{
    window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(()=>{{}}));
  }}
</script>
</body></html>"""


def write_webpage(jobs, path=WEBPAGE_PATH):
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_page(jobs))
    return path


# --------------------------------------------------------------------------- #
# Static email digest (new jobs only)
# --------------------------------------------------------------------------- #
def render_email(jobs):
    rows = []
    for j in jobs:
        lang = (j.get("language") or "").upper()
        rows.append(
            f'<p style="margin:.4rem 0"><b>{_esc(j.get("title"))}</b> '
            f'[{lang}] — {_esc(j.get("company"))} · {_esc(j.get("location"))} '
            f'({_esc(j.get("category"))}, {MODE_LABEL.get(j.get("work_mode"),"?")})<br>'
            f'<a href="{_esc(j.get("url"))}">Open &amp; apply →</a></p>')
    body = "".join(rows) if rows else "<p>No new roles this run.</p>"
    return f"<h2>JobRadar — {len(jobs)} new role(s)</h2>{body}"


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
    msg = MIMEText(render_email(jobs), "html", "utf-8")
    msg["Subject"] = f"JobRadar: {len(jobs)} new role(s)"
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
