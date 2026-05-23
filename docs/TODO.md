# TODO

---

## Immediate

- [ ] Run benchmark at 100 cases (currently 10 — not statistically significant)
- [ ] Run benchmark against llama3.2:3b (next model up from tinyllama)
- [ ] Add Groq free tier provider to benchmark (faster than CPU Ollama)
- [ ] Get API credits and run against GPT-4o — that number is the one that matters
- [ ] Merge `product-readme` into master once reviewed
- [ ] Merge `benchmark` into master once reviewed

---

## Benchmark (Python)

- [ ] Batching — pack N cases into one prompt, parse structured response
- [ ] Async parallel calls — fire all cases simultaneously, collect via asyncio
- [ ] Results persistence — save to `results/{model}/{timestamp}.json`
- [ ] Multi-model runner — one command, all models, one report
- [ ] Variable count matrix — run each model at 3, 5, 10, 15 variables
- [ ] Auto-generate comparison table as markdown after each run
- [ ] Provider abstraction — `BenchmarkProvider` ABC mirroring NL layer

---

## Interception Layer (the actual product — not built yet)

- [ ] Design the interception interface — where it hooks into an agent pipeline
- [ ] Build inline contradiction checker — receives LLM output, returns clean/blocked
- [ ] Re-query loop — if contradiction found, re-send to model with error context
- [ ] MCP tool: `verify_output` — agent calls this before acting on its own reasoning
- [ ] Latency measurement — prove <10ms overhead on the hot path

---

## Core Engine (Python)

- [ ] numpy vectorised evaluator — replace Python loop for n > 15
- [ ] Redis expression cache — skip recomputation on repeated expressions
- [ ] Benchmark engine speed at n=5,10,15,20 with and without numpy

### DPLL / SAT backend (removes variable count ceiling)

Current exhaustive truth table enumeration caps out at ~20 variables (2^20 = 1M rows).
DPLL finds satisfying assignments or proves UNSAT without visiting most of the search space —
same correctness guarantee, no artificial ceiling. This makes the engine viable for real
enterprise rule sets (50–100+ variables) and removes the one area where SymPy is objectively
better. Combine with the MCP server and the pitch becomes: Claude can verify any rule set
it reasons about, regardless of complexity.

- [ ] Implement DPLL satisfiability check as alternative backend
- [ ] Threshold switch — use truth table for n ≤ 16, DPLL for n > 16
- [ ] Keep exhaustive path as default for small n (simpler, easier to audit)
- [ ] Cross-verify DPLL vs truth table at n ≤ 16 — must agree on every case
- [ ] Update benchmark verify_with_z3 to also run DPLL cross-check
- [ ] Update README — remove "up to 26 variables" hard claim, replace with practical note
- [ ] Consider z3 as DPLL backend rather than reimplementing from scratch

---

## Go Extension (`boolean-algebra-engine-go`)

**Phase 1 — Core engine port**
- [ ] Set up repo — `boolean-algebra-engine-go`
- [ ] Port `core/parser.py` → Go (shunting-yard, same operator precedence)
- [ ] Port `core/evaluator.py` → Go (prefix stack, 2^n loop, no GIL)
- [ ] Port `core/synthesizer.py` → Go (Quine-McCluskey — most complex, set operations)
- [ ] Cross-verify Go vs Python — run same expressions through both, assert identical truth tables
- [ ] Port 90 Python tests → Go test suite — Go engine is correct if it passes all of them

**Phase 2 — Benchmark runner**
- [ ] Goroutine pool — one goroutine per case, results channel
- [ ] LLM provider interface — `Provider` interface, `Ask(prompt) string`
- [ ] Implement OllamaProvider in Go — HTTP to localhost:11434
- [ ] Implement OpenAICompatProvider in Go — covers Groq, Together, any compat endpoint
- [ ] Replace Python benchmark runner with Go binary — call as subprocess or rewrite
- [ ] Measure speedup vs Python asyncio — target 4-min full matrix vs 30-min

