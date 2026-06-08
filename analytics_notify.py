#!/usr/bin/env python3.11
"""
analytics_notify.py — daily Telegram digest for boolcalc traffic stats.

Usage:
    python analytics_notify.py            # fetch stats + send Telegram message
    python analytics_notify.py --setup    # print cron setup instructions
    python analytics_notify.py --dry-run  # print digest without sending

Cron (9am daily):
    0 9 * * * cd /path/to/repo && python analytics_notify.py >> /tmp/boolcalc-notify.log 2>&1
"""
from __future__ import annotations

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))
from ui.fetchers import fetch_pypi, fetch_github, fetch_docker, fetch_posthog

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
POSTHOG_KEY = os.environ.get("POSTHOG_PERSONAL_API_KEY", "")
POSTHOG_PROJECT = os.environ.get("POSTHOG_PROJECT_ID", "")


def _send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — cannot send.", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
            return resp.get("ok", False)
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)
        return False


def build_digest() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"<b>📦 boolcalc digest — {today}</b>\n"]

    # PyPI
    try:
        pypi = fetch_pypi()
        d = (pypi.get("recent") or {}).get("data", {})
        day = d.get("last_day", 0)
        week = d.get("last_week", 0)
        month = d.get("last_month", 0)
        lines.append(f"<b>PyPI</b>")
        lines.append(f"  Day: {day:,}  |  Week: {week:,}  |  Month: {month:,}")
    except Exception as e:
        lines.append(f"<b>PyPI</b>  ⚠️ {e}")

    lines.append("")

    # GitHub
    if GITHUB_TOKEN:
        try:
            gh = fetch_github(GITHUB_TOKEN)
            lines.append("<b>GitHub Traffic (14d)</b>")
            for repo_key, label in [
                ("bool-LLM-ngn", "bool-LLM-ngn"),
                ("boolean-algebra-engine-python", "bae-python"),
            ]:
                data = gh.get(repo_key, {})
                views = (data.get("views") or {}).get("count", 0)
                clones = (data.get("clones") or {}).get("count", 0)
                uv = (data.get("views") or {}).get("uniques", 0)
                lines.append(f"  {label}: {views:,} views ({uv} uniq)  |  {clones:,} clones")
        except Exception as e:
            lines.append(f"<b>GitHub</b>  ⚠️ {e}")
    else:
        lines.append("<b>GitHub</b>  ⚠️ GITHUB_TOKEN not set")

    lines.append("")

    # PostHog
    if POSTHOG_KEY and POSTHOG_PROJECT:
        try:
            ph = fetch_posthog(POSTHOG_KEY, POSTHOG_PROJECT)
            events = (ph.get("events") or {}).get("results", [])
            today_count = sum(1 for e in events if (e.get("timestamp", "") or "")[:10] == today)
            lines.append("<b>PostHog installs</b>")
            lines.append(f"  Today: {today_count}  |  Recent total: {len(events)}")
        except Exception as e:
            lines.append(f"<b>PostHog</b>  ⚠️ {e}")
    else:
        lines.append("<b>PostHog</b>  ⚠️ keys not set")

    lines.append("")

    # Docker
    try:
        docker = fetch_docker()
        if docker:
            pulls = docker.get("pull_count", 0)
            stars = docker.get("star_count", 0)
            lines.append("<b>Docker Hub</b>  (shrvx/bool-llm-ngn)")
            lines.append(f"  Pulls: {pulls:,}  |  Stars: {stars}")
        else:
            lines.append("<b>Docker Hub</b>  ⚠️ unreachable")
    except Exception as e:
        lines.append(f"<b>Docker Hub</b>  ⚠️ {e}")

    return "\n".join(lines)


def print_setup():
    script = Path(__file__).resolve()
    print("Add to crontab  (crontab -e):\n")
    print(f"  0 9 * * *  cd {script.parent} && python {script} >> /tmp/boolcalc-notify.log 2>&1\n")
    print("This sends the digest every day at 9:00 AM local time.")
    print("Make sure your .env file is present in the repo root with all keys set.")


if __name__ == "__main__":
    if "--setup" in sys.argv:
        print_setup()
        sys.exit(0)

    dry_run = "--dry-run" in sys.argv

    print("Fetching stats…")
    digest = build_digest()

    # Strip HTML tags for terminal output
    import re
    plain = re.sub(r"<[^>]+>", "", digest)
    print("\n" + plain)

    if dry_run:
        print("\n[dry-run] Not sending to Telegram.")
    else:
        print("\nSending to Telegram…")
        ok = _send_telegram(digest)
        print("Sent." if ok else "Failed — check logs above.")
