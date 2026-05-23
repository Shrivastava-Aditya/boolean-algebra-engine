# boolean-algebra-engine-python

A deterministic boolean algebra engine — evaluates expressions, generates truth tables, synthesises minimal forms, and verifies logical consistency.

Forked from [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — original Java implementation written during placement season.

---

## What it does

**Forward:** expression → full truth table, exhaustive 2^n evaluation, exact.

**Inverse:** truth table → minimal boolean expression via Quine-McCluskey.

**Verification:** satisfiability, contradiction, tautology, equivalence, pairwise conflict detection across rule sets.

---

## Operators

| Symbol | Operation | Precedence |
|--------|-----------|------------|
| `!` | NOT | 4 (highest) |
| `.` | AND | 3 |
| `^` | XOR | 2 |
| `+` | OR | 1 (lowest) |

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
  models.py        TruthTable, TruthTableRow, PerformanceMetrics
  parser.py        Shunting-yard — infix → prefix, validation, variable extraction
  evaluator.py     Prefix stack evaluator — exhaustive 2^n row enumeration
  synthesizer.py   Quine-McCluskey — truth table → minimal SOP expression

mcp_server/
  server.py        5 tools for agent integration (evaluate, simplify,
                   equivalent, satisfiable, check_prompt_logic)

api/
  routes.py        FastAPI — 7 endpoints, Redis cache, optional auth

nl/
  nl.py            Provider abstraction — Anthropic, OpenAI, Ollama, OpenAI-compat

cli/
  main.py          typer + rich — REPL and one-shot, all output formats

ui/
  app.py           Streamlit — Expression, Rule Auditor, Plain English modes

tests/             90 tests — unit, integration, edge cases, round-trips

benchmark.py       LLM hallucination benchmark — engine as oracle
visualisations.ipynb  Colab notebook — complexity vs variables, conflict graph
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

table, _ = evaluate("A.(B+C)")
print(table.variables)    # ['A', 'B', 'C']
print(table.minterms)     # [5, 6, 7]
print(table.satisfiable)  # True

minimal, _ = synthesize(table)
print(minimal)            # A.C+A.B
```

---

## check_prompt_logic

```python
from mcp_server.server import check_prompt_logic

result = check_prompt_logic([
    "A.B",   # approve: good credit AND income verified
    "C",     # approve: collateral exists
    "!A",    # reject:  bad credit
    "!B.!C", # reject:  no income AND no collateral
])
print(result["summary"])
# {'total': 4, 'contradictions': 0, 'conflicting_pairs': 3}
```

---

## Benchmark

Measures LLM hallucination rate on boolean logic. Engine is the oracle — ground truth by exhaustive enumeration, no human labelers.

```bash
ollama pull tinyllama
python3 benchmark.py
```

First result: tinyllama (1B) · 3 variables · 10 cases · **40% hallucination rate**.

See `FAILURES.md` for real-world severity analysis of each failure.

---

## Branches

| Branch | What |
|---|---|
| `master` | Project — engine, interfaces, tests |
| `product-readme` | Product brief — what it proves, what it's for |
| `benchmark` | Benchmark methodology, multi-model results (in progress) |

---

## Related

- [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — original Java version
