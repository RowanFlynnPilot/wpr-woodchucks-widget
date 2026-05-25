# WPR Northwoods Widget

## Project Overview
Embeddable widget for **Wausau Pilot & Review** covering the **Wausau Woodchucks** (baseball, Northwoods League) and the **Wausau Ignite** (softball, NWL Softball). One self-contained HTML file serves both — the team is picked from `?team=woodchucks` or `?team=ignite` in the URL. Defaults to `woodchucks` when no param is set (preserves the original single-team embed URL).

Deployed to GitHub Pages and embedded in WPR's WordPress site via iframe.

## Architecture
```
scraper/fetch_nwl.py --team all
  ↓ (GitHub Actions cron, every ~30 min during game hours)
docs/data/<team>/{schedule,standings,meta}.json
docs/data/<team>/events.json (hand-edited from each team's official promo page)
  ↓
docs/index.html (single file, reads ?team= URL param)
  ↓ (GitHub Pages serves from /docs)
WordPress iframe with postMessage auto-resize listener
```

## Data Sources

| Team       | Sport    | API base                                              | Team ID |
|------------|----------|-------------------------------------------------------|---------|
| Woodchucks | Baseball | `https://scorebook.northwoodsleague.com/api/`         | 68      |
| Ignite     | Softball | `https://scorebook-softball.northwoodsleague.com/api/`| 5       |

Both endpoints return the **same response shape**, so one fetcher in `fetch_nwl.py` handles both. Both have open CORS, but we cache to static JSON for reliability.

### Common endpoints (both hosts)
- `/api/schedule` — returns full league schedule (`teamid=` param is silently ignored; scraper filters client-side)
- `/api/standings` — three groups: `[0]`=1st half, `[1]`=2nd half, `[2]`=full. Each group is a dict keyed by division name.

### Status codes
`0` = Scheduled · `1` = In Progress · `2` = Final · `3` = Postponed · `4` = Suspended

### Standings division keys
- **Baseball**: `"Great Lakes East"`, `"Great Lakes West"`, `"Great Plains East"`, `"Great Plains West"`
- **Softball**: `"NWL Softball"` (single division)

The widget's standings JSON always uses `great_lakes_west` / `great_lakes_east` keys. For softball, the scraper buckets the single `"NWL Softball"` division into `great_lakes_west` so the widget renders it without UI changes; `great_lakes_east` stays empty and the widget hides the East section.

### How the softball API was found
The NWL site's React component bundle (`/wp-content/themes/NWL-Extend/components/index.js`) lazy-loads webpack chunks at runtime. The main bundle has no URL strings — they live in numbered chunks (`<id>.<hash>.js`). Chunk **768** hardcodes `scorebook-softball.northwoodsleague.com`. If the team adds a third sport in the future, check this bundle the same way.

## Brand Palettes

### WPR (used in the teal sponsor band at the bottom)
- Teal: `#4aaba7` / `#3a8e8b` · Cream: `#faf7f2` · Ink: `#1a1a1a`
- Fonts: Source Sans 3 (body), Bebas Neue (display), JetBrains Mono (data/labels)

### Woodchucks (default team theme)
- Navy: `#162b4d` / `#1e3a66`
- Accent (cyan): `#00b8d4` / `#4dd0e1`
- Logo: navy rounded square with woodchuck mascot + bat (`docs/woodchucks-logo.png`)

### Ignite (softball team theme)
- Navy: `#001830` / `#1a3450`
- Accent (ice blue): `#48a8d8` / `#90c0c0`
- Logo: snowy owl wings outstretched (`docs/ignite-logo.png`)
- Single-division layout — standings heading is "NWL Softball", no East sub-divider

Brand values are applied at runtime by `applyBranding()` via CSS custom properties (`--chucks-navy`, `--chucks-cyan`, etc.). The variable names are legacy and shared by both teams — only the values change.

## Key Files

