# WPR Woodchucks Widget

## Project Overview
Embeddable widget for Wausau Pilot & Review covering the **Wausau Woodchucks** and the **Northwoods League**. Displays schedule, standings, box scores, and special events. Deployed to GitHub Pages and embedded in WPR's WordPress site via iframe.

## Architecture
```
scraper/fetch_nwl.py → GitHub Actions (cron) → docs/data/*.json → docs/index.html (GitHub Pages)
```

- **Data Source**: NWL Scorebook API at `https://scorebook.northwoodsleague.com/api/`
  - `/api/standings` — returns all standings (1st half, 2nd half, full) for the current/latest season
  - `/api/schedule?teamid=68` — returns full league schedule; filter for team 68 (Woodchucks)
  - API has `Access-Control-Allow-Origin: *` (CORS open), but we cache to static JSON for reliability
- **Scraper**: Python script fetches from the NWL API and writes JSON to `docs/data/`
- **Frontend**: Self-contained HTML widget in `docs/index.html`, reads from `docs/data/*.json`
- **Deployment**: GitHub Pages serves from `docs/` directory
- **Cron**: GitHub Actions runs scraper every 30 minutes during game hours (May–August), daily otherwise

## NWL API Details
- **Woodchucks team ID**: `68`
- **League**: `1` (baseball)
- **Division**: Great Lakes West (division ID `11`)
- **Season**: API returns latest season automatically; season ID 26 = 2026
- **Schedule response**: `{ schedule: { info: {...}, games: [...] } }`
  - Each game has: `id`, `date` (MM-DD-YYYY), `time`, `visitor_team`, `home_team`, opponent names/abbrs/logos, `status_code`, `status`, `broadcast`, etc.
  - `status_code`: 0=Scheduled, 1=In Progress, 2=Final, 3=Postponed, 4=Suspended
- **Standings response**: `{ standings: { info: {...}, groups: [...] } }`
  - Groups array has 3 entries: `[0]`=1st half, `[1]`=2nd half, `[2]`=full season
  - Each group is a dict keyed by division name: `"Great Lakes East"`, `"Great Lakes West"`, `"Great Plains East"`, `"Great Plains West"`
  - Access pattern: `groups[0]["Great Lakes West"]` = 1st half GL West standings
  - Each team entry: `{ team: { idteam, Name, Abv, ... }, W, L, T, PCT, GB, STREAK, LAST10 }`

## WPR Brand
- Teal: `#4aaba7` / `#3e9e9a` / `#0d7377`
- Cream: `#f5f0e8` / `#f6f2eb`
- Ink: `#1c1917` / `#181816`
- Fonts: Playfair Display (headlines), Source Sans 3 (body), JetBrains Mono (data/labels)

## Woodchucks Brand (used in widget)
- Navy: `#162b4d` / `#1e3a66`
- Cyan: `#00b8d4` / `#4dd0e1`
- Logo: dark background with woodchuck mascot + bat

## Key Files
- `docs/index.html` — the widget (self-contained HTML, loads data from `docs/data/`)
- `docs/data/schedule.json` — cached schedule with game results
- `docs/data/standings.json` — cached standings (all halves)
- `docs/data/meta.json` — last scrape timestamp and season info
- `scraper/fetch_nwl.py` — Python scraper
- `.github/workflows/scrape.yml` — GitHub Actions workflow

## WordPress Embed
```html
<iframe src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/"
        style="width:100%;max-width:720px;height:800px;border:none;"
        title="Wausau Woodchucks Schedule & Standings">
</iframe>
```

## Season Timeline
- **Late May**: Season opens (Memorial Day weekend)
- **Early July**: All-Star Break (Jul 7-9, 2026 at Field of Dreams)
- **Early August**: Regular season ends (~Aug 8-9)
- **Aug 9-13**: Playoffs
- Season is split into two halves for standings purposes

## Development
- Local preview: open `docs/index.html` in browser
- Test scraper: `cd scraper && python fetch_nwl.py`
- Future: migrate to React/Vite for frontend
