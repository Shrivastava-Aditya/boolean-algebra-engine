# Statements to Verify

A collection of real-world natural language statements that contain
hidden contradictions, redundancies, or logical inconsistencies.
Each one can be plugged into the NL layer and verified by the engine.

Format per statement:
- The statement in plain English
- Variables extracted
- Expressions derived
- What the engine is expected to find

---

## Personal Reasoning

---

### 1. The Linux/Mac Statement
> "I have been using Linux since a little longer than 6 years now, but I have been
> using Mac since close to 3 years. If I did not use Linux, I would have never switched
> to Mac. But me using Mac has no relation with me using Linux in any way."

**Variables:**
- `L` = I use Linux
- `M` = I use Mac

**Expressions:**
- Claim 3: `!L → !M` (no Linux means no Mac) → equivalent to `L+!M`
- Claim 4: M independent of L → `M` (always, regardless of L)

**Expected finding:** Conflicting pair. `L=0, M=1` satisfies claim 4 but
violates claim 3. Both cannot be true simultaneously.

---

### 2. The Independence Paradox
> "I make all my decisions independently. Nobody influences my choices.
> My mentor has been the biggest influence on my career decisions."

**Variables:**
- `I` = decisions made independently
- `M` = mentor influences decisions

**Expressions:**
- Claim 1+2: `I` (always independent, `M` irrelevant)
- Claim 3: `M` (mentor always influences)
- Combined: `I.M` — independent AND influenced simultaneously

**Expected finding:** Contradiction. Cannot be fully independent and
fully influenced at the same time.

---

### 3. The Effort Paradox
> "Hard work always leads to success. I worked extremely hard and did not succeed.
> Success is purely based on hard work."

**Variables:**
- `H` = hard work
- `S` = success

**Expressions:**
- Claim 1: `H → S` (hard work implies success) → `!H+S`
- Claim 2: `H=1, S=0` (worked hard, no success) — direct counterexample
- Claim 3: same as Claim 1

**Expected finding:** Claim 2 is a direct counterexample that falsifies Claims 1 and 3.
The statement is self-contradictory — the speaker refutes their own rule.

---

## System Prompts / AI Rules

---

### 4. The Helpful-But-Restricted Agent
> "Always be helpful to the user and answer every question fully.
> Never discuss competitor products under any circumstances.
> If a user asks to compare us to a competitor, give a full and helpful answer."

**Variables:**
- `H` = give full helpful answer
- `C` = question involves competitor

**Expressions:**
- Rule 1: `H` (always)
- Rule 2: `C → !H` (competitor question means no full answer)
- Rule 3: `C → H` (competitor comparison means full answer)

**Expected finding:** Rules 2 and 3 directly contradict. Rule 2 says no answer
when competitor is mentioned. Rule 3 says give a full answer. Both cannot apply.

---

### 5. The Privacy-But-Personalised Agent
> "We never store or remember any user data. Our system is fully privacy-preserving.
> Our AI remembers your preferences and personalises every response."

**Variables:**
- `S` = user data is stored
- `P` = responses are personalised

**Expressions:**
- Claim 1+2: `!S` (no data stored, ever)
- Claim 3: `P` (personalised → requires stored preferences → `S`)

**Expected finding:** Claim 3 requires `S=1` to be possible.
Claim 1 asserts `S=0` always. Direct contradiction.

---

### 6. The Safe-But-Capable Agent
> "This AI will never refuse a user request. User satisfaction is the top priority.
> This AI will refuse any request that could cause harm.
> Harm prevention is the top priority."

**Variables:**
- `R` = AI refuses the request
- `H` = request could cause harm

**Expressions:**
- Rule 1: `!R` (never refuses)
- Rule 3: `H → R` (harmful request → refuse)
- Rule 4: harm prevention is top priority (reinforces Rule 3)

**Expected finding:** Rules 1 and 3 conflict when `H=1`.
A harmful request simultaneously triggers "never refuse" and "always refuse."

---

## Business and Policy

---

### 7. The Equal-But-Premium Policy
> "All customers are treated equally regardless of their subscription tier.
> Premium customers receive priority support and faster response times.
> We do not discriminate between customer tiers."

**Variables:**
- `E` = all customers treated equally
- `P` = premium customers get priority

**Expressions:**
- Claim 1+3: `E` (equal treatment, always)
- Claim 2: `P` (premium gets priority, which breaks equality)

**Expected finding:** `E` and `P` cannot both be true. Priority by definition
means unequal treatment.

---

### 8. The Flat-But-Hierarchical Organisation
> "We are a flat organisation with no hierarchy. Every employee has equal say.
> All major decisions must be approved by the executive team.
> The CEO has final say on all strategic decisions."

