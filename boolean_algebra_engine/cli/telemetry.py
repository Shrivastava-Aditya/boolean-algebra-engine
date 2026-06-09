"""
cli/telemetry.py — anonymous usage telemetry for boolcalc.

Telemetry is ON by default. No personal data is collected.

What is sent:
  - Random install ID (UUID, generated once, never linked to identity)
  - Command name (evaluate / ask / check-rules / etc.)
  - OS platform (Linux / Darwin / Windows)
  - Python version (e.g. 3.12)
  - Package version
  - Variable count in expression (not the expression itself)

What is never sent:
  - The expression or rules text
  - Any user-identifiable information

Data goes to PostHog (posthog.com) and GoatCounter (goatcounter.com).
PostHog may resolve your IP for approximate GeoIP (country-level) and
then discards it.

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
import urllib.parse
import uuid
from pathlib import Path

try:
    from posthog import Posthog as _Posthog
    _ph = _Posthog(
        project_api_key="phc_Am4NNyVXotVffz6rcBy8xZVUZeaJCCbbHMu63pWMz3M8",
        host="https://us.i.posthog.com",
        disable_geoip=False,
    )
    atexit.register(_ph.shutdown)
except ImportError:
    _ph = None

try:
    import importlib.metadata as _meta
    _VERSION = _meta.version("boolean-algebra-engine")
except Exception:
    _VERSION = "unknown"

_GC_URL    = "https://shrvx.goatcounter.com/count"
_API_URL   = os.environ.get("BOOLCALC_TELEMETRY_URL", "")
_PH_KEY    = "phc_Am4NNyVXotVffz6rcBy8xZVUZeaJCCbbHMu63pWMz3M8"

_CONFIG_DIR  = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "boolcalc"
_CONFIG_FILE = _CONFIG_DIR / "telemetry.json"

_WELCOME     = "  \033[2m→ boolcalc collects anonymous usage stats. Opt out: BOOLCALC_NO_TELEMETRY=1\033[0m"
_NUDGE       = "  \033[2m→ Finding boolcalc useful? Star or open an issue: github.com/Shrivastava-Aditya/bool-LLM-ngn\033[0m"
_NUDGE_EVERY = 10
_NUDGE_MAX   = 3
_SURVEY_AT   = 5   # show survey after this many runs


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
    def _fire():
        try:
            url = f"{_GC_URL}?p={urllib.parse.quote(path)}&t={urllib.parse.quote(title)}"
            urllib.request.urlopen(url, timeout=3)
        except Exception:
            pass
    threading.Thread(target=_fire, daemon=True).start()


def _fetch_surveys() -> list[dict]:
    """Fetch active surveys from PostHog's public surveys endpoint."""
    try:
        url = f"https://us.i.posthog.com/api/surveys/?token={_PH_KEY}"
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        return data.get("surveys", [])
    except Exception:
        return []


def _run_survey(survey: dict) -> dict:
    """Render survey questions in the terminal and return responses dict."""
    questions = survey.get("questions", [])
    if not questions:
        return {}

    dim  = "\033[2m"
    bold = "\033[1m"
    rst  = "\033[0m"
    print(f"\n  {bold}Quick question about boolcalc{rst} {dim}(takes ~30s, Ctrl+C to skip){rst}")
    if survey.get("description"):
        print(f"  {dim}{survey['description']}{rst}")
    print()

    responses: dict = {}

    for i, q in enumerate(questions):
        qtype    = q.get("type", "open")
        question = q.get("question", "")
        required = q.get("required", False)

        print(f"  {bold}{question}{rst}")

        try:
            if qtype == "rating":
                scale   = q.get("scale", 10)
                low_lbl = q.get("lowerLabel", "Not likely")
                high_lbl = q.get("upperLabel", "Very likely")
                print(f"  {dim}1–{scale}  ({low_lbl} → {high_lbl}){rst}")
                while True:
                    raw = input("  > ").strip()
                    if not raw and not required:
                        break
                    if raw.isdigit() and 1 <= int(raw) <= scale:
                        responses[_survey_key(i)] = int(raw)
                        break
                    print(f"  {dim}Enter a number between 1 and {scale}{rst}")

            elif qtype in ("single_choice", "multiple_choice"):
                choices = q.get("choices", [])
                for idx, c in enumerate(choices, 1):
                    print(f"  {dim}{idx}.{rst} {c}")
                multi = qtype == "multiple_choice"
                hint  = "comma-separated numbers" if multi else "number"
                while True:
                    raw = input(f"  > ({hint}) ").strip()
                    if not raw and not required:
                        break
                    try:
                        picks = [int(x.strip()) for x in raw.split(",")]
                        if all(1 <= p <= len(choices) for p in picks):
                            selected = [choices[p - 1] for p in picks]
                            responses[_survey_key(i)] = selected if multi else selected[0]
                            break
                    except ValueError:
                        pass
                    print(f"  {dim}Invalid choice{rst}")

            elif qtype == "link":
                link = q.get("link", "")
                if link:
                    print(f"  {dim}{link}{rst}")
                input("  Press Enter to continue... ")

            else:  # open
                raw = input("  > ").strip()
                if raw:
                    responses[_survey_key(i)] = raw

        except (EOFError, KeyboardInterrupt):
            print(f"\n  {dim}Skipped — thanks anyway!{rst}\n")
            return responses

        print()

    print(f"  {dim}Thanks for your feedback!{rst}\n")
    return responses


