# Architecture

## Package layout

All installed code lives under `boolean_algebra_engine/`. Five subpackages, one direction of dependency.

```
boolean_algebra_engine/
├── core/          pure logic — zero external dependencies
├── nl/            LLM translation layer — depends on core
├── cli/           terminal interface — depends on core, nl
├── api/           REST API — depends on core, nl
└── mcp/           MCP server — depends on core
```

Dependency rule: **core knows nothing outside itself**. Every other layer is a thin wrapper.

```
cli ──┐
api ──┼──► nl ──► core
mcp ──┘           ▲
                  │
              (direct)
```

---

## Subpackages

### `core/` — engine
- `parser.py` — infix → prefix (shunting-yard). Operators: `!` `.` `^` `+`
- `evaluator.py` — prefix stack evaluator. Produces `TruthTable` with `2^n` rows
- `synthesizer.py` — truth table → minimal expression (Quine-McCluskey)
- `models.py` — `TruthTable`, `TruthTableRow`, `PerformanceMetrics` dataclasses

No pip dependencies. Pure Python 3.10+.

### `nl/` — natural language layer
- `nl.py` — `ask()` and `check_rules()`. Translates plain English to boolean expression via LLM, then runs through core engine. Provider-agnostic: `AnthropicProvider`, `OpenAIProvider`, `OllamaProvider`, `OpenAICompatProvider`.

Requires `anthropic` or `openai` depending on provider used.

### `cli/` — `boolcalc` command
- `entry.py` — thin entry point. Catches `ImportError` if `[cli]` extras not installed, prints friendly message
- `main.py` — typer app. `boolcalc "expr"` one-shot, `boolcalc` REPL, `boolcalc ask`, `boolcalc check-rules`
- `telemetry.py` — opt-in anonymous usage stats. GoatCounter backend. Config at `~/.config/boolcalc/telemetry.json`

Requires `typer`, `rich` (`pip install 'boolean-algebra-engine[cli]'`).

### `api/` — REST API
- `routes.py` — FastAPI app. Endpoints: `POST /evaluate`, `POST /synthesize`, `POST /nl/ask`, `POST /nl/check-rules`, `GET /stats`, `POST /telemetry`. Rate limiting via `slowapi`. Structured JSON request logging middleware.

Requires `fastapi`, `uvicorn`, `slowapi` (`pip install 'boolean-algebra-engine[api]'`).

### `mcp/` — MCP server
- `server.py` — exposes core functions as MCP tools: `evaluate`, `synthesize`, `check_equivalence`, `check_satisfiable`, `check_tautology`. Run with `python -m boolean_algebra_engine.mcp.server`.

Requires `mcp[cli]` (`pip install 'boolean-algebra-engine[mcp]'`).

---

## Install extras

| Extra | Installs | Use when |
|---|---|---|
| `cli` | `typer`, `rich` | using `boolcalc` terminal command |
| `mcp` | `mcp[cli]` | running the MCP server |
| `nl-anthropic` | `anthropic` | NL layer with Claude |
| `nl-openai` | `openai` | NL layer with OpenAI / Groq / compat |
| `nl` | `anthropic` | alias for `nl-anthropic` |
| `api` | `fastapi`, `uvicorn`, `slowapi` | running the REST API |
| `api-cache` | `api` + `redis` | API with Redis expression cache |
| `dev` | `pytest`, `httpx`, `z3-solver` | running tests |

Install multiple: `pip install 'boolean-algebra-engine[cli,api,nl]'`

---

## Entry points

| Surface | How to run |
|---|---|
| CLI | `boolcalc "A+B"` or `boolcalc` (REPL) |
| MCP server | `python -m boolean_algebra_engine.mcp.server` |
| REST API | `uvicorn boolean_algebra_engine.api.routes:app` |
| Python library | `from boolean_algebra_engine import evaluate, synthesize` |

---

## Root-level files

These are research and tooling scripts, not part of the installed package.

| File / Dir | What it is |
|---|---|
| `benchmark.py` | LLM hallucination benchmark runner. Runs N cases through a model, cross-checks against engine ground truth, outputs JSON to `results/` |
| `curve.py` | Variable-count degradation study — runs benchmark at n=3,5,7,10 variables, measures how hallucination rate climbs |
| `curve_plot.py` | Plots the variable-count degradation curve from `results/curve/` |
| `dashboard.py` | Live benchmark dashboard — SSE streaming, opens in browser during a benchmark run |
| `demo.py` | Quick demo script showing evaluate + synthesize in action |
| `ui/app.py` | Streamlit web UI. Run: `streamlit run ui/app.py` |
| `results/` | Raw benchmark output JSON, gitignored from package builds |
| `core/` | Backward-compat shim — re-exports from `boolean_algebra_engine.core`. For scripts that ran before the namespace refactor |
| `mcp_server/` | Backward-compat shim — re-exports from `boolean_algebra_engine.mcp`. Same reason |
| `index.html` | Project landing page (served by the web deployment) |
| `thanks.html` | Post-waitlist thank-you page |
| `waitlist.html` | Waitlist signup page |
| `docs/DESIGN.md` | Original planning and architecture doc — historical, predates namespace refactor |
| `docs/changelog.md` | Release history |
| `docs/TODO.md` | Backlog — benchmark work, Go port, DPLL backend, hosted product |
| `publish.sh` | PyPI release script — `python -m build && twine upload dist/*` |

---

## Telemetry

CLI only. Library usage is silent.

- **First run**: welcome message + opt-in prompt (once ever)
- **Per command**: if opted in, fires GoatCounter ping + structured JSON to `BOOLCALC_TELEMETRY_URL` (if set)
- **Every 10 runs**: dim nudge line linking to GitHub (max 3 times total)
- **Disable**: `BOOLCALC_NO_TELEMETRY=1`
- **Config**: `~/.config/boolcalc/telemetry.json`

GoatCounter paths: `/cli/{command}/{os}/{python}`, `/cli/install/welcome`, `/cli/install/telemetry-yes|no`, `/cli/nudge/N`
