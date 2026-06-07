# Internal Reference — boolean-algebra-engine

> Internal only. Not for public repo. Last updated: 2026-06-07

---

## Repositories

| Repo | Remote | Visibility | Purpose |
|---|---|---|---|
| `boolean-algebra-engine-python` | `origin` | Private | Development, internal docs, full history |
| `bool-LLM-ngn` | `public` | Public | Public-facing, PyPI source, README |

Both remotes share the same git history. Internal docs pushed to `origin` only.

---

## Accounts and Services

| Service | Account | Purpose | Tier |
|---|---|---|---|
| GitHub | `Shrivastava-Aditya` | Source hosting, two repos | Free |
| PyPI | `Shrivastava-Aditya` (OIDC) | Package distribution | Free |
| GoatCounter | `shrvx.goatcounter.com` | CLI telemetry + web analytics | Free (cloud) |
| PostHog | — | Structured per-user CLI telemetry | Planned — free tier |

> If this project forms as an entity, all service accounts should migrate to a shared org account. Keep a separate password manager entry per service.

---

## Environment Variables

| Variable | Required by | Where to get it | Notes |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | `nl/` layer, API `/nl/*` | console.anthropic.com | Used for Claude NL provider |
| `OPENAI_API_KEY` | `nl/` layer (OpenAI provider) | platform.openai.com | Optional — only if using OpenAI |
| `REDIS_URL` | `api-cache` extra | Self-hosted or Redis Cloud | Optional — expression caching |
| `BOOLCALC_TELEMETRY_URL` | `cli/telemetry.py` | Internal API endpoint URL | Optional — POST structured telemetry JSON |
| `BOOLCALC_NO_TELEMETRY` | `cli/telemetry.py` | Set to `1` | Disables all CLI telemetry |

No secrets are committed to either repo. `publish.sh` uses PyPI OIDC (Trusted Publishing) — no stored token.

---

## Python Dependencies

### Core (no extras — always installed)
```
requires-python = ">=3.10"
```
Zero pip dependencies. Pure stdlib only.

### `[cli]`
```
typer >= 0.12.0
rich  >= 13.0.0
```

### `[mcp]`
```
mcp[cli] >= 1.0.0
```

### `[nl]` / `[nl-anthropic]`
```
anthropic >= 0.50.0
```

### `[nl-openai]`
```
openai >= 1.0.0
```

### `[api]`
```
fastapi  >= 0.100.0
uvicorn  >= 0.20.0
slowapi  >= 0.1.9
```

### `[api-cache]`
```
fastapi  >= 0.100.0
uvicorn  >= 0.20.0
slowapi  >= 0.1.9
redis    >= 5.0.0
```

### `[dev]`
```
pytest     >= 8.0.0
httpx      >= 0.24.0
z3-solver  >= 4.12.0
```

### Build / release tools (not in pyproject — manual install)
```
build   (python -m build)
twine   (upload to PyPI)
```

---

## Infrastructure

### Current (as of v0.3.6)
- **No hosted server** — API is not deployed. Runs locally or self-hosted only.
- **PyPI** — package is distributed via PyPI. Release via `publish.sh`.
- **GoatCounter** — `shrvx.goatcounter.com`. Receives CLI telemetry pings and web analytics. No server required.
- **GitHub Actions** — CI via Trusted Publishing for PyPI releases. Workflow in `.github/workflows/`.

### Planned
- Hosted API (FastAPI on a cloud instance — Fly.io / GCP Cloud Run / bare VM)
- Redis for expression caching (`api-cache` extra)
- PostHog for structured per-install CLI telemetry

---

## Server Architecture (when hosted)

```
                    ┌─────────────────────┐
  boolcalc CLI ─────►  GoatCounter cloud  │  (already live)
                    └─────────────────────┘

                    ┌─────────────────────┐
  HTTP clients ─────►  FastAPI (uvicorn)  │  (not yet hosted)
                    │  boolean_algebra_   │
                    │  engine.api.routes  │
                    │         │           │
                    │    core engine      │
                    │         │           │
                    │   Redis (optional)  │
                    └─────────────────────┘

                    ┌─────────────────────┐
  LLM agents  ──────►   MCP server        │  (local only, not hosted)
                    │   python -m         │
                    │   boolean_algebra_  │
                    │   engine.mcp.server │
                    └─────────────────────┘
```

### API rate limits (current)
- `/nl/ask`, `/nl/check-rules` — 10 req/min per IP
- All other endpoints — 60 req/min per IP
- Returns `429` on breach (`slowapi`)

### API observability
- `GET /stats` — uptime, request counts, error rates, provider usage, per-endpoint breakdown (in-memory, resets on restart)
- `POST /telemetry` — accepts CLI telemetry payloads, counts in `_stats`
- Structured JSON request log via `log_requests` middleware (stdout)

---

## Release Process

```bash
# 1. Bump version in two places:
#    pyproject.toml → version = "X.Y.Z"
#    boolean_algebra_engine/cli/telemetry.py → _VERSION = "X.Y.Z"

# 2. Update docs/changelog.md

# 3. Commit
git commit -m "vX.Y.Z — description"

# 4. Push (private only for internal changes, both for public releases)
git push origin master
git push public master   # omit for internal-only commits

# 5. Publish to PyPI
bash publish.sh
```

---

## Telemetry Data Flow

```
User runs boolcalc
       │
       ├─► GoatCounter ping (always, anonymous)
       │   path: /cli/{command}/{os}/{python}
       │
       └─► Structured JSON POST (if opted in + BOOLCALC_TELEMETRY_URL set)
           payload: { install_id, version, os, python, command, variable_count }
           destination: BOOLCALC_TELEMETRY_URL → /telemetry endpoint → _stats (in-memory)

First run only:
       ├─► GoatCounter: /cli/install/welcome
       └─► GoatCounter: /cli/install/telemetry-yes|no

Every 10 runs (max 3×):
       └─► GoatCounter: /cli/nudge/N
```

Config stored at `~/.config/boolcalc/telemetry.json`:
```json
{
  "opted_in": true,
  "install_id": "<uuid4>",
  "run_count": 42,
  "nudge_count": 1
}
```

---

## Test Suite

```bash
pip install -e ".[dev]"
pytest tests/
```

| File | Covers |
|---|---|
| `tests/test_parser.py` | Infix → prefix conversion, operator precedence |
| `tests/test_evaluator.py` | Truth table generation, all operators |
| `tests/test_synthesizer.py` | Quine-McCluskey minimization |
| `tests/test_models.py` | Dataclass correctness |
| `tests/test_edge_cases.py` | Single variable, tautologies, contradictions |
| `tests/test_integration.py` | End-to-end evaluate + synthesize |

---

## IT Suite — Future Considerations

If the project incorporates as an entity, the following accounts/services should be under a shared org identity (not personal accounts):

| Category | Tool | Notes |
|---|---|---|
| Source control | GitHub org | Migrate both repos under org |
| Package registry | PyPI org | Migrate `boolean-algebra-engine` to org ownership |
| Analytics | PostHog | Product analytics — free tier covers early stage |
| Error tracking | Sentry | When hosted API goes live |
| Cloud hosting | Fly.io / GCP / AWS | For hosted API |
| Email | Google Workspace / Proton for Business | For support@, noreply@ |
| Secrets management | Doppler / 1Password Teams | Env vars, API keys |
| Status page | Instatus / Betterstack | When hosted API is public |
| Domain | — | `boolcalc.dev` or similar |
