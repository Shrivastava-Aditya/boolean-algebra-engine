# Product Brief — Boolean Algebra Engine

A running record of what this is, what it does, why it matters, and how to talk about it.
Use this to deconstruct the product for marketing, pitching, or scoping the next layer.

---

## What it is

A deterministic boolean algebra engine that evaluates logical expressions with mathematical
certainty. It is the computation layer underneath what could become a product for developers,
prompt engineers, and anyone who needs to verify that their rules are logically sound.

---

## What it does today

**Forward:** Give it a boolean expression, it returns the full truth table — every possible
input combination and its output. No guessing, no approximation. Exhaustive.

**Inverse:** Give it a truth table (what you want to happen), it returns the minimal boolean
expression that produces it. Uses the Quine-McCluskey algorithm.

**Verification tools:**
- Is this expression satisfiable? (does any input make it true?)
- Is it a contradiction? (is it always false?)
- Is it a tautology? (is it always true — i.e. redundant?)
- Are these two expressions logically equivalent?
- Do these rules ever conflict — can they never both be satisfied simultaneously?

**check_prompt_logic:** Pass a list of rules. Get back which ones are contradictions,
which are tautologies, which pairs always conflict, which are duplicates.
This is the product.

---

## How credibility works

The engine's credibility is not a claim — it's a consequence of how it works.

It uses **exhaustive enumeration**. For `n` variables it evaluates exactly `2^n` rows.
Every possible input combination is checked. Nothing is sampled or predicted.

- Satisfiable → it found an actual row where output = 1
- Contradiction → it checked every row, all were 0
- Equivalent → it compared output columns row-by-row across the full table
- Conflict → it evaluated the conjunction of both rules for every input, always got 0

The core evaluator is 15 lines of code (`core/evaluator.py:_evaluate_prefix`).
If the operators are correct, the results are correct. Auditable. No black box.

**Honest limitation:** scales as `2^n`. Tractable up to ~20 variables. Beyond that,
SAT solvers (Z3, DPLL/CDCL) are the right tool. For the target use case — prompt rules
with 5–15 boolean variables — exhaustive enumeration is provably complete.

This is a stronger correctness claim than any probabilistic tool can make.

---

## What doesn't exist in this space

| Tool | Gap |
|---|---|
| `sympy.logic` | Academic, no MCP, no NL layer, not LLM-native |
| Z3 / SAT4J / Alloy | Powerful but built for researchers, not developers or prompt engineers |
| Online truth table generators | No API, no synthesis, no MCP, no NL |

The raw computation exists in academia. The product doesn't.

The competition isn't Z3. The competition is "the developer manually reads their
if-conditions and hopes for the best."

---

## The moat

Not the algorithm. These three things together don't exist anywhere:

1. **MCP integration** — Claude calls the engine instead of predicting logic, anchoring
   its reasoning to ground truth
2. **NL layer** *(next to build)* — describe rules in plain English, engine verifies them,
   Claude explains results back
3. **Packaging** — pip-installable, REPL, REST-deployable, notebook-ready

---

## The NL layer (not built yet)

Right now you write expressions manually: `A.B+!A.C`

The NL layer removes that barrier entirely:

```
"Access is granted if the user is authenticated and admin, or authenticated
and read-only, but never if unauthenticated"
        ↓  Claude parses (Claude API call 1)
  (A.B + A.C).!(!A)
        ↓  engine evaluates
   truth table + minimal form + contradiction/tautology check
        ↓  Claude explains (Claude API call 2)
"Your rule simplifies to A.(B+C) — authentication is always required.
 No contradictions found."
```

One afternoon of work. Two Claude API calls sandwiching the engine.
Claude handles the fuzzy parts. Engine handles the deterministic parts.
Neither does the other's job.

---

## The $5 product

`check_prompt_logic` with an NL interface:

> Paste your system prompt rules in plain English.
> Get back: contradictions, redundancies, unreachable conditions, conflicting pairs.

