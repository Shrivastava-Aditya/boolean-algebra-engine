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

---

## Go Extension (`boolean-algebra-engine-go`)

- [ ] Set up repo — `boolean-algebra-engine-go`
- [ ] Port `core/parser.py` → Go (shunting-yard)
- [ ] Port `core/evaluator.py` → Go (prefix stack, 2^n loop)
- [ ] Port `core/synthesizer.py` → Go (Quine-McCluskey — most complex port)
- [ ] Verify Go engine against Python engine — same truth tables for all test cases
- [ ] Goroutine benchmark runner — replace Python asyncio with goroutine pool
- [ ] Results channel pattern — collect LLM responses as they complete
- [ ] CUDA evaluator — 1 row = 1 GPU thread, 2^n parallel
- [ ] Expose Go engine via HTTP — Python interfaces call Go instead of Python core
- [ ] CLI in Go — `boolcalc` binary, replaces Python CLI for speed

---

## Architecture Refactor (after Go extension)

- [ ] Update DESIGN.md — reflect Go engine as compute layer, Python as interface layer
- [ ] Define the Python ↔ Go boundary — subprocess vs HTTP vs CGo
- [ ] Update pyproject.toml — mark `core/` as reference implementation, not production path
- [ ] Update benchmark.py — call Go engine for ground truth generation
- [ ] Update README on master — reflect two-repo architecture
- [ ] Update PRODUCT.md — reflect Go as the scale path

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
