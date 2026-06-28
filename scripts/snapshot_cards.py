#!/usr/bin/env python3
"""
Daily snapshot script — renders the ?mini=tickets cards as static PNGs
that can be embedded in email newsletters (where iframes are stripped).

Serves docs/ locally, opens each team's card in headless Chromium, waits
for the async pitcher / probable-starters fetches to finish, and writes
the cropped card to docs/snapshots/<team>-today.png.

Run by .github/workflows/snapshot.yml once a day, then commits the PNGs
back to the repo. GitHub Pages serves them as
  https://rowanflynnpilot.github.io/wpr-woodchucks-widget/snapshots/<team>-today.png

Usage:
    pip install -r scripts/requirements.txt
    playwright install --with-deps chromium
    python scripts/snapshot_cards.py
"""

import functools
import http.server
import os
import socketserver
import sys
import threading
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install -r scripts/requirements.txt")
    sys.exit(1)

PORT = 8765
ROOT = Path(__file__).parent.parent
DOCS_DIR = ROOT / "docs"
SNAPSHOTS_DIR = DOCS_DIR / "snapshots"
TEAMS = ["woodchucks", "ignite"]
# Retina-quality PNG so the 380px-wide embed looks crisp on high-DPI screens.
DEVICE_SCALE = 2


def start_server():
    """Serve docs/ on PORT in a background daemon thread."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(DOCS_DIR)
    )
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"Local server running on http://127.0.0.1:{PORT}")
    return httpd


def snapshot_team(page, team):
    url = f"http://127.0.0.1:{PORT}/?team={team}&mini=tickets"
    print(f"\n[{team}] Loading {url}")
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_selector(".mt", timeout=10000)

    # Wait for the async hydration (pitcher line + probable starters) to land.
    # If the API hasn't published a piece of data yet the widget renders a
    # fallback like "Probable starters not yet posted." in place of the loader,
    # which also satisfies this wait. Tolerate timeout so a stuck fetch doesn't
    # break the snapshot — we'll just capture whatever's on screen.
    try:
        page.wait_for_function(
            "document.querySelectorAll('.mt-loading').length === 0",
            timeout=15000,
        )
        print(f"[{team}] Hydration complete")
    except Exception as e:
        print(f"[{team}] WARNING: hydration didn't fully complete ({e}). Snapshotting anyway.")

    # Brief settle for web font swap + opponent logo decode.
    page.wait_for_timeout(1200)

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    out = SNAPSHOTS_DIR / f"{team}-today.png"
    page.locator(".mt").screenshot(path=str(out))
    print(f"[{team}] Wrote {out} ({out.stat().st_size:,} bytes)")


def main():
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    start_server()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 420, "height": 700},
            device_scale_factor=DEVICE_SCALE,
        )
        page = context.new_page()
        for team in TEAMS:
            snapshot_team(page, team)
        browser.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
