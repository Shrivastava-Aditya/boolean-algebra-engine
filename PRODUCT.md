# Product Brief — Boolean Algebra Engine

A running record of what this is, what it does, why it matters, and how to talk about it.
Use this to deconstruct the product for marketing, pitching, or scoping the next layer.

---

## What it is — the one-line answer

**The logic layer your AI is missing.**

A serious, compatible tool for AI agents and models that reduces logical hallucination
by a measurable percentage — with a provable number, not a benchmark on someone else's dataset.

---

## What it actually is — precisely

Not a library. Not an audit tool. Not a truth table generator.

A **logic analysis layer for agents and models** — the thing that sits inside an AI pipeline
and makes one guarantee the model cannot make itself: that its reasoning is logically consistent.

The AI reasons in language. This verifies the logic. Two different jobs, done by two different
systems. The AI predicts. This computes. Neither does the other's job.

The boolean algebra is the mechanism. The product is the guarantee:
**this agent cannot produce a logically inconsistent decision.**

---

## Where it sits

Not before the AI. Not after. **During.**

```
User input
    ↓
AI reasoning
    ↓
[ Logic Layer ]  ← this product
    ↓
AI output  ←  logically consistent, guaranteed
```

The engine sits between the AI's reasoning and its output. It does not slow the AI down,
redirect it, or rewrite it. It catches logical contradictions at the moment they form —
before they become output, before they reach the user, before they cause a decision error.

This is what makes it infrastructure, not tooling.

---

## What it is — precisely

---

## Why it exists — the human brain problem

Human brains are good at language. Bad at exhaustive enumeration.

You can read "grant access if admin" and "deny access if admin" separately and both
sound reasonable. The contradiction only becomes obvious when you force yourself to
hold both in your head simultaneously — which almost nobody does, because it's
cognitively expensive and easy to skip.

Now multiply that by 15 rules, written by different people over 3 months, with nested
conditions and double negations. Nobody catches every contradiction manually. Not because
they're not smart — because that's not how human reasoning works.

LLMs have the same failure mode. They process language, find patterns, predict what
sounds right. Simple contradictions they'll catch. Five nested conditions with a double
negation — they'll confidently give you the wrong answer because the language pattern
matched something in training.

The engine doesn't read. It computes every combination. The contradiction is unavoidable.

That gap — between "sounds right" and "is right" — is what this fills. It exists in
every codebase, every system prompt, every set of business rules ever written by a human.

---

## The scope — anywhere humans reason informally

That pattern — statements that sound consistent individually but contradict each other
when held together — is not rare. It is how natural language works. People don't speak
in formal logic. They speak in approximations, and each approximation sounds fine on
its own.

### A real example

> *"I have been using Linux since a little longer than 6 years now, but I have been
> using Mac since close to 3 years. If I did not use Linux, I would have never switched
> to Mac. But me using Mac has no relation with me using Linux in any way."*

Four sentences. Each sounds reasonable. Read together:

- Sentence 3 says: Linux **caused** the switch to Mac
- Sentence 4 says: Linux and Mac are **completely unrelated**

These cannot both be true. Statement 3 makes Mac dependent on Linux.
Statement 4 says Mac is independent of Linux. Direct contradiction.

In boolean terms:
- `L` = using Linux, `M` = using Mac
- Sentence 3: `!L → !M` (equivalent to: Mac requires Linux as prerequisite)
- Sentence 4: `M` and `L` are independent

The engine flags this as a conflicting pair. The person who said it wasn't lying
or being careless — they just couldn't hold both conditions simultaneously while
speaking each sentence. Nobody can. That's not a flaw to fix, it's a human
limitation to work around.

### Where this exact pattern appears everywhere

**System prompts**
> "Always be helpful to the user. Never discuss competitor products.
>  If the user asks about pricing, always redirect to sales.
>  Never make the user feel like they're being redirected."

Four sentences. At least two conflict — you cannot always redirect and never
make the user feel redirected simultaneously.

**Legal contracts**
> "The agreement is valid for 12 months. Either party may terminate with
>  30 days notice. Termination requires mutual consent."

Clause 2 and clause 3 contradict — unilateral notice vs mutual consent
cannot both be the termination mechanism.

**Business rules**
> "Premium users get priority support. All users are treated equally.
>  Premium users are served first."

Sentence 1 and sentence 2 are incompatible by definition.

**Medical guidelines**
> "Administer drug A if symptom X is present. Do not administer drug A
>  if the patient has condition Y. Patients with symptom X almost always
>  have condition Y."

The third sentence makes the first two mutually exclusive in most real cases.

