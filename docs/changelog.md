# Changelog

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
