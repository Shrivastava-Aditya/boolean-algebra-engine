"""
ui/fetchers.py — pure data-fetch functions with no Streamlit dependency.
Imported by both ui/analytics.py (Streamlit) and analytics_notify.py (CLI).
"""
from __future__ import annotations

import json
import urllib.request
import urllib.parse

GITHUB_REPOS = [
    "Shrivastava-Aditya/bool-LLM-ngn",
    "Shrivastava-Aditya/boolean-algebra-engine-python",
]


def _get(url: str, headers: dict | None = None, timeout: int = 8) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


def fetch_pypi() -> dict:
    base = "https://pypistats.org/api/packages/boolean-algebra-engine"
    return {
        "recent": _get(f"{base}/recent"),
        "overall": _get(f"{base}/overall"),
        "system": _get(f"{base}/system"),
        "python": _get(f"{base}/python_major"),
    }


def fetch_github(token: str) -> dict:
    results = {}
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    for repo in GITHUB_REPOS:
        short = repo.split("/")[1]
        base = f"https://api.github.com/repos/{repo}/traffic"
        results[short] = {
            "views":     _get(f"{base}/views", headers),
            "clones":    _get(f"{base}/clones", headers),
            "referrers": _get(f"{base}/popular/referrers", headers),
            "paths":     _get(f"{base}/popular/paths", headers),
        }
    return results


def fetch_posthog(api_key: str, project_id: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    base = f"https://us.posthog.com/api/projects/{project_id}"
    params = urllib.parse.urlencode({"event": "install", "limit": 500})
    events = _get(f"{base}/events/?{params}", headers)
    insight_url = (
        f"{base}/insights/trend/?events=%5B%7B%22id%22%3A%22install%22%7D%5D"
        f"&breakdown=os&breakdown_type=event&date_from=-30d"
    )
    breakdown = _get(insight_url, headers)
    return {"events": events, "breakdown": breakdown}


def fetch_docker() -> dict | None:
    return _get("https://hub.docker.com/v2/repositories/shrvx/bool-llm-ngn/")
