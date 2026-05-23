# 🏟️ WPR Northwoods Widget

Embeddable widgets for [Wausau Pilot & Review](https://wausaupilotandreview.com) covering the **Wausau Woodchucks** (baseball) and **Wausau Ignite** (softball) of the Northwoods League.

One repo, one widget, two embeds — the team is picked via the URL.

## Features

- **Schedule** — Full season with month navigation, home/away filters, game times, and ticket links
- **Standings** — Great Lakes Division with 1st Half / 2nd Half / Full Season toggle (Woodchucks); roster placeholder until softball API opens (Ignite)
- **Results** — Final scores for completed games
- **Events** — Theme nights, promos, community events, and special dates (editorial — JSON file per team)

## Architecture

```
NWL Scorebook API → Python scraper → GitHub Actions (cron) → docs/data/<team>/*.json → docs/index.html (?team=…) → GitHub Pages
```

The widget reads `?team=woodchucks` or `?team=ignite` from the URL, then loads from `docs/data/<team>/`. Defaults to `woodchucks` when no param is set (preserves the original embed URL).

| Team | Data source |
|------|-------------|
| Woodchucks | Scraped from `scorebook.northwoodsleague.com/api/` every ~30 min during game hours |
| Ignite | Scraped from `scorebook-softball.northwoodsleague.com/api/` (separate softball subdomain), same cadence |

## WordPress Embed

Drop these in Custom HTML blocks. Both widgets share one parent-side listener — paste it once at the bottom of the page.

### Woodchucks

```html
<iframe
  id="wpr-widget-woodchucks"
  data-team="woodchucks"
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/?team=woodchucks"
  style="width:100%;max-width:720px;height:600px;border:none;display:block;margin:0 auto;"
  title="Wausau Woodchucks Schedule & Standings"
  loading="lazy"
  scrolling="no">
</iframe>
```

### Ignite

```html
<iframe
  id="wpr-widget-ignite"
  data-team="ignite"
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/?team=ignite"
  style="width:100%;max-width:720px;height:600px;border:none;display:block;margin:0 auto;"
  title="Wausau Ignite Schedule & Standings"
  loading="lazy"
  scrolling="no">
</iframe>
```

### Shared resize listener (paste once)

```html
<script>
  window.addEventListener('message', function (e) {
    if (!e.data || e.data.type !== 'wpr-widget-resize') return;
    var f = document.querySelector('iframe[data-team="' + e.data.team + '"]');
    if (f && typeof e.data.height === 'number') f.style.height = e.data.height + 'px';
  });
</script>
```

If WordPress strips the `<script>` tag (security plugin / user role), both widgets still work — they just stay at the initial 600px height with internal scrolling.

## Setup

### 1. Enable GitHub Pages
**Settings → Pages**, source: **Deploy from a branch**, branch `main`, folder `/docs`.

### 2. GitHub Actions cron
The workflow at `.github/workflows/scrape.yml` runs the scraper for **both teams** in sequence:
- **During season (May–Aug)**: every 30 min during game hours
- **Off-season**: daily at noon CT
- Manual trigger via the **Actions** tab

## Local Development

```bash
# Install scraper deps
pip install -r scraper/requirements.txt

# Run the scraper (defaults to --team all; both Woodchucks + Ignite)
python scraper/fetch_nwl.py
python scraper/fetch_nwl.py --team ignite   # just one team
python scraper/fetch_nwl.py --schedule-only # skip standings

# Preview locally
python -m http.server 8765 --directory docs
# then open http://localhost:8765/?team=woodchucks or ?team=ignite
```

## Data Files

```
docs/data/
  woodchucks/
    schedule.json   # auto-updated by scraper
    standings.json  # auto-updated by scraper
    meta.json       # auto-updated by scraper
    events.json     # editorial — hand-edited
  ignite/
    schedule.json   # auto-updated by scraper
    standings.json  # auto-updated by scraper
    meta.json       # auto-updated by scraper
    events.json     # editorial — hand-edited
```

## NWL API Reference

Baseball (Woodchucks) — host `scorebook.northwoodsleague.com`:

| Endpoint | Description |
|----------|-------------|
| `/api/schedule?teamid=68` | Full baseball schedule (filtered client-side for team 68) |
| `/api/standings` | League standings (all baseball divisions, all halves) |

Softball (Ignite) — host `scorebook-softball.northwoodsleague.com` (separate subdomain, same response shape):

| Endpoint | Description |
|----------|-------------|
| `/api/schedule?teamid=5` | Full softball schedule (filtered client-side for team 5) |
| `/api/standings` | NWL Softball standings |

Both have open CORS, but we cache to static JSON via the scraper for reliability and rate-limit safety.

---

Built for [Wausau Pilot & Review](https://wausaupilotandreview.com) · Data from [northwoodsleague.com](https://northwoodsleague.com)
