# boolean-algebra-engine-python

A deterministic boolean algebra engine. Not a model — a program that runs algorithms.
Expression in, exact answer out. No weights, no inference, no probability.

Built for verifying that logic is actually correct — not just that it sounds correct.

Forked from [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — the original Java implementation written during placement season.

---

## The problem it solves

Human brains are good at language. Bad at exhaustive enumeration.

You can read "grant access if admin" and "deny access if admin" separately and both sound fine.
The contradiction only appears when you force both conditions to hold simultaneously — which nobody does manually across 10+ rules written by different people over several months.

LLMs have the same failure mode. They predict what sounds right. Simple contradictions they catch. Five nested conditions with a double negation — they'll confidently give the wrong answer.

This engine doesn't read. It computes every combination. The contradiction is unavoidable.

```python
from mcp_server.server import check_prompt_logic

result = check_prompt_logic([
    "A.B",    # approve: good credit AND income verified
    "C",      # approve: collateral exists
    "!A",     # reject:  bad credit
    "!B.!C",  # reject:  no income AND no collateral
])

# summary: {'total': 4, 'contradictions': 0, 'conflicting_pairs': 3}
# Rule 1 always conflicts with Rule 3
# Rule 1 always conflicts with Rule 4
# Rule 2 always conflicts with Rule 4
```

Three conflicts found in under 5ms. Nobody catches these by reading the rules.

---

## Operators

| Symbol | Operation | Precedence |
|--------|-----------|------------|
| `!`    | NOT       | 4 (highest) |
| `.`    | AND       | 3 |
| `^`    | XOR       | 2 |
| `+`    | OR        | 1 (lowest) |

Variables: uppercase `A`–`Z`. Parentheses override precedence.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Interface Layer                     │
│   CLI/REPL    MCP Server    REST API    Streamlit UI  │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────┴──────────────────────────────┐
│                     NL Layer                          │
│   plain English → expression → plain English          │
│   Anthropic · OpenAI · Ollama · OpenAI-compat         │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────┴──────────────────────────────┐
│                   Core Engine                         │
│   parser (shunting-yard) → evaluator (prefix stack)   │
│                         → synthesizer (Quine-McCluskey)│
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────┴──────────────────────────────┐
│             Acceleration Layer (planned)               │
│         numpy · CUDA · Redis                          │
└──────────────────────────────────────────────────────┘
```

`core/` has zero external dependencies. Every layer above is a thin wrapper. Independently deployable, independently testable.

---

## Project structure

```
core/
  models.py          TruthTable, TruthTableRow, PerformanceMetrics dataclasses
  parser.py          Shunting-yard — infix → prefix, variable extraction, validation
  evaluator.py       Prefix stack evaluator — exhaustive 2^n row enumeration
  synthesizer.py     Quine-McCluskey — truth table → minimal SOP expression

mcp_server/
  server.py          5 tools Claude calls mid-conversation (evaluate, simplify,
                     equivalent, satisfiable, check_prompt_logic)

api/
  routes.py          FastAPI — 7 endpoints, Redis cache, optional auth

nl/
  nl.py              Provider abstraction — Anthropic, OpenAI, Ollama, OpenAI-compat
                     ask() and check_rules() — NL in, verified result out

cli/
  main.py            typer + rich — REPL and one-shot, all output formats

ui/
  app.py             Streamlit — Expression, Rule Auditor, Plain English modes
                     matplotlib heatmap + conflict matrix

tests/               90 tests — unit, integration, edge cases, round-trips
```

---

## Quickstart

```bash
git clone https://github.com/Shrivastava-Aditya/boolean-algebra-engine-python
cd boolean-algebra-engine-python
pip install -e ".[dev]"
python3 -m pytest tests/
```

---

## Core usage

```python
from core.evaluator import evaluate
from core.synthesizer import synthesize

# Forward: expression → truth table
table, metrics = evaluate("A.(B+C)")

print(table.variables)    # ['A', 'B', 'C']
print(table.minterms)     # [5, 6, 7]
print(table.satisfiable)  # True
print(table.tautology)    # False
print(metrics.eval_time_ms)

for row in table.rows:
    print(row.inputs, "->", row.output)

# Inverse: truth table → minimal expression
minimal, _ = synthesize(table)
print(minimal)            # A.C+A.B

# Distributive law — both sides simplify identically
t1, _ = evaluate("A.(B+C)")
t2, _ = evaluate("A.B+A.C")
print(t1.minterms == t2.minterms)  # True
```

---

## MCP server — Claude integration

```bash
python3.11 -m mcp_server.server
```

Add to Claude Desktop config and Claude can call `evaluate`, `simplify`, `equivalent`,
`satisfiable`, and `check_prompt_logic` mid-conversation — computing exact results
instead of predicting them.

---

## NL layer — plain English in, verified result out

```python
from nl.nl import ask, check_rules, AnthropicProvider

# Single statement
result = ask(
    "Approve if credit score is good and income is verified, or if collateral exists",
    provider=AnthropicProvider()
)
print(result.expression)   # A.B+C
print(result.satisfiable)  # True
print(result.minimal)      # A.B+C
print(result.explanation)  # plain English from Claude

# Multi-rule audit
result = check_rules([
    "Approve if credit score is good and income is verified",
    "Reject if credit score is bad",
    "Approve if collateral exists",
], provider=AnthropicProvider())

print(result["summary"])
```

Providers: `AnthropicProvider`, `OpenAIProvider`, `OllamaProvider` (local, no key),
`OpenAICompatProvider` (Groq, Together, LM Studio, vLLM).

---

## REST API

```bash
pip install -e ".[api]"
uvicorn api.routes:app --port 8000
```

```bash
curl -X POST http://localhost:8000/check-rules \
  -H "Content-Type: application/json" \
  -d '{"rules": ["A.B", "C", "!A", "!B.!C"]}'
```

7 endpoints: `/evaluate`, `/simplify`, `/equivalent`, `/satisfiable`, `/check-rules`,
`/nl/ask`, `/nl/check-rules`. Redis cache optional — degrades gracefully without it.

---

## Streamlit UI

```bash
pip install -e ".[cli]"
streamlit run ui/app.py --server.port 8080
```

Three modes: Expression evaluator with truth table heatmap, Rule Auditor with conflict
matrix (N×N matplotlib grid, red cells = always-conflicting pairs), Plain English verifier.

---

## CLI

```bash
pip install -e ".[cli]"

boolcalc "A.(B+C)"
boolcalc "A.(B+C)" --format json
boolcalc "A.(B+C)" --synthesize
boolcalc -i   # REPL mode
echo "A+B" | boolcalc
```

---

## What it verifies

| Check | What it means |
|---|---|
| Satisfiable | At least one input combination outputs 1 |
| Contradiction | Always outputs 0 — rule never fires |
| Tautology | Always outputs 1 — rule is redundant |
| Equivalent | Two expressions produce identical output for all inputs |
| Conflict | Two rules can never both be satisfied simultaneously |
| Minimal form | Shortest expression producing identical output |

All results are mathematically exact. Exhaustive enumeration up to ~20 variables.

---

## How the correctness guarantee works

The evaluator checks every one of `2^n` input combinations. Nothing is sampled or predicted.

- `n = 5` → 32 rows
- `n = 10` → 1,024 rows
- `n = 20` → 1,048,576 rows

Each row is independent — which is also the CUDA opportunity: one thread per row.
The core evaluator is 15 lines of code. If the operators are correct, the results are correct.
No black box. Fully auditable.

---

## Roadmap

| Layer | Status |
|---|---|
| `core/` — parser, evaluator, synthesizer | Done |
| `tests/` — 90 tests | Done |
| `cli/` — REPL + one-shot, all formats | Done |
| `mcp_server/` — 5 tools for Claude | Done |
| `api/` — FastAPI, 7 endpoints, Redis cache | Done |
| `nl/` — 4 LLM providers, ask + check_rules | Done |
| `ui/` — Streamlit, heatmap, conflict matrix | Done |
| numpy vectorised evaluator | Next |
| CUDA acceleration | Planned |

---

## Related

- [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — original Java version
- [boolean-algebra-engine-go](https://github.com/Shrivastava-Aditya/boolean-algebra-engine-go) — future Go version for GPU/CUDA
