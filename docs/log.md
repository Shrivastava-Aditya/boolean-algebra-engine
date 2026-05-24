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

### Prompt: "is this a serious product / what do you think about pricing / distribution strategy / update README and PRODUCT.md"
- Established the product is serious — infrastructure for AI pipelines, not a library
- Identified the missing thread: the feedback loop, the logic layer sitting inside AI reasoning
- Defined what it catches: logical hallucination (provable) vs factual hallucination (out of scope)
- Latency story: <10ms vs 500-3000ms for self-critique/constitutional AI
- Pricing reframed: infrastructure pricing ($99-999/month per pipeline) — but not yet, no x% yet
- Distribution: phased — use it yourself → find x% → communities → market → paid
- Honest state: even the builder hasn't used it yet. That's next.
- README rewritten with logic layer positioning
- PRODUCT.md updated with hallucination reduction, latency, reframed competitive landscape, moat, pricing, distribution

### Session end
Next: test the engine against something real. Find x%. That's the only thing that matters now.

---

## Session 2

### Prompt: "make it public on github"
- Repo visibility changed from private to public via `gh repo edit --visibility public --accept-visibility-change-consequences`
- Install command now works without auth: `pip install git+https://github.com/Shrivastava-Aditya/boolean-algebra-engine-python.git`

### Prompt: "visualisations — complexity vs variables, conflict graph"
- Created `visualisations.ipynb` — Colab-ready notebook with two cells:
  - **Complexity vs variables**: XOR chains `A^B^C^...` across n=1–10, plots prime implicant count and eval time vs variable count. Shows 2^n scaling visually.
  - **Conflict graph**: rules as nodes, networkx graph, red edges for always-conflict pairs, yellow for equivalent pairs. Swap in any rule set.
- Committed and pushed to master.

### Insight: "Language is fuzzy. Logic is not."

Core principle surfaced during session:

- LLMs live in the fuzzy part — they predict, approximate, sometimes get it wrong
- The engine lives in the math part — same input, same output, every time, no approximation
- Wiring them together gives you the flexibility of language with the correctness of math

**The self-referential use case — engine validates the NL layer:**

The NL layer is a probabilistic parser. If you give it a logically consistent set of rules in plain English and its parsed output contains contradictions — the NL layer hallucinated.

```
plain English rules (known consistent)
        ↓
    NL layer parses
        ↓
    engine checks
        ↓
contradiction found? → NL layer made a parsing error
```

This gives you a measurable, automatable accuracy score for the NL layer itself — without human-labeled boolean expressions. You only need to label whether the original natural language rules were consistent or contradictory, which any human can do. The engine tells you if the NL layer agreed.

The deterministic layer validates the probabilistic layer. They close the loop.

**The general principle:**
Wherever you can reduce a problem to discrete computation — offload it from the LLM entirely. Let the LLM do language. Let math do math.

### Insight: Proving and measuring hallucination reduction — the experiment design

Two separate problems, solved in order.

**Step 1 — Prove hallucination exists**

The engine is the oracle. You don't need human labelers.

1. Generate rule sets where the correct answer is computed by the engine — not guessed
2. Ask an LLM the same question over those rules
3. Compare LLM answer vs engine answer
4. Every disagreement is a provable hallucination

If the engine says `A.!A` is a contradiction and the LLM says it's satisfiable — the LLM is wrong. Provably. No ambiguity.

**Step 2 — Measure the decrement**

Baseline first. Then wire the layer in.

```
Without layer:  LLM output → user              → X% contain logical contradictions
With layer:     LLM output → engine checks      → contradictions intercepted → user sees 0%
```

The decrement is X% — the full baseline rate — for the class of errors the engine catches. Binary. Either it catches it or it doesn't.

**The experiment**

Generate 500 rule sets of 3–7 rules each. Compute ground truth with the engine. Ask an LLM a question requiring all rules simultaneously. Count disagreements with engine — that's baseline X%. Run same 500 with logic layer intercepting. Count what reaches output. That's the reduction number. Publish it.

