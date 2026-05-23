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

## CBT / Therapy — Client Logical Coherence

These are statements a client might make in a therapy session.
Each contains a hidden contradiction between what they believe about
themselves and what they simultaneously claim. In CBT, surfacing
these contradictions is the work. The engine makes them explicit.

Note: this is not a replacement for a therapist. It is a tool that
could assist a therapist in identifying patterns in what a client says —
the same way a spellchecker assists a writer without replacing them.

---

### 15. The Worthiness Trap
> "I know I am a good person deep down.
> I do not deserve good things happening to me.
> Good things only happen to good people."

**Variables:**
- `G` = I am a good person
- `D` = I deserve good things
- `H` = good things happen to me

**Expressions:**
- Claim 1: `G` (I am good)
- Claim 2: `!D` (I don't deserve good things)
- Claim 3: `G → D` (good person implies deserving good things)

**Expected finding:** Claim 1 and Claim 3 together imply `D`.
Claim 2 asserts `!D`. The client simultaneously believes they are good
and that being good does not apply to them. Classic cognitive distortion —
the rule applies to everyone except themselves.

---

### 16. The Control Paradox
> "I cannot control anything that happens to me. Everything is out of my hands.
> I am responsible for everything that goes wrong in my life.
> If I had done things differently, none of this would have happened."

**Variables:**
- `C` = I have control over outcomes
- `R` = I am responsible for what goes wrong

**Expressions:**
- Claim 1+2: `!C` (no control at all)
- Claim 3+4: `R` (fully responsible — which requires control)

**Expected finding:** `R` implies `C` — you cannot be responsible for
outcomes you have zero control over. The client holds both simultaneously.
Zero control and full responsibility. This is one of the most common
contradictory belief patterns in depression and anxiety.

---

### 17. The Lovability Contradiction
> "I am unlovable. No one could truly love me if they knew the real me.
> I push people away before they can get close enough to find out.
> I desperately want connection and to be loved."

**Variables:**
- `L` = I am lovable
- `P` = I allow people to get close
- `W` = I want to be loved

**Expressions:**
- Claim 1+2: `!L` (unlovable, always)
- Claim 3: `!P` (push people away — prevents love from being tested)
- Claim 4: `W` (wants love — requires belief that `L` is possible)

**Expected finding:** `W` — genuinely wanting love — implies some belief
that love is possible, which requires `L`. But Claim 1 asserts `!L`.
The client acts to prevent the very thing they want, and believes they
want something they simultaneously believe is impossible for them.

---

### 18. The Perfectionism Loop
> "If I cannot do something perfectly, there is no point doing it at all.
> I never do anything perfectly.
> I must keep trying because giving up is not an option."

**Variables:**
- `P` = I do something perfectly
- `T` = there is a point in trying
- `K` = I keep trying

**Expressions:**
- Claim 1: `!P → !T` (no perfection = no point)
- Claim 2: `!P` (never perfect — always true)
- Claim 3: `K` (must keep trying = there is a point)

**Expected finding:** Claim 1 + Claim 2 together imply `!T` always.
Claim 3 asserts `K`, which requires `T`. The client is locked in a loop —
trying is pointless by their own rule, but they must keep trying.
The rule makes all effort meaningless, yet effort continues.

---

### 19. The Burden Belief
> "I am a burden to everyone around me.
> Everyone would be better off without me.
> The people in my life choose to stay because they care about me."

**Variables:**
- `B` = I am a burden to others
- `W` = others would be better off without me
- `S` = people choose to stay because they care

**Expressions:**
- Claim 1: `B` (burden, always)
- Claim 2: `W` (better off without me)
- Claim 3: `S` (people stay because they care — contradicts `W`)

**Expected finding:** If `W` is true — people would genuinely be better
off without the client — then `S` (staying because they care) requires
those people to act against their own wellbeing. Claim 3 implies `!W`.
The client's belief that people care contradicts their belief that they
are a burden. Both are held simultaneously.

**Important note:** Statement 19 is a clinical risk pattern. In a real
therapy context, surfacing this contradiction — "you believe people care
AND you believe they'd be better off without you — both cannot be true" —
is a meaningful therapeutic intervention.

---

### 20. The Anxiety Identity
> "I am an anxious person. That is just who I am, it cannot change.
> I want to feel calm and in control of my emotions.
> I have felt calm before, in certain situations."

**Variables:**
- `A` = I am always anxious (fixed identity)
- `C` = I can feel calm
- `W` = I want to feel calm

**Expressions:**
- Claim 1: `A` (always anxious, unchangeable — implies `!C` always)
- Claim 2: `W` (wants calm — implies belief `C` is possible)
- Claim 3: `C` (has felt calm — directly contradicts `A`)

**Expected finding:** Claim 3 is a direct counterexample to Claim 1.
The client has already felt calm — which falsifies "I am always anxious."
The belief is demonstrably false by their own testimony. The engine
surfaces this: `A` and `C` cannot both be true, and the client just
provided evidence for `C`.

---

### 21. The Self-Sabotage Split
> "I want to be successful more than anything.
> Every time I get close to success, something goes wrong.
> I do not believe I deserve to be successful.
> The things that go wrong are always external, never my fault."

**Variables:**
- `W` = I genuinely want success
- `D` = I believe I deserve success
- `F` = failures are caused by external factors (not me)
- `S` = I sabotage my own success

**Expressions:**
- Claim 1: `W` (wants success)
- Claim 3: `!D` (does not deserve it — in conflict with `W`)
- Claim 4: `F` (external causes only — `!S`)
- Pattern: `!D` often manifests as `S` — self-sabotage is the mechanism

**Expected finding:** `W` and `!D` are in tension — wanting something
you believe you don't deserve creates a drive to prevent it.
`F` (external causes) and `S` (self-sabotage) are mutually exclusive —
if the client is unconsciously sabotaging outcomes, the cause is internal.
The statement holds three contradictions simultaneously.

---

### How a therapist could use this

The engine does not diagnose or treat. It surfaces logical inconsistencies
in what a client says. A therapist could:

1. Transcribe or note the key belief statements a client makes in a session
2. Run them through `check_prompt_logic` or the NL layer
3. Get back which pairs conflict — mathematically, not subjectively
4. Use that as a starting point: "You said X and you said Y — can both be true?"

The engine makes implicit contradictions explicit. The therapeutic work
of understanding why those contradictions exist, and helping the client
resolve them, remains entirely human.

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
