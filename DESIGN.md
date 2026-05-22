# Boolean Algebra Calculator — Design Document

## Origin

Originally a Java project built during placement season prep. Three classes, monolithic, interactive prompts via Scanner. Being forked and rewritten in Python with a clean layered architecture for AI/MCP repurposing.

---

## Current Java State

| Class | Responsibility |
|---|---|
| `StringParser` | Infix → prefix conversion (shunting-yard) |
| `Logics` | Truth table generation + prefix stack evaluator |
| `Calculator` | Entry point — glues the two, handles I/O |

Bugs fixed before fork (see `log.md` for details): precedence inversion, unary NOT popping two operands, bracket-swap off-by-one, stack drain loop, duplicate parse call, phantom array allocation.

---

## Direction

Rewrite in Python. Structure the engine so cleanly that it can be wrapped by a CLI, an MCP server, or a REST API without touching core logic. Then layer AI on top via Claude API and MCP.

Full planned stack:

```
Natural Language Input (Claude API)
            ↓
    MCP Server / REST API
            ↓
        Core Engine          ← the thing we're building first
            ↓
     Truth Table + Result
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERFACES                           │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   CLI    │  │   REST   │  │   MCP    │  │  Python  │  │
│  │  REPL    │  │   API    │  │  Server  │  │ Library  │  │
│  │ boolcalc │  │ FastAPI  │  │ 5 tools  │  │ import   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼─────────────┼─────────────┼──────────────┼─────────┘
        │             │             │              │
┌───────┼─────────────┼─────────────┼──────────────┼─────────┐
│       │          NL LAYER         │              │         │
│       │                           │              │         │
│  ┌────┴──────────────────────┐    │              │         │
│  │   plain English → expr    │    │              │         │
│  │   expr → plain English    │    │              │         │
│  │                           │    │              │         │
│  │  AnthropicProvider        │    │              │         │
│  │  OpenAIProvider           │    │              │         │
│  │  OllamaProvider (local)   │    │              │         │
│  │  OpenAICompatProvider     │    │              │         │
│  └────────────┬──────────────┘    │              │         │
└───────────────┼───────────────────┼──────────────┼─────────┘
                │                   │              │
┌───────────────┼───────────────────┼──────────────┼─────────┐
│               │     CORE ENGINE   │              │         │
│               └───────────────────┘              │         │
│                         │◄─────────────────────── │         │
│                         │                                   │
│   ┌─────────────────────┼──────────────────────┐           │
│   │                     ▼                      │           │
│   │  parser.py     evaluator.py   synthesizer.py│           │
│   │  infix→prefix  truth table    Quine-McCluskey│          │
│   │  validate      2^n rows       minimal form  │           │
│   │  get_variables  ← CUDA here →  ← cache here │           │
│   └─────────────────────────────────────────────┘           │
│                                                             │
│               zero external dependencies                    │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────┐
│         ACCELERATION & CACHING (planned)                    │
│                        │                                    │
│   ┌────────────┐   ┌───┴──────────┐                        │
│   │   Redis    │   │     CUDA     │                        │
│   │ expression │   │ 1 row = 1    │                        │
│   │ parse      │   │ GPU thread   │                        │
│   │ session    │   │ 2^n parallel │                        │
│   │ cache      │   │              │                        │
│   └────────────┘   └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**Key properties:**
- Every interface is a thin wrapper — none contain logic
- `core/` knows nothing outside itself — swap any layer without touching it
- NL layer is provider-agnostic — any LLM, same engine underneath
- Redis and CUDA slot in without changing the core contract
- The engine is the only thing that is irreplaceable

---

## Repository Structure

```
boolean-algebra-engine/
│
├── core/                        # Pure logic — no I/O, no dependencies
│   ├── parser.py                    Infix → prefix (shunting-yard)
│   ├── evaluator.py                 Prefix stack evaluator
│   ├── synthesizer.py               Truth table → minimal expression (Quine-McCluskey)
│   └── models.py                    TruthTable, EvaluationResult dataclasses
│
├── mcp_server/                  # MCP wrapper — decorates core with @mcp.tool()
│   └── server.py
│
├── api/                         # REST API — FastAPI, cloud deployable (AWS Lambda etc.)
│   └── routes.py
│
├── cli/                         # CLI — typer/click, calls core directly
│   └── main.py
│
└── tests/
    ├── test_parser.py
    ├── test_evaluator.py
    ├── test_synthesizer.py
    └── test_api.py
