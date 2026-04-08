# 🏟️ WPR Woodchucks Widget

Embeddable widget for [Wausau Pilot & Review](https://wausaupilotandreview.com) covering the **Wausau Woodchucks** and the **Northwoods League**.

## Features

- **Schedule** — Full 2026 season with month navigation, home/away filters, game times, and ticket links
- **Standings** — Great Lakes Division with 1st Half / 2nd Half / Full Season toggle
- **Box Scores** — Linescore and expandable batting stats (populated during season)
- **Events** — Theme nights, promos, community events, and special dates

## Architecture

```
NWL Scorebook API → Python scraper → GitHub Actions (cron) → Static JSON → HTML Widget → GitHub Pages
```

Data is sourced from the NWL's Scorebook API (`scorebook.northwoodsleague.com/api/`) and cached as static JSON files. The widget reads from these local JSON files, with a fallback to the live API.

## Setup

### 1. Enable GitHub Pages

Go to **Settings → Pages** and set source to **Deploy from a branch**, branch `main`, folder `/docs`.

### 2. Enable GitHub Actions

The workflow at `.github/workflows/scrape.yml` runs automatically:
- **During season (May–Aug)**: Every 30 minutes during game hours
- **Off-season (Sep–Apr)**: Daily at noon CT

You can also trigger it manually from the **Actions** tab.

### 3. WordPress Embed

```html
<iframe
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/"
  style="width:100%;max-width:720px;height:800px;border:none;"
  title="Wausau Woodchucks Schedule & Standings">
</iframe>
```

## Local Development

```bash
# Install scraper dependencies
pip install -r scraper/requirements.txt

# Run the scraper to fetch fresh data
python scraper/fetch_nwl.py

# Preview the widget
open docs/index.html
```

## Data Files

| File | Description |
|------|-------------|
| `docs/data/schedule.json` | Woodchucks game schedule with results |
| `docs/data/standings.json` | GL West & East standings (all halves) |
| `docs/data/meta.json` | Last scrape timestamp |

## NWL API Reference

| Endpoint | Description |
|----------|-------------|
| `/api/schedule?teamid=68` | Full league schedule (filter for team 68) |
| `/api/standings` | League standings (all divisions, all halves) |
| `/api/divisions` | Division list with IDs |

Woodchucks team ID: `68` · Great Lakes West division ID: `11`

---

Built for [Wausau Pilot & Review](https://wausaupilotandreview.com) · Data from [northwoodsleague.com](https://northwoodsleague.com)
