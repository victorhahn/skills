# Report template

Use this structure verbatim. Skip sections that have no findings rather than printing "None".

---

```
# Test Coverage Quality Audit

**Scope:** <whole-repo | path/to/feature | "business logic detectors only"> 
**Stack:** <e.g., Vitest 1.6, React 18, Testing Library, MSW — Node 20 / Go 1.22>
**Coverage report:** <provided: coverage-summary.json | not provided>
**Mutation report:** <provided: stryker-incremental.json | not provided>
**Files scanned:** <N source, M test>

## Summary

<3-5 sentences max. Lead with the headline. Examples:

"The suite has solid structural discipline — tests co-located, no fake-timer leaks, MSW in use for outbound calls. The dominant risk is **assertion strength**: 14 tautological assertions across 11 files mean a class of logic regressions would not be caught. Secondary concern: 3 route handlers in src/api/billing carry non-trivial business logic that's only tested through HTTP integration paths."

If the result is mostly clean, say so — don't pad with low-severity findings.>

### Suite-wide signals (from detector S1, on exhaustive audits)

One or two lines, only when the numbers are striking. Skip if ratios look healthy. Examples:

- Assertion shape: **256 `toHaveBeenCalled()` (no args) vs 33 `toHaveBeenCalledWith(...)`** — 8:1. Call-shape regressions would not be caught across most of the suite.
- Error-path coverage: **5 `.toThrow` / `.rejects` across 87 test files** — under 1 per 17. Error-wrapping contracts (VError, NotFound, BadRequest) effectively untested.
- `as any` casts in tests: **109 across 14 files** — production type changes won't fail compile against the test corpus.

## 🔴 Critical findings (N)

### [C1] Tautological assertion in `src/services/billing.test.ts:42`

```ts
expect(result).toBeDefined();   // ← only assertion in test
```
Principle: Code coverage measures execution, not correctness. This test will pass for any non-undefined return value, including `null`, `0`, or wrong objects.

**Suggested fix shape:** assert on specific fields of `result` (no rewrite — diagnostic only).

---

<repeat for each critical finding>

## 🟠 High findings (N)

### [H7] Business logic in `src/routes/subscription.ts:23-67`

Route handler imports `db` (Prisma), branches on user tier and project count, returns HTTP errors. ~44 LOC of domain logic embedded in the handler. Tested only via supertest paths in `subscription.test.ts`, which means edge cases (tier transitions, count boundary) require HTTP scaffolding to verify.

Principle: Business logic coupled to HTTP infrastructure can't be tested without mocking the framework; the cost discourages edge-case coverage.

---

<repeat for each high finding>

## 🟡 Medium findings (N)

<Group similar findings when there are many. Example:>

### [M1] Snapshot density above threshold (3 files)

- `src/components/Dashboard.test.tsx` — 8 snapshots, 11 total assertions (73%)
- `src/components/UserCard.test.tsx` — 6 snapshots, 9 total assertions (67%)
- `src/components/Sidebar.test.tsx` — 5 snapshots, 8 total assertions (63%)

Principle: Large DOM snapshots capture implementation details and break on refactors; teams often update blindly.

---

### [M2] Missing co-located tests (12 files, sample shown)

After excluding types/barrels/configs, the following source files have no test sibling:
- `src/services/notification.ts` (87 LOC, exports 4 functions)
- `src/utils/permissions.ts` (52 LOC, exports 3 predicates)
- `src/hooks/useFeatureFlag.ts` (34 LOC, custom hook)
- ... (9 more — full list in detector output)

Principle: Co-located test files provide a static signal of intended coverage; absence flags untested modules.

---

## 🟢 Low findings (N) — included only on thorough audit request

<short bulleted list, one line each>

## Framework-specific observations

<Only when at least one framework-specific finding exists. Group by framework:>

### React + Testing Library
- `[R1]` Heavy use of `data-testid` in `src/components/Forms/` — 23 instances across 7 files. Consider accessible queries (`getByRole`, `getByLabelText`) for ~80% of these.
- `[R2]` `waitFor` with `userEvent.click` inside in `src/components/Modal.test.tsx:88` — side effect inside retry loop.

### Node (Express)
- `[N3]` `supertest` used in `src/api/external.test.ts` but routes call external API without MSW interception — tests are non-deterministic.

## Coverage gaps (only if coverage report provided)

<from coverage-summary.json:>
- Files with 0% coverage: `src/utils/retry.ts`, `src/lib/parse-headers.ts`
- Files with <50% branch coverage: `src/services/billing.ts` (32% branch), `src/auth/permissions.ts` (41% branch)

Aggregate: 76% statement, 68% branch.

## Surviving mutants (only if mutation report provided)

Top files by surviving mutants:
1. `src/services/billing.ts` — 12 surviving (mutation score 54%)
   - Example: `age >= 18` → `age > 18` survived in `canPurchaseAlcohol`
2. `src/utils/dates.ts` — 7 surviving
   - Example: `.filter(d => d > now)` → `.filter(d => true)` survived

## Recommended next 3 actions

1. **<Highest-leverage fix>**, e.g., "Extract billing tier validation from `src/routes/subscription.ts` into a pure function in `src/domain/subscription-rules.ts`. Unlocks edge-case testing without supertest scaffolding."
2. **<Second>**, e.g., "Replace 14 tautological assertions identified above with value assertions. Start with the 4 in `src/services/billing.test.ts` — that file currently has 0% mutation score on the changed code."
3. **<Third>**, e.g., "Add MSW interception to `src/api/external.test.ts`. Currently the test depends on external network and is the most likely source of recent CI flake."

---

## Notes on what this audit did NOT check

<Brief — keep the user honest about scope. Include if any of these are true:>
- Dynamic flakiness (order-dependency, timing-sensitive failures) — requires test execution.
- Actual line coverage — coverage report not provided.
- Mutation strength of individual files — mutation report not provided.
- Visual / accessibility regressions — out of scope.
```

---

## Style rules for the report

- **One finding = one bullet.** Don't merge multiple file:lines into a single bullet unless they're literally the same pattern in the same form. Grouping in M1/M2-style tables is fine.
- **Always cite file:line.** A finding without a location is unactionable.
- **Quote the offending snippet** when it's short (≤3 lines). For longer cases, reference and summarize.
- **Always include the principle.** One sentence. This is what makes the report educational.
- **No fix code.** Diagnostic only. Use "Suggested fix shape:" with a one-line direction if it's not obvious from the principle.
- **Bias toward fewer findings.** A report with 80 medium findings will be ignored. If you have that many, group aggressively and pick the top 10 worth surfacing individually.
- **Never report aggregate coverage % as a finding.** It belongs in the Summary, not as a smell.