```

### Core contract

`core/` has zero knowledge of anything outside itself. No HTTP, no MCP, no CLI args. Pure functions in, dataclasses out. Every other layer is a thin wrapper.

This means:
- MCP server breaks → core and CLI still work
- Deploy to AWS Lambda → point `api/` at it, done
- Swap REST framework → only `api/` changes
- Add new AI layer later → new folder, imports from `core/`

---

## Proposed CLI Interface

```
boolcalc [OPTIONS] <expression>

Options:
  -v, --vars <n>         Number of variables (default: auto-detect)
  -f, --format <fmt>     Output format: table (default), json, csv, minimal
  -o, --output <file>    Write output to file
      --satisfiable      Exit 0 if satisfiable, 1 if not
      --tautology        Exit 0 if tautology, 1 if not
      --minterm          Print minterms (rows where output = 1)
      --maxterm          Print maxterms (rows where output = 0)
      --simplify         Return minimal expression for given truth table
  -h, --help
      --version
```

### Output formats

**table** (default):
```
A | B | C | A+B.C
0 | 0 | 0 | 0
0 | 1 | 0 | 0
1 | 0 | 1 | 1
...
```

**json** (for piping/scripting):
```json
{
  "expression": "A+B.C",
  "variables": ["A", "B", "C"],
  "rows": [{ "A": 0, "B": 0, "C": 0, "output": 0 }, ...],
  "satisfiable": true,
  "tautology": false,
  "minterms": [3, 5, 6, 7]
}
```

**minimal**: one output value per line, useful for diff/grep.

---

## MCP Server (Phase 2)

Exposes core functions as tools Claude can call mid-conversation:

```python
@mcp.tool()
def evaluate(expression: str) -> TruthTable: ...

@mcp.tool()
def equivalent(expr1: str, expr2: str) -> bool: ...

@mcp.tool()
def satisfiable(expression: str) -> bool: ...

@mcp.tool()
def synthesize(truth_table: list[int]) -> str: ...

@mcp.tool()
def simplify(expression: str) -> str: ...
```

Use case: Claude stops guessing at boolean logic and computes it. Particularly useful for code review (checking redundant conditions, dead branches) and logic puzzle solving.

---

## AI Layer (Phase 3)

Natural language → expression via LLM, then expression → truth table via core engine, then result → plain English explanation via LLM. Supports any provider: Anthropic, OpenAI, Ollama (local), or any OpenAI-compatible endpoint.

```
"lights on when door open or motion detected but not both"
        ↓  LLM parses (provider-agnostic)
      D^M  + variable map: {D: "door open", M: "motion detected"}
        ↓  core engine
   truth table  ← CUDA accelerates this for large variable counts
        ↓  synthesizer
   minimal form: D^M
        ↓  LLM explains (provider-agnostic)
"Output is 1 exactly when door and motion states differ"
```

### Multi-rule pipeline — correct design

Each rule is a separate parse call. Variable assignments thread through as shared state:

```
Rule 1 → parse(sentence, variable_map={})           → expression + updated map
Rule 2 → parse(sentence, variable_map from Rule 1)  → expression + updated map
Rule 3 → parse(sentence, variable_map from Rule 2)  → expression + updated map
       → engine evaluates all expressions together
       → explain call → plain English summary
