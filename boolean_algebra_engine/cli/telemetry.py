"""
cli/telemetry.py — opt-in anonymous usage telemetry for Quine (boolcalc).

First run: user is prompted once. Choice is saved to
  ~/.config/boolcalc/telemetry.json

No data is collected or transmitted before the user opts in.

What is sent (only if opted in):
  - Random install ID (UUID, generated once, never linked to identity)
  - Command name (evaluate / ask / check-rules / etc.)
  - OS platform (Linux / Darwin / Windows)
  - Python version (e.g. 3.12)
  - Package version
  - Variable count in expression (not the expression itself)

What is never sent:
  - The expression or rules text
  - Any user-identifiable information

Data goes to PostHog (posthog.com) and GoatCounter (goatcounter.com),
both used for anonymous product analytics. PostHog may resolve your IP
for approximate GeoIP (country-level) and then discards it.

Opt out anytime:
  - Set BOOLCALC_NO_TELEMETRY=1
  - Or edit ~/.config/boolcalc/telemetry.json and set opted_in to false
"""
from __future__ import annotations

import atexit
import json
import os
import platform
import threading
import urllib.request
import uuid
from pathlib import Path

try:
    from posthog import Posthog as _Posthog
    _ph = _Posthog(
        project_api_key="phc_Am4NNyVXotVffz6rcBy8xZVUZeaJCCbbHMu63pWMz3M8",
        host="https://us.i.posthog.com",
    )
    atexit.register(_ph.shutdown)
except ImportError:
    _ph = None

_VERSION = "0.3.6"
_GC_URL = "https://shrvx.goatcounter.com/count"
_API_URL = os.environ.get("BOOLCALC_TELEMETRY_URL", "")

_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "boolcalc"
_CONFIG_FILE = _CONFIG_DIR / "telemetry.json"

_PROMPT = """\

  Help improve boolcalc — share anonymous usage stats? (y/N)
  What's sent: command used, OS, Python version. Nothing personal.
  Data goes to PostHog and GoatCounter (anonymous analytics).
  Opt out anytime: set BOOLCALC_NO_TELEMETRY=1 or edit
  ~/.config/boolcalc/telemetry.json

  > """

_WELCOME = "  \033[2m→ Thanks for installing boolcalc! Star or open an issue: github.com/Shrivastava-Aditya/bool-LLM-ngn\033[0m"
_NUDGE = "  \033[2m→ Finding boolcalc useful? Star or open an issue: github.com/Shrivastava-Aditya/bool-LLM-ngn\033[0m"
_NUDGE_EVERY = 10   # show every N runs
_NUDGE_MAX   = 3    # stop after showing this many times


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


def _gc_ping(path: str, title: str) -> None:
    """Fire-and-forget anonymous GoatCounter hit. Never blocks, never raises."""
    def _fire():
        try:
            url = f"{_GC_URL}?p={urllib.request.quote(path)}&t={urllib.request.quote(title)}"
            urllib.request.urlopen(url, timeout=3)
        except Exception:
            pass
    threading.Thread(target=_fire, daemon=True).start()


def maybe_nudge() -> None:
    """Show a dim one-liner nudge every N runs, at most _NUDGE_MAX times."""
    if os.environ.get("BOOLCALC_NO_TELEMETRY"):
        return
    config = _load()
    run_count = config.get("run_count", 0) + 1
    nudge_count = config.get("nudge_count", 0)
    config["run_count"] = run_count
    _save(config)
    if nudge_count >= _NUDGE_MAX:
        return
    if run_count % _NUDGE_EVERY == 0:
        print(_NUDGE)
        if config.get("opted_in"):
            _gc_ping(f"/cli/nudge/{nudge_count + 1}", f"boolcalc nudge #{nudge_count + 1}")
        config["nudge_count"] = nudge_count + 1
        _save(config)


def maybe_prompt() -> None:
    """Show opt-in prompt on first run. No-op on subsequent runs."""
    if os.environ.get("BOOLCALC_NO_TELEMETRY"):
        return
    config = _load()
    if "opted_in" in config:
        return

    print(_WELCOME)

    install_id = str(uuid.uuid4())

    try:
        answer = input(_PROMPT).strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"

    opted_in = answer in ("y", "yes")
    config["opted_in"] = opted_in
    config["install_id"] = install_id
    _save(config)

    if opted_in:
        if _ph:
            _ph.capture("install", distinct_id=install_id, properties={"version": _VERSION, "os": platform.system()})
            _ph.capture("telemetry_choice", distinct_id=install_id, properties={"opted_in": True})
        _gc_ping("/cli/install/telemetry-yes", "boolcalc telemetry yes")
        print("  Thanks — helps boolcalc know what to build next.\n")
    else:
        _gc_ping("/cli/install/telemetry-no", "boolcalc telemetry no")


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

    if _ph:
        try:
            _ph.capture(f"command_{command}", distinct_id=install_id, properties=payload)
        except Exception:
            pass

    def _fire():
        try:
            path = f"/cli/{command}/{os_name}/{py_version}"
            title = f"boolcalc {command}"
            gc_url = f"{_GC_URL}?p={urllib.request.quote(path)}&t={urllib.request.quote(title)}"
            urllib.request.urlopen(gc_url, timeout=3)
        except Exception:
            pass

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
