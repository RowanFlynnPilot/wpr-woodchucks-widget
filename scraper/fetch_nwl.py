#!/usr/bin/env python3
"""
Wausau Woodchucks / NWL Data Scraper
Fetches schedule, standings, and game data from the NWL Scorebook API
and writes static JSON files to docs/data/ for the widget to consume.

API Base: https://scorebook.northwoodsleague.com/api/
Woodchucks Team ID: 68

Usage:
    python fetch_nwl.py                  # Fetch all data
    python fetch_nwl.py --schedule-only  # Fetch schedule only
    python fetch_nwl.py --standings-only # Fetch standings only
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)

API_BASE = "https://scorebook.northwoodsleague.com/api"
WOODCHUCKS_TEAM_ID = 68
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "data"

# Standings group structure:
# The API returns 3 groups: [0]=1st half, [1]=2nd half, [2]=full season
# Each group is a dict with division names as keys:
#   "Great Lakes East", "Great Lakes West", "Great Plains East", "Great Plains West"
HALF_INDICES = {"first_half": 0, "second_half": 1, "full": 2}


def fetch_json(endpoint, params=None):
    """Fetch JSON from the NWL Scorebook API."""
    url = f"{API_BASE}/{endpoint}"
    print(f"  Fetching {url} ...")
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def fetch_schedule():
    """Fetch the Woodchucks schedule and filter for team 68."""
    data = fetch_json("schedule", params={"teamid": WOODCHUCKS_TEAM_ID})
    if not data or "schedule" not in data:
        print("  WARNING: No schedule data returned")
        return None

    info = data["schedule"]["info"]
    all_games = data["schedule"]["games"]

    # Filter for Woodchucks games
    games = []
    for g in all_games:
        is_home = g["home_team"] == WOODCHUCKS_TEAM_ID
        is_away = g["visitor_team"] == WOODCHUCKS_TEAM_ID
        if not (is_home or is_away):
            continue

        opponent_name = g["visitor_team_name"] if is_home else g["home_team_name"]
        opponent_abbr = g["visitor_team_abv"] if is_home else g["home_team_abv"]
        opponent_logo = g.get("visitor_team_logo") if is_home else g.get("home_team_logo")

        # Parse date from MM-DD-YYYY to YYYY-MM-DD
        try:
            dt = datetime.strptime(g["date"], "%m-%d-%Y")
            iso_date = dt.strftime("%Y-%m-%d")
            day_abbr = dt.strftime("%a")
        except ValueError:
            iso_date = g["date"]
            day_abbr = ""

        game_entry = {
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
        }

        # Add score data if game is final or in progress
        if g.get("status_code", 0) >= 1:
            game_entry["visitor_score"] = g.get("visitor_score")
            game_entry["home_score"] = g.get("home_score")
            if is_home:
                game_entry["chucks_score"] = g.get("home_score")
                game_entry["opponent_score"] = g.get("visitor_score")
            else:
                game_entry["chucks_score"] = g.get("visitor_score")
                game_entry["opponent_score"] = g.get("home_score")

        games.append(game_entry)

    schedule_data = {
        "season": info.get("season"),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_games": len(games),
        "games": games,
    }

    return schedule_data


def fetch_standings():
    """Fetch league standings (all halves)."""
    data = fetch_json("standings")
    if not data or "standings" not in data:
        print("  WARNING: No standings data returned")
        return None

    info = data["standings"]["info"]
    groups = data["standings"]["groups"]

    def extract_division_by_name(group, division_name):
        """Extract team standings for a specific division from a group dict."""
        if not group or division_name not in group:
            return []
        teams = group[division_name]
        return [
            {
                "team_id": t["team"]["idteam"],
                "name": t["team"]["Name"],
                "abbr": t["team"].get("Abv", ""),
                "division": t["team"].get("division", ""),
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
            for t in teams
        ]

    standings_data = {
        "season": info.get("season"),
        "season_name": info.get("season_name", ""),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "great_lakes_west": {},
        "great_lakes_east": {},
    }

    for half_name, idx in HALF_INDICES.items():
        if idx < len(groups):
            group = groups[idx]
            standings_data["great_lakes_west"][half_name] = extract_division_by_name(group, "Great Lakes West")
            standings_data["great_lakes_east"][half_name] = extract_division_by_name(group, "Great Lakes East")
        else:
            standings_data["great_lakes_west"][half_name] = []
            standings_data["great_lakes_east"][half_name] = []

    return standings_data


def write_json(filename, data):
    """Write data to a JSON file in the output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {filepath} ({filepath.stat().st_size:,} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Fetch NWL Woodchucks data")
    parser.add_argument("--schedule-only", action="store_true", help="Fetch schedule only")
    parser.add_argument("--standings-only", action="store_true", help="Fetch standings only")
    args = parser.parse_args()

    fetch_all = not args.schedule_only and not args.standings_only

    print(f"=== WPR Woodchucks Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    if fetch_all or args.schedule_only:
        print("\n[1/2] Fetching schedule...")
        schedule = fetch_schedule()
        if schedule:
            write_json("schedule.json", schedule)
            print(f"  → {schedule['total_games']} games for season {schedule['season']}")

    if fetch_all or args.standings_only:
        print("\n[2/2] Fetching standings...")
        standings = fetch_standings()
        if standings:
            write_json("standings.json", standings)
            print(f"  → Season: {standings['season_name']}")

    # Write meta
    meta = {
        "last_scrape": datetime.now(timezone.utc).isoformat(),
        "team_id": WOODCHUCKS_TEAM_ID,
        "team_name": "Wausau Woodchucks",
        "api_base": API_BASE,
    }
    write_json("meta.json", meta)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
