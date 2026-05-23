# Demo Explained — Plain English

---

## The Scenario

A fintech startup built an AI agent that automatically approves or rejects loan
applications. Six different people wrote six rules over six months. Each rule made
sense when it was written. Nobody ever checked them all together.

The rules:

| Rule | Who wrote it | What it says |
|---|---|---|
| 1 | Engineering, Q1 | Approve if credit score is good AND income is verified |
| 2 | Risk team, Q1 | Approve if collateral exists — income doesn't matter |
| 3 | Compliance, Q2 | Reject if credit score is bad — no exceptions |
| 4 | Risk team, Q2 | Reject if income unverified AND no collateral |
| 5 | Engineering, Q3 | Approve if good credit AND verified income AND collateral |
| 6 | Compliance, Q3 | Block auto-approval if income is unverified |

Three variables that matter:
- **A** = credit score is good
- **B** = income is verified
- **C** = collateral exists

Every applicant is some combination of these three yes/no facts.
That's 8 possible combinations (2³). The engine checks all 8 for every rule.

---

## The 10 Things The Engine Does

---

### 1. Evaluate each rule individually

**What it is:**
Run each rule through the engine. See when it fires, when it doesn't.

**Simple version:**
You hand the engine Rule 1 — "approve if A and B". It checks all 8 combinations
and tells you: this rule fires in 2 out of 8 cases. These are the 2 cases.
No guessing. Just the table.

**Why it matters:**
Before you can check if rules conflict, you need to know when each one fires.
This is step zero. The baseline.

---

### 2. Find the minimal form — detect redundancy

**What it is:**
The synthesizer takes the truth table and finds the shortest possible expression
that produces the same output.

**Simple version:**
Rule 5 says "approve if good credit AND income AND collateral."
Rule 1 already says "approve if good credit AND income."
Rule 2 already says "approve if collateral."

Anyone satisfying Rule 5 already satisfies Rule 1 or Rule 2.
Rule 5 adds nothing. It is a dead rule — it can be deleted entirely.

The engine proves this by showing that the minimal form of
"Rule 1 OR Rule 2 OR Rule 5" is identical to "Rule 1 OR Rule 2."

**Why it matters:**
Dead rules in an AI system are noise. They make the logic harder to read,
harder to maintain, and create false confidence that the system is more
thorough than it is.

---

### 3. Equivalence checking — are two rules actually the same?

**What it is:**
Compare two rules. Check if they produce identical output for every
possible input combination.

**Simple version:**
Someone asks: "Rule 3 (reject if bad credit) and Rule 6 (block if income
unverified) — are these the same thing?"

The engine checks all 8 combinations for both.
Rule 3 fires when A=0 (bad credit), regardless of income.
Rule 6 fires when B=0 (unverified income), regardless of credit.

They fire in different cases. They are NOT the same rule.

If they had been the same — the engine would have caught the duplicate,
and the team could have removed one.

**Why it matters:**
Teams write the same rule twice without realising it, especially when rules
are written by different people. Duplicate rules waste space and create
confusion about which one is authoritative.

---

### 4. Contradiction detection — rules that fire simultaneously

**What it is:**
Check whether two rules can both be true at the same time. If they can,
and one says approve and the other says reject — that is a conflict.
The system has no defined behaviour for that case.

**Simple version:**
Rule 2 says: approve if collateral exists (C=1).
Rule 3 says: reject if bad credit (A=0).

What happens when an applicant has bad credit but owns collateral? (A=0, C=1)

Both rules fire at the same time.
Rule 2 says approve. Rule 3 says reject.
The AI agent picks whichever runs first.

Two applicants with identical profiles could get opposite decisions
depending on system state. That is a compliance violation.

The engine finds this by evaluating "Rule 2 AND Rule 3" — if that
combined expression is ever true, the rules conflict.

**Why it matters:**
This is the most dangerous finding. It is invisible to anyone reading
the rules individually. You only catch it by forcing both conditions to
hold simultaneously — which is exactly what the engine does.

---

### 5. Full audit — check all rules at once

**What it is:**
Pass all six rules to `check_prompt_logic`. Get back a complete report:
which rules are contradictions, which are tautologies, which pairs always
conflict, which are duplicates.

**Simple version:**
Instead of checking rules one by one, you hand all six to the engine
and it runs the full analysis automatically. One call. Complete report.