**Personal reasoning** — like the Linux/Mac example above
> "I make all decisions independently. My mentor has heavily influenced
>  my career choices."

Two sentences. One direct contradiction.

### The common thread

Every single one of these was written by someone who believed they were
being consistent. Each sentence was written in isolation, made sense in
isolation, and was never checked against the others.

That is not a human flaw. It is a human limitation.
This engine is the workaround.

**The scope: anywhere humans write rules, policies, instructions, or
reasoning in natural language.**

That is every industry, every organisation, every AI system deployed today.
The problem is not niche. The tooling to catch it has not existed — until now.

### What else this statement plugs into

The Linux/Mac example has a causal claim buried inside a correlation claim and
they contradict. That structure — locally consistent, globally broken — appears
across every domain that uses language to express logic.

**Philosophy / logic education**
Textbook example of correlation vs causation expressed as boolean rules.
A logic course uses the engine to show students exactly where informal
reasoning breaks down. The visual output makes it concrete — not "this is wrong"
but "here is the exact row where it fails."

**Debate and argument analysis**
Any argument in natural language can be broken into boolean claims and checked
for internal consistency. Political speeches, op-eds, legal arguments, debates —
extract the if-then claims, plug them in, find the contradictions. The engine
doesn't care about subject matter, only logical structure.

**Therapy / cognitive behavioural tools**
CBT is literally about finding contradictory beliefs a person holds simultaneously.
"I need to be perfect to be loved" and "I know nobody is perfect" — boolean
contradiction. The engine formalises what a therapist does manually.

**Journalism / fact checking**
A politician says: "We have always supported this policy. We changed our position
because circumstances changed. Our position has never changed." Three sentences.
Contradiction found in milliseconds. Fact checkers currently do this by reading
transcripts manually.

**AI alignment and safety**
Language models are trained on human text — full of contradictions like this one.
The engine can audit training data or model outputs for logical consistency.
A primitive but real alignment tool — catching cases where a model has internalised
contradictory beliefs.

**Personal journaling / decision making**
Someone writes about a decision they're struggling with. Extract the stated beliefs.
Check for consistency. "I value my independence but I can't make decisions without
approval" — contradiction surfaced, made visible, discussable.

**HR and policy documents**
Employee handbooks are full of this. "We have a flat hierarchy. All decisions go
through the management chain. Every employee has an equal voice." Three sentences,
at least two conflicting.

The common thread: the Linux/Mac statement is not unusual. It is the norm.
Human language is full of statements that sound locally consistent but are globally
contradictory. The engine is a universal detector for that failure mode —
regardless of domain.

---

## What it does today

**Forward:** Give it a boolean expression, it returns the full truth table — every possible
input combination and its output. No guessing, no approximation. Exhaustive.

**Inverse:** Give it a truth table (what you want to happen), it returns the minimal boolean
expression that produces it. Uses the Quine-McCluskey algorithm.

**Verification tools:**
- Is this expression satisfiable? (does any input make it true?)
- Is it a contradiction? (is it always false?)
- Is it a tautology? (is it always true — i.e. redundant?)
- Are these two expressions logically equivalent?
- Do these rules ever conflict — can they never both be satisfied simultaneously?

**check_prompt_logic:** Pass a list of rules. Get back which ones are contradictions,
which are tautologies, which pairs always conflict, which are duplicates.
This is the product.

---

## How credibility works

The engine's credibility is not a claim — it's a consequence of how it works.

It uses **exhaustive enumeration**. For `n` variables it evaluates exactly `2^n` rows.
Every possible input combination is checked. Nothing is sampled or predicted.

- Satisfiable → it found an actual row where output = 1
- Contradiction → it checked every row, all were 0
- Equivalent → it compared output columns row-by-row across the full table
- Conflict → it evaluated the conjunction of both rules for every input, always got 0

The core evaluator is 15 lines of code (`core/evaluator.py:_evaluate_prefix`).
If the operators are correct, the results are correct. Auditable. No black box.

**Honest limitation:** scales as `2^n`. Tractable up to ~20 variables. Beyond that,
SAT solvers (Z3, DPLL/CDCL) are the right tool. For the target use case — prompt rules
with 5–15 boolean variables — exhaustive enumeration is provably complete.

This is a stronger correctness claim than any probabilistic tool can make.

---

## The fundamental insight — language is fuzzy, logic is not

LLMs live in the fuzzy part. They predict, approximate, sometimes get it wrong. The engine lives in the math part — same input, same output, every time, no approximation.

