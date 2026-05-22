# Session Log

Running log of decisions, prompts, and outcomes. Use this to recover context if session is lost.

---

## Session 1

### Prompt: "See through this project"
Explored the Java codebase — 3 classes (`Calculator`, `Logics`, `StringParser`), monolithic CLI, Scanner-based I/O.

**Findings:**
- Correct core algorithm (truth table generation, prefix stack evaluator)
- 6 bugs identified (see below)

---

### Prompt: "What application do you see this fulfilling?"
Identified 4 use cases:
1. Education / truth table verifier
2. Digital circuit design aid
3. Boolean simplification preprocessor
4. Logic puzzle / SAT checker

Best fit: embedded engine in a simulation project (as README hinted).

---

### Prompt: "Fix the bugs"
All 6 bugs fixed on branch `api-refactor`:

| # | File | Bug | Fix |
|---|---|---|---|
| 1 | `StringParser.java:10-11` | `infixToPreFix()` called twice in constructor | Reuse `prefixString.toCharArray()` |
| 2 | `StringParser.java:16-28` | Precedence inverted — OR=4 (highest), NOT=1 (lowest) | NOT=4, AND=3, XOR=2, OR=1 |
| 3 | `StringParser.java:37-47` | Extra `i++` inside bracket-swap loop skipped chars after every bracket | Removed inner `i++` |
| 4 | `StringParser.java:71-73` | `for (i=0; i<=stack.size(); i++)` — size shrinks as popped, never fully drains | Replaced with `while (!stack.isEmpty())` |
| 5 | `Logics.java:66-69` | `!` (NOT) popped two operands — it's unary | `!` now pops one operand only |
| 6 | `Calculator.java:7` | Field init `new int[(int)Math.pow(2,gates)]` with `gates=0` → size 1 array | Changed to `int[] array;` |

---

### Prompt: "Write a doc, make a separate branch"
- Created branch: `api-refactor`
- Created `DESIGN.md` with CLI interface design, module breakdown, output formats, milestones
- User chose **polished CLI tool** as the API target direction

---

### Prompt: "Can we do something AI/ML oriented?"
Proposed 3 directions:
1. **NL → Expression** via Claude API (most immediately impressive)
2. **Truth table → Expression synthesis** inverse problem (Quine-McCluskey / genetic algo)
3. **Neural network as boolean circuit** (educational)

**Recommendation:** Combine 1 + 2. Claude API handles NL input and output explanation, core engine handles evaluation, synthesizer handles inverse problem.

---

### Prompt: "Python and Go over Java would be just 3-5 lines"
Agreed — Python rewrite decided. Java was written for placement season prep, not for this use case. Python wins on ecosystem (Claude SDK, sympy, rich, typer/click).

---

### Prompt: "What can an MCP server do with this?"
MCP server exposes core tools Claude can call mid-conversation:
- `evaluate`, `simplify`, `equivalent`, `satisfiable`, `synthesize`

Key insight: **Claude stops guessing at boolean logic and computes it.** Grounding LLM reasoning with actual evaluation. Useful for code review (dead branches, redundant conditions) and logic puzzles.

---

### Prompt: "Repurposing in Python first makes more sense?"
Yes — confirmed order:
1. Python rewrite (core engine)
2. MCP server (wrap core)
3. Claude API NL layer
4. Expression synthesis

Avoids Java subprocess overhead from Python, keeps everything one language.

---

### Prompt: "Fork and restructure with clean wrappers"
Decided final architecture:

```
core/          ← pure logic, zero external dependencies
mcp_server/    ← MCP wrapper, decorates core
api/           ← FastAPI REST, cloud deployable
cli/           ← typer/click CLI
tests/
```

Principle: `core/` has no knowledge of anything outside itself. Every other layer is a thin wrapper. Independently deployable, independently testable.

---

### Prompt: "Each time I prompt, just put that here and the result"
Log every prompt and a short summary of the result in `log.md` as the conversation progresses.