Summary of what it finds:
- 1 redundant rule (Rule 5)
- 2 conflicting pairs (Rule 2 vs Rule 3, Rule 2 vs Rule 6)
- 0 duplicate rules
- 0 rules that are always true or always false

**Why it matters:**
This is the product. Paste your rules. Get back what is wrong.
The entire analysis takes under 5ms.

---

### 6. REST API — calling the engine from anything

**What it is:**
The engine running as a web service. Any language, any system, any team
can call it over HTTP with a simple POST request.

**Simple version:**
Instead of installing the Python package, you just call a URL.
Your Java backend calls it. Your Node.js frontend calls it. Your
Zapier automation calls it. Language doesn't matter.

```
POST /check-rules
{ "rules": ["A.B", "C", "!A", "!B.!C", "A.B.C", "!B"] }

→ { contradictions: 0, conflicting_pairs: 2, redundant: 1 }
```

**Why it matters:**
This is how you sell it to teams that can't or won't install a Python package.
One hosted endpoint. Any team. Any stack. No setup.

---

### 7. NL layer — plain English in, verified result out

**What it is:**
You describe your rules in plain English. Claude translates them into
boolean expressions. The engine evaluates them. Claude explains the results
back in plain English.

**Simple version:**
Instead of writing `A.B + C`, you write:

> "Approve if credit score is good and income is verified,
>  or if collateral exists regardless of income"

Claude reads that, figures out A=credit, B=income, C=collateral,
writes `A.B+C`, hands it to the engine, gets the truth table back,
and explains the result in plain English.

Works with Claude, GPT-4, local Llama3 (free, offline), or any
OpenAI-compatible model. The engine underneath is always the same.

**Why it matters:**
This is what makes it accessible to non-developers. The compliance officer
who wrote Rule 3 does not know what `!A` means. But they can describe their
rule in a sentence and get a verified answer back.

---

### 8. numpy — evaluate all rows at once

**What it is:**
Instead of evaluating one row at a time in a Python loop, use numpy
to evaluate all rows simultaneously as array operations.

**Simple version:**
Current engine: loops through 8 rows one by one. Takes ~3ms.
numpy version: runs all 8 rows at the same time. Takes ~0.1ms.

For 64 rows (6 variables) or 1M rows (20 variables), the difference
compounds. This is the stepping stone to CUDA — same logic,
different compute backend.

**Why it matters:**
Performance baseline. Every future optimisation (CUDA, caching)
gets measured against this. You can't optimise what you can't measure.

---

### 9. pandas — truth table as a spreadsheet

**What it is:**
Convert the truth table into a pandas DataFrame so you can filter,
sort, group, and export it like any other data.

**Simple version:**
The truth table becomes a spreadsheet where each row is a scenario
and each column is a variable. Then you can ask:

- "Show me every scenario where the loan gets approved"
- "How many applicants get approved without income verification?"
- "Export this to CSV for the audit trail"

```python
approved_without_income = df[(df["B"] == 0) & (df["output"] == 1)]
# → 2 scenarios — collateral alone is enough
```

**Why it matters:**
Analysts and compliance teams live in spreadsheets and DataFrames.
This hands them the truth table in a format they already know how to use.
No boolean algebra required.

---

### 10. matplotlib — see the logic visually

**What it is:**
Turn the truth table into charts. Heatmap, bar chart, side-by-side
comparison of two rules.

**Simple version:**
Instead of reading a table of 0s and 1s, you see a green/red heatmap
where green means approved and red means rejected. Patterns that are
invisible in a table become obvious visually.

Side-by-side comparison of Rule 1+2 vs Rule 1+2+5 shows identical
bar charts — proof that Rule 5 adds nothing, visible in one glance.

**Why it matters:**
For demos, presentations, and convincing non-technical stakeholders.
A chart that shows "these two rules produce identical outcomes" is
more convincing than a line of Python output. This is marketing material
generated automatically from the engine.

---

## The Punchline

Six rules. Three variables. Written by four people over six months.

The engine found:
- 1 dead rule (Rule 5 — can be deleted)
- 2 conflicts where the AI agent would pick a winner arbitrarily (Rule 2 vs 3, Rule 2 vs 6)

Total time: **4.5ms.**

Nobody caught these by reading the rules. The engine caught them by checking
every combination. That is the difference between assuming logic is correct
and knowing it is.
