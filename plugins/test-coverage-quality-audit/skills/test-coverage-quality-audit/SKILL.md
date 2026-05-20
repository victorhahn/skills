---
name: test-coverage-quality-audit
description: Audit a codebase for test coverage *quality* — not just line %. Detects tautological assertions, business logic leaks into controllers, snapshot abuse, fake-timer/store leaks, over-mocking of internals, missing tests, and framework-specific anti-patterns in JS/TS (Jest, Vitest, Testing Library, MSW, Playwright) and Go. Use whenever the user says "audit our tests", "check test quality", "are our tests meaningful", "find coverage gaps", "test smell review", "review the tests for this feature", "are these tests any good", "what's wrong with our test suite", or pastes a repo path / PR diff and asks about testing rigor. Produces a severity-tagged diagnostic report with file:line citations — does not run tests or modify code. Strongly prefer this skill over generic code review for any question that touches test integrity, assertion strength, mock strategy, or coverage adequacy.
---

# Test Coverage Quality Audit

A diagnostic skill. Reads source + test files, produces a severity-tagged report. **Never runs tests, installs deps, or mutates code.**

## What this skill is opinionated about

Line coverage is a noise metric past ~70%. The real questions:

1. **Can these tests actually fail?** (assertion integrity)
2. **Is the business logic testable at all, or buried in HTTP/UI infrastructure?** (architectural)
3. **Are the tests resilient to internal refactors, or coupled to implementation?** (over-mocking, snapshots, internal-module mocks)
4. **Will this suite stay green by accident?** (flake-prone patterns)

Heuristics in `references/detectors.md` are tuned for **statically detectable** signal. Dynamic things (mutation scores, order-dependency, actual coverage %) are accepted as optional user-provided inputs, never inferred.

## Workflow

### 1. Detect intent

The user can invoke this skill three ways. Identify which before reading any code:

| Intent | Signal | Behavior |
|---|---|---|
| **Whole-repo exhaustive** | "audit our tests", "review the test suite", points at repo root | Full sweep, all detector categories, sample large directories |
| **Targeted slice** | Names a directory, feature, PR diff, or set of files | Restrict scope. Skip co-location/structural detectors if scope is just a few files |
| **Topic slant** | "find business logic in controllers", "check for over-mocking", "are our async tests safe" | Run only the relevant detector categories. Skip the rest. |

If ambiguous, ask one short question before proceeding.

### 2. Detect ecosystem

Read these to determine framework + runner — needed to load the right detectors:

- `package.json` → look for `jest`, `vitest`, `@testing-library/*`, `playwright`, `cypress`, `msw`, framework (`react`, `vue`, `next`, `express`, `fastify`)
- `tsconfig.json` → strict mode? noImplicitAny?
- `go.mod` → Go project?
- Test file naming convention: glob for `**/*.{test,spec}.{ts,tsx,js,jsx}` and `**/*_test.go`

Report what you found in the audit Summary section. If the repo is a monorepo, audit each package separately (or ask the user to scope).

### 2a. Architectural awareness — what is this code actually shaped like?

Before applying H7 (business logic in controllers) or N1 (mocked req/res), spend 60 seconds checking what the codebase calls "controllers" and what they actually are. The detector catalog assumes the user's naming reflects the code's shape, which is often false.

Quick checks:

- Open one or two files in `src/controllers/` (or equivalent). Do they import `Request`/`Response` from Express? Do they read `req.body` / write `res.json`? **If no, they're a service layer, not HTTP handlers** — and H7 may not apply. Look further up at `src/routes/` or `src/handlers/` for the actual HTTP boundary.
- If route handlers exist and delegate to controllers via plain payloads (`controller.create(payload, user)`), that's already the *extracted* architecture H7 would recommend. Don't flag H7; instead audit whether the service layer is itself *too fat* (validation + persistence + audit + cache + rollback in one function — see H10).
- **When the user's framing contradicts the architecture, push back in the report.** Open the Summary with the correction: "The premise of the question doesn't match the code: `src/controllers/` are a service layer, not Express handlers." Then audit what's actually there. This is more useful than silently applying detectors against the wrong abstraction.

### 2b. Recognize legitimate mock-server architectures

Before flagging H1 (manual fetch/axios mocking) or N3 (missing MSW), check whether the repo runs an explicit mock-server container/process. Look for:

- A `mock-services/` or `__mocks__/server/` directory containing an Express app
- A `docker-compose.test.yml` that brings up a service exposing mocked endpoints
- A `config/test.js` (or equivalent) that points outbound HTTP at `http://localhost:<port>` or `http://mocks:<port>`