---

### Prompt: "Yes commit and push"
Two commits made on `python-rewrite`. Push failed — remote is HTTPS, needs auth. User pushed manually.

### Prompt: "Done."
Branch `python-rewrite` live on remote.

### Prompt: "Why is CLI not available, how can I enable that"
Installed `gh` CLI via dnf from official GitHub RPM repo. User authenticated via browser.

### Prompt: "Logged in"
- Renamed repo: `Boolean-Algebra-Calculator` → `boolean-algebra-java`
- Created new repo: `boolean-algebra-engine` (Python project home)
- Updated local remote URL to point at `boolean-algebra-java`

### Prompt: "Rename it to engine-python, because we will repurpose it in Go too, mostly for CUDA/GPU"
- Renamed `boolean-algebra-engine` → `boolean-algebra-engine-python`
- Future plan: `boolean-algebra-engine-go` for GPU/CUDA work

---

### Prompt: "Fork over this branch for that"
Created branch `python-rewrite` off `api-refactor`. Python rewrite will happen here.

---

### Prompt: "Yes please (start Python rewrite)"
- Stripped Java files, set up structure: `core/`, `cli/`, `mcp_server/`, `api/`, `tests/`
- Wrote `core/models.py` — `TruthTableRow`, `TruthTable`, `EvaluationResult` dataclasses
- Wrote `core/parser.py` — `get_variables`, `validate`, `infix_to_prefix`
- Wrote `core/evaluator.py` — prefix stack evaluator, `evaluate()` returns `TruthTable`
- Fixed Python 3.9 compat (`from __future__ import annotations`)
- Verified: `A+B`, `A.!A`, `A.(B+C)` all produce correct truth tables

---

### Prompt: "Yes (write synthesizer)"
- Wrote `core/synthesizer.py` — Quine-McCluskey algorithm
- Takes a `TruthTable`, returns minimal boolean expression string
- Fixed leftover `stack.push(c) if False else` junk in `parser.py`
- Verified: `A.(B+C)` and `A.B+A.C` both reduce to `A.C+A.B`, `A.!A` → `0`, `A^B` → `!A.B+A.!B`

---

### Prompt: "Yes document test"
Added module-level docstrings to all 5 test files explaining scope, approach,
and what each group of tests covers. Added per-test docstrings explaining the
specific behaviour under test. 90/90 still passing.

### Prompt: "Yes do that and document"
Added `test_integration.py` and `test_edge_cases.py`:
- Integration: full pipeline round-trips, De Morgan, distribution, absorption, consensus theorem
- Edge cases: single variable, synthesizer on 0/1/single/all-but-one minterms, nested parens, 4-5 variable stress, all operators together, operator precedence, all invalid input paths
- Fixed absorption test — variable context mismatch (`A+A.B` vs `A` use different variable sets)
- 90/90 passing

### Prompt: "Tests obviously"
- Wrote 48 tests across `test_models.py`, `test_parser.py`, `test_evaluator.py`, `test_synthesizer.py`
- Covers: truth table properties, validation, prefix conversion, De Morgan's laws, distribution law, round-trip synthesis, minimization (`A.B+A.!B` → `A`)
- 48/48 passed

---

## Current State

- Repo: `boolean-algebra-engine-python`
- `core/` complete and tested: `models.py`, `parser.py`, `evaluator.py`, `synthesizer.py`
- `tests/` complete: 48 tests, all passing
- **Next step: `cli/`**

---

## Decisions Made

| Decision | Reason |
|---|---|
| Python over Java | Ecosystem, conciseness, Claude API SDK |
| Fork Java, don't delete | Preserve original, good reference |
| `core/` has zero I/O | Independently testable, wrappable by anything |
| MCP before REST API | More immediately useful for AI use case |
| Auto-detect variables | Removes friction from current manual `--vars` |