```

Each call has one responsibility. Variable map is explicit, inspectable, cacheable via Redis.

### Acceleration layers

- **Redis** — cache variable maps, parse results, truth tables. Same expression always
  produces the same result — skip recomputation on repeat. Session state for multi-turn.
- **CUDA** — `2^n` rows are independent. Each row maps 1:1 to a GPU thread.
  Drop-in replacement for the Python evaluation loop in `core/evaluator.py`.

---

## REST API Plan (Phase 4)

FastAPI. Stateless endpoints wrapping core directly. Redis for caching.
Deployable to any cloud (AWS Lambda, GCP Cloud Run, Fly.io, bare VM).

### Endpoints

```
POST /evaluate
  body: { "expression": "A.(B+C)" }
  returns: { expression, variables, rows, satisfiable, tautology,
             minterms, maxterms, eval_time_ms }

POST /simplify
  body: { "expression": "A.B+A.!B" }
  returns: { original, minimal, changed, prime_implicant_count }

POST /equivalent
  body: { "expression1": "A.(B+C)", "expression2": "A.B+A.C" }
  returns: { equivalent, differing_rows }

POST /satisfiable
  body: { "expression": "A.!A" }
  returns: { satisfiable, example }

POST /check-rules
  body: { "rules": ["A.B", "!A+!B", "A.!A"] }
  returns: { rules: [...], pairwise: [...], summary: {...} }

POST /nl/ask
  body: { "sentence": "lights on when door open or motion detected",
          "provider": "anthropic" }
  returns: { expression, variables, minimal, satisfiable, explanation, rows }

POST /nl/check-rules
  body: { "rules": ["grant if admin", "deny if admin"],
          "provider": "anthropic" }
  returns: { rules, pairwise, summary, parse_errors }
```

### Headers
```
X-API-Key: <key>          authentication (Pro/Team tiers)
X-Cache: HIT | MISS       Redis cache status
X-Eval-Time-Ms: 0.21      engine timing
```

### Caching strategy
```
/evaluate, /simplify, /equivalent, /satisfiable  →  cache by expression (Redis, TTL 24h)
/check-rules                                     →  cache by sorted rule set (Redis, TTL 1h)
/nl/ask                                          →  cache parse result by sentence (Redis, TTL 1h)
/nl/check-rules                                  →  no cache (variable map is stateful)
```

### Error responses
```json
{ "error": "invalid_expression",
  "message": "Unknown character '@' at position 3",
  "expression": "A@B" }
