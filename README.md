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

![Engine vs LLM](https://raw.githubusercontent.com/Shrivastava-Aditya/boolean-algebra-engine-python/engine-PyPI/images/viz_4_engine_vs_llm.png)

The engine is the oracle — ground truth is computed by exhaustive enumeration, not guessed by a human labeler.

**First result:** tinyllama (1B) · 3 variables · 10 cases · **40% hallucination rate.**

The methodology: generate rule sets where the correct logical answer is known (computed by the engine), ask an LLM the same question, compare. Every disagreement is a provable hallucination. No ambiguity. No interpretation.

![Benchmark results](https://raw.githubusercontent.com/Shrivastava-Aditya/boolean-algebra-engine-python/engine-PyPI/images/benchmark_results.png)

Full benchmark across models is in progress. See `BENCHMARK_PLAN.md`.

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

## Use cases

The same pattern appears everywhere: statements that sound consistent individually, contradict each other when held together. The engine is a universal detector for that failure mode.

### System prompts

> "Always be helpful to the user and answer every question fully.
> Never discuss competitor products under any circumstances.
> If a user asks to compare us to a competitor, give a full and helpful answer."

Rule 2 says no answer when a competitor is mentioned. Rule 3 says give a full answer. Both cannot apply. The engine finds this in milliseconds.

### Business rules

> "All customers are treated equally regardless of subscription tier.
> Premium customers receive priority support and faster response times."

`E` (equal treatment) and `P` (priority treatment) cannot both be true. Conflicting pair found.

### Legal contracts

> "This agreement renews automatically each year unless cancelled.
> Either party may terminate with 30 days written notice.
> Termination requires written consent from both parties."

Clause 2 (unilateral termination) and Clause 3 (mutual consent) directly contradict. The contract has no defined termination mechanism.

### Medical protocols

> "Administer medication A when the patient has symptom X.
> Do not administer medication A if the patient has condition Y.
> Patients presenting with symptom X almost always have condition Y."

Rules 1 and 2 conflict whenever `X=1, Y=1`. Rule 3 makes this the common case. The protocol contradicts itself for the majority of patients it was written to treat.

### Personal reasoning

> "I have been using Linux for over 6 years and Mac for 3 years.
> If I did not use Linux, I would have never switched to Mac.
> But my use of Mac has no relation to my use of Linux in any way."

- Sentence 3: `!L → !M` — Linux caused the switch to Mac
- Sentence 4: M and L are independent

`L=0, M=1` satisfies sentence 4 but violates sentence 3. Both cannot be true simultaneously. Conflicting pair.

More real-world examples across therapy, philosophy, journalism, and AI alignment in `statements.md`.

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

## Visualisations

![Truth table heatmap](https://raw.githubusercontent.com/Shrivastava-Aditya/boolean-algebra-engine-python/engine-PyPI/images/viz_2_truth_table.png)

The Streamlit UI generates two classes of charts automatically from engine output:

**Truth table heatmap** — every row rendered as a green/red grid. A contradiction is an entirely red output column. A pattern of minterms becomes visually obvious in one glance.

**Conflict matrix** — N×N grid, one cell per rule pair. Red `✗` means always conflict. Green `✓` means no overlap. Yellow `≡` means duplicate rule. Three red cells in a matrix of 6 rules is immediately visible before the user finishes scrolling.

![Failure panel](https://raw.githubusercontent.com/Shrivastava-Aditya/boolean-algebra-engine-python/engine-PyPI/images/viz_3_failure_panel.png)

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

---

## Related

- [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — original Java version, written during placement season
