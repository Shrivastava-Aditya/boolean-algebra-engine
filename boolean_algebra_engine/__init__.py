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
    """Fire a one-time anonymous install ping to PostHog on first import.

    Uses only stdlib — no posthog package required. Runs in a daemon thread
    so it never blocks import or process exit. Skipped if BOOLCALC_NO_TELEMETRY=1.
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

            config_dir = Path(
                os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            ) / "boolcalc"
            flag = config_dir / "install_id"

            if flag.exists():
                return

            # Skip dev machines
            _DEV_IPS = {"80.225.206.105"}
            try:
                current_ip = urllib.request.urlopen(
                    "https://api.ipify.org", timeout=2
                ).read().decode().strip()
                if current_ip in _DEV_IPS:
                    return
            except Exception:
                pass

            config_dir.mkdir(parents=True, exist_ok=True)
            install_id = str(uuid.uuid4())
            flag.write_text(install_id)

            version = importlib.metadata.version("boolean-algebra-engine")

            payload = json.dumps({
                "api_key": "phc_Am4NNyVXotVffz6rcBy8xZVUZeaJCCbbHMu63pWMz3M8",
                "event": "install",
                "distinct_id": install_id,
                "properties": {
                    "version": version,
                    "os": platform.system(),
                    "python": f"{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}",
                },
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