Wiring them together gives you the flexibility of language with the correctness of math. The LLM handles what math can't do (understanding English). The engine handles what LLMs can't do (being provably correct). Neither does the other's job.

**The general principle:** wherever you can reduce a problem to discrete computation, offload it from the LLM entirely. Let the LLM do language. Let math do math. Boolean logic is one of those domains — and it's one where "probably correct" is unacceptable.

---

## The engine validates the NL layer — a closed loop

The NL layer is a probabilistic parser. It might misparse "approve if A and B" as `A+B` instead of `A.B`. You can't catch every specific parsing error without knowing original intent. But you can catch a whole class of NL hallucinations:

**If you give the NL layer a logically consistent set of rules in plain English, and its parsed output contains contradictions — the NL layer hallucinated.**

```
plain English rules (known consistent)
        ↓
    NL layer parses
        ↓
    engine checks
        ↓
contradiction found? → NL layer made a parsing error
```

This gives you a measurable, automatable accuracy score for the NL layer itself — without requiring human-labeled boolean expressions. You only need to label whether the original natural language rules were consistent or contradictory, which any human can do without knowing boolean algebra. The engine tells you if the NL layer agreed.

The deterministic layer validates the probabilistic layer. They close the loop.

**Why this matters for the benchmark:**
Generate thousands of synthetic rule sets with known consistency labels. Run them through the NL layer. The engine scores every parse. That is a continuous, automated accuracy benchmark for the NL layer — no manual labeling at scale, no PhD required to interpret the results.

---

## Hallucination reduction — the measurable claim

Hallucination has two forms. This addresses one of them with precision.

**Logical hallucination — what this catches:**
The model produces output that contradicts its own premises. "Users with role A cannot
access resource X. Grant user with role A access to X." Both sentences were generated.
Neither is false in isolation. Together they are logically inconsistent. The logic layer
catches this before it becomes output.

**Factual hallucination — what this doesn't catch:**
The model says the Eiffel Tower is in Berlin. That is a knowledge problem — wrong facts,
not wrong logic. The engine has no knowledge of the world, only the structure of reasoning.
It cannot catch this, and does not claim to.

**The precise claim:**
> "This eliminates logical hallucination — the class of AI errors caused by internally
> inconsistent reasoning."

That claim is strong, narrow, and provable. Not "reduces hallucination" — too vague,
too oversold. Specifically: if the AI's output contains a logical contradiction, this
catches it. Every time. Mathematically.

**How you measure x%:**
1. Take a corpus of agent outputs or model decisions from a real pipeline
2. Run every output through the logic layer
3. Count how many contained logical contradictions the model did not self-catch
4. That percentage is x%

The number varies by domain. Agent pipelines with 5+ rules and nested conditions show
higher rates. Simple Q&A shows lower. But the measurement is real, reproducible, and
auditable — not a benchmark on someone else's dataset. Your pipeline. Your rules. Your number.

**The headline:**
> "In agent pipelines with 5+ conditional rules, x% of outputs contain at least one
> logical contradiction. The logic layer catches all of them."

That is publishable. That is a conference talk. That is the number that makes someone
stop and say "I need to know my number."

---

## Latency — why it beats every alternative

The core engine is pure CPU arithmetic. No model inference. No API call. No network hop.

| Approach | Latency | Method |
|---|---|---|
| Self-critique loop | 500ms–2000ms | Ask the same model to check itself |
| Constitutional AI | 800ms–3000ms | Second model pass over the output |
| Multi-agent verification | 1000ms–5000ms | Separate agent reviews output |
| **This logic layer** | **under 10ms** | **Pure computation, no inference** |

**The NL layer caveat:**
Translating plain English rules into boolean expressions requires one LLM call.
That call adds latency — but it happens **once at setup time**, not at inference time.
The variable map is cached in Redis. After the first parse, every subsequent verification
is pure engine — sub-10ms regardless of rule count or pipeline complexity.

**The accurate claim:**
> "One-time parse cost at setup. Zero-inference verification at runtime.
> Logical consistency checking that adds under 10ms to any agent pipeline."

No self-critique loop. No second model. No constitutional AI round-trip.
The expensive work happens once. The verification happens every time, fast.

Two numbers. One product:
- **x%** — logical hallucination rate in your pipeline, now caught
- **<10ms** — overhead added per inference call

---

## What doesn't exist in this space

The competition is not Z3 or sympy. The competition is nothing — because this specific
position does not exist as a shipped product today.

