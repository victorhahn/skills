# Specialist Briefs

Each section below is a complete brief for one specialist. When dispatching, copy the relevant section verbatim into the subagent prompt, prepend the recon summary, and add the scope (paths to scan, paths to skip) and compliance context.

All specialists share these rules:
- **Evidence required.** Cite specific files, lines, versions, CVE IDs, measurements, or compliance controls. No speculation.
- **Skip the obvious.** Don't flag missing semicolons, formatting, or anything a linter catches. Don't flag generated files, vendored code, lockfiles, or anything in `.gitignore`-adjacent paths.
- **Use the structured finding format** from SKILL.md.
- **Score honestly.** A Confidence: Med finding is a real signal; a Confidence: Low finding gets dropped. Inflating impact to look thorough wastes the user's time.
- **Modern reference points.** Where applicable, ground findings in widely-accepted modern engineering practice: 12-factor, OWASP ASVS / Top 10, CNCF observability practices, SOC 2 Trust Services Criteria, HIPAA Security Rule (45 CFR §164.308/.310/.312), supply-chain guidance (SLSA, SBOM).

---

## 1. Security & Compliance

**Mission:** Identify security gaps and compliance posture issues with concrete evidence. This specialist always runs, even in focused-mode audits.

**Look for:**

### Security
- **Secrets in code:** API keys, tokens, passwords, private keys committed to the repo or in env templates. Check `.env*`, config files, test fixtures, comments.
- **Dependency CVEs:** vulnerable packages with active CVEs at the installed version. Cite CVE ID and CVSS score. Distinguish reachable vs unreachable vulns when possible.
- **AuthN/AuthZ gaps:** missing auth on routes, broken access control patterns (e.g., user-controlled IDs without ownership checks), JWT misuse (no expiry, no signature verification, alg=none), missing CSRF protection on state-changing routes.
- **Input validation:** untrusted input reaching shell exec, SQL string concatenation, NoSQL injection patterns, unsanitized HTML rendering, deserialization of untrusted data, SSRF risks (user-controlled URLs).
- **Crypto:** use of weak/deprecated algorithms (MD5, SHA-1 for security, DES, ECB mode), hand-rolled crypto, missing TLS verification, weak random sources (`Math.random` for tokens).
- **Secrets management:** secrets in env vars without rotation, no use of a secrets manager (AWS Secrets Manager, Vault) where one is warranted, secrets logged accidentally.
- **Logging hygiene:** PII/PHI written to logs, full request bodies dumped, tokens in URLs that hit access logs.

### SOC 2 (Trust Services Criteria — focus on Security/CC, Availability/A, Confidentiality/C)
- **CC6 (Logical access):** is there an access-control layer? Are admin actions distinguished from user actions? Is there role-based or attribute-based access control?
- **CC7 (System operations):** are there audit logs for sensitive operations (auth, data access, admin changes)? Are they immutable / append-only?
- **CC8 (Change management):** does the repo enforce code review (CODEOWNERS, branch protection signals in CI config)?
- **A1 (Availability):** are there health checks, graceful degradation, retries with backoff?
- **C1 (Confidentiality):** is data classified? Is sensitive data encrypted at rest?

### HIPAA Security Rule (when PHI is in play — confirmed during recon)
- **§164.312(a) Access control:** unique user IDs, automatic logoff, encryption/decryption of ePHI.
- **§164.312(b) Audit controls:** mechanisms to record and examine activity in systems with ePHI.
- **§164.312(c) Integrity:** mechanisms to ensure ePHI is not improperly altered/destroyed.
- **§164.312(d) Person/entity authentication:** verifying identity before access.
- **§164.312(e) Transmission security:** encryption in transit, integrity controls.
- **§164.308 administrative safeguards:** access management, workforce training references in docs.
- **PHI handling specifics:** PHI in logs, PHI in error messages, PHI in URL query strings, PHI in non-prod environments (test fixtures!), retention/disposal logic.