**What's provable vs not**

| Claim | Provable? |
|---|---|
| LLMs produce logically contradictory outputs | Yes — engine is oracle |
| Engine catches 100% of those contradictions | Yes — exhaustive enumeration |
| Hallucination reduced by X% | Yes — scoped to logical contradictions only |
| Factual hallucination reduced | No — out of scope, don't claim it |

**The structural advantage**

Most hallucination benchmarks require human labeling at scale. This one doesn't. Ground truth is free to generate — the engine computes it. 500 test cases cost nothing. 50,000 cost nothing. That's what makes this benchmark publishable and reproducible.

### First benchmark run — 2026-05-23

Model: tinyllama (1.1B, CPU, Ollama)
Cases: 10 (5 conflicting, 5 compatible)
Tool: benchmark.py, engine as oracle

Results:
- Hallucination rate: 40%
- Conflicting pairs: 60% missed (model said "yes, compatible" when they always conflict)
- Compatible pairs: 20% missed
- Engine caught: 100% of errors

Failed cases:
- A.!B  +  A.B+!A.!B   → engine=no,  llm=yes
- (A+B).(A+C)  +  !A   → engine=yes, llm=no
- A.B  +  !A+!B         → engine=no,  llm=yes  (De Morgan — always false together)
- A.B.C  +  !C          → engine=no,  llm=yes

This is symbolic notation, no natural language, no ambiguity.
The easiest possible version of the test. Rate on real pipelines will be higher.

Next: run at 100 cases with a stronger model. That number is publishable.

### Session 2 wrap-up — 2026-05-23

**What was built this session:**

- Repo made public → pip installable from GitHub
- `visualisations.ipynb` — Colab notebook, complexity vs variables + conflict graph
- `benchmark.py` — LLM hallucination benchmark, engine as oracle
- Installed Ollama + tinyllama locally, ran first benchmark
- **First result: 40% hallucination rate, tinyllama 1B, 10 cases, 3 variables**
- `visualise_results.py` — 4 Reddit-ready visualisations saved to `images/`
- `FAILURES.md` — real-world severity analysis of all 4 failures
- `BENCHMARK_PLAN.md` — batching, async, goroutines, multi-model, variable matrix
- `TODO.md` — full build list across all layers
- Branch structure: `master` (project) · `product-readme` (product) · `benchmark` (measurement)
- Repo made private again

**Key decisions:**
- Go extension is the scale path — goroutines for benchmark runner, CUDA for engine
- Python stays as reference implementation and interface layer
- Variable increment test is the study — hallucination rate vs n variables, per model
- The degradation curve never reaches zero — that is the finding

**What's next:**
- Run benchmark at 100 cases
- Add Groq free tier provider (fast, no cost)
- Run variable increment test at n=3,5,7,10
- Get API credits for GPT-4o run
- Merge product-readme and benchmark into master

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
- `ui/app.py` — Streamlit UI, 3 modes, dark theme, matplotlib heatmap + conflict matrix
- **Next: public launch prep**

---

### Prompt: "can we also show a matplotlib for something? if we are into demozone"
- Added truth table heatmap to Expression mode — green/red grid, output column highlighted in gold
- Added conflict matrix to Rule Auditor — N×N grid, red ✗ for conflicts, green ✓ for safe pairs
- Installed matplotlib + numpy under python3.11

### Prompt: "update PRODUCT.md with everything we just figured out"
Major repositioning. The product is not a library with wrappers — it is a logic layer
for AI agents and models. Key findings:
- What it is: inference-time logical consistency verifier, sits between AI reasoning and output
- The claim: reduces logical hallucination by x% (measurable, reproducible, your pipeline)
- The latency advantage: <10ms runtime overhead vs 500-3000ms for self-critique/constitutional AI
- The gap: no existing tool makes this specific claim — inference-time, measurable, agent-native, plain English
- Logical hallucination (caught) vs factual hallucination (not caught) — precise, defensible claim
- Three deployment positions: agent pipelines, system prompt validation, LLM output verification
Updated: What it is, Where it sits, Hallucination reduction section, Latency section,
What doesn't exist (reframed), Moat (reframed around position not algorithm),
How it can be used (logic layer framing)

