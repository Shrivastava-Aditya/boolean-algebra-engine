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

Natural language → expression via Claude API, then expression → truth table via core engine, then result → plain English explanation via Claude API.

```
"lights on when door open or motion detected but not both"
        ↓  Claude parses (Claude API)
      D^M
        ↓  core engine
   truth table
        ↓  synthesizer
   minimal form: D^M
        ↓  Claude explains (Claude API)
"Output is 1 exactly when door and motion states differ"
```

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

## Milestones

| # | Milestone | Status |
|---|---|---|
| 0 | Fix Java bugs, document, branch | Done |
| 1 | Python rewrite — `core/` only | Done |
| 2 | Tests — 90 tests across all core modules | Done |
| 3 | CLI — REPL + one-shot, all output formats | Done |
| 4 | MCP server | Planned |
| 5 | REST API (FastAPI) | Planned |
| 6 | Web UI (Streamlit or React on FastAPI) | Planned |
| 7 | Claude API NL layer | Planned |
| 8 | CUDA acceleration for truth table evaluation | Planned |
| 9 | Expression caching layer | Planned |
| 10 | Demo notebook (`demo.ipynb`) | Planned |