**Skip:** generic "use HTTPS" reminders without evidence the codebase doesn't, theoretical security improvements without a real attack surface, defense-in-depth additions where the primary control is already strong.

**Confidence calibration:** A High-confidence security finding has either a clear exploit path, a real CVE ID, or a clear violation of a named compliance control. Med-confidence means "this is a structural weakness worth fixing but the exploit path isn't obvious without runtime context."

---

## 2. Dependencies & Supply Chain

**Mission:** Find dependency-related liabilities and modernization opportunities with real payoff.

**Look for:**
- **Vulnerable packages with active CVEs** at the installed version. Cross-check against `npm audit`, `go list -m -u all`, `pip-audit`, Wiz/Snyk output if present.
- **Unmaintained packages:** last release >2 years ago, archived repos, single-maintainer projects with no recent activity, packages whose function is now in std lib.
- **Unused dependencies:** packages declared but never imported. Run with `depcheck`, `knip`, or equivalent if available; otherwise grep imports.
- **Deprecated transitives** pinned by direct deps — flag the direct dep as needing an update.
- **Version drift across a monorepo:** the same package at multiple versions across workspaces (causes bundle bloat, divergent behavior).
- **Lockfile hygiene:** missing lockfile, lockfile out of sync with manifest, lockfile committed but `package-lock=false` style configs in place.
- **SBOM gaps:** no SBOM generation in CI for projects that ship binaries or images.
- **Supply-chain controls:** unverified package sources, missing `npm ci` / `pip install --require-hashes`, no Dependabot/Renovate, missing CODEOWNERS.

**Skip:** "version X.Y is one minor behind latest" with no concrete reason. Dep updates are only meaningful when they unlock a feature, patch a CVE, drop maintenance, or remove an unmaintained package.

**Modern reference points:** SLSA framework levels, npm provenance, Sigstore.

---

## 3. Test Coverage & Quality

**Mission:** Identify gaps in test coverage that genuinely threaten regression safety, and test patterns that are creating maintenance drag. Treat test coverage as a *first-class quality fundamental*: it is the investment the team makes in being able to change the code with confidence — including refactors, dependency bumps, framework migrations, and AI-agent-authored PRs. A codebase with thin coverage on critical paths cannot be safely modernized; coverage gaps therefore directly bottleneck most other improvements on this audit. Findings here often warrant elevated Impact (3+) because they unlock everything downstream.

**Framing for scoring:**
- A coverage gap on a load-bearing critical path is **not** "we should write more tests someday" — it is "this code cannot be safely changed right now". Score it accordingly.
- Tier-1 wins in this category are almost always "add the missing test *before* doing the risky thing it would have protected." Make this explicit in the rollout plan: tests-first sequencing.

**Look for:**

### Coverage of load-bearing paths (highest priority)
- **Critical paths with no coverage:** auth flows, payment/checkout flows, PHI access paths, data-mutating endpoints, anything in the request path of an SLO, anything where a regression would page someone or expose data. Read the coverage report if one exists; otherwise sample by tracing requests through the code.
- **Critical paths with only happy-path coverage:** the success case is tested, but error / timeout / partial-failure / auth-rejected / rate-limited branches are not.
- **Migration-blocking gaps:** code that the team is likely to want to refactor or upgrade soon (e.g., framework on EOL trajectory, deprecated APIs in heavy use) and where current coverage would not catch a behavior change introduced by the migration. Call these out explicitly — they directly bottleneck modernization findings elsewhere in this audit.

### Test integrity
- **Brittle / over-mocked tests:** tests that mock the unit under test, snapshot tests on volatile output, tests asserting implementation details (call counts, internal method invocation). These pass while production breaks.
- **Missing real integration tests:** services with only unit tests, no end-to-end on the happy path, no test against a real DB / real network / real queue where prod behavior depends on it. Mocks substituted for real integration tests is a well-known anti-pattern — mocks pass while the real boundary (DB migration, network protocol, queue semantics) breaks in production. Flag this aggressively when seen.
- **Contract tests at service seams:** for services that integrate with others, are there contract tests (Pact, consumer-driven, or even golden-file shape tests) that would catch a breaking schema change?

