"""
ui/analytics.py — unified analytics dashboard for boolcalc.

Run:
    streamlit run ui/analytics.py
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

import streamlit as st
from ui.fetchers import (
    fetch_pypi as _fetch_pypi,
    fetch_github as _fetch_github,
    fetch_posthog as _fetch_posthog,
    fetch_docker as _fetch_docker,
    GITHUB_REPOS,
)

st.set_page_config(
    page_title="boolcalc analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .stApp { background-color: #0d1117; color: #e6edf3; }
  .block-container { padding-top: 1.5rem; }
  [data-testid="stMetricValue"] { font-size: 2rem !important; }
  .source-header {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #388bfd;
    font-weight: 600;
    margin-bottom: 4px;
  }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cached wrappers (Streamlit cache layer over pure fetchers)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_pypi() -> dict:
    return _fetch_pypi()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_github(token: str) -> dict:
    return _fetch_github(token)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_posthog(api_key: str, project_id: str) -> dict:
    return _fetch_posthog(api_key, project_id)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_docker() -> dict | None:
    return _fetch_docker()


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------

def _missing_key(name: str):
    st.warning(f"`{name}` not set in `.env` — skipping this panel.", icon="⚠️")


def render_pypi(data: dict):
    st.markdown('<div class="source-header">PyPI</div>', unsafe_allow_html=True)
    recent = data.get("recent") or {}
    d = recent.get("data", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Last day", f"{d.get('last_day', 0):,}")
    c2.metric("Last week", f"{d.get('last_week', 0):,}")
    c3.metric("Last month", f"{d.get('last_month', 0):,}")

    # Python version breakdown
    py_data = data.get("python") or {}
    py_rows = py_data.get("data", [])
    if py_rows:
        versions: dict[str, int] = {}
        for row in py_rows:
            v = row.get("python_version") or "unknown"
            versions[v] = versions.get(v, 0) + row.get("downloads", 0)
        import pandas as pd
        df = pd.DataFrame(sorted(versions.items(), key=lambda x: -x[1]), columns=["Python", "Downloads"])
        st.bar_chart(df.set_index("Python"), height=200)

    # System breakdown
    sys_data = data.get("system") or {}
    sys_rows = sys_data.get("data", [])
    if sys_rows:
        systems: dict[str, int] = {}
        for row in sys_rows:
            s = row.get("system") or "unknown"
            systems[s] = systems.get(s, 0) + row.get("downloads", 0)
        import pandas as pd
        df2 = pd.DataFrame(sorted(systems.items(), key=lambda x: -x[1]), columns=["OS", "Downloads"])
        st.bar_chart(df2.set_index("OS"), height=200)


def render_github(data: dict):
    st.markdown('<div class="source-header">GitHub Traffic</div>', unsafe_allow_html=True)
    cols = st.columns(len(GITHUB_REPOS))
    for col, repo in zip(cols, GITHUB_REPOS):
        short = repo.split("/")[1]
        repo_data = data.get(short, {})
        with col:
            st.caption(f"**{short}**")
            views = repo_data.get("views") or {}
            clones = repo_data.get("clones") or {}
            c1, c2 = st.columns(2)
            c1.metric("Views (14d)", f"{views.get('count', 0):,}", f"{views.get('uniques', 0):,} unique")
            c2.metric("Clones (14d)", f"{clones.get('count', 0):,}", f"{clones.get('uniques', 0):,} unique")

            referrers = repo_data.get("referrers") or []
            if referrers:
                st.caption("Top referrers")
                import pandas as pd
                df = pd.DataFrame(referrers)[["referrer", "count", "uniques"]]
                st.dataframe(df, hide_index=True, use_container_width=True)

            paths = repo_data.get("paths") or []
            if paths:
                st.caption("Top paths")
                import pandas as pd
                df2 = pd.DataFrame(paths)[["path", "count", "uniques"]]
                st.dataframe(df2, hide_index=True, use_container_width=True)


def render_posthog(data: dict):
    st.markdown('<div class="source-header">PostHog — Install Pings</div>', unsafe_allow_html=True)
    events_resp = data.get("events") or {}
    events = events_resp.get("results", [])

    if not events:
        st.info("No install events found in the last 500 records.")
        return

    # Daily counts
    from collections import Counter
    import pandas as pd
    daily: Counter = Counter()
    os_counts: Counter = Counter()
    ver_counts: Counter = Counter()

    for ev in events:
        ts = ev.get("timestamp", "")[:10]
        if ts:
            daily[ts] += 1
        props = ev.get("properties", {})
        os_counts[props.get("os", "unknown")] += 1
        ver_counts[props.get("version", "unknown")] += 1

    c1, c2 = st.columns(2)
    c1.metric("Total installs (recent)", len(events))
    c2.metric("Unique days", len(daily))

    if daily:
        df = pd.DataFrame(sorted(daily.items()), columns=["Date", "Installs"])
        st.line_chart(df.set_index("Date"), height=200)

    cols = st.columns(2)
    with cols[0]:
        st.caption("By OS")
        df_os = pd.DataFrame(os_counts.most_common(), columns=["OS", "Count"])
        st.bar_chart(df_os.set_index("OS"), height=180)
    with cols[1]:
        st.caption("By version")
        df_ver = pd.DataFrame(ver_counts.most_common(10), columns=["Version", "Count"])
        st.bar_chart(df_ver.set_index("Version"), height=180)


def render_docker(data: dict):
    st.markdown('<div class="source-header">Docker Hub — shrvx/bool-llm-ngn</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Pulls", f"{data.get('pull_count', 0):,}")
    c2.metric("Stars", f"{data.get('star_count', 0):,}")
    last_updated = data.get("last_updated", "")[:10] or "—"
    c3.metric("Last updated", last_updated)
    st.caption(data.get("description") or "")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 📊 boolcalc analytics")
    st.caption("Aggregated traffic across all distribution channels.")
    st.divider()

    github_token = os.environ.get("GITHUB_TOKEN", "")
    posthog_key = os.environ.get("POSTHOG_PERSONAL_API_KEY", "")
    posthog_project = os.environ.get("POSTHOG_PROJECT_ID", "")

    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()

    st.divider()
    st.caption(f"Last loaded: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    st.caption("Cache TTL: 1 hour")

# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

st.title("boolcalc analytics")
st.caption("PyPI · GitHub · PostHog · Docker Hub")
st.divider()

# PyPI — no auth needed
with st.spinner("Fetching PyPI stats…"):
    pypi_data = fetch_pypi()
with st.container(border=True):
    render_pypi(pypi_data)

st.divider()

# GitHub — needs token
with st.container(border=True):
    if not github_token:
        st.markdown('<div class="source-header">GitHub Traffic</div>', unsafe_allow_html=True)
        _missing_key("GITHUB_TOKEN")
    else:
        with st.spinner("Fetching GitHub traffic…"):
            gh_data = fetch_github(github_token)
        render_github(gh_data)

st.divider()

# PostHog — needs key + project id
with st.container(border=True):
    if not posthog_key or not posthog_project:
        st.markdown('<div class="source-header">PostHog — Install Pings</div>', unsafe_allow_html=True)
        _missing_key("POSTHOG_PERSONAL_API_KEY / POSTHOG_PROJECT_ID")
    else:
        with st.spinner("Fetching PostHog events…"):
            ph_data = fetch_posthog(posthog_key, posthog_project)
        render_posthog(ph_data)

st.divider()

# Docker Hub — no auth needed
with st.container(border=True):
    with st.spinner("Fetching Docker Hub stats…"):
        docker_data = fetch_docker()
    if docker_data:
        render_docker(docker_data)
    else:
        st.markdown('<div class="source-header">Docker Hub</div>', unsafe_allow_html=True)
        st.warning("Could not reach Docker Hub API.", icon="⚠️")