### Prompt: "we dont really need to use the UI this way / but update the product md"
- Updated PRODUCT.md stack table — all layers now marked built
- Added "The visualisation layer" section — describes heatmap and conflict matrix as demo tools

---

---

## Session 3 — 2026-05-23

### Prompt: "what do you think can be a good strategy for distribution of this project?"
Three audiences, three paths identified:
- **PyPI** — pip-installable library for Python developers (already had pyproject.toml)
- **MCP registry** — for Claude/agent builders; highest-leverage given the interception layer direction
- **Docker + Go binary** — for infrastructure/ops teams; Go binary makes the <10ms latency claim credible

Lead with r/LocalLLaMA once 100-case benchmark is ready. That audience gives the most honest technical feedback.

### Prompt: "which Reddit community?"
- **r/LocalLLaMA** — best fit for benchmark results (model comparisons, hallucination rates)
- **r/Python** — for the library/tool angle
- **r/compsci** — for the algorithm angle (QM, shunting-yard)
- **r/ClaudeAI** — when `verify_output` MCP tool is built

### Prompt: "make a package then that we can publish"
- Fixed `pyproject.toml` license format: `{ text = "GPL-3.0-only" }` → `"GPL-3.0-only"` (SPDX string)
- Removed deprecated `License :: OSI Approved :: GNU General Public License v3 (GPLv3)` classifier
- Built with `python -m build` — both `.whl` and `.tar.gz` produced cleanly
- Validated with `twine check dist/*` — both PASSED
- Confirmed package name `boolean-algebra-engine` available on PyPI

### Prompt: "update the description — disconnected from real purpose"
Updated `pyproject.toml` description from:
> "Boolean algebra engine — evaluate expressions, generate truth tables, synthesize minimal forms"

To:
> "Deterministic logic layer for AI agents — catch logical contradictions in system prompts, rules, and agent reasoning"

### PyPI publish — versions 0.1.0 → 0.1.5
Multiple iterations due to PyPI immutability (cannot overwrite a published version):
- **0.1.0** — first publish, original description
- **0.1.1** — author email updated to `aditya.shrivastava.architect@proton.me`
- **0.1.2** — description updated to product-focused copy
- **0.1.3** — README rewritten (product-first), images included
- **0.1.4** — image URLs fixed to raw GitHub links
- **0.1.5** — first automated release via GitHub Actions CI/CD

Auth path: `~/.pypirc` written directly with token. Token `Bool-1` scoped to `boolean-algebra-engine` package.

### Prompt: "make a separate branch engine-PyPI"
- Created branch `engine-PyPI` off `benchmark`
- All PyPI-related changes (pyproject.toml, README, CI) committed here
- Pushed to remote

### README rewrite
Rewrote `README.md` from architecture-first to product-first:
- Hook: "The logic layer your AI is missing"
- Problem: fintech loan approval demo (6 rules, 4 people, 4.5ms, 2 compliance violations found)
- Benchmark: 40% hallucination rate, tinyllama 1B, engine as oracle
- Use cases across: system prompts, business rules, legal contracts, medical protocols, personal reasoning
- Images from `images/` directory included
- Technical details (operators, interfaces, credibility) pushed to bottom
- Removed: architecture diagram, roadmap

### Prompt: "images not displaying — repo is private"
`raw.githubusercontent.com` returns 404 for private repos. Immediate fix: point URLs at `engine-PyPI` branch. Long-term fix: host as GitHub release assets once repo goes public.