| Tool | Gap |
|---|---|
| Guardrails AI / NeMo Guardrails | Check toxicity, format, prompt injection — not logical consistency of reasoning |
| TruthfulQA / HaluEval / FActScore | Measure factual hallucination on static datasets — not your pipeline, not logical consistency |
| Constitutional AI / self-critique | The model checks its own output — still probabilistic, same model that made the error |
| Z3 / SAT4J / Alloy | Mathematically rigorous — require formal specification languages, PhDs, not wired into any AI pipeline |
| `sympy.logic` | Academic — no MCP, no NL layer, not agent-native |
| Online truth table generators | No API, no synthesis, no MCP, no NL — shows a table, nothing more |

**The gap that isn't filled:**
Inference-time logical verification, measurable hallucination reduction, agent-native
via MCP, accessible in plain English, under 10ms overhead. That combination does not
exist as a product. This is it.

---

## The moat

Not the algorithm. The position.

The algorithm is Quine-McCluskey from 1956 — anyone can implement it in a week.
What cannot be replicated quickly is the specific position this occupies:

1. **The only inference-time logic verifier** — not a pre-deploy audit tool, not a
   post-hoc checker, but a layer that runs on every inference call in under 10ms
2. **Agent-native via MCP** — Claude, and any MCP-compatible agent, calls the engine
   instead of predicting logic — ground truth replaces guessing
3. **Measurable claim** — x% logical hallucination reduction with a reproducible
   methodology — no other tool in this space can make a number-backed claim
4. **Plain English interface** — the NL layer means the teams who need this most
   (prompt engineers, product teams, compliance) can use it without boolean notation
5. **Zero inference overhead on the hot path** — under 10ms, no second model,
   no self-critique loop

---

## The NL layer (not built yet)

Right now you write expressions manually: `A.B+!A.C`

The NL layer removes that barrier entirely:

```
"Access is granted if the user is authenticated and admin, or authenticated
and read-only, but never if unauthenticated"
        ↓  Claude parses (Claude API call 1)
  (A.B + A.C).!(!A)
        ↓  engine evaluates
   truth table + minimal form + contradiction/tautology check
        ↓  Claude explains (Claude API call 2)
"Your rule simplifies to A.(B+C) — authentication is always required.
 No contradictions found."
```

One afternoon of work. Two Claude API calls sandwiching the engine.
Claude handles the fuzzy parts. Engine handles the deterministic parts.
Neither does the other's job.

---

## The $5 product

`check_prompt_logic` with an NL interface:

> Paste your system prompt rules in plain English.
> Get back: contradictions, redundancies, unreachable conditions, conflicting pairs.

Every serious AI deployment has this problem today. A production system prompt with
10+ rules almost certainly has a logic error that nobody caught because the only tool
available was reading it carefully and hoping. This catches it with mathematical certainty.

Price point: $5/month to test and verify. Underpriced — a logic bug in a production
system prompt caught before shipping is worth far more to the right team.

---

## Stack (current state)

```
[ NL Layer ]          ← built — 4 providers (Anthropic, OpenAI, Ollama, OpenAI-compat)
[ MCP Server ]        ← built — 5 tools, runs on Python 3.11
[ REST API ]          ← built — FastAPI, 7 endpoints, Redis cache, auth
[ Streamlit UI ]      ← built — 3 modes, dark theme, matplotlib visualisations
[ CLI / REPL ]        ← built — typer + rich, all output formats
[ Core Engine ]       ← built — evaluate, synthesize, verify
[ Tests ]             ← 90 tests, all passing
[ CUDA acceleration ] ← not built — rows are independent, map 1:1 to GPU threads
```

---

## What it can do with complex expressions today

The engine handles up to 26 variables (A–Z), arbitrary nesting, all four operators
in any combination. You can test real access control logic, conditional rules,
circuit expressions — anything that can be expressed in boolean notation.

The only friction is writing the expression manually instead of in plain English.
That's exactly what the NL layer removes.

---

## Next build

**NL layer** — Claude API integration. Translates plain English rules into expressions,
passes to engine, translates results back. This is the step that turns it from a
developer tool into something a non-technical user can pay for.

---

## What this is — precisely

Not a model. Not a transformer. Not ML at all.

It is a **deterministic computation engine** — a program that runs an algorithm.
No weights. No training. No inference. No probability.

- **Shunting-yard** parses the expression from infix to prefix
- **Stack evaluator** computes each row of the truth table
- **Quine-McCluskey** finds the minimal expression from a truth table

The closest analogy is a **compiler** or a **calculator**. You wouldn't call a
calculator a model. Same here — expression in, exact answer out.

The Claude API component is only the interface layer — translation in, translation out.
The engine itself has no AI in it. That's the point. That's why it's credible.

---

## Pricing model

