# Variable Curve Study

**The core finding:** hallucination rate is not fixed — it degrades as logical complexity increases.
Every LLM has a breaking point. This study finds it, per model, with proof.

---

## The Question

At what variable count does each model stop reasoning and start guessing?

A model handling 3-variable expressions (8 truth table rows) may score 70%.
The same model on 10-variable expressions (1024 rows) likely scores near 0%.
The curve between those points is the finding.

---

## Methodology

**Ground truth:** engine evaluates every expression by exhaustive enumeration — provably correct.
Cross-verified with z3 (CDCL SAT solver). Zero ambiguity in labeling.

**Cases:** pairs of boolean expressions. Question: can both rules be true simultaneously?
- Conflict case — conjunction is UNSAT (correct answer: no)
- Compatible case — conjunction is SAT (correct answer: yes)

**Variable counts to test:** 3, 5, 7, 10, 15
- n=3  →  8 rows
- n=5  →  32 rows
- n=7  →  128 rows
- n=10 →  1,024 rows
- n=15 →  32,768 rows (numpy vectorised evaluator needed here)

**Cases per configuration:** 100 minimum for statistical significance.

**Models to run:**
- tinyllama (1.1B)
- llama3.2:3b (3B)
- gemma3:4b (4B)
- llama3.1:8b or mistral:7b (7-8B)
- GPT-4o (frontier — the control)

---

## What Needs to Be Built

### 1. Extended expression pool
`benchmark.py` currently generates expressions with up to 4 variables (A, B, C, D).
Need pools for 5, 7, 10, 15 variables — more complex nesting, longer chains.

```python
# add to benchmark.py
EXPRESSIONS_5VAR = [...]   # 5-variable expressions
EXPRESSIONS_7VAR = [...]   # 7-variable expressions
EXPRESSIONS_10VAR = [...]  # 10-variable expressions
```

### 2. `--vars` flag
Scope case generation to a specific variable count.

```bash
python3 benchmark.py --provider groq --model llama3.2:3b --cases 100 --vars 5
python3 benchmark.py --provider groq --model llama3.2:3b --cases 100 --vars 7
```

### 3. Numpy vectorised evaluator (for n > 15)
Current evaluator is a Python loop over 2^n rows — fine up to n=15.
Above that, numpy evaluates all rows as a matrix operation.

```python
# core/evaluator.py — threshold switch
if n_vars <= 15:
    return _eval_python(expr)   # current path
else:
    return _eval_numpy(expr)    # vectorised
```

### 4. Multi-run script
One command runs a model across all variable counts and saves results.

```bash
python3 curve.py --provider groq --model llama3.2:3b --cases 100
# runs at n=3,5,7,10,15 — saves results/curve/llama3.2:3b/{n}.json
```

### 5. Curve visualiser
Reads results from `results/curve/` and plots the degradation chart.

```
hallucination %
     100 |                              ....tinyllama
         |                     .........
      60 |              .......              ....llama3.2
         |        ......            .......
      20 |  ......            ......
         |
       0 +--+------+------+------+------+--→ variables (n)
          3     5     7    10    15
```

One line per model. x = variable count. y = hallucination rate.
The inflection point — where the line goes vertical — is the finding per model.

---

## Execution Order

1. **Add `--vars` flag** to benchmark.py — scope expression generation to n variables
2. **Extend expression pools** — add 5, 7, 10-variable expression sets
3. **Get Groq working** — 100 cases × 5 variable counts × 4 models = 2000 LLM calls, needs to be fast
4. **Run the matrix** — one model at a time, starting with tinyllama as baseline
5. **Numpy evaluator** — needed before running at n=15
6. **Build curve.py** — multi-run script that iterates variable counts automatically
7. **Visualise** — plot the degradation curve, one line per model

---

## The Output

A single chart. One line per model. Hallucination rate on y-axis, variable count on x-axis.

Every model's line starts somewhere below 100% and trends upward as complexity increases.
The x-position where each line hits ~100% is the model's logical complexity ceiling.

That chart is the paper. That chart is the Reddit post. That chart is what makes this real.

---

## Blockers

- **Groq API** — needed for 100-case runs without local timeout issues
- **Expression pools** — need hand-crafted or generated sets for n=5,7,10 that are balanced and non-trivial
- **Numpy** — needed for n=15, straightforward port of current evaluator
