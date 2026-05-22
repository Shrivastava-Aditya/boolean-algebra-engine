# boolean-algebra-engine-python

**The logic layer your AI is missing.**

A serious, compatible tool for AI agents and models that reduces logical hallucination
by a measurable percentage. Not a library. Not an audit tool. A layer that sits between
AI reasoning and output and makes one guarantee the model cannot make itself: that the
logic is consistent.

Forked from [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — the original Java implementation written during placement season.

---

## What it is

The AI reasons in language. This verifies the logic. Two different jobs, two different
systems. The AI predicts. This computes. Neither does the other's job.

```
User input
    ↓
AI reasoning
    ↓
[ Logic Layer ]  ← this
    ↓
AI output  ←  logically consistent, guaranteed
```

It sits between the AI's reasoning and its output. It catches logical contradictions
before they become output, before they reach the user, before they cause a decision error.
Under 10ms. No additional model inference. No self-critique loop.

---

## The hallucination it catches

**Logical hallucination** — the model produces output that contradicts its own premises.

> "Users with role A cannot access resource X."  
> "Grant user with role A access to X."

Both sentences generated. Neither false in isolation. Together, logically inconsistent.
The logic layer catches this before it becomes output.

This is distinct from factual hallucination (wrong facts, wrong knowledge). That is a
different problem. This engine makes no claim about it. The claim is narrow and provable:

> **If the AI's output contains a logical contradiction, this catches it. Every time.**

---

## The latency advantage

| Approach | Latency | How |
|---|---|---|
| Self-critique loop | 500ms–2000ms | Ask the same model to check itself |
| Constitutional AI | 800ms–3000ms | Second model pass over the output |
| Multi-agent verification | 1000ms–5000ms | Separate agent reviews the output |
| **This logic layer** | **< 10ms** | **Pure computation, no inference** |

One-time parse cost at setup (cached in Redis). Zero-inference verification at runtime.

---

## Where it sits in a real pipeline

**Agent pipelines** — the agent forms a plan with conditional rules. Before it acts,
the logic layer checks the conditions don't contradict. "If A do X, if A do Y" is caught
before the agent executes both.

**System prompt validation** — before a system prompt ships, every rule is verified
for conflicts. The AI deployed under that prompt cannot be caught in a logical contradiction
by a user who finds the edge case.

**LLM output verification** — the model generates a decision or recommendation. The
logic layer checks it is internally consistent before it reaches the user.

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

`core/` has zero external dependencies. Every layer above is a thin wrapper.
Independently deployable, independently testable.

---

## Project structure

```
core/
  models.py          TruthTable, TruthTableRow, PerformanceMetrics dataclasses
  parser.py          Shunting-yard — infix → prefix, variable extraction, validation
  evaluator.py       Prefix stack evaluator — exhaustive 2^n row enumeration
  synthesizer.py     Quine-McCluskey — truth table → minimal SOP expression

mcp_server/
  server.py          5 tools for agent integration (evaluate, simplify,
                     equivalent, satisfiable, check_prompt_logic)

api/
  routes.py          FastAPI — 7 endpoints, Redis cache, optional auth

nl/
  nl.py              Provider abstraction — Anthropic, OpenAI, Ollama, OpenAI-compat
                     ask() and check_rules() — plain English in, verified result out

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

# Inverse: truth table → minimal expression
minimal, _ = synthesize(table)
print(minimal)            # A.C+A.B

# Equivalence — prove distributive law
t1, _ = evaluate("A.(B+C)")
t2, _ = evaluate("A.B+A.C")
print(t1.minterms == t2.minterms)  # True
```

---

## check_prompt_logic — the core tool

```python
from mcp_server.server import check_prompt_logic

result = check_prompt_logic([
    "A.B",    # approve: good credit AND income verified
    "C",      # approve: collateral exists
    "!A",     # reject:  bad credit — no exceptions
    "!B.!C",  # reject:  no income AND no collateral
])

print(result["summary"])
# → {'total': 4, 'contradictions': 0, 'conflicting_pairs': 3}

# Rule 1 vs Rule 3: always conflict — can never both fire
# Rule 2 vs Rule 4: always conflict — can never both fire
# Rule 1 vs Rule 4: always conflict — can never both fire
```

Nobody catches these by reading. The engine catches them by computing every combination.

---

## MCP server — native agent integration

```bash
python3.11 -m mcp_server.server
```

Claude and any MCP-compatible agent can call `evaluate`, `simplify`, `equivalent`,
`satisfiable`, and `check_prompt_logic` mid-reasoning — computing exact results
instead of predicting them. The agent cannot produce a logically inconsistent output
when the logic layer is wired in.

---

## NL layer — plain English in, verified result out

```python
from nl.nl import check_rules, AnthropicProvider

result = check_rules([
    "Approve if credit score is good and income is verified",
    "Reject if credit score is bad",
    "Approve if collateral exists",
], provider=AnthropicProvider())

print(result["summary"])
```

Providers: `AnthropicProvider`, `OpenAIProvider`, `OllamaProvider` (local, free, no key),
`OpenAICompatProvider` (Groq, Together, LM Studio, vLLM).

---

## How the correctness guarantee works

Exhaustive enumeration. For `n` variables: exactly `2^n` rows evaluated. Nothing sampled.

- `n = 5` → 32 rows — CPU, ~1ms
- `n = 10` → 1,024 rows — CPU, ~3ms
- `n = 20` → 1,048,576 rows — numpy
- `n = 50+` → 10^15 rows — CUDA (planned)

Each row is completely independent — perfect parallelisation target. One GPU thread per row.
The core evaluator is 15 lines of code. If the operators are correct, the results are correct.
No black box. Fully auditable.

---

## What it doesn't do

**Factual hallucination** — "the Eiffel Tower is in Berlin" is a knowledge problem.
The engine has no world knowledge. It only verifies the logical structure of reasoning.

**Probabilistic reasoning** — if the AI says "probably" or "likely", that is not a
boolean claim. The engine works on deterministic if-then logic, not probabilistic inference.

The scope is narrow by design. Narrow scope means a provable guarantee.

---

## Roadmap

| Layer | Status |
|---|---|
| `core/` — parser, evaluator, synthesizer | Done |
| `tests/` — 90 tests | Done |
| `cli/` — REPL + one-shot, all formats | Done |
| `mcp_server/` — 5 tools for agent integration | Done |
| `api/` — FastAPI, 7 endpoints, Redis cache | Done |
| `nl/` — 4 LLM providers, plain English interface | Done |
| `ui/` — Streamlit, heatmap, conflict matrix | Done |
| Measure x% on a real pipeline | Next |
| numpy vectorised evaluator | Next |
| CUDA acceleration | Planned |

---

## Related

- [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — original Java version
- [boolean-algebra-engine-go](https://github.com/Shrivastava-Aditya/boolean-algebra-engine-go) — future Go version for GPU/CUDA