### Prompt: "can we set branch path in env variable for CI/CD?"
Created `publish.sh`:
- Reads `RELEASE_BRANCH` env var, defaults to current git branch
- Patches image URLs in README using `sed` before build
- Restores README after build (source file stays clean)
- Usage: `./publish.sh` or `RELEASE_BRANCH=master ./publish.sh`

### Prompt: "make a CI file for PyPI releases"
Created `.github/workflows/publish.yml`:
- Triggers on `v*` tag push
- Patches image URLs to use git tag (permanent, stable URLs)
- Builds with `python -m build`
- Publishes to PyPI via `TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}`
- Creates GitHub release with dist files attached
- `PYPI_API_TOKEN` added to repo secrets

### First automated release — v0.1.5
```
git tag v0.1.5 && git push origin v0.1.5
```
GitHub Actions triggered — build, publish, release created automatically.

---

## Session 4 — 2026-05-23

### Published versions 0.1.9 → 0.1.11
- 0.1.9 — Trusted Publishing (PyPI OIDC, no stored token), CI switched from twine + API key
- 0.1.10 — Renamed public repo from `boolean-LLM-eval` → `bool-LLM-ngn`, updated all URLs
- 0.1.11 — Bumped after 0.1.10 failed (400 Bad Request — version already existed after Trusted Publisher mismatch)
- Trusted Publisher mismatch: PyPI config still pointed at old repo name, updated manually

### Public repo renamed: `boolean-LLM-eval` → `bool-LLM-ngn`
- Shorter, cleaner, still signals what it is
- All URL references updated: README, pyproject.toml, publish.yml CI

### Benchmarked gemma3:4b — 36.4% hallucination rate
- Better than tinyllama (50%) and llama3.2:3b (50%), but still not reasoning
- 9/20 cases timed out — Gemma3:4b too large for 8 parallel workers on local VM
- Fix: `--workers 2` for local runs; long term: Groq free tier

### Added live web dashboard (`dashboard.py`, `--web` flag)
- Pure stdlib — zero new dependencies (Python http.server + SSE)
- Cases stream live to localhost:8080 as they complete
- Shows: config panel, progress bar, per-case table, final stats, benchmark chart
- Accessible on public IP for VM users (binds to 0.0.0.0)

### Created `docs/VARIABLE_CURVE.md`
- Full methodology and build plan for the variable curve study
- Variable counts: 3, 5, 7, 10, 15 — each doubles truth table rows
- Models: tinyllama, llama3.2:3b, gemma3:4b, llama3.1:8b, GPT-4o
- What to build: `--vars` flag, extended expression pools, numpy evaluator, curve.py, visualiser
- The chart (hallucination rate vs variable count per model) is the finding

### Distribution — first posts
- Posted on r/ollama — benchmark results, 3 upvotes / 2 comments / 4h (not dead, too early to judge)
- Posted on r/Boolean — math angle: "70 year old math that proves GPT is lying"
- Strategy: r/LocalLLaMA next, HN after variable curve study is complete

### Named the project: Quine
- After Willard Van Orman Quine and the Quine-McCluskey algorithm already in the synthesizer
- Sharp, CS-credible, directly tied to the codebase

### Infrastructure vision confirmed
- CUDA — GPU-parallel truth table evaluation (1 thread per row, 2^n parallel)
- Redis — expression cache + job queue
- Kubernetes — horizontal scaling of LLM workers for multi-model matrix runs
- Dataset of hallucination rates across models and variable counts over time is the asset
- Prometheus/Grafana deferred — relevant only when hosted API has real traffic

### Groq signup blocked
- Trace ID: `0034b9a8237d570e3ce12b00fc35230b` — server-side error, nothing actionable locally
- Fallback: `--workers 2` for local Gemma runs until Groq clears
- OpenAI/Anthropic keys also not yet available

### Key insight this session
The benchmark is evidence. The interception layer is the product.
The variable curve (hallucination rate vs complexity, per model) is the finding that makes this HN-worthy and research-publishable.

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
