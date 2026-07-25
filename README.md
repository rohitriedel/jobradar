# JobRadar

Twice-daily sweep for **Scrum Master / Agile Coach / Team Coach** roles across
Europe (English or German), de-duplicated, delivered as a web page + email.
You review and apply yourself.

## Evening 1 (this version)
`fetch (Adzuna + JSearch) → filter (title + language) → dedupe → web page + email`

## Setup
```bash
cd ~/Desktop/JobRadar
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then paste your keys into .env
```

Get the two free keys:
- **Adzuna**: https://developer.adzuna.com/  → app_id + app_key
- **JSearch (RapidAPI)**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch → subscribe to the free Basic plan, copy your RapidAPI key

Email is optional for now — leave the SMTP fields blank and it just writes `index.html`.

## Run
```bash
source .venv/bin/activate
python main.py
open index.html
```

## Coming in Evening 2
- Claude tailors your CV + a pitch per job
- Alert-inbox parser (StepStone/Indeed saved-search emails)
- Move the schedule to GitHub Actions + host the page on GitHub Pages