### Suite health (trust and iteration speed)
- **Flaky tests:** `.skip`, `xfail`, retry decorators, time-based assertions, ordering-dependent tests, tests using `sleep()`, tests that depend on wall-clock or environment. A flaky suite is worse than no suite — it teaches engineers to ignore failures.
- **Slow suites:** test runs that take long enough that engineers stop running them locally. CI pipelines where the test stage gates iteration speed unnecessarily.
- **Missing tiers:** no separation between fast unit tier and slower integration tier; CI runs everything every time even when only docs changed.
- **Fixture / factory chaos:** every test inlines setup, no shared factories, lots of duplicated mock data drifting between tests.

**Output extras (these should always appear if findings exist):**

1. **Top 3-5 uncovered critical paths** with a one-paragraph sketch of the minimum first test for each. This makes Tier 1 wins immediately actionable.
2. **Migration-blocker map:** explicitly list each modernization / refactor finding elsewhere in this audit that requires a coverage addition first, naming the test that needs to exist before that work can safely begin.

**Skip:**
- Demanding 100% line coverage. Coverage is a means, not an end. Don't flag "this util is at 70% coverage" without identifying which uncovered branch matters.
- Flagging missing tests on deprecated code slated for removal.
- Coverage on trivial getters/setters or framework-generated code.

**Modern reference points:**
- The test pyramid (lots of fast unit, fewer integration, even fewer E2E) — but a healthy pyramid means *real* integration tests at the middle, not unit tests in costume.
- Behavior-driven / spec-driven tests over implementation-coupled tests.
- Hermetic tests — no shared mutable state, deterministic ordering.
- Contract tests for service boundaries.
- Test coverage as an enabler of migration: the canonical sequence is *characterization tests first, then refactor, then rerun*. See `welc-legacy-code` patterns.

---

## 4. Code Quality

**Mission:** Find code that is genuinely harder to work with than it should be, with evidence.

**Look for:**
- **Dead code:** unreferenced exports, files with no imports, feature flags that are permanently on/off, commented-out blocks older than 6 months. Use grep / `ts-prune` / `knip` / `unimport` style analysis.
- **Duplication:** copy-paste blocks across modules (>20 lines, >2 sites). Note: small duplication is often correct; only flag when the duplication clearly hides a missing abstraction.
- **Complexity hotspots:** functions with cyclomatic complexity > ~15, files with > ~500 lines and high churn, deeply nested conditionals (>4 levels). Cite the actual metric where possible.
- **Local type-safety smells:** in-module `any`, unsafe casts, missing generics in shared utilities. (Boundary type safety and contract drift belong to the **Type Safety & Data Contracts** specialist — defer to them on those findings.)
- **Inconsistent error handling:** mix of throw/return/Result types within the same module, silently-swallowed errors, generic `catch(e) {}`, `panic` in library code.
- **Boundary leakage:** business logic in controllers/handlers, DB calls in domain models, framework concerns leaking into core logic.
- **God objects / files:** modules with >10 unrelated responsibilities, classes with >20 public methods, "utils" files that have grown into junk drawers.

**Skip:** style preferences, naming preferences without a clarity argument, "this could be more functional / more OOP", refactors that don't measurably reduce complexity, duplication that exists for good reasons (testability, decoupling).

**Modern reference points:** "A Philosophy of Software Design" (deep modules), Domain-Driven Design boundaries, hexagonal/clean architecture concerns, type-driven development.

---

## 5. Type Safety & Data Contracts

**Mission:** Identify gaps in end-to-end type safety and data-contract consistency. This is treated as a first-class quality dimension, not a stylistic preference — drift between hand-maintained types and the runtime contract is a recurring source of production bugs and a primary class of error introduced by AI agents working in unfamiliar code. Findings here often warrant elevated Impact (3+) because the cost compounds over time.