Every serious AI deployment has this problem today. A production system prompt with
10+ rules almost certainly has a logic error that nobody caught because the only tool
available was reading it carefully and hoping. This catches it with mathematical certainty.

Price point: $5/month to test and verify. Underpriced — a logic bug in a production
system prompt caught before shipping is worth far more to the right team.

---

## Stack (current state)

```
[ NL Layer ]          ← not built — Claude API, two calls
[ MCP Server ]        ← built — 5 tools, runs on Python 3.11
[ CLI / REPL ]        ← built — typer + rich, all output formats
[ Core Engine ]       ← built — evaluate, synthesize, verify
[ Tests ]             ← 90 tests, all passing
[ REST API ]          ← not built — FastAPI, planned
[ Web UI ]            ← not built — planned
[ CUDA acceleration ] ← not built — rows are independent, map 1:1 to GPU threads
```

---

## What it can do with complex expressions today

The engine handles up to 26 variables (A–Z), arbitrary nesting, all four operators
in any combination. You can test real access control logic, conditional rules,
circuit expressions — anything that can be expressed in boolean notation.

The only friction is writing the expression manually instead of in plain English.
That's exactly what the NL layer removes.

---

## Next build

**NL layer** — Claude API integration. Translates plain English rules into expressions,
passes to engine, translates results back. This is the step that turns it from a
developer tool into something a non-technical user can pay for.

---

## What this is — precisely

Not a model. Not a transformer. Not ML at all.

It is a **deterministic computation engine** — a program that runs an algorithm.
No weights. No training. No inference. No probability.

- **Shunting-yard** parses the expression from infix to prefix
- **Stack evaluator** computes each row of the truth table
- **Quine-McCluskey** finds the minimal expression from a truth table

The closest analogy is a **compiler** or a **calculator**. You wouldn't call a
calculator a model. Same here — expression in, exact answer out.

The Claude API component is only the interface layer — translation in, translation out.
The engine itself has no AI in it. That's the point. That's why it's credible.

---

## Pricing model

The cost to serve is near zero — no GPU, no inference, just CPU arithmetic.
That changes the pricing logic entirely. You're not charging per token.
You're charging for access to a workflow.

| Tier | Who | Price | What |
|---|---|---|---|
| **Free** | Devs, students | $0 | CLI, pip install, unlimited local use |
| **Pro** | Prompt engineers, solo builders | $9–15/month | Hosted API, NL interface, `check_prompt_logic` UI |
| **Team** | Companies shipping LLM products | $49–99/month | Higher rate limits, audit logs, team access |

**Why free at the bottom:** the engine is GPL-3.0 — anyone can run it locally.
Charging for the CLI would kill adoption. The money is in the hosted product
and the NL layer, neither of which is easy to self-host (needs Claude API keys,
a frontend, and maintenance).

**Dual license:** GPL-3.0 for open source use. Commercial license for anyone
embedding it in a proprietary product. Standard model — Redis, MongoDB, Elasticsearch
all did this. Open core keeps adoption high, commercial license captures enterprise value.

---

## Where the defensibility is

The engine is the commodity. Quine-McCluskey is a 1950s algorithm — anyone can
implement it. What's not easy to replicate quickly:

1. MCP integration — Claude Desktop plugin, works out of the box
2. NL interface — the UX of describing rules in plain English
3. `check_prompt_logic` — the specific workflow nobody has productised
4. Distribution — pip package, hosted API, Claude plugin, notebook-ready
5. Trust — deterministic, auditable, 90 tests, open source core

The moat is distribution and workflow, not the algorithm.

---

## Model-agnostic logic verifier

This engine doesn't belong to any one AI stack. It sits alongside any agent or model
already in use — Claude, GPT, Gemini, Llama, or anything custom.

**Integration surface:**

| Integration | How |
|---|---|
| Claude Desktop / Claude Code | MCP server — already built, plug and play |
| Any OpenAI-compatible agent | REST API (FastAPI) — one HTTP call |
| LangChain / LlamaIndex | Wrap `evaluate()` as a tool — 5 lines |
| CrewAI / AutoGen multi-agent | One agent specialises in logic, calls engine |
| Jupyter / notebook workflows | `pip install`, import directly |
| n8n / Zapier automations | REST API endpoint |
| Any custom Python agent | Direct import from `core/` |