**Variables:**
- `F` = flat hierarchy, equal say
- `A` = executives approve decisions
- `C` = CEO has final say

**Expressions:**
- Claim 1+2: `F` (flat, equal)
- Claim 3: `A` (exec approval required — breaks `F`)
- Claim 4: `C` (CEO final say — breaks `F`)

**Expected finding:** `F` conflicts with both `A` and `C`. Three separate
conflicting pairs.

---

### 9. The Transparent-But-Confidential Policy
> "We are fully transparent with our users about how their data is used.
> Certain data processing activities are confidential for business reasons.
> Users have a right to know everything we do with their data."

**Variables:**
- `T` = fully transparent, users know everything
- `X` = some activities are confidential (not disclosed)

**Expressions:**
- Claim 1+3: `T` (full transparency, always)
- Claim 2: `X` (confidential activities exist → `!T` for those)

**Expected finding:** `T` and `X` cannot both be true. Confidentiality
by definition means some information is withheld — which breaks full transparency.

---

## Legal and Compliance

---

### 10. The Termination Clause Contradiction
> "This agreement renews automatically each year unless cancelled.
> Either party may terminate with 30 days written notice.
> Termination requires written consent from both parties."

**Variables:**
- `U` = unilateral termination possible (one party can end it)
- `M` = mutual consent required for termination

**Expressions:**
- Clause 2: `U` (either party can terminate = unilateral)
- Clause 3: `M` (mutual consent required = not unilateral)

**Expected finding:** `U` and `M` are direct contradictions. Either one party
can end it, or both must agree — not both.

---

### 11. The No-Exceptions Exception
> "This policy applies to all employees without exception.
> Senior executives are exempt from this policy during company events.
> No exemptions will be granted under any circumstances."

**Variables:**
- `A` = policy applies to everyone
- `E` = exemptions exist

**Expressions:**
- Clause 1+3: `A.!E` (everyone, no exceptions)
- Clause 2: `E` (exemptions exist for executives)

**Expected finding:** Clause 2 directly contradicts Clauses 1 and 3.

---

## Medical and Clinical

---

### 12. The Treatment Protocol Conflict
> "Administer medication A when the patient has symptom X.
> Do not administer medication A if the patient has condition Y.
> Patients presenting with symptom X almost always have condition Y."

**Variables:**
- `X` = patient has symptom X
- `Y` = patient has condition Y
- `A` = administer medication A

**Expressions:**
- Rule 1: `X → A`
- Rule 2: `Y → !A`
- Rule 3: `X → Y` (symptom X implies condition Y in most cases)

**Expected finding:** Rules 1 and 2 conflict whenever `X=1, Y=1`.
Rule 3 makes this the common case. The protocol contradicts itself
for the majority of patients it is designed to treat.

---

## Philosophical / Self-Referential

---

### 13. The Free Will Paradox
> "Every human action is determined by prior causes.
> Humans are morally responsible for their actions.
> Moral responsibility requires that actions could have been otherwise."

**Variables:**
- `D` = actions are fully determined (no alternative was possible)
- `R` = humans are morally responsible
- `A` = actions could have been otherwise

**Expressions:**
- Claim 1: `D` → implies `!A` (determined = no alternatives)
- Claim 2: `R`
- Claim 3: `R → A` (responsibility requires alternatives)

**Expected finding:** Claim 1 implies `!A`. Claim 3 requires `A` for `R`.
Combined: `D` makes `R` impossible. All three claims cannot be simultaneously true.

---

### 14. The Rules-About-Rules
> "There are no absolute rules. Everything is relative and context-dependent.
> This principle applies universally without exception."

**Variables:**
- `Ab` = absolute rules exist
- `U` = this principle is universal (absolute)

**Expressions:**
- Claim 1: `!Ab` (no absolute rules)
- Claim 2: `U` (this principle is universal = an absolute rule)

**Expected finding:** Classic self-refuting statement. Claiming "no absolute rules"
absolutely is itself an absolute rule. `!Ab` and `U` cannot both be true.

---

## How to run these through the engine

```python
# Option 1 — NL layer (requires API key)
from nl.nl import check_rules, AnthropicProvider

result = check_rules([
    "If I did not use Linux I would never have switched to Mac",
    "Me using Mac has no relation with me using Linux",
], provider=AnthropicProvider())

print(result["summary"])

# Option 2 — direct expressions (no API key needed)
from mcp_server.server import check_prompt_logic

result = check_prompt_logic(["L+!M", "M"])
print(result["summary"])

# Option 3 — CLI
# boolcalc check-rules \
#   "If I did not use Linux I would never have switched to Mac" \
#   "Me using Mac has no relation with me using Linux" \
#   --provider anthropic
```
