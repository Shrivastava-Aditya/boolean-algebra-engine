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

### Prompt: "In REPL mode I would love a description and instruction manual too"
Added REPL_BANNER (project description, what it does, operator table) shown on launch. Expanded REPL_HELP into a full instruction manual with commands, output formats, and examples with annotations. Banner shows once on start, manual shows on `help`/`h`/`?`.

### Prompt: "Is it not interactable like Claude Code"
Added REPL mode to CLI — `python3 -m cli.main -i` or auto-launches when called with no args in a tty. Supports all same flags inline (e.g. `A+B --format json`), `help`, `exit`/`quit`/Ctrl+C. Fixed `@app.callback` conflict that was breaking one-shot mode.

### Prompt: "Yes build a CLI then I will integrate it in pynb"
Built `cli/main.py` using typer + rich. Commands:
- `boolcalc "expr"` — rich truth table to terminal
- `--format json/csv/minimal` — structured output for scripting/notebooks
- `--synthesize` — print minimal expression
- `--minterms / --maxterms` — print index lists
- `--satisfiable / --tautology` — exit-code only, no output (scriptable)
- `--metrics` — show timing and memory
- `--output file` — write to file
- stdin support: `echo "A+B" | boolcalc`
All formats tested and working.

### Prompt: "And document and update log if we haven't"
Added module and function docstrings to all four core modules:
- `models.py` — module docstring, class/property docstrings for all three dataclasses
- `parser.py` — module docstring with operator precedence table, docstrings for all three public functions
- `evaluator.py` — module docstring explaining CUDA context, docstrings for `_evaluate_prefix` and `evaluate()` with full Args/Returns/Example
- `synthesizer.py` — module docstring explaining QM algorithm and special cases, docstrings for all internal helpers and `synthesize()` with full Args/Returns/Example
90/90 tests still passing.

### Prompt: "Include machine time and memory calculator as output"
Added `PerformanceMetrics` dataclass to `models.py` — captures `eval_time_ms`, `synth_time_ms`, `peak_memory_bytes`, `rows_evaluated`, `prime_implicant_count`. Both `evaluate()` and `synthesize()` now return `(result, PerformanceMetrics)` tuples. Updated all 90 tests to unpack tuples. Baseline numbers visible now — CUDA and caching improvements will be measurable against them.

### Prompt: "Yes, of course, before we build it deeply"
Added `pyproject.toml` — package name `boolean-algebra-engine`, GPL-3.0, Python 3.9+, optional deps `cli` (typer+rich) and `dev` (pytest), `boolcalc` entry point wired to `cli.main:app`. Installs cleanly with `pip install -e ".[dev]"`, 90/90 tests still passing.

### Prompt: "Can you update a readme.md"
Rewrote README.md — covers what the engine does (forward + inverse), operators, project structure, quickstart, core usage examples, roadmap, and links to related repos.

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

### Prompt: "Yes write use cases and make repo private"
- Repo set to private via `gh repo edit --visibility private`
- Added 20 use cases to `DESIGN.md` across 6 categories: developer tooling, education, digital/hardware design, AI/LLM accuracy, deep learning, packaging/integration
- Updated milestones table to reflect current done/planned state
- Key insight: engine is a deterministic verifier for LLM boolean reasoning, and maps onto Binary Neural Networks directly

### Prompt: "Can you expose a port on VM and publish an index.html describing this project over there?"
- Opened port 8080 via `firewall-cmd`
- Wrote full dark-themed commercial landing page at `index.html` (~600 lines, pure HTML/CSS/JS)
- Sections: hero with pipeline diagram, stats, forward/inverse code examples, CLI terminal demo, operator table, 20 use cases across 6 categories, deep learning connections, ASCII architecture diagram, 10-milestone roadmap with status tags, footer
- Started Python HTTP server on port 8080 (background process)
- Live at: `http://80.225.206.105:8080`

---

### Prompt: "Yes please (build MCP server)"
- Installed Python 3.11 via dnf (MCP SDK requires >=3.10, VM was on 3.9)
- Installed `mcp[cli]` 1.27.1 under python3.11
- Wrote `mcp_server/server.py` with 5 tools:
  - `evaluate` — expression → full truth table + metrics
  - `simplify` — expression → minimal SOP form
  - `equivalent` — two expressions → same truth table?
  - `satisfiable` — expression → any row outputs 1?
  - `check_prompt_logic` — list of rules → contradictions, tautologies, pairwise conflict/equivalence analysis
- All 5 tools smoke tested and verified correct
- Added `mcp = ["mcp[cli]>=1.0.0"]` to `pyproject.toml` optional dependencies
- Run with: `python3.11 -m mcp_server.server`

---

### Prompt: "yes write this into PRODUCT.md and DESIGN.md and write an API plan first"
- Added full pipeline architecture (Redis + CUDA) to PRODUCT.md and DESIGN.md
- Added multi-call parse pipeline design with threaded variable maps
- Added REST API plan to DESIGN.md — 7 endpoints, caching strategy, auth, deployment
- Built `api/routes.py` — FastAPI, all 7 endpoints, Redis cache, auth middleware, graceful degradation
- All endpoints smoke tested: evaluate, simplify, equivalent, satisfiable, check-rules, health
- Cache degrades gracefully when Redis not available
- Updated pyproject.toml: api, api-cache, dev extras