**The deeper point:**

Every one of those agents has the same problem — they hallucinate on boolean logic.
This isn't a Claude problem or a GPT problem. It's a fundamental limitation of how
transformers work. They predict the next token. They don't compute. So they get logic
wrong under pressure — especially with negations, nested conditions, and edge cases.

This engine doesn't replace any of those models. It augments them. It gives them a
reliable tool to call for the one class of problems they should never be predicting.

**The position:**

Model-agnostic logic verifier. One integration, works with whatever AI stack the
customer already uses. The customer doesn't switch anything — they add one tool
and every logic problem in their pipeline gets an exact answer instead of a guess.

---

## How it can be used

Three levels depending on who's using it and what they're building.

### 1. Directly — as a tool you run yourself

- **CLI:** `boolcalc "A.B+!A.C" --synthesize` — instant truth table in terminal
- **REPL:** interactive session, test expressions one by one, explore incrementally
- **Notebook:** `from core.evaluator import evaluate` — drop into any Jupyter workflow
- **Scripting:** pipe expressions in, get JSON or CSV out, chain with other tools

### 2. As a library — embedded in your code

```python
from core.evaluator import evaluate
from core.synthesizer import synthesize

table, _ = evaluate("(A.B) + (!A.C)")
minimal, _ = synthesize(table)
```

Any Python project can import it. Access control systems, rule engines, config
validators, test generators — anything with conditional logic can use this to verify it.

### 3. As a tool inside an AI agent — the most powerful use

- Claude calls `evaluate` mid-conversation to verify its own reasoning
- An agent building a system prompt calls `check_prompt_logic` to audit it before deploying
- A code review agent calls `equivalent` to check if two conditions in a PR are logically identical
- A multi-agent pipeline has one specialised logic-verification agent that handles all
  boolean reasoning for the others

### Concrete scenarios

| Who | What they do | What they get |
|---|---|---|
| Prompt engineer | Paste system prompt rules | Contradictions and redundancies caught before shipping |
| Developer in code review | Compare two conditional guards | Exact answer on whether they behave identically |
| Security engineer | Model access control as boolean expressions | Conditions that always grant or always deny access |
| Teacher | Build logic coursework | Auto-generated truth tables, student answer verification |
| AI agent | Check plan against constraints | `check_prompt_logic` on its own reasoning, not a guess |
| Solo builder | Describe rules in plain English (NL layer) | Verified, minimal, explained — no notation required |

### The pattern

Anywhere a human or an AI is currently reading logic and hoping they got it right —
this replaces hope with certainty.

---

## Why nothing in the market goes this deep

The closest thing is **Z3** from Microsoft Research. Extraordinarily powerful — handles
boolean logic and far beyond. But it was built for formal verification researchers and
compiler engineers. Nobody is shipping it as a product for prompt engineers or AI teams.
No NL layer, no MCP integration, no "paste your rules and get plain English back."
It's a tool you need a PhD to use comfortably.

Everything else — sympy, online truth table generators, logic textbook tools — stops
at the computation. They give you an answer. They don't sit inside your AI pipeline,
they don't speak plain English, they don't audit your system prompt, they don't tell
you why two rules conflict.

**What makes this different is the depth of the stack:**

- The computation layer is rigorous enough to be academically credible
- The MCP layer means it lives inside the AI tools people already use
- The NL layer (when built) means it speaks the same language as the people who need it most
- The `check_prompt_logic` framing turns a 1950s algorithm into a workflow a
  non-mathematician actually wants

Most tools pick one layer and stop. This goes all the way from a 1950s algorithm to
a plain English conversation, with every layer in between solid and independently
deployable.

**The combination that doesn't exist anywhere else:**

Academic rigour + AI-native integration + natural language interface = one product.

That stack, end to end, is not shipped by anyone right now.
