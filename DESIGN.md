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
| 1 | Python rewrite — `core/` only | Next |
| 2 | CLI wrapper | — |
| 3 | MCP server | — |
| 4 | REST API (FastAPI) | — |
| 5 | Claude API NL layer | — |
| 6 | Expression synthesis (Quine-McCluskey) | — |
| 7 | Tests across all layers | — |