### Prompt: "can we use other Models as well (NL layer)"
- Rebuilt `nl/nl.py` with provider abstraction — `Provider` ABC, one `complete()` method
- Four built-in providers: `AnthropicProvider`, `OpenAIProvider`, `OllamaProvider`, `OpenAICompatProvider`
- Ollama runs fully locally — no API key, no cost
- OpenAICompatProvider covers Groq, Together AI, LM Studio, vLLM, any OpenAI-compatible endpoint
- CLI updated: `--provider`, `--model`, `--base-url` flags on `ask` and `check-rules` commands
- Adding a new model = one class, one method, nothing else changes

---

### Prompt: "take one complex example and deconstruct it for multiple use cases"
- Chose cloud deployment gate scenario: `T.(A+H.O).W.!I` — 6 variables, 64 rows
- Ran full truth table — 5 deploy-allowed rows out of 64
- Minimal form: `H.!I.O.T.W + A.!I.T.W` — two clear deployment paths
- Finding: incident flag (`I=1`) is absolute blocker with no exceptions
- Finding: one-approver condition redundant when two approvers present
- Explained in plain English — "the door analogy"
- Eval: 3.7ms, synth: 0.8ms total

### Prompt: "That linux statement, when plugged with this can also give output in matplotlib"
- Confirmed: L=using Linux, M=using Mac, contradiction at L=0 M=1
- Identified as the flagship demo — personal, relatable, visual
- One red cell in the heatmap = the exact row where the statement breaks down

### Prompt: "what other things can this statement plug into"
- Identified 7 domains: philosophy/logic education, debate analysis, CBT,
  journalism/fact-checking, AI alignment, personal journaling, HR policy
- Written into PRODUCT.md under "What else this statement plugs into"

### Prompt: "write one more section of CBT / therapy consultancy"
- Added 7 CBT statements to `statements.md` (statements 15-21):
  worthiness trap, control paradox, lovability contradiction,
  perfectionism loop, burden belief, anxiety identity, self-sabotage split
- Each has variables, boolean expressions, expected findings, clinical context
- Statement 19 (burden belief) flagged as clinical risk pattern
- Added therapist usage guide: transcribe beliefs → engine → conflicting pairs → intervention

### Prompt: "write some statements that can be verifiable"
- Created `statements.md` — 21 verifiable statements across 6 categories:
  personal reasoning, system prompts, business policy, legal, medical, philosophical
- Each has plain English statement, variable map, boolean expressions, expected finding
- Three usage methods shown: NL layer, direct expressions, CLI

### Prompt: "write a clear demo script"
- Created `demo.py` — 514 lines, 10 sections, loan approval scenario
- Created `DEMO_EXPLAINED.md` — 286 lines, plain English explanation of all 10 sections
- Punchline: 6 rules, 4 people, 6 months, 2 compliance violations found in 4.5ms

### Prompt: "give me an architecture of what we have"
- Added full ASCII architecture diagram to `DESIGN.md`
- Shows all 4 interface layers, NL layer, core engine modules, acceleration layer

### Prompt: "can it be self-distributing"
- Identified 3 self-distribution mechanisms: MCP ecosystem, pip package, viral demo
- The compounding loop: find it → catch real bug → tell someone → repeat
- One good public demo with a real finding seeds the loop

---

## Current State

- Repo: `boolean-algebra-engine-python` (private)
- `core/` — done, documented, 90 tests passing
- `cli/` — done, REPL + one-shot, all formats, NL commands
- `mcp_server/` — done, 5 tools, Python 3.11
- `api/` — done, 7 endpoints, Redis cache, auth, graceful degradation
- `nl/` — done, 4 providers (Anthropic, OpenAI, Ollama, OpenAI-compat)
- `demo.py` — end-to-end demo, 10 sections
- `DEMO_EXPLAINED.md` — plain English walkthrough
- `PRODUCT.md` — full product brief, scope, pricing, distribution, replicability
- `DESIGN.md` — architecture diagram, 47 use cases, REST API plan, milestones
- `statements.md` — 21 verifiable statements across 6 domains + 7 CBT patterns
- `index.html` — commercial landing page
- **Next: web UI → public launch**

---

## Decisions Made

| Decision | Reason |
|---|---|
| Python over Java | Ecosystem, conciseness, Claude API SDK |
| Fork Java, don't delete | Preserve original, good reference |
| `core/` has zero I/O | Independently testable, wrappable by anything |
| Repo private for now | Commercialisation in progress — dual license model |
| MCP before REST API | More immediately useful for AI use case |
| Auto-detect variables | Removes friction from current manual `--vars` |
| Provider abstraction in NL | Any LLM works — not locked to Anthropic |
| Separate parse calls with threaded variable map | Each call single-responsibility, map is inspectable and cacheable |
| GPL-3.0 core + commercial license | Open adoption, enterprise monetisation |
| statements.md as playground | Real examples drive demos, marketing, and testing |