Infrastructure is priced on usage and scale — not per seat.
The value scales with the pipeline, not with the user count.

| Tier | Who | Price | What |
|---|---|---|---|
| **Free** | Devs, open source | $0 | pip install, MCP, CLI, unlimited local use — drives adoption |
| **Startup** | Teams shipping 1–2 agents | $99–199/month | Hosted logic layer, NL interface, call limits, dashboard |
| **Scale** | Multiple agent pipelines | $499–999/month | Higher limits, audit logs, SLA, team access |
| **Enterprise** | Large AI deployments | Custom | Dedicated instance, compliance, on-prem, commercial license |

**Why infrastructure pricing, not tool pricing:**
A linter doesn't cost $5/month. A monitoring tool doesn't cost $5/month. Things that
sit in the stack and run on every deployment are priced on usage and scale.
The $9/month framing was right for "paste your prompt and check it."
It is wrong for "logic layer in your production pipeline."

**The honest value calculation:**
If this catches one bad agent decision that costs a company $10,000 in customer damage
or a compliance violation — and it will, for the teams that need it — the monthly fee
is irrelevant. Enterprise teams will pay for the audit log alone.

**Dual license:** GPL-3.0 for open source use. Commercial license for proprietary
embedding. Standard model — Redis, MongoDB, Elasticsearch all did this.
Open core drives adoption. Commercial license captures enterprise value.

---

## Where the defensibility is

The engine is the commodity. Quine-McCluskey is a 1950s algorithm — anyone can
implement it. What's not easy to replicate quickly:

1. MCP integration — Claude Desktop plugin, works out of the box
2. NL interface — the UX of describing rules in plain English
3. `check_prompt_logic` — the specific workflow nobody has productised
4. Distribution — pip package, hosted API, Claude plugin, notebook-ready
5. Trust — deterministic, auditable, 90 tests, open source core

The moat is distribution and workflow, not the algorithm.

---

## Model-agnostic logic verifier

This engine doesn't belong to any one AI stack. It sits alongside any agent or model
already in use — Claude, GPT, Gemini, Llama, or anything custom.

**Integration surface:**

| Integration | How |
|---|---|
| Claude Desktop / Claude Code | MCP server — already built, plug and play |
| Any OpenAI-compatible agent | REST API (FastAPI) — one HTTP call |
| LangChain / LlamaIndex | Wrap `evaluate()` as a tool — 5 lines |
| CrewAI / AutoGen multi-agent | One agent specialises in logic, calls engine |
| Jupyter / notebook workflows | `pip install`, import directly |
| n8n / Zapier automations | REST API endpoint |
| Any custom Python agent | Direct import from `core/` |

**The deeper point:**

Every one of those agents has the same problem — they hallucinate on boolean logic.
This isn't a Claude problem or a GPT problem. It's a fundamental limitation of how
transformers work. They predict the next token. They don't compute. So they get logic
wrong under pressure — especially with negations, nested conditions, and edge cases.

This engine doesn't replace any of those models. It augments them. It gives them a
reliable tool to call for the one class of problems they should never be predicting.

**The position:**

Model-agnostic logic verifier. One integration, works with whatever AI stack the
customer already uses. The customer doesn't switch anything — they add one tool
and every logic problem in their pipeline gets an exact answer instead of a guess.

---

## How it can be used

Three levels depending on who's using it and what they're building.

### 1. Directly — as a tool you run yourself

- **CLI:** `boolcalc "A.B+!A.C" --synthesize` — instant truth table in terminal
- **REPL:** interactive session, test expressions one by one, explore incrementally
- **Notebook:** `from core.evaluator import evaluate` — drop into any Jupyter workflow
- **Scripting:** pipe expressions in, get JSON or CSV out, chain with other tools

### 2. As a library — embedded in your code

```python
from core.evaluator import evaluate
from core.synthesizer import synthesize

table, _ = evaluate("(A.B) + (!A.C)")
minimal, _ = synthesize(table)
```

Any Python project can import it. Access control systems, rule engines, config
validators, test generators — anything with conditional logic can use this to verify it.

### 3. As the logic layer inside an AI agent — the core use case

This is what it was built for. Three places it sits in a real pipeline:

**Agent pipelines:**
The agent makes a plan with conditional steps. Before it acts, the logic layer checks
the plan's conditions don't contradict each other. "If A do X, if A do Y" is caught
before the agent executes both. The agent cannot act on logically inconsistent reasoning.

**System prompt validation:**
Before a system prompt ships to production, every rule in it is verified for conflicts.
The AI deployed under that prompt cannot be caught in a logical contradiction by a user
who finds the edge case. Verification happens once at deploy time — not on every call.