If any of these exist, the codebase has a deliberate mock-server architecture that legitimately substitutes for MSW. Note it in the report as a sound design choice and do not flag absent MSW. The H1 detector still applies for *additional* in-test fetch stubs (those would bypass the mock server).

### 3. Optional inputs

Ask the user (or accept if already provided) whether they have:

- A coverage summary file (`coverage/coverage-summary.json`, `coverage/lcov.info`, or text output). If yes, use it for the **Coverage Gaps** section.
- A Stryker mutation report (`reports/mutation/mutation.json`). If yes, use it for the **Surviving Mutants** section.

If neither is provided, say so explicitly in the report. Do not silently skip.

### 4. Load detector catalog

Read `references/detectors.md` — the full pattern catalog with grep templates, AST hints, severity, and one-line principle citations. This is the core of the skill.

For framework-specific patterns (React act/RTL, Vue Pinia/composables, Node Express/MSW, Go t.Parallel), load `references/frameworks.md` and apply only the sections matching the detected stack.

### 5. Run detection passes

Use `Grep` and `Read` aggressively. For each detector category:

1. Run the grep pattern across the in-scope directory
2. Read suspicious matches in context (the pattern alone is rarely enough — verify it's a true positive)
3. Record file:line + the actual offending snippet
4. Apply the severity rubric below

**Sampling rule for large codebases:** If a detector returns >50 matches in one category, sample diversely (different directories/files) for the top 20 and mention the total count. Do not paginate through hundreds of identical findings.

### 6. Apply severity rubric

| Severity | Definition | Examples |
|---|---|---|
| **🔴 Critical** | Test cannot fail, hides real bugs, or asserts nothing meaningful | Empty test body, tautological assertion, missing await before async assertion, test inside `if` |
| **🟠 High** | Real quality problem that will allow regressions or cause flakes | Manual `global.fetch` mock, fake timer leak, store not reset, business logic buried in controller |
| **🟡 Medium** | Worth fixing, but not actively broken | Snapshot-heavy component test, missing test file for non-trivial module, over-mocked internals |
| **🟢 Low** | Style/consistency observations — only include if user asked for thorough audit | Naming inconsistency, missing `describe` blocks, AAA pattern violations |

**Bias toward fewer, higher-confidence findings.** A finding the user dismisses as a false positive damages trust in the whole report. When unsure, downgrade severity or omit.

**Severity elevation rule — concentration in highest-logic files.** When a Medium finding (missing tests, weak assertions) is concentrated in the largest / most branchy / highest-business-value files in the codebase, elevate it to High or Critical. Example: M2 ("missing co-located test") for ten 50-LOC utility files is Medium. M2 for the 848-LOC rollback orchestrator that no other test covers is Critical. The severity reflects *impact*, not pattern occurrence count.

When you elevate, say so in the finding: `**Severity rationale:** elevated from Medium to Critical because the missing tests are concentrated on the highest-logic files in the directory.`

### 7. Write the report

Follow `references/report-template.md` exactly. Output to stdout (do not write a file unless the user asks).

End the report with **Recommended next 3 actions** — pick the highest-leverage fixes, not just the highest-severity. "Extract `processSubscription` business logic from `routes/billing.ts`" beats "10 snapshot tests are too verbose" even if both are flagged.

## Anti-scope

Do not include in v1:

- Suggested code rewrites or `--fix` mode (diagnostic only — user asked for this explicitly)
- AAA pattern enforcement (too prescriptive, high false-positive rate)
- Coverage tool selection advice (Istanbul vs V8) — that's a config question, not an audit signal
- Order-dependency detection (requires test execution)
- Contract testing presence checks (boring, low signal)
- Mutation testing as a primary heuristic (treat Stryker scores as an optional input, not something we infer)
- Test data builder vs factory style preferences (not a bug)

## Push-back triggers

If the user asks for something that this skill is designed to avoid, push back briefly:

- "Get us to 100% coverage" → Explain why that's an anti-pattern past ~70% and offer to audit *quality* instead.
- "Fix the tests" → This skill is diagnostic only; recommend a follow-up task.
- "Just look at line coverage" → Offer to consume their coverage report and combine it with quality findings.

## Reference files

- `references/detectors.md` — full pattern catalog (load first, in step 4). Severity-prefixed IDs: C1-C5 critical, H1-H10 high (incl. H6b — mocking the dependency the unit exists to wrap), M1-M5 medium, L1-L3 low, S1 suite-wide quantitative ratios.
- `references/frameworks.md` — framework-specific detectors (load on-demand based on stack)
- `references/report-template.md` — exact output format (load before writing the report)
