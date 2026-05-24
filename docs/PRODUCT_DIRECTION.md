# Product Direction

## The Problem We're Solving

AI agents running compliance, eligibility, and decision logic are built on boolean rule sets written by humans across teams over months. Nobody verifies those rules are internally consistent before the agent goes live. When two rules contradict each other, the agent picks a winner arbitrarily — and the decision is wrong by definition, provably.

This isn't a model quality problem. Even a 70B model gets ~20% of boolean logic questions wrong. You can't ask an LLM if your rules conflict and trust the answer. You need a deterministic layer that computes it.

---

## The Market

**Primary targets: Drata, Vanta, and their customers.**

Drata and Vanta run compliance automation agents that continuously check SOC 2, ISO 27001, HIPAA, and other framework controls. Those controls are boolean rules:

- "Access must be revoked within 24 hours of offboarding AND manager approval required"
- "MFA required for all admin accounts OR hardware key exemption applies"
- "Data encrypted at rest AND encryption key rotation every 90 days"

As frameworks evolve and teams add controls, conflict probability grows silently. The agent makes arbitrary decisions at conflict points — and audit results depend on which rule fired first, not what the policy actually requires.

**Other verticals with the same problem:**
- Fintech — loan approval, fraud detection, credit eligibility rules
- Insurance — underwriting rules, claims eligibility, policy conditions
- Healthcare — treatment eligibility, billing compliance, access control
- Legal — contract clause conflict detection

---

## Why No Formal Tieup Needed

Drata and Vanta both have public APIs and published integration ecosystems. Their control definitions are accessible. The play:

1. Pull their publicly documented SOC 2 / ISO 27001 control sets via API
2. Translate controls to boolean expressions via the NL layer
3. Run `check_prompt_logic` — find real conflicts
4. Surface results back in plain English: "Control 14 conflicts with Control 31 — they cannot both be satisfied simultaneously"

This is a third-party integration, same as any tool in their ecosystem. No partnership needed to build it or demo it.

**The demo that gets attention:** find a real conflict in a published compliance framework using publicly available controls. Publish it. That's the blog post, the Reddit post, the HN submission — and it gets Drata's attention without needing a meeting first.

---

## Pricing

**$49/month per framework or API integration.**

Justification:
- One bad compliance decision costs more than $49 — failed audits, customer churn, regulatory liability
- Drata customers are paying $15k-$100k/year for compliance automation — $49/month is noise
- Per-framework pricing scales naturally: SOC 2 = $49, ISO 27001 = $49, HIPAA = $49
- API access (for teams building their own agents) = $49/month flat

**Tiers to consider:**
| Tier | Price | What |
|---|---|---|
| Starter | $49/month | 1 framework, up to 50 rules |
| Growth | $149/month | 3 frameworks, up to 200 rules, plain-English explanations |
| Enterprise | Custom | Unlimited frameworks, API access, dedicated support |

---

## What Needs to Be Built

### Phase 1 — Make the demo (2-3 weeks)
- Pull Drata/Vanta public control set
- NL layer: plain English rule → boolean expression (already exists, needs hardening)
- Plain-English conflict explanation: "Rule X and Rule Y conflict because..."
- Landing page chart: compliance drift — conflict rate as rule count grows

### Phase 2 — Integration (4-6 weeks)
- Drata API connector: pull live control definitions
- Vanta API connector: same
- Conflict report output: PDF or JSON, audit-ready format
- Webhook: alert when a new control creates a conflict with existing ones

### Phase 3 — Product (ongoing)
- Dashboard: live view of rule set health per framework
- Remediation suggestions: when a conflict is found, suggest which rule to modify
- Version history: track when conflicts were introduced

---

## The One-Sentence Pitch

> Your compliance agent is running on rules nobody has verified. When controls conflict, your agent makes an arbitrary decision — and your customer's audit depends on which rule fired first, not what the policy requires. This engine finds those conflicts before they reach an audit.

---

## Immediate Next Steps

1. Pull Drata's public SOC 2 control set
2. Run it through `check_prompt_logic`
3. If conflicts are found — write the blog post
4. Normalize benchmark to 100 cases across all models (credibility fix)
5. Build the compliance drift chart for the landing page