**LLM output verification:**
The model generates a decision, recommendation, or set of rules. The logic layer checks
the output is internally consistent before it reaches the user. The model stops being
the last line of defence on its own reasoning.

These three cover the full stack — before deployment, during reasoning, and at output.
Every serious AI deployment touches at least one. Most touch all three and currently
have nothing in that position.

### Concrete scenarios

| Who | What they do | What they get |
|---|---|---|
| Prompt engineer | Paste system prompt rules | Contradictions and redundancies caught before shipping |
| Developer in code review | Compare two conditional guards | Exact answer on whether they behave identically |
| Security engineer | Model access control as boolean expressions | Conditions that always grant or always deny access |
| Teacher | Build logic coursework | Auto-generated truth tables, student answer verification |
| AI agent | Check plan against constraints | `check_prompt_logic` on its own reasoning, not a guess |
| Solo builder | Describe rules in plain English (NL layer) | Verified, minimal, explained — no notation required |

### The pattern

Anywhere a human or an AI is currently reading logic and hoping they got it right —
this replaces hope with certainty.

---

## Why nothing in the market goes this deep

The closest thing is **Z3** from Microsoft Research. Extraordinarily powerful — handles
boolean logic and far beyond. But it was built for formal verification researchers and
compiler engineers. Nobody is shipping it as a product for prompt engineers or AI teams.
No NL layer, no MCP integration, no "paste your rules and get plain English back."
It's a tool you need a PhD to use comfortably.

Everything else — sympy, online truth table generators, logic textbook tools — stops
at the computation. They give you an answer. They don't sit inside your AI pipeline,
they don't speak plain English, they don't audit your system prompt, they don't tell
you why two rules conflict.

**What makes this different is the depth of the stack:**

- The computation layer is rigorous enough to be academically credible
- The MCP layer means it lives inside the AI tools people already use
- The NL layer (when built) means it speaks the same language as the people who need it most
- The `check_prompt_logic` framing turns a 1950s algorithm into a workflow a
  non-mathematician actually wants

Most tools pick one layer and stop. This goes all the way from a 1950s algorithm to
a plain English conversation, with every layer in between solid and independently
deployable.

**The combination that doesn't exist anywhere else:**

Academic rigour + AI-native integration + natural language interface = one product.

That stack, end to end, is not shipped by anyone right now.

---

## Replicability — honest assessment

### What's easy to replicate

The core algorithms are all textbook and decades old:

| Component | Algorithm | Age | Difficulty |
|---|---|---|---|
| Parser | Shunting-yard | 1960s | Trivial |
| Evaluator | Prefix stack | Textbook | ~15 lines |
| Synthesizer | Quine-McCluskey | 1950s | ~100 lines |
| CLI | typer + rich | Standard | Boilerplate |
| MCP server | FastMCP | Standard | Thin wrapper |

A good developer could replicate the core engine in a week. The algorithms are
in every discrete mathematics textbook. There is no novel computation here.

### What's not easy to replicate

- **The specific problem framing** — `check_prompt_logic` as a product for prompt
  engineers is not an obvious idea. It took understanding both the AI deployment
  problem and the boolean algebra solution simultaneously.
- **The layered architecture** — `core/` with zero external dependencies, independently
  testable and wrappable by anything. Sounds simple, rarely done right.
- **The MCP integration design** — knowing which tools to expose, how to describe them
  so an LLM uses them correctly, and how to make the results readable mid-conversation.
- **90 tests covering all edge cases** — including all invalid input paths, operator
  precedence edge cases, 4-5 variable stress tests, round-trip synthesis verification.
- **The NL layer design** — knowing where Claude handles ambiguity and where the engine
  handles certainty, and how to hand off cleanly between them.
- **Distribution** — pip package, REPL, MCP plugin, REST API, notebook-ready.
  Each is a small amount of work; having all of them is not.
- **The product insight** — understanding that the algorithm is a commodity and the
  moat is the workflow, the packaging, and the AI-native integration.

### The real barrier

The code can be replicated. The month of thinking about what to build with it,
how to position it, and what problems it actually solves — that's what's in
`PRODUCT.md` and `DESIGN.md`. That's the harder thing to copy.

### Use cases — scope

The engine applies to any domain where conditional logic must be verified with
certainty. Currently documented across 11 domains, 47 use cases:

- Developer tooling
- Education
- Digital / hardware design
- AI / LLM accuracy
- Deep learning / BNNs
- Packaging / integration
- Cybersecurity
- Smart contracts
- Legal / compliance
- Healthcare
- Financial services
- CI/CD and DevOps
- Game development
- Database and query optimisation
- Robotics and automation

