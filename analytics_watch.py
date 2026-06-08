#!/usr/bin/env python3.11
"""
analytics_watch.py — real-time install watcher.

Polls PostHog every 5 minutes for new install events and fires a Telegram
notification immediately for each new one, with location, OS, and version.

Usage:
    python analytics_watch.py           # run continuously
    python analytics_watch.py --once    # check once and exit (good for cron)

Cron every 5 minutes:
    */5 * * * * cd /path/to/repo && python analytics_watch.py --once >> /tmp/boolcalc-watch.log 2>&1

State is stored in ~/.config/boolcalc/watch_state.json to avoid re-notifying
events across restarts.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")
POSTHOG_KEY         = os.environ.get("POSTHOG_PERSONAL_API_KEY", "")
POSTHOG_PROJECT     = os.environ.get("POSTHOG_PROJECT_ID", "")
POLL_INTERVAL       = 300  # seconds

_STATE_FILE = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "boolcalc" / "watch_state.json"


def _load_state() -> dict:
    try:
        return json.loads(_STATE_FILE.read_text()) if _STATE_FILE.exists() else {}
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def _get(url: str, headers: dict) -> dict | None:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[fetch error] {url}: {e}", file=sys.stderr)
        return None


def _send_telegram(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[telegram] token or chat_id not set", file=sys.stderr)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print(f"[telegram error] {e}", file=sys.stderr)


def _flag(country: str) -> str:
    flags = {
        "United States": "🇺🇸", "India": "🇮🇳", "Hong Kong": "🇭🇰",
        "China": "🇨🇳", "United Kingdom": "🇬🇧", "Germany": "🇩🇪",
        "France": "🇫🇷", "Canada": "🇨🇦", "Australia": "🇦🇺",
        "Japan": "🇯🇵", "Singapore": "🇸🇬", "Brazil": "🇧🇷",
        "Netherlands": "🇳🇱", "South Korea": "🇰🇷", "Russia": "🇷🇺",
    }
    return flags.get(country, "🌍")


def _format_event(ev: dict) -> str:
    props = ev.get("properties", {})
    country = props.get("$geoip_country_name", "Unknown")
    city    = props.get("$geoip_city_name", "")
    os_name = props.get("os", "?")
    version = props.get("version", "?")
    ip      = props.get("$ip", "?")
    ts      = ev.get("timestamp", "")[:16].replace("T", " ")
    location = f"{city}, {country}" if city else country

    return (
        f"📦 <b>New install</b>\n"
        f"{_flag(country)} {location}\n"
        f"🖥 {os_name}  •  v{version}\n"
        f"🕐 {ts} UTC\n"
        f"<code>{ip}</code>"
    )


def fetch_recent_installs() -> list[dict]:
    if not POSTHOG_KEY or not POSTHOG_PROJECT:
        return []
    headers = {"Authorization": f"Bearer {POSTHOG_KEY}"}
    params = urllib.parse.urlencode({"event": "install", "limit": 50, "order_by": "-timestamp"})
    data = _get(f"https://us.posthog.com/api/projects/{POSTHOG_PROJECT}/events/?{params}", headers)
    return (data or {}).get("results", [])


def check_once() -> int:
    state = _load_state()
    seen: set = set(state.get("seen_ids", []))
    events = fetch_recent_installs()

    new_events = [e for e in events if e.get("uuid") not in seen]

    # Sort oldest-first so notifications arrive in order
    new_events.sort(key=lambda e: e.get("timestamp", ""))

    notified = 0
    for ev in new_events:
        uid = ev.get("uuid")
        msg = _format_event(ev)
        print(f"[new install] {ev.get('timestamp', '')[:19]} — sending notification")
        print(msg.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", ""))
        _send_telegram(msg)
        seen.add(uid)
        notified += 1

    if not new_events:
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] no new installs")

    # Keep seen set bounded to last 500 IDs
    state["seen_ids"] = list(seen)[-500:]
    _save_state(state)
    return notified


def run_loop() -> None:
    print(f"Watching for new installs every {POLL_INTERVAL}s — Ctrl+C to stop")
    while True:
        check_once()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if not POSTHOG_KEY:
        print("POSTHOG_PERSONAL_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set", file=sys.stderr)
        sys.exit(1)

    if "--once" in sys.argv:
        check_once()
    else:
        run_loop()
