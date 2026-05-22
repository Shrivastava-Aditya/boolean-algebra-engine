# boolean-algebra-engine-python

A boolean algebra engine written in Python. Evaluates boolean expressions against truth tables and synthesizes minimal expressions from truth tables using Quine-McCluskey.

Forked from [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — the original Java implementation written during placement season prep.

---

## What it does

**Forward:** expression → truth table
```
A.(B+C)  →  A | B | C | out
             0 | 0 | 0 |  0
             0 | 0 | 1 |  0
             0 | 1 | 0 |  0
             0 | 1 | 1 |  0
             1 | 0 | 0 |  0
             1 | 0 | 1 |  1
             1 | 1 | 0 |  1
             1 | 1 | 1 |  1
```

**Inverse:** truth table → minimal expression (Quine-McCluskey)
```
minterms [5, 6, 7]  →  A.C+A.B
```

---

## Operators

| Symbol | Operation | Precedence |
|--------|-----------|------------|
| `!`    | NOT       | 4 (highest) |
| `.`    | AND       | 3 |
| `^`    | XOR       | 2 |
| `+`    | OR        | 1 (lowest) |

Variables must be uppercase letters `A`–`Z`. Parentheses override precedence as usual.

---

## Project structure

```
core/                   Pure logic — no I/O, no dependencies
  models.py               TruthTable, TruthTableRow, EvaluationResult dataclasses
  parser.py               Validation, variable detection, infix → prefix conversion
  evaluator.py            Prefix stack evaluator — evaluate() entry point
  synthesizer.py          Quine-McCluskey — synthesize() entry point

tests/                  90 tests across all core modules
  test_models.py
  test_parser.py
  test_evaluator.py
  test_synthesizer.py
  test_integration.py     Full pipeline, Boolean laws, equivalence checks
  test_edge_cases.py      Boundary inputs, stress tests, error paths

cli/                    (coming) typer-based CLI
mcp_server/             (coming) MCP server — exposes core as Claude tools
api/                    (coming) FastAPI REST API — cloud deployable
```

---

## Quickstart

```bash
git clone https://github.com/Shrivastava-Aditya/boolean-algebra-engine-python
cd boolean-algebra-engine-python
pip install pytest
python3 -m pytest tests/
```

### Using the core directly

```python
from core.evaluator import evaluate
from core.synthesizer import synthesize

# Forward: expression → truth table
t = evaluate('A.(B+C)')
print(t.variables)     # ['A', 'B', 'C']
print(t.minterms)      # [5, 6, 7]
print(t.satisfiable)   # True
print(t.tautology)     # False

for row in t.rows:
    print(row.inputs, '->', row.output)

# Inverse: truth table → minimal expression
print(synthesize(t))   # A.C+A.B

# Check logical equivalence
t1 = evaluate('A.(B+C)')
t2 = evaluate('A.B+A.C')
print(t1.minterms == t2.minterms)  # True — distributive law
```

---

## Roadmap

| # | Layer | Status |
|---|-------|--------|
| 1 | `core/` — parser, evaluator, synthesizer | Done |
| 2 | `tests/` — 90 tests, all passing | Done |
| 3 | `cli/` — polished CLI with `--format json`, `--satisfiable`, `--minterm` flags | Next |
| 4 | `mcp_server/` — MCP server, exposes core as tools Claude can call | Planned |
| 5 | `api/` — FastAPI REST API, deployable to cloud | Planned |
| 6 | Natural language layer via Claude API | Planned |

---

## Related

- [boolean-algebra-java](https://github.com/Shrivastava-Aditya/boolean-algebra-java) — original Java version
- [boolean-algebra-engine-go](https://github.com/Shrivastava-Aditya/boolean-algebra-engine-go) — future Go version (GPU/CUDA)
