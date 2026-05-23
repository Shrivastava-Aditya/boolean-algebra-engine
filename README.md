# boolean-algebra-engine

**The logic layer your AI is missing.**

AI agents hallucinate on boolean logic — not sometimes, reliably. They predict the next token. They don't compute. This engine does. Deterministic, exhaustive, under 10ms. It sits inside your agent pipeline and makes one guarantee the model cannot make itself: that its reasoning is logically consistent.

```bash
pip install boolean-algebra-engine
```

---

## The problem

Six rules. Three variables. Written by four people over six months.

A fintech AI agent auto-approves or rejects loan applications based on these rules — nobody ever verified them together. The engine checks all 8 input combinations for every rule, in every combination:

```python
from mcp_server.server import check_prompt_logic

result = check_prompt_logic([
    "A.B",    # approve: good credit AND income verified
    "C",      # approve: collateral exists
    "!A",     # reject:  bad credit
    "!B.!C",  # reject:  no income AND no collateral
    "A.B.C",  # approve: good credit AND income AND collateral
    "!B",     # block:   income unverified
])

print(result["summary"])
# {'total': 6, 'contradictions': 0, 'tautologies': 0,
#  'conflicting_pairs': 2, 'redundant': 1}
```

**What it found in 4.5ms:**
- Rule 2 (`C`) and Rule 3 (`!A`) conflict — an applicant with bad credit but collateral triggers both approve and reject simultaneously. The agent picks a winner arbitrarily. That is a compliance violation.
- Rule 5 (`A.B.C`) is dead — anyone satisfying it already satisfies Rule 1 or Rule 2. It can be deleted.

Nobody caught these by reading the rules. The engine caught them by checking every combination.

---

## The benchmark

The engine is the oracle — ground truth is computed by exhaustive enumeration, not guessed. Every LLM disagreement is a provable hallucination.

**Methodology:** generate pairs of boolean expressions where the correct answer (satisfiable or not) is known exactly. Ask the LLM. Compare. No ambiguity, no human labeling, no interpretation.

```
python3 benchmark.py --provider ollama --model tinyllama --cases 20
python3 benchmark.py --provider ollama --model llama3.2:3b --cases 20
```

**tinyllama — 1.1B parameters**

```
╭──────────────────────── Benchmark ─────────────────────────╮
│ Model        ollama/tinyllama                              │
│ Cases        20  (10 conflict · 10 compatible)             │
│ Variables    3  (A, B, C)                                  │
│ Temperature  0  (deterministic)                            │
│ Max tokens   5  (yes/no answer only)                       │
│ Workers      8 parallel inference calls                    │
╰────────────────────────────────────────────────────────────╯

  ollama/tinyllama — 20/20 cases | 50.0% hallucination rate

  #      Rule 1          Rule 2          vars    engine  llm
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1  ✗   B               !B              B         no    yes
  2  ✗   A.B+C           !A.!B.!C        A B C     no    yes
  3  ✗   A.B             A.!B            A B       no    yes
  4  ✓   A+!B            A.(B+C)         A B C    yes    yes
  5  ✗   A.B             A^B             A B       no    yes
  6  ✓   !A+B.C          B               A B C    yes    yes
  7  ✓   A.B+C           A+B             A B C    yes    yes
  8  ✓   A+B.C.D         C               A B C D  yes    yes
  9  ✓   A.B             B               A B      yes    yes
 10  ✓   !C              !B              B C      yes    yes
 ...

╭─────────── Results — ollama/tinyllama ─────────────╮
│ Model:               ollama/tinyllama               │
│ Total cases:         20  (10 conflict · 10 compat)  │
│ Variables:           3  (A, B, C)                   │
│ Temperature:         0  (deterministic)             │
│ Max tokens:          5                              │
│ Correct:             10                             │
│ Hallucinated:        10                             │
│ Hallucination rate:  50.0%                          │
│ Missed conflicts:    10/10  (100.0%)                │
│ Missed compatibles:  0/10   (0.0%)                  │
╰─────────────────────────────────────────────────────╯
```

**llama3.2:3b — 3B parameters**