```

### Deployment
- Docker container, single `Dockerfile`
- `uvicorn api.routes:app --host 0.0.0.0 --port 8080`
- Environment vars: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `REDIS_URL`
- Health check: `GET /health → { status: ok, version: 0.1.0 }`

---

## Use Cases

### Developer Tooling
1. **Condition verification** — paste a boolean guard clause from code, check if it's a tautology (always grants), contradiction (never fires), or has redundant branches
2. **Logical equivalence checking** — verify two expressions are identical without running the code
3. **Access control auditing** — model permission logic as boolean expressions, find conditions that always allow or always deny access

### Education
4. **Truth table generation** — instant truth tables for digital logic and discrete math coursework
5. **Karnaugh map verification** — check hand-solved K-map answers against Quine-McCluskey output
6. **Boolean law demonstration** — teach De Morgan, distribution, absorption interactively in the REPL

### Digital / Hardware Design
7. **Gate expression minimization** — reduce logic before HDL (VHDL/Verilog) implementation
8. **Combinational circuit verification** — confirm a circuit expression produces the intended output column
9. **BNN layer mapping** — Binary Neural Networks use `+1/-1` weights, which map directly to boolean circuits; synthesize and minimize BNN layers

### AI / LLM Accuracy
10. **Tool-augmented reasoning** — via MCP, LLMs verify their boolean reasoning against ground truth instead of predicting it; eliminates hallucination on logic problems
11. **Deterministic verifier** — boolean logic is one domain where "probably correct" is unacceptable; the engine provides exact answers the LLM can anchor to
12. **Neuro-symbolic bridge** — sits at the discrete computation end; as neuro-symbolic AI matures, deterministic boolean verifiers become critical primitives

### Deep Learning
13. **Neural network as boolean circuit** — every neuron is a soft threshold gate; find the exact boolean function a trained binary network approximates
14. **BNN formal verification** — for binary/quantized networks, safety property verification is literally boolean satisfiability; the engine handles the SAT check
15. **Feature interaction analysis** — find the minimal boolean expression describing when a model fires over binary features; interpretability tool
16. **Logic-based constraints** — encode boolean rules as specifications; verify a network satisfies them by evaluating against truth tables
17. **CUDA acceleration target** — truth table rows are independent, map 1:1 to GPU threads; GPU-accelerated boolean evaluation is the compute primitive for large BNN layers

### Packaging / Integration
18. **pip-installable library** — `evaluate()` and `synthesize()` as clean Python functions, embeddable in any project
19. **REST API** — cloud-deployable via FastAPI, callable from any language
20. **Jupyter notebooks** — interactive boolean exploration, visualise truth tables, demo layer for teaching

### Cybersecurity
21. **Firewall rule auditing** — model firewall and network ACL rules as boolean expressions, find conditions that always allow traffic or always block it regardless of input
22. **Access policy verification** — check IAM and RBAC policies for contradictions — rules that can never be satisfied or always grant access unconditionally
23. **Security constraint checking** — verify that no combination of flags, roles, or conditions creates an unintended open path in an authentication or authorisation system

### Smart Contracts
24. **Pre-deployment logic verification** — Solidity and EVM contract conditions modeled as boolean expressions, verified before deploying on-chain where a logic bug costs real money and cannot be undone
25. **Condition equivalence across contract versions** — check that updated contract logic is equivalent to the original, or find exactly which cases changed
26. **Contradiction detection in contract clauses** — find clauses that can never be triggered or always override each other

### Legal / Compliance
27. **Contract clause verification** — model conditional contract clauses as boolean rules, check if any two clauses are contradictory or if a condition can never be satisfied
28. **Regulatory rule consistency** — compliance rulesets often span dozens of conditions across multiple documents; find conflicts before they become violations
29. **Policy deduplication** — identify equivalent rules across policy documents that can be consolidated

### Healthcare
30. **Treatment eligibility rules** — clinical decision rules modeled as boolean expressions, verified so no patient falls through contradictory or unreachable criteria
31. **Clinical decision tree verification** — check that every branch of a decision protocol is reachable and that no combination of symptoms leads to an undefined outcome
32. **Drug interaction logic** — contraindication rules expressed as boolean conditions, verified for completeness and internal consistency

### Financial Services
33. **Trading rule verification** — model algorithmic trading conditions, find rules that can never fire or always fire regardless of market state
34. **Risk condition auditing** — verify that risk gate logic has no contradictions — conditions where a trade is simultaneously allowed and blocked
35. **Regulatory compliance checks** — financial regulations often combine multiple boolean conditions; verify the implementation matches the written rule exactly

### CI/CD and DevOps
36. **Deployment gate logic** — verify pipeline conditions (branch, environment, test status, flag) have no contradictions that would permanently block or always skip a stage
37. **Feature flag consistency** — check that feature flag combinations don't produce contradictory behaviour across services
38. **Environment promotion rules** — verify that promotion conditions between dev/staging/prod are logically consistent and have no unreachable states

### Game Development
39. **Game state machine verification** — model trigger conditions and state transitions as boolean expressions, find unreachable states or always-true transitions
40. **Quest and unlock logic** — verify that achievement and unlock conditions are satisfiable — that the player can actually reach them
41. **Balancing condition checks** — find conditions where a game mechanic always fires or never fires regardless of player state

### Database and Query Optimisation
42. **WHERE clause simplification** — convert complex SQL WHERE conditions to minimal boolean form before execution planning
43. **Query equivalence checking** — verify two queries with different WHERE clauses return identical result sets for all inputs
44. **Dead filter detection** — find filter conditions that are contradictions — they always return zero rows

### Robotics and Automation
45. **Sensor trigger verification** — model actuator trigger conditions as boolean expressions, verify safety interlocks can never be simultaneously satisfied with activation conditions
46. **Safety interlock auditing** — check that no combination of sensor states bypasses a safety condition
47. **Control logic minimization** — reduce gate logic in embedded control systems before implementation

---

## Operator Reference

| Symbol | Operation | Precedence |
|---|---|---|
| `!` | NOT (unary) | 4 (highest) |
| `.` | AND | 3 |
| `^` | XOR | 2 |
| `+` | OR | 1 (lowest) |

Variables: uppercase letters `A`–`Z`. Auto-detected from expression.

---

## Market Position

### What exists
| Tool | What it does | Why it's not this |
|---|---|---|
| `sympy.logic` | Truth tables, simplification, SAT | Academic, no MCP, no NL layer, not LLM-native |
| Z3 / SAT4J / Alloy | Formal verification, extremely powerful | Built for researchers, steep learning curve, no conversational interface |
| Online truth table generators | Web toys | No API, no synthesis, no MCP |

### What doesn't exist
- An MCP-native boolean engine an LLM can call mid-conversation to verify its own reasoning
- A `check_prompt_logic` tool — "paste your system prompt rules, get back contradictions" as a usable product
- A full NL → boolean expression → verification → plain English pipeline, packaged for developers

### The gap
The raw computation exists in academia. The **product** doesn't.

Z3 can do everything this engine does and more — but almost nobody ships Z3 to a non-specialist. The competition isn't Z3. The competition is "the developer manually reads their if-conditions and hopes for the best."

### The moat
Not the algorithm. The three things that don't exist together anywhere:
1. **MCP integration** — Claude calls the engine instead of predicting logic
2. **NL layer** — non-specialists describe rules in plain English, engine verifies them
3. **Packaging** — pip-installable, embeddable, REST-deployable, notebook-ready

### The core insight
Boolean logic is one domain where "probably correct" is unacceptable. This engine is deterministic — same expression always produces the same truth table, no approximation, no hallucination. It hands LLMs a ground-truth anchor for the one class of reasoning they reliably get wrong.

### Credibility — how it's verified

The engine's credibility comes from **exhaustive enumeration**. It does not sample, approximate, or predict — it evaluates every single possible input combination. For `n` variables it produces exactly `2^n` rows, each computed independently by a stack evaluator running the actual operators.

**What that means in practice:**
- **Satisfiable** — an actual row where output = 1 was found, not inferred
- **Contradiction** — every row was checked, all were 0
- **Equivalent** — output columns compared row-by-row across the full truth table
- **Conflict** — conjunction of both rules evaluated for every input, always returned 0

**The honest limitation:** scales as `2^n`. Tractable up to ~20 variables (1M rows). At 30+ variables, SAT solvers (Z3, DPLL/CDCL) are the right tool — they avoid evaluating every row. For the prompt logic use case, where rules typically have 5–15 boolean variables, exhaustive enumeration is not just credible — it's **provably complete**. No edge case is missed.

**Auditable by design:** the core evaluator is 15 lines (`core/evaluator.py:_evaluate_prefix`). If the operators are implemented correctly, the results are correct. No black box, no model weights, no probability — just arithmetic.

This is a stronger correctness claim than any probabilistic tool can make.

---

### The $5 product
`check_prompt_logic` — paste a list of rules from a system prompt, get back:
- Which rules are contradictions (always false)
- Which rules are tautologies (always true, i.e. redundant)
- Which pairs always conflict (can never both be satisfied)
- Which pairs are equivalent (duplicate rules)

Every serious AI deployment has this problem. Nobody has the tooling for it.

---

## Milestones

| # | Milestone | Status |
|---|---|---|
| 0 | Fix Java bugs, document, branch | Done |
| 1 | Python rewrite — `core/` only | Done |
| 2 | Tests — 90 tests across all core modules | Done |
| 3 | CLI — REPL + one-shot, all output formats | Done |
| 4 | MCP server | Done |
| 5 | REST API (FastAPI) | Done |
| 6 | Web UI (Streamlit or React on FastAPI) | Planned |
| 7 | Claude API NL layer | Planned |
| 8 | CUDA acceleration for truth table evaluation | Planned |
| 9 | Expression caching layer | Planned |
| 10 | Demo notebook (`demo.ipynb`) | Planned |
