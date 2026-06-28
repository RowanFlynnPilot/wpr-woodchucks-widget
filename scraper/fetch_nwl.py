#!/usr/bin/env python3
"""
NWL Data Scraper (Woodchucks + Ignite)

Fetches schedule and standings from the NWL Scorebook API and writes static
JSON files to docs/data/<team>/ for the widget to consume.

Baseball (Woodchucks): https://scorebook.northwoodsleague.com/api/
Softball (Ignite):     https://scorebook-softball.northwoodsleague.com/api/

Both endpoints return the same response shape, so one fetcher handles both.

Usage:
    python fetch_nwl.py --team woodchucks
    python fetch_nwl.py --team ignite
    python fetch_nwl.py --team all              # both, sequentially
    python fetch_nwl.py --team woodchucks --schedule-only
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)

TEAMS = {
    "woodchucks": {
        "name": "Wausau Woodchucks",
        "sport": "Baseball",
        "team_id": 68,
        "api_base": "https://scorebook.northwoodsleague.com/api",
        # Baseball uses Great Lakes East/West divisions.
        "divisions": ["Great Lakes West", "Great Lakes East"],
    },
    "ignite": {
        "name": "Wausau Ignite",
        "sport": "Softball",
        "team_id": 5,
        "api_base": "https://scorebook-softball.northwoodsleague.com/api",
        # Softball is one division ("NWL Softball"). Bucketed into great_lakes_west
        # for now so the widget renders it without UI changes; great_lakes_east stays empty.
        "divisions": ["NWL Softball"],
    },
}

OUTPUT_ROOT = Path(__file__).parent.parent / "docs" / "data"

# API returns 3 groups: [0]=1st half, [1]=2nd half, [2]=full season
HALF_INDICES = {"first_half": 0, "second_half": 1, "full": 2}


def fetch_json(api_base, endpoint, params=None):
    """Fetch JSON from a given NWL Scorebook API base."""
    url = f"{api_base}/{endpoint}"
    print(f"  Fetching {url} ...")
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def fetch_schedule(team, logo_map=None):
    """Fetch the team's schedule and filter for this team's games.

    If `logo_map` is provided (a dict), it gets populated with every team's
    `team_id -> logo_url` from the league-wide schedule. We use this to enrich
    the standings (which the API returns without logos) in a second pass.
    """
    team_id = team["team_id"]
    data = fetch_json(team["api_base"], "schedule", params={"teamid": team_id})
    if not data or "schedule" not in data:
        print("  WARNING: No schedule data returned")
        return None

    info = data["schedule"]["info"]
    all_games = data["schedule"]["games"]

    # Build logo map from the full league schedule (every team appears as
    # home or visitor in at least one game).
    if logo_map is not None:
        for g in all_games:
            for side in ("home", "visitor"):
                tid = g.get(f"{side}_team")
                logo = g.get(f"{side}_team_logo")
                if tid and logo and tid not in logo_map:
                    logo_map[tid] = logo

    games = []
    for g in all_games:
        is_home = g["home_team"] == team_id
        is_away = g["visitor_team"] == team_id
        if not (is_home or is_away):
            continue

        opponent_name = g["visitor_team_name"] if is_home else g["home_team_name"]
        opponent_abbr = g["visitor_team_abv"] if is_home else g["home_team_abv"]
        opponent_logo = g.get("visitor_team_logo") if is_home else g.get("home_team_logo")

        try:
            dt = datetime.strptime(g["date"], "%m-%d-%Y")
            iso_date = dt.strftime("%Y-%m-%d")
            day_abbr = dt.strftime("%a")
        except ValueError:
            iso_date = g["date"]
            day_abbr = ""

        entry = {
            "id": g["id"],
            "date": iso_date,
            "day": day_abbr,
            "time": g["time"].strip(),
            "home": is_home,
            "opponent": opponent_name,
            "opponent_abbr": opponent_abbr,
            "opponent_logo": opponent_logo,
            "location": g.get("location", ""),
            "status_code": g.get("status_code", 0),
            "status": g.get("status", "Scheduled"),
            "broadcast": g.get("broadcast", ""),
            "broadcast_label": g.get("broadcast_label", ""),
            # Game-specific ticket purchase URL (when available). Mini-tickets
            # variant uses this; falls back to TEAM.ticketsUrl on the widget side.
            "tickets_url": g.get("tickets_url", "") or "",
        }

        if g.get("status_code", 0) >= 1:
            entry["visitor_score"] = g.get("visitor_score")
            entry["home_score"] = g.get("home_score")
            if is_home:
                # Widget reads chucks_score / opponent_score regardless of team
                # (legacy name from the Woodchucks-only era — kept stable for the
                # frontend; means "our team's score").
                entry["chucks_score"] = g.get("home_score")
                entry["opponent_score"] = g.get("visitor_score")
            else:
                entry["chucks_score"] = g.get("visitor_score")
                entry["opponent_score"] = g.get("home_score")

        games.append(entry)

    return {
        "season": info.get("season"),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_games": len(games),
        "games": games,
    }


def fetch_standings(team, logo_map=None):
    """Fetch league standings (all halves) for this team's sport.

    `logo_map` (built by fetch_schedule) supplies the team_id -> logo URL
    lookup; the standings API doesn't include logos itself.
    """
    data = fetch_json(team["api_base"], "standings")
    if not data or "standings" not in data:
        print("  WARNING: No standings data returned")
        return None

    info = data["standings"]["info"]
    groups = data["standings"]["groups"]
    lmap = logo_map or {}

    def extract(group, division_name):
        if not group or division_name not in group:
            return []
        return [
            {
                "team_id": t["team"]["idteam"],
                "name": t["team"]["Name"],
                "abbr": t["team"].get("Abv", ""),
                "division": t["team"].get("division", ""),
                "logo": lmap.get(t["team"]["idteam"]) or "",
                "W": t["W"],
                "L": t["L"],
                "T": t.get("T", 0),
                "PCT": t["PCT"],
                "GB": t["GB"],
                "STREAK": t.get("STREAK", ""),
                "LAST10": t.get("LAST10", ""),
                "first_half_clinched": t["team"].get("first_half_clinched", 0),
                "second_half_clinched": t["team"].get("second_half_clinched", 0),
            }
            for t in group[division_name]
        ]

    # The widget keys off great_lakes_west / great_lakes_east. Softball only has
    # one division ("NWL Softball") — bucket it into great_lakes_west so the
    # widget renders it without UI changes; great_lakes_east stays empty.
    primary_division = team["divisions"][0]
    secondary_division = team["divisions"][1] if len(team["divisions"]) > 1 else None

    standings = {
        "season": info.get("season"),
        "season_name": info.get("season_name", ""),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "great_lakes_west": {},
        "great_lakes_east": {},
    }

    for half_name, idx in HALF_INDICES.items():
        group = groups[idx] if idx < len(groups) else None
        standings["great_lakes_west"][half_name] = extract(group, primary_division)
        standings["great_lakes_east"][half_name] = extract(group, secondary_division) if secondary_division else []

    return standings


def write_json(output_dir, filename, data):
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {filepath} ({filepath.stat().st_size:,} bytes)")


def run_team(slug, args):
    team = TEAMS[slug]
    output_dir = OUTPUT_ROOT / slug
    fetch_all = not args.schedule_only and not args.standings_only

    print(f"\n=== {team['name']} ({team['sport']}) — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    logo_map = {}

    if fetch_all or args.schedule_only:
        print(f"\n[schedule]")
        schedule = fetch_schedule(team, logo_map=logo_map)
        if schedule:
            write_json(output_dir, "schedule.json", schedule)
            print(f"  ->{schedule['total_games']} games for season {schedule['season']} ({len(logo_map)} team logos cached)")

    if fetch_all or args.standings_only:
        # Standings need the logo map. If we skipped --schedule, do a quick
        # logo-only fetch first so standings rows still get their logos.
        if not logo_map:
            print(f"\n[logo lookup]")
            fetch_schedule(team, logo_map=logo_map)
            print(f"  ->{len(logo_map)} team logos cached")
        print(f"\n[standings]")
        standings = fetch_standings(team, logo_map=logo_map)
        if standings:
            write_json(output_dir, "standings.json", standings)
            print(f"  ->Season: {standings['season_name']}")

    meta = {
        "last_scrape": datetime.now(timezone.utc).isoformat(),
        "team_id": team["team_id"],
        "team_name": team["name"],
        "sport": team["sport"],
        "api_base": team["api_base"],
    }
    write_json(output_dir, "meta.json", meta)


def main():
    parser = argparse.ArgumentParser(description="Fetch NWL data for Woodchucks and/or Ignite")
    parser.add_argument(
        "--team",
        choices=list(TEAMS.keys()) + ["all"],
        default="all",
        help="Which team to fetch (default: all)",
    )
    parser.add_argument("--schedule-only", action="store_true", help="Fetch schedule only")
    parser.add_argument("--standings-only", action="store_true", help="Fetch standings only")
    args = parser.parse_args()

    targets = list(TEAMS.keys()) if args.team == "all" else [args.team]
    for slug in targets:
        run_team(slug, args)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