```
╭──────────────────────── Benchmark ─────────────────────────╮
│ Model        ollama/llama3.2:3b                            │
│ Cases        20  (10 conflict · 10 compatible)             │
│ Variables    4  (A, B, C, D)                               │
│ Temperature  0  (deterministic)                            │
│ Max tokens   5  (yes/no answer only)                       │
│ Workers      8 parallel inference calls                    │
╰────────────────────────────────────────────────────────────╯

  ollama/llama3.2:3b — 20/20 cases | 50.0% hallucination rate

  #      Rule 1          Rule 2          vars    engine  llm
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1  ✓   B               !B              B         no     no
  2  ✓   A.B+C           !A.!B.!C        A B C     no     no
  3  ✓   A.B             A.!B            A B       no     no
  4  ✗   A+!B            A.(B+C)         A B C    yes     no
  5  ✓   A.B             A^B             A B       no     no
  6  ✗   !A+B.C          B               A B C    yes     no
  7  ✗   A.B+C           A+B             A B C    yes     no
  8  ✗   A+B.C.D         C               A B C D  yes     no
  9  ✗   A.B             B               A B      yes     no
 10  ✗   !C              !B              B C      yes     no
 ...

╭─────────── Results — ollama/llama3.2:3b ───────────╮
│ Model:               ollama/llama3.2:3b             │
│ Total cases:         20  (10 conflict · 10 compat)  │
│ Variables:           4  (A, B, C, D)                │
│ Temperature:         0  (deterministic)             │
│ Max tokens:          5                              │
│ Correct:             10                             │
│ Hallucinated:        10                             │
│ Hallucination rate:  50.0%                          │
│ Missed conflicts:    0/10   (0.0%)                  │
│ Missed compatibles:  10/10  (100.0%)                │
╰─────────────────────────────────────────────────────╯
```

Both models score 50% — equal to a coin flip — but in opposite directions. tinyllama always answers "yes", llama3.2:3b always answers "no". Neither is reasoning. Both are outputting a constant.

The `vars` column shows how many variables each case involves. The `engine` column is ground truth. Every mismatch with `llm` is a provable hallucination — not an opinion.

![Benchmark results — 20 cases](https://raw.githubusercontent.com/Shrivastava-Aditya/boolean-algebra-engine-python/engine-PyPI/images/benchmark_20cases.png)

Per-case strips (bottom row of the chart): every conflict cell is uniformly one colour per model, every compatible cell is the opposite. No case-by-case variation — no reasoning happening at all.

---

## Install

```bash
# Core engine — zero dependencies
pip install boolean-algebra-engine

# With CLI
pip install "boolean-algebra-engine[cli]"

# With MCP server (for Claude Desktop)
pip install "boolean-algebra-engine[mcp]"

# With REST API
pip install "boolean-algebra-engine[api]"

# With NL layer (Anthropic)
pip install "boolean-algebra-engine[nl-anthropic]"

# With NL layer (OpenAI)
pip install "boolean-algebra-engine[nl-openai]"
```

---

## Core API

```python
from core.evaluator import evaluate
from core.synthesizer import synthesize

# Forward: expression → truth table
table, _ = evaluate("A.(B+C)")
print(table.variables)    # ['A', 'B', 'C']
print(table.minterms)     # [5, 6, 7]
print(table.satisfiable)  # True

# Inverse: truth table → minimal expression
minimal, _ = synthesize(table)
print(minimal)            # A.C+A.B

# Verification
from core.evaluator import are_equivalent, check_satisfiable
print(are_equivalent("A.(B+C)", "A.B+A.C"))  # True — distributive law
```

`core/` has zero external dependencies. Import it into any Python project.

---

## MCP — Claude calls the engine

Wire the engine into Claude Desktop and Claude stops predicting boolean logic. It computes it.

```json
{
  "mcpServers": {
    "boolean-algebra-engine": {
      "command": "python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

Five tools Claude can call mid-conversation:
- `evaluate` — expression → truth table
- `simplify` — expression → minimal form
- `equivalent` — are two expressions identical?
- `satisfiable` — does any input make this true?
- `check_prompt_logic` — audit a full rule set for contradictions, tautologies, conflicts, duplicates

---

## Operators

| Symbol | Operation | Precedence |
|--------|-----------|------------|
| `!` | NOT | 4 (highest) |
| `.` | AND | 3 |
| `^` | XOR | 2 |
| `+` | OR | 1 (lowest) |

Variables: uppercase `A`–`Z`. Parentheses override precedence. Up to 26 variables, arbitrary nesting.

---

## Interfaces

| Interface | How |
|---|---|
| **Python library** | `from core.evaluator import evaluate` — embed in any project |
| **CLI / REPL** | `boolcalc "A.B+!A.C"` — instant truth table in terminal |
| **MCP server** | Claude Desktop plugin — plug and play |
| **REST API** | `POST /check-rules` — callable from any language or stack |
| **NL layer** | Plain English → expression → verified result (Anthropic, OpenAI, Ollama, any OpenAI-compat) |
| **Streamlit UI** | Three modes: Expression, Rule Auditor, Plain English |

---

## Credibility

The engine does not sample, approximate, or predict. It evaluates every possible input combination:

- **Satisfiable** — an actual row where output = 1 was found
- **Contradiction** — every row was checked, all were 0
- **Equivalent** — output columns compared row-by-row across the full truth table
- **Conflict** — conjunction of both rules evaluated for every input, always returned 0

The core evaluator is 15 lines (`core/evaluator.py`). No black box, no model weights, no probability — just arithmetic. This is a stronger correctness claim than any probabilistic tool can make.

90 tests across unit, integration, edge cases, and round-trips. All passing.

