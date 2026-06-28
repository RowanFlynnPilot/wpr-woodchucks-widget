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

### Mini variants (for in-article embeds)

Compact 280px-tall version designed to drop into the middle of an article. Shows team logo, current record, last game with auto-recap, next scheduled game, and a "View full" CTA to the standalone widget. Mobile-friendly down to ~320px.

```html
<!-- Woodchucks mini -->
<iframe
  data-team="woodchucks"
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/?team=woodchucks&mini=true"
  style="width:100%;max-width:480px;height:280px;border:none;display:block;margin:0 auto;"
  title="Wausau Woodchucks — at a glance"
  loading="lazy"
  scrolling="no">
</iframe>

<!-- Ignite mini -->
<iframe
  data-team="ignite"
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/?team=ignite&mini=true"
  style="width:100%;max-width:480px;height:280px;border:none;display:block;margin:0 auto;"
  title="Wausau Ignite — at a glance"
  loading="lazy"
  scrolling="no">
</iframe>
```

The mini variants use the **same resize listener** as the full widgets — paste the `<script>` block once at the bottom of the page and it covers both. Mini and full can live on the same article page.

### Newsletter-style card (`?mini=tickets`)

Compact two-section card built for daily newsletter blocks (~390px tall, max 380px wide):

- **Last game** — opponent, final score (W/L color-coded), and the winning/losing pitcher line with each pitcher's season record + ERA
- **Next game** — date, time, opponent, venue, and both probable starters with their season W-L / ERA (when the league has posted them)
- **Tickets button** — small, secondary action; uses the game-specific ticket URL when the scraper has one, otherwise falls back to the team's general single-game tickets page
- **Full coverage link** — points to the WP&R landing page at `wausaupilotandreview.com/woodchucks-ignite/`

```html
<!-- Woodchucks newsletter card -->
<iframe
  data-team="woodchucks"
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/?team=woodchucks&mini=tickets"
  style="width:100%;max-width:380px;height:400px;border:none;display:block;margin:0 auto;"
  title="Woodchucks last & next"
  loading="lazy"
  scrolling="no">
</iframe>

<!-- Ignite newsletter card -->
<iframe
  data-team="ignite"
  src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/?team=ignite&mini=tickets"
  style="width:100%;max-width:380px;height:400px;border:none;display:block;margin:0 auto;"
  title="Ignite last & next"
  loading="lazy"
  scrolling="no">
</iframe>
```

**For web placement** (WordPress posts, articles) — the iframe above works perfectly.

**For email** (Mailchimp, Beehiiv, ConvertKit, native Mail clients, etc.) — every major email client strips `<iframe>` tags. Use the **static daily snapshot PNG** instead (next section).

### Email-friendly daily snapshot PNG

A GitHub Action ([`.github/workflows/snapshot.yml`](.github/workflows/snapshot.yml)) renders the `?mini=tickets` card to a static PNG once every morning (11:00 UTC = 6 AM CDT / 5 AM CST) and commits it to `docs/snapshots/`. The PNGs are served by GitHub Pages at:

- https://rowanflynnpilot.github.io/wpr-woodchucks-widget/snapshots/woodchucks-today.png
- https://rowanflynnpilot.github.io/wpr-woodchucks-widget/snapshots/ignite-today.png

Email-safe embed code — works in **Gmail, Outlook, Apple Mail, Yahoo Mail, mobile and desktop**:

```html
<!-- Woodchucks -->
<a href="https://wausaupilotandreview.com/woodchucks-ignite/" style="text-decoration:none">
  <img src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/snapshots/woodchucks-today.png"
       alt="Wausau Woodchucks — last game and probable starters"
       width="380" style="max-width:100%;height:auto;display:block;border:0;border-radius:8px">
</a>

<!-- Ignite -->
<a href="https://wausaupilotandreview.com/woodchucks-ignite/" style="text-decoration:none">
  <img src="https://rowanflynnpilot.github.io/wpr-woodchucks-widget/snapshots/ignite-today.png"
       alt="Wausau Ignite — last game and probable starters"
       width="380" style="max-width:100%;height:auto;display:block;border:0;border-radius:8px">
</a>
```

The image is 760px wide at 2x retina for sharp rendering; the `width="380"` attribute tells email clients to display it at standard size. The whole image is a clickable link to the WP&R landing page (where the live interactive widget lives). For a per-game tickets deep-link from email, the recipient lands on the WP&R article first and can click through from the live widget there.

The PNG is overwritten in place every morning, so the embed URL stays stable forever — no email-platform reconfiguration needed day-to-day.

To trigger a fresh snapshot manually (e.g. mid-day before a special newsletter):
1. Go to the [Actions tab](https://github.com/RowanFlynnPilot/wpr-woodchucks-widget/actions/workflows/snapshot.yml)
2. Click "Run workflow" → "Run workflow"
3. Wait ~2 min for it to finish and commit; PNG URL updates automatically

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