**Look for:**

### Sources of truth
- **Hand-maintained types where a generator exists.** OpenAPI specs that exist but whose types are duplicated by hand. Database schemas where ORM types are hand-maintained instead of introspected. Protobuf definitions whose Go/TS structs are typed by hand. GraphQL SDL with hand-written client types. Each of these is a drift waiting to happen.
- **Missing single source of truth.** No schema for the HTTP API, no SDL for GraphQL, no migration-derived types for DB. The codebase is implicitly defining contracts in multiple places.
- **Stale generated artifacts.** Generated clients/types committed but the generator script hasn't been run in months. The artifact disagrees with the upstream schema.

### Boundary type safety
- **Untyped network boundaries.** `fetch().then(r => r.json())` returning `any`, then propagating through code without validation. No runtime parsing (Zod, io-ts, valibot, pydantic) at the seam.
- **Untyped queue / event boundaries.** Kafka/SQS/EventBridge consumers that accept `any` and read fields with bracket notation.
- **Untyped DB results.** Raw SQL with hand-typed result shapes, ORMs with `unknown` returns, or types that don't match nullability of the schema.
- **Untyped third-party SDK boundaries.** `(externalLib as any).doThing()` patterns, missing type stubs, hand-rolled `.d.ts` shims.

### Domain consistency across services
- **One concept, multiple shapes.** The same domain entity (User, Order, Event) defined differently in each service, with subtle field differences. Especially dangerous when services serialize to each other.
- **Inconsistent nullability/optionality.** A field marked optional in one service and required in another that consumes it.
- **String-typed enums and IDs.** "status" as a free-form string instead of a literal union; UUIDs and entity IDs all typed as `string` with no branded/nominal typing where it would catch real mistakes.

### Escape hatches and erosion
- **`any` outside the true edge.** A controlled `any` at an external boundary is fine if it's immediately parsed into a typed shape. `any` propagating into business logic is a finding.
- **`as` casts that bypass checking.** Especially `as unknown as T`. Each is a place the type system stopped helping.
- **Disabled type checks.** `@ts-ignore`, `@ts-expect-error` without explanation, `// type: ignore`, large swaths of `// eslint-disable @typescript-eslint/no-explicit-any`.
- **Type coverage tooling missing or unused.** Projects with `tsc --noEmit` in CI but `strict: false`, or `strictNullChecks: false`. Python projects without `mypy`/`pyright` in CI. Go projects with `interface{}`/`any` in domain code.

### Modern reference points
- **Contract-first development** — schema is source of truth; code is downstream.
- **Type-driven development** — make illegal states unrepresentable.
- **Parse, don't validate** — types should encode that something has been checked.
- **End-to-end type safety as a default.** Generate types from schemas (OpenAPI, Zod, Protobuf) rather than maintaining parallel hand-written definitions. Prefer type-safe generated clients over hand-rolled fetch wrappers.

### Skip
- Stylistic type preferences (interface vs type alias, etc.) — these are linter concerns, not audit findings.
- Demanding 100% strictness on legacy modules without a migration path — call out the cost/benefit honestly.
- Type changes that improve theoretical safety but break ergonomics with no real bug history — note them as Tier 3 with low priority.

### Confidence calibration
- **High confidence:** named schema exists, generator exists, but types are hand-maintained AND a drift is visible (or has caused an incident). Or: untyped `JSON.parse` reaching business logic. Or: domain entity has visibly different shapes across services.
- **Med confidence:** structural anti-pattern is present (e.g., `any` at boundaries) but no specific drift incident cited yet.

---

## 6. Modernization

**Mission:** Find modernization opportunities that produce real payoff — not migrations for migration's sake.