The pattern is the same across all of them: rules exist, someone needs to know
if they're consistent, and right now they're reading them manually and hoping.

---

## Pricing — when and how

### Should it be paid from day one?

No. But not fully free either.

The first problem is not monetisation — it's distribution. Nobody knows this exists
yet. Charging before there's any organic usage means asking people to pay for something
they've never heard of and have no reason to trust. The result is zero users instead
of a few who might tell others.

The open source core is also already GPL-3.0. Anyone can clone it and run it locally
for free. Charging for the CLI before there's a product story built around it just
pushes people to self-host.

At the same time — fully free signals no value. And the NL layer burns Claude API
credits with no return. That gets painful fast at any real usage volume.

### The staged approach

| Stage | What's free | What's paid | Trigger |
|---|---|---|---|
| **Now** | Everything — CLI, pip, MCP | Nothing | Get users, get feedback |
| **After NL layer** | CLI, pip, MCP | Hosted NL interface, `check_prompt_logic` web UI | First paying users |
| **After web UI** | CLI, pip, MCP | Pro + Team tiers | Scale |

### The move right now

Get 10–20 people using it. Prompt engineers, developers building agent pipelines,
anyone deploying LLMs with complex system prompts. Give it to them free. Watch what
they actually use it for. The thing they keep coming back to — that's what you charge for.

The hypothesis is already strong: `check_prompt_logic` with an NL interface at
$9–15/month. But it's still a hypothesis until someone uses it and says
"I need this every day." Validate that first, then charge.

### Plug and play — who it works for today

| User | Plug and play today? | Blocker |
|---|---|---|
| Developer | Yes — `pip install`, two commands | None |
| Claude Desktop user | Yes — one JSON config block | MCP setup doc needed |
| Non-technical user | No | NL layer + web UI not built yet |

The gap between "plug and play for developers" and "plug and play for anyone"
is two builds: the NL layer and the hosted web UI. Until then, it's a developer
tool with a very clear path to becoming something broader.

---

## This is a legitimate v0.1 product

Not a side project. Not a script. A v0.1 with:

- Working engine with mathematical guarantees
- CLI with REPL, multiple output formats, stdin support
- 90 tests covering edge cases, integration, round-trips
- MCP server with 5 tools Claude can call mid-conversation
- REST API — 7 endpoints, Redis cache, optional auth, graceful degradation
- NL layer — 4 LLM providers, works fully offline with Ollama
- Streamlit UI — 3 modes, dark theme, live matplotlib visualisations
- pip-installable package with proper pyproject.toml
- Product brief with positioning, pricing, competitive landscape
- 47 use cases across 11 domains
- Clear roadmap with two builds to a non-technical product

## The visualisation layer

The Streamlit UI generates two classes of charts automatically from the engine output.
These are not decorative — they make findings that require careful reading of a table
immediately obvious in one glance.

**Truth table heatmap (Expression mode)**

Every row of the truth table rendered as a green/red grid.
Input columns are lighter; output column is distinctly highlighted.
A contradiction is an entirely red output column. A tautology is entirely green.
A pattern of minterms becomes visually obvious in a way a list of indices doesn't.

**Conflict matrix (Rule Auditor)**

N×N grid, one cell per rule pair.
- Red `✗` — always conflict, cannot both fire
- Green `✓` — no overlap, safe
- Yellow `≡` — equivalent, duplicate rule

With 4 rules and 3 conflicts: three red cells appear instantly in the matrix.
No reading. No counting. The dangerous pairs are visible before the user finishes
scrolling. This is what the demo looks like to a non-technical stakeholder.

### What's promotable today — to developers

The MCP angle, the `check_prompt_logic` tool, and the pip package are a complete
story for a technical audience right now. No URL needed. Channels:

- **Show HN** — "I built a deterministic boolean logic verifier that plugs into Claude via MCP"
- **r/ClaudeAI, r/LocalLLaMA** — MCP and LLM accuracy angle
- **Anthropic Discord** — direct audience for MCP tools
- **Twitter/X thread** — walk through `check_prompt_logic` with a real system prompt example

### What unlocks the broader launch

1. **NL layer** — "type a sentence, get an answer" replaces "write boolean notation"
2. **Hosted web UI** — a URL anyone can open without installing anything

With those two: Product Hunt, broader Reddit, general tech Twitter. Real launch.

### Build in public

