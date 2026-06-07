"""
cli/telemetry.py — opt-in anonymous usage telemetry for boolcalc.

First run: user is prompted once. Choice is saved to
  ~/.config/boolcalc/telemetry.json

What is sent (if opted in):
  - Random install ID (UUID, generated once, never linked to identity)
  - Command name (evaluate / simplify / ask / check-rules / etc.)
  - OS (Linux / Darwin / Windows)
  - Python version (e.g. 3.12)
  - Package version
  - Variable count in expression (not the expression itself)

What is never sent:
  - The expression or rules text
  - IP address (not included in payload)
  - Any user-identifiable information

Telemetry goes to GoatCounter (already in use for web analytics) and
optionally to a structured API endpoint via BOOLCALC_TELEMETRY_URL.
"""
from __future__ import annotations

import json
import os
import platform
import threading
import urllib.request
import uuid
from pathlib import Path

_VERSION = "0.3.1"
_GC_URL = "https://shrvx.goatcounter.com/count"
_API_URL = os.environ.get("BOOLCALC_TELEMETRY_URL", "")

_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "boolcalc"
_CONFIG_FILE = _CONFIG_DIR / "telemetry.json"

_PROMPT = """\

  Help improve Quine — share anonymous usage stats? (y/N)
  What's sent: command used, OS, Python version. Nothing personal.
  Opt out anytime: set BOOLCALC_NO_TELEMETRY=1 or edit
  ~/.config/boolcalc/telemetry.json

  > """


def _load() -> dict:
    try:
        return json.loads(_CONFIG_FILE.read_text()) if _CONFIG_FILE.exists() else {}
    except Exception:
        return {}


def _save(config: dict) -> None:
    try:
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE.write_text(json.dumps(config, indent=2))
    except Exception:
        pass


def maybe_prompt() -> None:
    """Show opt-in prompt on first run. No-op on subsequent runs."""
    if os.environ.get("BOOLCALC_NO_TELEMETRY"):
        return
    config = _load()
    if "opted_in" in config:
        return

    try:
        answer = input(_PROMPT).strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"

    opted_in = answer in ("y", "yes")
    config["opted_in"] = opted_in
    config["install_id"] = str(uuid.uuid4())
    _save(config)
    if opted_in:
        print("  Thanks — helps us know what to build next.\n")


def send(command: str, **kwargs) -> None:
    """Fire-and-forget telemetry. Never blocks, never raises."""
    if os.environ.get("BOOLCALC_NO_TELEMETRY"):
        return
    config = _load()
    if not config.get("opted_in"):
        return

    os_name = platform.system() or "Unknown"
    py_version = f"{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}"
    install_id = config.get("install_id", "unknown")

    payload = {
        "install_id": install_id,
        "version": _VERSION,
        "os": os_name,
        "python": py_version,
        "command": command,
        **{k: v for k, v in kwargs.items() if v is not None},
    }

    def _fire():
        # GoatCounter: structured path gives OS/command/python breakdown in dashboard
        try:
            path = f"/cli/{command}/{os_name}/{py_version}"
            title = f"boolcalc {command}"
            gc_url = f"{_GC_URL}?p={urllib.request.quote(path)}&t={urllib.request.quote(title)}"
            urllib.request.urlopen(gc_url, timeout=3)
        except Exception:
            pass

        # Structured API endpoint (set BOOLCALC_TELEMETRY_URL to enable)
        if _API_URL:
            try:
                data = json.dumps(payload).encode()
                req = urllib.request.Request(
                    _API_URL,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass

    threading.Thread(target=_fire, daemon=True).start()