**Look for:**
- **Language version features unused:** code on a recent runtime but not using features that would simplify it (e.g., Node 20+ with hand-rolled fetch wrappers, TS 5+ with `as const` opportunities, Go 1.21+ without `slices`/`maps` packages, Python 3.11+ without `match`/`ExceptionGroup`).
- **Deprecated APIs in active use:** framework APIs marked deprecated in the installed version, scheduled-for-removal patterns.
- **Std-lib replacements for third-party deps:** native `fetch` replacing `axios`/`node-fetch`, native `crypto` for simple cases, `Intl` for date/number formatting, etc. Prefer built-in over third-party where capability is equivalent — fewer deps means less CVE surface and less cleanup later.
- **Framework upgrade opportunities** with real payoff: not "Vue 2 → Vue 3 because newer", but "Vue 2 reaches EOL on date X" or "upgrading unlocks a feature the team has been waiting on".
- **Build/tooling modernization:** Webpack → Vite where iteration speed matters, ESLint+Prettier → Biome, Jest → Vitest, etc. Flag only when the team would benefit, not on principle.
- **Infrastructure as code modernization:** outdated Terraform module versions, deprecated AWS APIs, hand-rolled patterns where modules now exist.

**Skip:** "X is the new hotness" without a concrete payoff. Migrations whose effort exceeds payoff by an order of magnitude. Breaking changes to public APIs unless there's a strong reason.

**Cite:** the current version, the target version, the specific feature/fix that justifies the move, and an estimate of effort.

---

## 7. Performance

**Mission:** Find performance issues that *matter* — backed by measurement, profile data, or structural anti-patterns.

**Look for:**
- **Profile data signals:** if APM (Datadog, New Relic, Honeycomb, etc.), flamegraphs, or other profile data is available, use it. Query telemetry rather than speculating about hot paths.
- **Database anti-patterns:** N+1 queries, missing indexes (cross-reference against query patterns), full-table scans on hot paths, no pagination, unbounded result sets.
- **Hot-path I/O patterns:** synchronous I/O in request handlers, blocking calls in event loops, missing connection pooling, missing caching where access patterns warrant it.
- **Bundle weight (frontend):** large dependencies with smaller alternatives, missing code-splitting, dependencies imported in full when tree-shakeable, missing dynamic imports for rare paths.
- **Memory issues:** unbounded caches, listener leaks, big arrays held longer than needed, large object allocations in hot loops.
- **Concurrency anti-patterns:** missing parallelism on independent work, over-parallelism saturating connection pools, serial fan-out where fan-out-then-gather would work.

**Skip:** micro-optimizations without measurement (`++i` vs `i++`), speculative caching where the cache cost exceeds the win, "this could be O(n) instead of O(n log n)" when n is small.

**Cite:** the measurement (latency, throughput, memory, bundle bytes) where possible. If no measurement is available, name the anti-pattern explicitly and explain when it bites.

**Modern reference points:** USE method, RED method, p99 over averages, profile-driven optimization.

---

## 8. Standards, Patterns & Agentic Readiness

**Mission:** Treat codebase-wide standards and patterns as a first-class quality fundamental. Strong, consistently-applied patterns make every future change cheaper; pattern drift compounds into a tax on every change. This specialist's primary job is to find places where the codebase is **snowflaking** — implementations that unnecessarily deviate from a pattern that could emerge — and to propose convergence as iterative work. The secondary job is agentic readiness: the docs, ground-truth surfaces, and explicit-intent code that let engineers and AI agents navigate the codebase safely.

**Operating mindset:** Be opinionated but humble. The goal is not to impose a foreign pattern — it's to surface the pattern that's *already trying to emerge* in the codebase and propose that the outliers converge to it. The canonical implementation is usually already in the repo; the specialist just has to name it.

**Look for:**

### Snowflake detection (primary mandate)

A snowflake is a unique-for-no-reason implementation of work that has already been done elsewhere in the repo. Look in particular at:

- **Cross-cutting concerns done multiple ways:** date/time handling, pagination, retry logic, error wrapping, input validation, config loading, feature-flag access, logger setup, HTTP client construction, queue/event publishing, DB transaction handling.
- **The same external API called from multiple places** with different patterns (one place uses a generated client, another hand-rolled fetch with custom error handling, a third uses an unrelated library).
- **Multiple test-fixture / factory styles** for the same domain entity.
- **One-off utilities that duplicate library or std-lib functionality:** custom `deepEqual`, custom `groupBy`, custom URL parsing, custom UUID generation.
- **Repeated boilerplate that a small helper would collapse**, when the helper is *not* a premature abstraction — i.e., the duplicated logic genuinely is the same, not just superficially similar.

For each snowflake finding, the output must:
1. **Name the pattern** that could emerge (e.g., "all DB transactions should go through `withTx` in `db/tx.ts`").
2. **Identify the canonical implementation** already in the repo (or note that one needs to be chosen / extracted).
3. **List the outliers** with file/line refs.
4. **Score the convergence work**, usually as Tier 2 or Tier 3 — convergence requires care to avoid regressions and rarely qualifies as a Tier 1 quick win unless the snowflake is small and self-contained.
5. **Be explicit about cost/benefit.** A snowflake that's painful to maintain or a frequent source of bugs justifies convergence. A snowflake in a stable backwater might be best left alone — flag it but score Impact honestly.

### Pattern consistency more broadly

Beyond pure snowflakes, look at conventions that have drifted across the codebase even though no single occurrence is "wrong":
- **Naming:** mixed case styles for the same kind of thing (handlers, types, files), inconsistent module/file naming patterns.
- **Async patterns:** mix of callbacks / promises / async-await within the same code generation, mix of Promise.all vs sequential awaits with no clear rule.
- **Config strategy:** env vars in some places, JSON/YAML files in others, hardcoded constants in a third, no documented "where does configuration live" rule.
- **Logging:** multiple logger libraries, inconsistent log levels, inconsistent structured-vs-unstructured choices.
- **Error handling:** mixed throw / return-Result / callback-error / panic styles within the same domain.
- **Folder structure:** comparable concerns organized differently across the repo (e.g., one service uses `domain/` `infra/` `http/`, another flat).

### Standards enforcement

Patterns only stay healthy if they're enforced. Look at:
- **Lint / format / type-check config:** is there a single source of truth (Biome, ESLint+Prettier, golangci-lint, Ruff, mypy/pyright)? Is it consistently configured and enforced in CI on every PR? Are `eslint-disable` / `@ts-ignore` / `nolint` exceptions documented or scattered?
- **Custom lint rules / codemods:** for patterns that matter, is there a programmatic enforcement (custom ESLint rule, `dependency-cruiser`, `arch-unit`-style boundary checks) — or is enforcement entirely cultural?
- **CI gates:** does CI block PRs that violate the standards, or are violations advisory? Are there CODEOWNERS for sensitive surfaces?
- **Branch protection signals:** is `main` protected? Are reviews required?

### Explicitness of intent

Code that says what it means without making the reader reverse-engineer it. Look for:
- **Magic values that should be named constants or enums** — string literals scattered through code that represent a closed set.
- **Boolean parameters that hide intent** — `fetchUser(id, true, false)` patterns where the booleans should be named options.
- **Implicit assumptions in code** that would be a one-line explicit check — preconditions, invariants, expected shapes.
- **Cleverness that obscures intent** — heavy chaining, one-liners that pack three operations, point-free style where named steps would read better.

