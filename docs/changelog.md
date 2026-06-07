# Changelog

## v0.3.3 — 2026-06-07
- Non-intrusive GitHub feedback nudge — dim one-liner shown every 10 runs, max 3 times ever, never blocking
- Nudge tracks `run_count` and `nudge_count` in `~/.config/boolcalc/telemetry.json`
- Respects `BOOLCALC_NO_TELEMETRY=1`

## v0.3.2 — 2026-06-07
- Opt-in anonymous CLI telemetry — first-run prompt, saves to `~/.config/boolcalc/telemetry.json`
- Sends: command used, OS, Python version, variable/rule count, anonymous install ID. Never sends expressions or user data
- `BOOLCALC_NO_TELEMETRY=1` disables entirely
- GoatCounter backend active immediately; `BOOLCALC_TELEMETRY_URL` enables structured API posting
- `POST /telemetry` endpoint added to API, visible in `/stats`

## v0.3.1 — 2026-06-07
- Rate limiting on API: 10 req/min per IP on `/nl/*` endpoints, 60 req/min on engine endpoints — returns 429 on breach
- `boolcalc --help` no longer exposes the internal `main` subcommand
- `slowapi>=0.1.9` added to `api` and `api-cache` extras

## v0.3.0 — 2026-06-07
Fix CLI entry point and clean up package namespace.

- `boolcalc "A+B"` now works directly — no longer requires the hidden `main` subcommand
- All submodules (`core`, `mcp`, `nl`, `cli`, `api`) moved under the `boolean_algebra_engine` namespace — no more top-level package pollution on install
- `from boolean_algebra_engine import evaluate, synthesize` is now the canonical import
- MCP server path updated to `python -m boolean_algebra_engine.mcp.server`
- Backward-compat shims retained at `core/` and `mcp_server/` for repo runners
- README code examples updated to match actual working imports

## v0.2.3 — 2026-05-24
Add dynamic shields.io badges and switch downloads badge to pepy.tech.

## v0.1.11 — 2026-05-23
Add live web dashboard and fix benchmark timeout/crash bugs.

## v0.1.10 — 2026-05-23
Rename public repo reference from `boolean-LLM-eval` to `bool-LLM-ngn`.

## v0.1.9 — 2026-05-23
Switch CI to Trusted Publishing (PyPI OIDC) — no stored token required.

## v0.1.8 — 2026-05-23
Point package URLs and CI workflow to the public repo.

## v0.1.7 — 2026-05-23
Fix image URLs to resolve correctly from the public repo.

## v0.1.6 — 2026-05-23
Add zero-setup Quick start, z3 verification layer, and refresh benchmark console output.

## v0.1.5 — 2026-05-23
Add CI/CD via GitHub Actions and initial PyPI distribution.