def _survey_key(index: int) -> str:
    return "$survey_response" if index == 0 else f"$survey_response_{index}"


def maybe_nudge() -> None:
    """Increment run counter, show nudge every N runs, trigger survey at run N."""
    if os.environ.get("BOOLCALC_NO_TELEMETRY"):
        return
    config = _load()
    run_count   = config.get("run_count", 0) + 1
    nudge_count = config.get("nudge_count", 0)
    config["run_count"] = run_count
    _save(config)

    # Survey — show once at SURVEY_AT runs
    if run_count == _SURVEY_AT and not config.get("survey_done") and config.get("opted_in"):
        surveys = _fetch_surveys()
        if surveys:
            survey     = surveys[0]
            install_id = config.get("install_id", "unknown")

            if _ph:
                _ph.capture(
                    "survey shown",
                    distinct_id=install_id,
                    properties={"$survey_id": survey["id"], "$survey_name": survey.get("name", "")},
                )

            responses = _run_survey(survey)
            if responses and _ph:
                _ph.capture(
                    "survey sent",
                    distinct_id=install_id,
                    properties={
                        "$survey_id":   survey["id"],
                        "$survey_name": survey.get("name", ""),
                        **responses,
                    },
                )
            config["survey_done"] = True
            _save(config)
        return

    # Nudge
    if nudge_count >= _NUDGE_MAX:
        return
    if run_count % _NUDGE_EVERY == 0:
        print(_NUDGE)
        if config.get("opted_in"):
            _gc_ping(f"/cli/nudge/{nudge_count + 1}", f"boolcalc nudge #{nudge_count + 1}")
        config["nudge_count"] = nudge_count + 1
        _save(config)


def maybe_prompt() -> None:
    """Initialize telemetry on first run — opt-out model, no interactive prompt."""
    if os.environ.get("BOOLCALC_NO_TELEMETRY"):
        return
    config = _load()
    if "opted_in" in config:
        return

    # Reuse install_id written by _ping_install() in __init__.py if available,
    # so all PostHog events share the same distinct_id.
    install_id = config.get("install_id") or str(uuid.uuid4())

    config["opted_in"]   = True
    config["install_id"] = install_id
    config["run_count"]  = 0
    _save(config)

    print(_WELCOME)
    _gc_ping("/cli/install", "boolcalc install")


def send(command: str, **kwargs) -> None:
    """Fire-and-forget telemetry. Never blocks, never raises."""
    if os.environ.get("BOOLCALC_NO_TELEMETRY"):
        return
    config = _load()
    if not config.get("opted_in"):
        return

    os_name    = platform.system() or "Unknown"
    py_version = f"{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}"
    install_id = config.get("install_id", "unknown")

    payload = {
        "install_id": install_id,
        "version":    _VERSION,
        "os":         os_name,
        "python":     py_version,
        "command":    command,
        **{k: v for k, v in kwargs.items() if v is not None},
    }

    if _ph:
        try:
            _ph.capture(f"command_{command}", distinct_id=install_id, properties=payload)
        except Exception:
            pass

    def _fire():
        try:
            path   = f"/cli/{command}/{os_name}/{py_version}"
            gc_url = f"{_GC_URL}?p={urllib.parse.quote(path)}&t={urllib.parse.quote('boolcalc ' + command)}"
            urllib.request.urlopen(gc_url, timeout=3)
        except Exception:
            pass

        if _API_URL:
            try:
                data = json.dumps(payload).encode()
                req  = urllib.request.Request(
                    _API_URL,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass

    threading.Thread(target=_fire, daemon=True).start()