### Agentic readiness (supporting concerns)
- **CLAUDE.md / README accuracy:** is there a CLAUDE.md? Is it accurate to the current code? Does it cover non-obvious workflows (run tests, deploy, common tasks)? Does it lie? An out-of-date doc is worse than no doc.
- **Module boundaries:** can a new engineer (or agent) tell which files own which concerns? Are there clear public surfaces, or is everything implicitly public?
- **Ground-truth surfaces:** OpenAPI specs, Protobuf definitions, DB schemas, JSON schemas — are they checked in, current, and authoritative? Or scattered/stale? (Coordinate with the Type Safety & Data Contracts specialist; don't double-report.)
- **Comments rot:** comments that disagree with the code, `TODO` with no owner/date older than 6 months.

**Skip:**
- Stylistic preferences with no maintenance impact (tabs vs spaces — that's the linter's job).
- "This could be more idiomatic" without a concrete pattern in the codebase to converge toward.
- Demands for more comments for their own sake. Comments are worth flagging only when accuracy or ground-truth is at stake — well-named code is the better default.
- Renaming things to follow some external "best practice" naming convention when the repo already has an internally consistent (if unusual) convention.

**Modern reference points:**
- Contract-first development.
- "Make illegal states unrepresentable" — patterns should mechanically prevent the wrong thing.
- "There should be one — and preferably only one — obvious way to do it" (Zen of Python).
- Architectural fitness functions — automated enforcement of pattern conformance.
- "Documentation is a hint, not ground truth" — but ground-truth surfaces (schemas, types, generated clients) need to be authoritative.

---

# Domain Fan-out Patterns

When the user requests a focused audit (Mode B), replace the relevant single specialist with a fan-out of 3-5 sub-specialists. Each sub-specialist has a narrower lens within the domain. Below are templates — adapt to context.

## Performance fan-out
- **DB & I/O:** N+1, missing indexes, sync I/O, connection pooling, serialization overhead
- **Hot-path CPU:** profile-driven, algorithmic complexity in hot loops, regex/JSON parse hotspots
- **Memory & GC:** unbounded caches, leaks, large allocations, GC pressure signals
- **Concurrency:** parallelism opportunities, thread/goroutine misuse, lock contention
- **Frontend bundle & runtime:** bundle size, code-splitting, render performance, large dep audit
- **Network / API:** payload size, missing compression, missing caching headers, chatty APIs

## Security fan-out
- **AuthN/AuthZ:** session, token, RBAC/ABAC, ownership checks
- **Injection & input validation:** SQL/NoSQL/command/template injection, deserialization, SSRF
- **Cryptography & secrets:** algorithm choices, key management, secret leakage
- **Dependency CVEs & supply chain:** vulnerable packages, SBOM, signed builds
- **Cloud / IAM posture:** overly broad IAM policies, public S3, missing network segmentation (if Terraform/IaC present)
- **Logging & data handling:** PII/PHI in logs, error-message info leaks, debug endpoints in prod

## Compliance fan-out (HIPAA / SOC 2)
- **Access control:** identity, authentication, authorization, automatic logoff
- **Audit logging:** what's logged, where, retention, immutability, alerting
- **Encryption:** at rest (DB, object storage, backups), in transit (TLS versions, cert handling)
- **Data handling:** classification, PHI/PII tagging, retention, disposal, non-prod data hygiene
- **Change management & SDLC:** code review enforcement, branch protection, deployment controls
- **Availability / incident response:** health checks, runbooks, on-call references in repo

## Modernization fan-out
- **Language/runtime:** version-current features, deprecated APIs
- **Framework:** upgrade path, EOL exposure, capability unlocks
- **Tooling:** build, lint, test runner, package manager
- **Patterns:** outdated idioms with measurable replacement (e.g., callbacks → async/await)
- **Infra/IaC:** module versions, deprecated cloud APIs

## Tests fan-out
- **Coverage gaps on critical paths**
- **Brittle / over-mocked patterns**
- **Missing integration & contract tests**
- **Flaky tests & infrastructure**
- **Performance: slow tests blocking iteration**

## Quality fan-out
- **Dead code & feature-flag debt**
- **Complexity hotspots**
- **Type-safety holes**
- **Error handling consistency**
- **Module boundaries & coupling**

---

# Final notes for all specialists

You are not trying to be exhaustive. You are trying to surface the **highest-value real findings** that a competent senior engineer would identify if they had a day to look. If you only have three findings, return three findings. If you have twenty, return your top ten and note the rest in a "ruled out / lower priority" tail with one line each.

Your audience is the orchestrator, who will deduplicate and rank. Your job is signal density — not volume.
