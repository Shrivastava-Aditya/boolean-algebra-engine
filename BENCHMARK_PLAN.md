# Benchmark Build Plan

Current state: sequential, synchronous, single model, 10 cases, CPU Ollama.
Target state: batched, async, multi-model, 1000+ cases, API + local.

---

## The problem

Each LLM call takes 10–30 seconds on CPU Ollama.
100 cases × 30s = 50 minutes. One model.
10 models × 100 cases = 8+ hours. Unusable.

The engine generates ground truth in under 1ms per case.
The bottleneck is entirely LLM inference. Not the engine.

---

## What needs to be built

### Layer 1 — Batching

Instead of one prompt per case, pack multiple cases into one prompt.

```
Current:
  prompt 1 → case 1 → wait → answer
  prompt 2 → case 2 → wait → answer
  ...

Batched:
  prompt 1 → case 1, case 2, ..., case 10 → wait → 10 answers
```

One API call returns N answers. Parse the response into a list.
10x throughput with zero infrastructure change.

Design:
- `batch_size` parameter — default 10, tunable per model
- Structured output prompt: "Answer each pair with yes or no, one per line, in order."
- Parser: split response by line, match to cases by index
- Fallback: if model returns malformed output, re-send as individual calls

Risk: small models (tinyllama) struggle with structured multi-output.
Mitigation: use batching only for models above a quality threshold.

---

### Layer 2 — Async parallel calls

Cases are completely independent. No case depends on any other.
Perfect parallelisation target.

```
Current:
  case 1 → wait 30s → case 2 → wait 30s → ...

Async:
  case 1 ─┐
  case 2 ─┤→ all fire simultaneously → collect results
  case 3 ─┘
```

Implementation:
- `asyncio` + `aiohttp` for API models (Anthropic, OpenAI, Groq)
- `concurrent.futures.ThreadPoolExecutor` for Ollama (not async-native)
- `max_concurrent` parameter — respect rate limits per provider
- Collect all results, match back to cases by index

Expected speedup: 10–50x depending on provider rate limits.

---

### Layer 3 — Multi-model runner

Run the same case set against multiple models in one command.
Results stored per model, compared in a single report.

```
benchmark.py --models tinyllama,llama3,mistral,gpt-4o --cases 100 --vars 3,5,10
```

Architecture:
- `models.json` — registry of models, providers, rate limits, batch sizes
- One case set generated once (engine, seeded), shared across all models
- Each model runs async, results written to `results/{model}/{timestamp}.json`
- Report aggregates all results into comparison table

---

### Layer 4 — Variable count matrix

Run each model across increasing variable counts.
This is where the study becomes publishable.

```
         | 3 vars | 5 vars | 10 vars | 15 vars |
---------|--------|--------|---------|---------|
tinyllama|  40%   |   ?    |    ?    |    ?    |
llama3   |   ?    |   ?    |    ?    |    ?    |
mistral  |   ?    |   ?    |    ?    |    ?    |
gpt-4o   |   ?    |   ?    |    ?    |    ?    |
```

Design:
- `--vars 3,5,10,15` generates separate case sets per variable count
- Engine handles ground truth at all counts (numpy kicks in at n > 15)
- Same model, same cases, different complexity — shows degradation curve

---

### Layer 5 — Results storage and reporting

Right now results print to stdout and are gone.
At scale you need persistence.

```
results/
  tinyllama/
    2026-05-23_10cases_3vars.json
    2026-05-23_100cases_5vars.json
  llama3/
    ...
  report.md     ← auto-generated comparison table
```

Each result file:
```json
{
  "model": "tinyllama",
  "timestamp": "2026-05-23T05:00:00Z",
  "n_vars": 3,
  "n_cases": 10,
  "hallucination_rate": 0.40,
  "conflict_miss_rate": 0.60,
  "compat_miss_rate": 0.20,
  "cases": [...]
}
```

Report auto-generates the comparison matrix as markdown.
Append-only — each run adds a row, history is preserved.

---

### Layer 6 — Provider abstraction

Mirror the NL layer's provider abstraction.
One interface, swap the backend.

```python
class BenchmarkProvider:
    async def ask(self, prompt: str) -> str: ...
    async def ask_batch(self, prompts: list[str]) -> list[str]: ...

class OllamaProvider(BenchmarkProvider): ...
class AnthropicProvider(BenchmarkProvider): ...
class OpenAIProvider(BenchmarkProvider): ...
class GroqProvider(BenchmarkProvider): ...   # free tier, fast
```

Groq is important — free tier, OpenAI-compatible, runs Llama3/Mistral at
~10x Ollama CPU speed. Bridges the gap between local and paid API.

---

## Build order

| Step | What | Unlocks |
|---|---|---|
| 1 | Batching | 10x throughput, no infrastructure |
| 2 | Async parallel | 10–50x throughput, same cases |
| 3 | Results storage | Persistence, history, reproducibility |
| 4 | Provider abstraction | Groq free tier, any API model |
| 5 | Multi-model runner | Full comparison matrix |
| 6 | Variable count matrix | The publishable study |

---

## Target benchmark run time

| Configuration | Current | After batching + async |
|---|---|---|
| 1 model, 10 cases, 3 vars | ~5 min | ~30s |
| 1 model, 100 cases, 3 vars | ~50 min | ~3 min |
| 4 models, 100 cases, 3 vars | ~3 hrs | ~10 min |
| 4 models, 100 cases, 3+5+10 vars | ~9 hrs | ~30 min |

The 30-minute full matrix run is what makes continuous benchmarking viable.
Run it weekly. Track model improvement (or regression) over time.

---

## What this produces

A reproducible, continuously-updated hallucination benchmark across:
- N models (any provider)
- M variable counts (complexity axis)
- K cases per configuration (statistical significance)

Ground truth generated by exhaustive enumeration — exact, free, scalable.
No human labelers. No static dataset. No benchmark saturation.

The methodology is the contribution. The numbers are the finding.