**Phase 3 — CUDA acceleration**
- [ ] CUDA evaluator — 1 row = 1 GPU thread, 2^n rows parallel
- [ ] Benchmark CUDA vs Go CPU loop at n=10, 15, 20, 30
- [ ] numpy bridge — Python can call Go CUDA evaluator via subprocess or HTTP
- [ ] Profile memory at n=20 (1M rows) and n=25 (32M rows)

**Phase 4 — Integration**
- [ ] Expose Go engine via HTTP — `POST /evaluate`, `POST /synthesize`
- [ ] Python core/ calls Go HTTP instead of running Python evaluator
- [ ] CLI in Go — `boolcalc` binary, faster startup than Python typer
- [ ] Update DESIGN.md — Go as compute layer, Python as interface layer
- [ ] Update pyproject.toml — mark Python core/ as reference implementation

---

## Architecture Refactor (after Go extension)

- [ ] Update DESIGN.md — reflect Go engine as compute layer, Python as interface layer
- [ ] Define the Python ↔ Go boundary — subprocess vs HTTP vs CGo
- [ ] Update pyproject.toml — mark `core/` as reference implementation, not production path
- [ ] Update benchmark.py — call Go engine for ground truth generation
- [ ] Update README on master — reflect two-repo architecture
- [ ] Update PRODUCT.md — reflect Go as the scale path

---

## Variable Increment Test

The core study — how hallucination rate changes as logical complexity increases.
Each step adds variables, doubling the truth table rows the model must reason over.

- [ ] Extend EXPRESSIONS pool — add 4-variable and 5-variable expressions to benchmark.py
- [ ] Add `--vars` flag to benchmark.py — generates case pool scoped to n variables
- [ ] Run tinyllama at n=3 (8 rows) — baseline, already done: 40%
- [ ] Run tinyllama at n=5 (32 rows) — expect rate to climb
- [ ] Run tinyllama at n=7 (128 rows) — expect significant degradation
- [ ] Run tinyllama at n=10 (1024 rows) — upper bound for small model
- [ ] Repeat matrix for llama3.2:3b once Groq/API credits available
- [ ] Plot degradation curve — hallucination rate vs variable count, per model
- [ ] Add `visualise_results.py` chart — line chart, one line per model, x=variables, y=hallucination%
- [ ] Document inflection point — at what n does each model fall apart completely
- [ ] Cross-verify: engine generates ground truth at all n, numpy kicks in at n>15

**Expected shape of the curve:**
```
hallucination %
     100 |                              ....llama_tiny
         |                     .........
      60 |              .......              ....llama3
         |        ......            .......
      20 |  ......            ......
         |
       0 +--+------+------+------+------+--→ variables (n)
          3     5     7    10    15    20
```
Bigger models degrade more slowly but the curve never reaches zero.
That is the finding. That is the paper.

---

## Study / Publication

- [ ] Run full model matrix (tinyllama, llama3, mistral, GPT-4o) at 3+5+10 variables
- [ ] Write up methodology — engine as oracle, ground truth generation, reproducibility
- [ ] Statistical significance — 100+ cases per configuration minimum
- [ ] Write the paper / technical post — problem, methodology, results, implications
- [ ] Show HN post — after the number is real and the methodology is documented

---

## Infrastructure (hosted product)

- [ ] Hosted API — deploy FastAPI to a cloud instance
- [ ] Dashboard — show contradiction rate over time per pipeline
- [ ] Usage tracking — calls, models, contradiction rates per customer
- [ ] Auth — API key management
- [ ] Pricing page — free / startup / scale / enterprise tiers

---

## Docs

- [ ] Add `CONTRIBUTING.md` — how to add a new benchmark provider
- [ ] Add operator reference to README
- [ ] Document the Go ↔ Python boundary once decided
- [ ] Keep `log.md` updated each session
