from boolean_algebra_engine.core.evaluator import evaluate
from boolean_algebra_engine.core.synthesizer import synthesize
from boolean_algebra_engine.core.parser import validate
from boolean_algebra_engine.core.models import TruthTable, TruthTableRow, PerformanceMetrics

__all__ = [
    "evaluate",
    "synthesize",
    "validate",
    "TruthTable",
    "TruthTableRow",
    "PerformanceMetrics",
]


def _ping_install() -> None:
    """Fire an anonymous install ping to PostHog once per version per machine.

    Uses only stdlib — no posthog package required. Runs in a daemon thread
    so it never blocks import or process exit. Skipped if BOOLCALC_NO_TELEMETRY=1.

    Shares telemetry.json with the CLI so PostHog sees a single distinct_id
    across install pings and command events.
    """
    import os
    if os.environ.get("BOOLCALC_NO_TELEMETRY"):
        return

    import threading

    def _fire() -> None:
        try:
            import json
            import platform
            import uuid
            import urllib.request
            import importlib.metadata
            from pathlib import Path

            version = importlib.metadata.version("boolean-algebra-engine")

            config_dir = Path(
                os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            ) / "boolcalc"
            # Share telemetry.json with cli/telemetry.py so install_id is consistent
            state_file = config_dir / "telemetry.json"

            state = {}
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                except Exception:
                    pass

            # Skip if already pinged for this version
            if version in state.get("seen_versions", []):
                return

            # Fetch IP — skip dev machines, pass explicitly for GeoIP
            _DEV_IPS = {"80.225.206.105"}
            current_ip = None
            try:
                current_ip = urllib.request.urlopen(
                    "https://api.ipify.org", timeout=2
                ).read().decode().strip()
                if current_ip in _DEV_IPS:
                    return
            except Exception:
                pass

            # Reuse existing install_id if CLI has already written one; otherwise mint a new one
            install_id = state.get("install_id") or str(uuid.uuid4())
            seen = state.get("seen_versions", [])
            seen.append(version)

            state["install_id"]    = install_id
            state["seen_versions"] = seen
            config_dir.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(state, indent=2))

            props = {
                "version": version,
                "os": platform.system(),
                "python": f"{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}",
            }
            if current_ip:
                props["$ip"] = current_ip

            payload = json.dumps({
                "api_key": "phc_Am4NNyVXotVffz6rcBy8xZVUZeaJCCbbHMu63pWMz3M8",
                "event": "install",
                "distinct_id": install_id,
                "properties": props,
            }).encode()

            req = urllib.request.Request(
                "https://us.i.posthog.com/capture/",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass

    threading.Thread(target=_fire, daemon=True).start()


_ping_install()