```
docs/
  index.html                # the widget (single file, all CSS+JS inline)
  woodchucks-logo.png       # 96x96 transparent
  ignite-logo.png           # 96x96 transparent
  wpr-logo.png              # for the sponsor band
  data/
    woodchucks/
      schedule.json         # auto-updated by scraper
      standings.json        # auto-updated by scraper
      meta.json             # auto-updated by scraper
      events.json           # editorial — hand-edited
    ignite/
      schedule.json         # auto-updated by scraper
      standings.json        # auto-updated by scraper
      meta.json             # auto-updated by scraper
      events.json           # editorial — hand-edited
scraper/
  fetch_nwl.py              # TEAMS dict at top maps slug → API base + team_id
  requirements.txt          # just `requests`
.github/workflows/
  scrape.yml                # runs `python scraper/fetch_nwl.py --team all` on cron
```

## WordPress Embed

Two iframes + one shared listener (the listener routes by `data-team`):

```html
<iframe id="wpr-widget-woodchucks" data-team="woodchucks"
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/?team=woodchucks"
  style="width:100%;max-width:720px;height:600px;border:none;display:block;margin:0 auto;"
  title="Wausau Woodchucks Schedule & Standings" loading="lazy" scrolling="no"></iframe>

<iframe id="wpr-widget-ignite" data-team="ignite"
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/?team=ignite"
  style="width:100%;max-width:720px;height:600px;border:none;display:block;margin:0 auto;"
  title="Wausau Ignite Schedule & Standings" loading="lazy" scrolling="no"></iframe>

<script>
  window.addEventListener('message', function (e) {
    if (!e.data || e.data.type !== 'wpr-widget-resize') return;
    var f = document.querySelector('iframe[data-team="' + e.data.team + '"]');
    if (f && typeof e.data.height === 'number') f.style.height = e.data.height + 'px';
  });
</script>
```

Resize message contract: `{ type: 'wpr-widget-resize', team: 'woodchucks'|'ignite', height: <number> }`. Posted on `ResizeObserver` of `<html>`.

## Season Timeline

### Woodchucks (Baseball)
- **Late May**: Season opens (Memorial Day weekend) — 2026 opener May 28
- **Early July**: NWL All-Star Break at Field of Dreams (Jul 7–9)
- **Early August**: Regular season ends (~Aug 8)
- Season is split into 1st/2nd halves for standings

### Ignite (Softball)
- **Mid June**: Season opens — 2026 opener Jun 9
- **Late July**: Regular season ends (~Jul 31)
- Single half (no split standings)

## Editorial Events Refresh (Annual)

Each team publishes a promotional schedule page once a year:
- Woodchucks: `https://northwoodsleague.com/wausau-woodchucks/2026-promotional-schedule/`
- Ignite: `https://northwoodsleague.com/wausau-ignite/2026-promotional-schedule-2/`

Set a calendar reminder for **late April / early May** each year to re-curate `docs/data/<team>/events.json` from the new season's promo page. ~20 min per team.

## Development

```bash
# Install scraper deps (one-time)
pip install -r scraper/requirements.txt

# Run scraper (defaults to --team all)
python scraper/fetch_nwl.py
python scraper/fetch_nwl.py --team ignite     # one team
python scraper/fetch_nwl.py --schedule-only   # skip standings

# Preview locally
python -m http.server 8765 --directory docs
# http://localhost:8765/?team=woodchucks  or  ?team=ignite
```

## Common Edits

- **Add an event**: edit `docs/data/<team>/events.json`, push. Widget picks it up on next reload.
- **Add a new team**: extend `TEAMS` in both `scraper/fetch_nwl.py` and the `TEAMS` block at the top of `docs/index.html` (~30 lines per team for the widget config).
- **Brand tweaks**: change values in the team's `brand:` object in `docs/index.html`.
- **Season year rollover**: bump `seasonYear` in each `TEAMS` entry; the rest follows.
