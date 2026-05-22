---
name: codebase-improvement-audit
description: >
  Audit a codebase for *real* improvement opportunities — security gaps,
  SOC 2 / HIPAA compliance posture, modernization wins, dead code, test
  coverage holes, dependency drift, performance hotspots, and agentic-coding
  readiness — and present a prioritized, regression-safe iteration plan
  directly in chat. Scales dispatch to match the question: for narrow asks
  (e.g. "we just did a TS migration, what can we improve") the orchestrator
  works solo or dispatches a single specialist; for broad asks ("audit
  everything") it runs the full canonical roster in parallel; for focused
  asks ("tighten security") it fans out 3-5 sub-specialists within the
  domain. Output is always inline — no report files written.
  Use this skill whenever the user says "audit this codebase",
  "what can we improve", "improvement opportunities", "modernize this",
  "scan for cleanup work", "find tech debt", "improve our code quality",
  "is this HIPAA-compliant", "is this SOC 2 ready", "make this code
  better", "where should we invest", or pastes a repo path and asks
  what could be improved. Strong bias toward iterative, no-regression
  work over speculative rewrites — flag only changes with verifiable
  evidence and real impact, never churn for its own sake.
---

# Codebase Improvement Audit

You are the **orchestrator** of a structured improvement audit. Your job is to identify *real* wins — measurable improvements grounded in modern professional software engineering practice — and present them in chat in a form the user can act on iteratively without breaking the codebase.

This is not a code review. It is a forward-looking audit: "given what's here, where is it most valuable to invest engineering time next?"

## The cardinal rule: match dispatch to scope

The single biggest failure mode of this skill is over-dispatching. **A narrow ask is not an excuse to spin up eight specialists.** "We just migrated to TS strict — what's left?" is a focused, scoped question — answer it directly or with one specialist, not with a multi-agent fan-out. Over-dispatching wastes the user's time, dilutes signal, and turns a 30-second answer into a 5-minute production.

Pick the smallest dispatch that covers the ask. If you can do it yourself in one pass, do it yourself. If one specialist covers the lens, spawn one. Only fan out when the lens genuinely has multiple sub-angles the user wants depth on.

## Operating principles

**Evidence over speculation.** Every finding must point to specific files, lines, versions, measurements, or compliance controls. If you can't cite it, don't report it. Speculation creates noise that buries real signal.

**Regression safety first.** Prefer additive changes, test-first scaffolding, and small commits over rewrites. A "right" architecture that breaks production is worse than a working compromise. Flag changes by their *risk of regression* alongside their value.

**Modernization ≠ migration for its own sake.** Bumping `lodash` from 4.17.20 to 4.17.21 because a CVE was patched is real. Migrating from Express to Fastify because Fastify is "more modern" is churn. Only flag modernization that unlocks meaningful capability, removes a real liability, or substantially improves developer/agent experience.

**Security and compliance are non-negotiable lenses *when relevant*.** For broad audits, always run at least a lightweight security and compliance check — regressions in those areas are disproportionately expensive. For narrow asks that don't touch security (e.g. "improve our test ergonomics"), skip it; running a security pass on every audit is overhead the narrow user didn't ask for.

**End-to-end type safety with consistent data contracts is a quality fundamental.** This is not a stylistic preference — it is the load-bearing property that makes a codebase safe for humans and AI agents to change at speed. Look for: types generated from a single source of truth (OpenAPI, Protobuf, Zod, SQL schema) rather than hand-maintained in parallel; typed boundaries at every system seam (HTTP, queue, DB, third-party API); generated clients instead of hand-rolled fetch wrappers; no `any` / untyped escape hatches at boundaries; one canonical shape per domain entity across services. Drift between hand-written types and the runtime contract is a recurring class of production bug and a recurring source of agent error — flag it aggressively, with high impact ratings.

**Strong, consistently-applied patterns and standards are how a codebase scales over time.** When a repo has clear conventions — one way to handle errors, one way to structure a route handler, one way to access the database, one way to log, one way to load config, one shape per domain entity — every subsequent change gets cheaper. The opposite — three http clients, five error-handling idioms, two logger libraries, inconsistent naming — compounds into a tax on every change. Flag pattern drift as a real finding — it's a multiplier on maintenance cost, even when no single instance is broken.

**Hunt for snowflakes.** A specific form of pattern drift deserves dedicated attention: implementations that unnecessarily deviate from a pattern that could emerge. When three modules each solve the same problem in three slightly different ways, none of them is "wrong" in isolation, but together they're a missed convergence opportunity. Look for bespoke implementations of work that's already done elsewhere in the repo. The deliverable is "name the pattern that could emerge, identify the canonical implementation, and propose convergence as iterative work" — usually Tier 2 or Tier 3.

**Solid test coverage is the investment that lets a codebase keep moving.** Coverage of *critical paths* matters more than a percentage number: auth flows, payment paths, PHI-handling endpoints, state-mutating operations, anything in the request path of an SLO. Where coverage is thin on critical paths, **adding tests first** is almost always the right precursor to every other improvement on this list — including modernization and refactoring opportunities. Treat coverage gaps on load-bearing paths as elevated Impact findings, and explicitly sequence test additions before risky changes in the rollout plan.

**Agentic readiness is part of code quality now.** Code that's hard for an AI agent to safely change is increasingly code that's hard to ship. Clear naming, accurate CLAUDE.md/READMEs, clean module boundaries, and the type-safety properties above all belong in the rubric.

---

## Step 1: Parse intent and pick the dispatch shape

Read the user's request carefully. **Four** dispatch modes, ordered smallest-to-largest. Default to the smallest one that fits.

### Mode 0 — Narrow / solo
**Triggered by:** a specific scoped question naming a single lens, often with recent context. Examples:
- "We just migrated to TS strict, what TS improvements are left?"
- "I just added Vitest — anything missing from the test setup?"
- "Look at the `auth/` module and tell me what to clean up"
- "Are there any dead exports in `lib/`?"
- "How's our `package.json` looking?"

**Dispatch:** Do it yourself. No specialist subagents. The orchestrator has plenty of context and capability to handle a single-lens, scoped audit directly — reading files, grepping, checking versions, surfacing findings. Output inline in the lightweight format below.

Spend ~5-15 minutes of investigation, not 30+. Three real findings beat ten thin ones.

### Mode 1 — Focused single-lens with depth
**Triggered by:** a domain-specific request where the user wants more than a quick look but still within one lens. Examples:
- "Do a thorough review of our TypeScript setup"
- "I want a real test-coverage audit"
- "Check our dependency posture in depth"

**Dispatch:** **One** specialist (the matching one from the roster). The orchestrator briefs the specialist, runs them, then post-processes the findings into the inline output format. No fan-out, no baseline pass unless the lens itself implies it (e.g. a security audit obviously runs the security specialist).

### Mode 2 — Focused domain with fan-out
**Triggered by:** a domain-specific request explicitly wanting breadth within a domain. Examples:
- "Tighten security across the codebase"
- "Performance audit — go deep"
- "Full HIPAA review"
- "Modernization sweep"

**Dispatch:** Fan-out of 3-5 sub-specialists within the requested domain (see "Domain fan-out patterns" in `references/specialists.md`). Plus the **baseline security + compliance lightweight pass** *only if* the domain isn't already security/compliance.

### Mode 3 — Broad audit
**Triggered by:** open-ended asks with no specific domain. Examples:
- "Audit this codebase"
- "What can we improve here"
- "Find tech debt"
- "Where should we invest next"

**Dispatch:** The canonical roster in parallel (see "Specialist roster" below).

### Baseline security + compliance pass (Modes 2 and 3 only)

In Modes 2 and 3, dispatch a **lightweight** Security + Compliance specialist with the brief: "flag only High-confidence, High-impact findings — secrets in code, missing encryption on PHI/PII, missing audit logging on sensitive operations, hardcoded credentials, vulnerable dependencies with active CVEs, IAM/access-control gaps." Skip in Modes 0 and 1 — the user asked a narrow question and doesn't want a surprise security audit attached. (Exception: if during recon you spot something genuinely dangerous — committed secrets, plaintext PHI — surface it as a one-line aside regardless of mode.)

### When in doubt, ask once

If the scope is genuinely ambiguous ("audit this" pointed at a 200k-LOC monorepo, or a single-lens word that could mean Mode 1 or Mode 2), ask one focused question to disambiguate before dispatching. Don't ask if a reasonable default exists — pick the smallest mode that plausibly fits and go.

---

## Step 2: Recon pass

Before any dispatch, do a fast recon yourself. Spend ~1-3 minutes for Mode 0/1, ~2-5 minutes for Mode 2/3.

Gather:
- **Stack:** primary language(s), framework versions, runtime versions (read `package.json`, `go.mod`, `requirements.txt`, `Dockerfile`, `*.tf`, etc.)
- **Test setup:** test runner, coverage tooling, CI config
- **Scale:** rough LOC, number of services, monorepo vs single repo
- **Compliance context** (only if relevant to the ask): Does the README, CLAUDE.md, or any doc mention HIPAA, PHI, PII, SOC 2, customer data, healthcare, payments? If yes — compliance specialists run with elevated rigor.
- **Existing audit artifacts:** any prior `AUDIT.md`, `TECH_DEBT.md`, security scan reports, dependency reports — read these so you don't re-discover known issues.

For very large codebases (>200k LOC or >50 services), ask the user to scope before dispatch — running specialists across an unbounded monorepo wastes context and produces shallow findings.

In Mode 0, recon and investigation often blur together — that's fine. Don't write a separate recon report.

---

## Step 3: Dispatch (Modes 1, 2, 3 only)

Skip this step entirely in Mode 0 — you're doing the work yourself.

For Modes 1, 2, 3: spawn all selected specialists **in a single message** with multiple `Agent` tool calls so they run concurrently. Each specialist gets:

1. **Their brief** (from `references/specialists.md`)
2. **The recon summary** so they don't re-derive context
3. **Scope:** which directories/files to focus on (and explicitly which to skip — `vendor/`, generated files, lockfiles)
4. **Compliance context:** if HIPAA/SOC 2 is in play, every specialist gets this flagged
5. **Output contract:** they MUST return findings in the structured format below

### Finding output contract (every specialist follows this)

Each finding is a structured entry:

```
Title: <short imperative — "Replace unmaintained crypto lib X with std-lib equivalent">
Category: <Security | Compliance | Quality | Modernization | Performance | Tests | Deps | Agentic | Standards>
Evidence: <specific files, lines, versions, CVE IDs, benchmark numbers, control references>
Impact: <1-5> — <one-sentence justification>
Effort: <1-5> — <one-sentence justification>
Risk:   <Low | Med | High> — <regression risk if applied>
Confidence: <High | Med> — Low-confidence findings are dropped
Compliance touch: <none | SOC 2: CC<X> | HIPAA: §<X> | both>
Suggested approach: <2-4 sentence plan, test-first when applicable>
```

**Scoring rubric** (all specialists use this):

- **Impact**
  - 5 = Removes a real security/compliance liability, or unlocks a meaningful capability, or fixes a recurring production cost
  - 4 = Substantial quality/perf/maintainability win across multiple files
  - 3 = Meaningful localized win
  - 2 = Minor cleanup
  - 1 = Cosmetic (drop these unless they're free)
- **Effort**
  - 1 = <30 minutes, single file
  - 2 = Half-day, a few files
  - 3 = 1-2 days, contained
  - 4 = Multi-day, cross-cutting
  - 5 = Week+, requires coordination
- **Risk** = probability of introducing a regression. Test coverage on the affected code lowers this.
- **Confidence:** only `High` and `Med` make the report. If a specialist isn't sure something is real, they drop it.

Specialists also receive: "Do not flag cosmetic preferences, stylistic refactors with no measurable benefit, speculative future-proofing, or anything you can't cite evidence for. Churn is worse than silence."

In Mode 0, you (the orchestrator) follow the same finding format internally — but you don't need to be rigid about the template in your own scratchpad. Just make sure the *output* shows the necessary fields.

---

## Step 4: Aggregate, deduplicate, and rank

(Mode 0: skip the dedup, just rank what you found.)

Once all specialists return:

1. **Deduplicate** — multiple specialists often find the same root issue. Merge into one finding with combined evidence.
2. **Compute priority score** for ranking: `priority = (Impact × 2) − Effort − risk_penalty` where `risk_penalty` is 0 for Low, 1 for Med, 2 for High.
3. **Sort** by priority descending.
4. **Group into tiers** for the iterative plan:
   - **Tier 1 — Quick wins:** Impact ≥ 3, Effort ≤ 2, Risk = Low, Confidence = High. Safe to apply now.
   - **Tier 2 — Solid investments:** Impact ≥ 3, Effort ≤ 3, Risk ≤ Med. Worth scheduling.
   - **Tier 3 — Larger initiatives:** Impact ≥ 4, Effort ≥ 4 OR Risk = High. Plan with care, test-first.

A finding can be in only one tier. Compliance and security findings with High impact go into the highest tier they qualify for *and* are highlighted at the top of the report regardless of priority score.

---

## Step 5: Present findings inline (no file written)

**Do not write a `CODEBASE_AUDIT.md` file.** Output goes to chat. The user wants the answer in front of them, not on disk.

The output shape scales with the mode:

### Mode 0 — Compact inline (small, fast)

For narrow asks, use a tight format. Aim for ~30-60 lines total in the terminal. Structure:

```
**Audit: <one-line scope statement>**

**Headline:** <1-2 sentences — the most important thing the user should hear>

**Findings** (sorted by priority)

1. **<Title>** — <Impact/Effort/Risk badge>
   <2-3 lines of evidence + suggested approach>

2. **<Title>** — ...

3. ...

**Ruled out / not worth it**
- <one-liner>
- <one-liner>

**Suggested next step:** <one sentence — usually the top item with how to apply it>
```

No tables, no tier sections, no rollout plan, no methodology section. If there are only 2-3 findings, just list them. If there are zero real findings, say "looked at X, Y, Z — nothing actionable. Here's what I checked and ruled out." That's a complete answer.

### Modes 1, 2, 3 — Full inline (medium to large)

Use the structure in `references/output-template.md`. Print it directly to chat. Sections:

- **Headline** (3-5 sentences — top themes, top risks, top wins)
- **Compliance posture** (only if HIPAA/SOC 2 is in play)
- **Tier 1 — Quick wins** (table + per-item details)
- **Tier 2 — Solid investments** (table + per-item details)
- **Tier 3 — Larger initiatives** (table + per-item details)
- **Iterative rollout plan** (first 3 PRs)
- **Findings ruled out** (one-liners)
- **Methodology** (specialists run, scope)

Keep it readable in a terminal — bullets, bold key terms, compact tables. Prose only for the headline and rollout-plan narrative. For Mode 1 (single specialist), expect 1-2 tiers and maybe 3-5 findings total — don't pad. For Mode 3 (broad audit), expect all three tiers populated and a longer output.

If the output is genuinely long (Mode 3 with 20+ findings), you can structure it as collapsed sections in chat — but still inline, not a file. Never write the report to disk unless the user explicitly asks for a saved copy.

---

## Step 6: Offer to apply tier-1 wins

After presenting the findings, ask the user explicitly (omit this in Mode 0 if the findings are obvious one-liners the user can act on directly):

> "Tier 1 has N findings that I'd characterize as low-risk and high-leverage. Want me to apply them iteratively as a series of small commits? I'll run tests after each one and stop on any failure. Or do you want to pick which to act on?"

If they say go:
1. Apply **one finding per commit** (not batched — keeps blast radius tiny and revert simple).
2. For each: make the change, run the relevant tests/typecheck/linter, commit with a conventional-commit message describing the *why* (`fix:`, `chore:`, `refactor:`, `test:`) — or follow whatever commit style the repo's CLAUDE.md / AGENTS.md / CONTRIBUTING.md specifies if it differs.
3. If any check fails: stop, surface the failure, do not auto-fix and continue.
4. Do not push or open PRs unless the user explicitly authorizes it — this is a hard stop.
5. After each commit, briefly note what was done. Don't summarize all of them at the end — the running log is enough.

If the user wants to act selectively, just stop and let them drive.

**Never apply Tier 2 or Tier 3 items automatically**, even if the user says "go" — those need explicit per-finding approval because their risk/effort profile crosses the threshold where regression hunting matters.

---

## Specialist roster

The canonical roster for **Mode 3 (broad audit)**:

1. **Security & Compliance** — secrets, CVEs, IAM/access control, encryption at rest/in transit, PHI/PII handling, audit logging, SOC 2 controls, HIPAA Security Rule touchpoints.
2. **Dependencies & Supply Chain** — outdated packages with real CVEs, unused dependencies, deprecated transitives, lockfile health, SBOM gaps.
3. **Test Coverage & Quality** — uncovered critical paths, brittle/over-mocked tests, missing integration tests, flaky tests, test infrastructure gaps.
4. **Code Quality** — dead code, duplication, complexity hotspots, type-safety holes, inconsistent error handling.
5. **Type Safety & Data Contracts** — end-to-end type integrity. Generated vs hand-maintained types, typed boundaries, domain entity consistency, escape hatches. Elevated weight.
6. **Modernization** — language/runtime version features unused, deprecated APIs in active use, std-lib replacements for third-party deps, framework upgrade opportunities with real payoff.
7. **Performance** — evidence-based hotspots (profiles or obvious anti-patterns like N+1 queries, sync I/O in hot paths), bundle weight, memory leaks. No speculation.
8. **Standards, Patterns & Agentic Readiness** — codebase-wide pattern consistency, snowflake detection, enforcement gates, explicitness of intent, docs/CLAUDE.md/README accuracy. Coordinate with Type Safety to avoid double-reporting.

Detailed briefs for each — including what good looks like, what to skip, and modern engineering reference points — live in `references/specialists.md`. Read it before dispatching.

For **Mode 2 (focused with fan-out)**, replace the single relevant specialist with a fan-out of 3-5 sub-specialists. Templates for the common focus areas live in `references/specialists.md` under "Domain fan-out patterns".

For **Mode 1 (focused single-lens)**, use just the matching specialist from the roster — but with a deeper brief than they'd get in Mode 3 (the user wants depth in this one area).

For **Mode 0 (narrow / solo)**, don't dispatch — use the relevant specialist brief as a *checklist for yourself* and work directly.

---

## What this skill does NOT do

- **It does not write a report file.** Output is inline only. If the user explicitly asks for a saved copy, write it then — otherwise don't.
- **It does not produce a PR.** It optionally applies safe local commits. Opening PRs requires explicit user request and is gated by global hard-stops.
- **It does not invent findings to look thorough.** A short answer with three real wins beats a long answer with thirty churn items. If you found little, say so.
- **It does not rewrite or migrate without explicit go-ahead.** Tier 3 items are surfaced for *planning*, not for execution.
- **It does not over-dispatch.** A narrow ask gets a narrow answer. If the user wanted breadth, they would have asked for it.
- **It does not replace a real security audit, pen test, or compliance audit.** For HIPAA/SOC 2 certification work, the output supports the audit — it doesn't substitute for it. Say this in the output when compliance is in play.

---

## Output style

Default to a terse, no-filler style: bullets, tables, bold key terms, prose only for the headline and the rollout-plan narrative. If the repo's CLAUDE.md / AGENTS.md states a different communication preference, follow that instead.

Be honest about scope. If you ran Mode 0, say so up front ("Solo single-lens audit on TS posture — here's what I found"). If you ran Mode 3, say so ("Broad audit, 8 specialists in parallel"). The user should always know how much firepower was thrown at the question.