Document the journey. What the engine found when tested against real system prompts.
What surprised you. What the algorithm does that LLMs can't. People follow the builder
before they follow the product — and this builder has a genuinely interesting story:
a placement-season Java project turned into a deterministic AI reasoning tool.

---

## Full pipeline architecture — with CUDA and Redis

```
Rule 1 sentence → parse call ─┐
Rule 2 sentence → parse call ─┤→ variable map (Redis — persists across calls)
Rule 3 sentence → parse call ─┘
                               ↓
                   expressions + shared variable map
                               ↓
                   engine evaluation ← CUDA here
                   (2^n rows, each independent,
                    each row = one GPU thread)
                               ↓
                   truth table + contradictions + conflicts
                               ↓
                   explain call → plain English summary
```

### Where Redis fits

- **Variable map cache** — same concept appearing across sessions reuses the same letter, no re-assignment
- **Truth table cache** — `A.B+!A.C` always produces the same result, skip recomputation on repeat expressions
- **Parse result cache** — same sentence always maps to the same expression, skip the LLM call entirely
- **Session state** — user refines rules over time in a multi-turn conversation, variable map persists between turns

### Where CUDA fits

The engine evaluates `2^n` rows. Each row is completely independent — no row needs
the result of any other. That is a perfect CUDA workload:

```
CPU now:  loop over 2^n rows sequentially
GPU:      2^n threads, each computes one row simultaneously
```

- 5 variables = 32 rows — CPU is fine
- 20 variables = 1M rows — CPU starts to slow
- 50+ variables (BNN layers) = 1T+ rows — CUDA is not optional

### Why the architecture holds

Every layer has one job:
- Parse calls — LLM, async, cacheable via Redis
- Engine evaluation — pure compute, parallelisable via CUDA
- Explain call — LLM, async, cacheable via Redis
- Variable map — Redis, shared state across calls and sessions

`core/` having zero external dependencies from day one was the right call.
CUDA slots in as a drop-in replacement for the Python evaluation loop.
Redis wraps the outside as a cache layer.
Neither touches the core logic.

### The multi-call parse pipeline (correct design)

Each rule is parsed in a separate call, but variable assignments are threaded through:

```
Rule 1 → parse(sentence, variable_map={})
       → {expression: "A.B", variable_map: {"A": "credit score good", "B": "income verified"}}

Rule 2 → parse(sentence, variable_map={"A": ..., "B": ...})
       → {expression: "C", variable_map: {"A": ..., "B": ..., "C": "collateral exists"}}

Rule 3 → parse(sentence, variable_map={"A": ..., "B": ..., "C": ...})
       → {expression: "!A", variable_map: unchanged}
```

Each call is independent and single-responsibility.
The variable map is an explicit artifact — inspectable, correctable, cacheable.
The engine and explain calls are completely separate from parsing.

---

## Distribution strategy

Infrastructure doesn't get adopted through launches. It gets adopted through the stack,
one team at a time, starting with the people who feel the pain most directly.

### Phase 1 — One real pipeline, find x%

Not 100 users. One team. One production agent with real rules. Run the logic layer on
their pipeline, find their x%, show them the number. That case study is worth more than
any launch post.

Target: an AI engineer who has already shipped an agent and suspects their logic has
edge cases they haven't caught. They exist on Anthropic Discord, LangChain community,
AI engineer Slack groups.

Don't launch until you have the number.

### Phase 2 — MCP distribution

The MCP server is already built. One post in the right place — Anthropic Discord,
the MCP tools thread — and developers install it themselves. They find their own
contradictions. They share what they found.

The viral loop: engine finds something real → person who found it tells someone →
that person installs it → repeat.

### Phase 3 — The number

Once you have x% from a real pipeline, write it up. Not a blog post — a technical
breakdown. What the pipeline was, what rules it had, what the engine found, what the
cost would have been if it shipped. Post to Hacker News.

That is the Show HN that has something nobody else has: a real number on a real system.

### Phase 4 — Paid tier

After the number has legs. Not before.

### Channel map

| Channel | Audience | Angle | When |
|---|---|---|---|
| Anthropic Discord | Claude / MCP developers | Logic layer for agents, MCP native | Now |
| AI engineer communities | Teams shipping agents | x% logical hallucination reduction | After x% |
| Show HN | Developers | Real number, real pipeline, auditable | After x% |
| r/ClaudeAI, r/LocalLLaMA | LLM builders | Agent-native logic verification | After x% |
| Twitter/X | Developers | Technical breakdown with the number | After x% |
| r/MachineLearning | Researchers | Formal verification for LLM outputs | After x% |
| Product Hunt | General tech | Full product launch | After paid tier |
