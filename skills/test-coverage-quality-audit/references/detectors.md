# Detector Catalog

Each detector below: **what to look for**, **how to find it** (grep/AST), **severity**, **principle** (one line — for the report). Apply with judgment, not regex purity.

A grep hit is a *candidate*, not a finding. Always read the surrounding context before recording it.

---

## Critical — tests that can't fail

### C1. Tautological assertions

Tests that pass regardless of correctness. The classic failure mode that produces "100% coverage, 0% confidence."

**Patterns to grep:**
```
expect\([^)]+\)\.toBeDefined\(\)\s*[;}]
expect\([^)]+\)\.toBeTruthy\(\)
expect\(typeof [^)]+\)\.toBe\(['"](?:boolean|string|number|object)['"]\)
expect\([^)]+\)\.toEqual\(expect\.anything\(\)\)
expect\([^)]+\)\.toBeInstanceOf\(Object\)
expect\([^)]+\)\.not\.toBeNull\(\)\s*[;\n]+\s*expect\([^)]+\)\.not\.toBeUndefined\(\)
```

**Verify before flagging:** A single `toBeDefined` *near* other meaningful assertions in the same test is fine. The smell is when it's the **only** assertion in the test body.

**Special case — `undefined === undefined` identity tautology:** When you see `expect(foo.bar).toBe(mockObj.someFn())` and `someFn` is a bare `jest.fn()` with no `mockReturnValue` configured, both sides resolve to `undefined`. The assertion compares undefined to undefined and passes regardless of whether `foo.bar` is ever assigned. To verify: find the mock factory for `mockObj`, check whether the called method has a `.mockReturnValue` / `.mockImplementation` anywhere in the file. If not, flag as Critical.

```ts
// In the test setup:
const mockProvider = { getMeter: jest.fn(), shutdown: jest.fn() };  // no return values
// Later, in a test:
expect(metric.meter).toBe(mockProvider.getMeter());  // undefined === undefined, always passes
```

**Principle:** "Code coverage measures execution, not correctness. Assertions that always pass — including identity checks between two undefined values — let logic errors through undetected."

---

### C2. Missing await on async assertions

Test resolves before the assertion runs; runner reports pass.

**Patterns:**
```
expect\([^)]+\)\.resolves\.    # must be returned or awaited
expect\([^)]+\)\.rejects\.
```

**Verify:** Check that the line is preceded by `await` or `return`. Floating `expect(promise).resolves.toBe(...)` is the bug.

Also flag async test bodies that contain `.then(...)` chains with assertions but no `return` on the chain.

**Principle:** "Unawaited promises let test functions complete before assertions execute — the runner sees no failure."

---

### C3. Empty test bodies / no expect

Test exists but never asserts.

**Patterns:**
```
(test|it)\([^,]+,\s*(?:async\s*)?\(\)\s*=>\s*\{\s*\}\s*\)   # empty body
```

Then for non-empty test bodies, count `expect(` occurrences inside each `test`/`it` block. Zero = flag.

**Verify:** Some test files use a custom `expect`-like helper. Read the file to confirm. Setup-only blocks marked `it.skip` or `it.todo` are fine — don't flag.

**Principle:** "A test body without assertions executes code but verifies nothing."

---

### C4. Tests gated behind runtime conditions

```
if\s*\(\s*process\.env\.|if\s*\(\s*__DEV__\s*\)\s*\{\s*(?:test|it|describe)\(
```

Tests inside conditionals run inconsistently — silently skipped in CI without showing as skipped.

**Principle:** "Conditionally-defined tests appear absent rather than skipped, hiding their non-execution."

---

### C5. Assertions against own-mock-fixture shape

When a test mocks a function via a hand-written stub (in `__mocks__/` or via `jest.mock(...)` with a factory) and then asserts on a property that the stub *always returns by construction*, the test cannot detect bugs in the function under test — it's checking that the mock returns the mock.

**Pattern shape:**

```ts
// __mocks__/read.js produces objects of shape { sourceId, accountId, ... } unconditionally
jest.mock('../../../src/models/shared/read');

const result = await sourcesCtrl.create(payload, testUser);
expect(result).toHaveProperty('sourceId');  // ← always true; mock always returns sourceId
expect(logsModel.create).toHaveBeenCalled();
```

**How to detect:**
1. Find tests using `toHaveProperty(<key>)`, `toHaveLength(N)`, `.not.toBeNull()` as the *only* return-value assertions on a mocked call chain.
2. Read the mock factory. If the mock unconditionally returns objects containing `<key>`, flag.
3. Especially flag when the function under test is supposed to *transform* the returned value but the assertion only checks a key the mock already provided.

**Severity:** Critical when concentrated (e.g., entire controller/model test directories follow this pattern). Medium for isolated occurrences.

**Principle:** "Assertions against mock-fixture shape verify the mock, not the unit under test. A regression that returns the mock unchanged still passes."

**Suggested fix shape:** assert on what the unit *adds*, *removes*, or *transforms* from the mock return — not on what the mock already contains.

---

## High — real quality problems

### H1. Manual fetch/axios mocking instead of MSW

Brittle, drift-prone, doesn't exercise the real HTTP stack.

**Patterns:**
```
global\.fetch\s*=\s*(?:jest|vi)\.fn
window\.fetch\s*=
(jest|vi)\.mock\(['"]axios['"]\)
fetchMock\.|nock\(
```

**Verify:** Check whether `msw` is in `package.json`. If yes, this is a clear smell. If no, downgrade to Medium — they haven't adopted MSW yet, which is itself a recommendation.

**Principle:** "Manual network mocks bypass the application's HTTP stack and drift from real responses; MSW intercepts at the network layer."

---

### H2. Fake timer leak

`useFakeTimers()` without paired cleanup leaks into subsequent tests.

**Patterns:**
```
(jest|vi)\.useFakeTimers\(
```

**Verify:** In the same file, look for `useRealTimers` in an `afterEach`/`afterAll`. If absent, flag. Also flag if `useFakeTimers` is at top-of-file (outside any hook) without a teardown.

**Principle:** "Fake timers mutate global clock state; without explicit restore, later tests inherit the mocked clock and behave non-deterministically."

---

### H3. Store/global state not reset

#### Pinia
```
useUserStore|useAuthStore|defineStore
```
Confirm by checking for `setActivePinia(createPinia())` inside a `beforeEach` in test files that consume the store.

#### Redux / Zustand
Look for store imports in tests without a reset between tests (`store.dispatch({type:'RESET'})`, `useStore.setState(...)`, `store.$reset()`).

**Principle:** "State persisting across tests creates polluter→victim chains; order changes cause spurious failures."

---

### H4. Manual `act()` wrapping in RTL

```
act\(\s*\(\s*\)\s*=>\s*\{\s*render\(
act\(\s*\(\s*\)\s*=>\s*\{\s*(?:user|fire)Event
```

RTL wraps these automatically. Manual wrapping is redundant — either harmless noise or signals confusion about async flow.

**Principle:** "React Testing Library wraps render and userEvent in act() automatically; manual wrapping adds noise or masks real async timing issues."

---

### H5. `test.concurrent` with shared state

```
(test|it)\.concurrent
```

**Verify:** In the same file, look for `(jest|vi)\.mock`, `beforeEach`, shared module-level variables. If present, the concurrent tests share state across goroutine-like execution — race conditions.

**Principle:** "Concurrent tests share the file's module context; mocks and lifecycle hooks don't interleave per-test, allowing race conditions."

---

### H6. Over-mocking of internal modules

```
(jest|vi)\.mock\(['"](\.\.?/|@/|~/)
```

Mocking your own code couples tests to internal structure and decays as the real implementation changes (mock drift).

**Verify before flagging:** Internal mocks for *boundaries* (your `./db`, `./logger`, `./external-api-client`) are reasonable. Internal mocks for *utility functions* or *domain logic* are the smell. Read the mock target file and judge.

**Principle:** "Mocks of internal modules silently drift from real implementations; tests stay green while production fails."

---

### H6b. Mocking the dependency the unit exists to configure

The sharper sibling of H6. When a module's *only purpose* is to wire up a third-party SDK (e.g., `Metric.ts` exists to configure OpenTelemetry's `MeterProvider`; `controllers/sources.js` exists to call DynamoDB's shared read/create/update/delete), mocking that SDK collapses the test into "did we call the constructor we wrote." It verifies wiring shape, not behavior.

**Detection:**
1. Identify the source file's primary dependency by reading its imports — is it a thin adapter over one SDK / shared layer?
2. Check whether the test file mocks that exact dependency at the module level.
3. If yes, examine the assertions. If they're predominantly `toHaveBeenCalled` / `toHaveBeenCalledWith(...)` on the mocked SDK rather than assertions on observable post-conditions, flag.

**Examples found in real codebases:**
- `Trace.ts` exists to configure `@opentelemetry/sdk-trace-base`. The test mocks all of `sdk-trace-base` and asserts the providers were constructed. A regression that wires the wrong span processor passes.
- `controllers/sources.js` exists to call `Source.create`/`Source.read`. The test mocks `models/shared/{create,read,update,delete}` and asserts a property exists on the return. A regression that skips validation passes.

**Severity:** High — often Critical when the entire affected test tier follows this pattern (the resulting "test count" is misleading).

**Principle:** "When a unit's purpose is to wire up a dependency, mocking that dependency leaves only the wiring shape under test — not the wiring's correctness."

**Suggested fix shape:** keep the SDK's *exporters* / *I/O boundaries* mocked (real boundaries) and let the SDK itself run. Assert on what the real SDK does when configured correctly (e.g., `InMemorySpanExporter` collecting the expected spans; in-memory test double of the shared layer).

---

### H7. Business logic in controllers/components

The highest-value finding and the highest-risk for false positives. **Conservative threshold required.**

Flag a route handler or React/Vue component as a candidate only when **all three** hold:
1. Imports a DB client / ORM (`db`, `prisma`, `drizzle`, `knex`, `mongoose`, `pg`, `mongodb`) or makes raw fetch/HTTP calls
2. Contains ≥2 conditional branches (`if`, `switch`, ternaries with logic)
3. Handler/component body is ≥20 LOC

Otherwise: do not flag.

**Heuristic grep starting points:**
```
# Express/Fastify handlers
(app|router)\.(get|post|put|patch|delete)\(['"][^'"]+['"],\s*(?:async\s*)?\(req,\s*res\)\s*=>
async function \w+\(req:\s*Request,\s*res:\s*Response\)

# Then check imports in same file for db/orm
```

**Principle:** "Business logic coupled to HTTP/UI infrastructure can't be tested without mocking the framework; the cost discourages edge-case coverage."

---

### H8. `any` and unsafe casts in tests

```
:\s*any\b|as\s+any\b|as\s+unknown\s+as\s+
```

Restrict to `**/*.{test,spec}.{ts,tsx}` files. Type assertions in tests defeat the purpose of typed mocks and let production type errors slip in.

**Verify:** Sometimes `as unknown as X` is the only way to mock a partial object. The smell is volume — flag the file if >3 such casts.

**Principle:** "Type assertions in tests sever the link between mocks and real types; production type changes don't fail tests."

---

### H9. Go — loop var not captured before t.Parallel

```
for\s+\w+,\s+\w+\s*:=\s*range\s+\w+\s*\{[^}]*t\.Run
```

In the body, check for `tt := tt` (or whatever the loop var is) before `t.Run`. If `t.Parallel()` is called inside `t.Run` and no capture line exists, flag.

Note: Go 1.22+ fixed loop variable scoping. Check `go.mod` for `go 1.22` or later before flagging — if the project is on 1.22+, this is no longer a bug.

**Principle:** "Pre-Go-1.22 loop variables share scope across iterations; concurrent subtests all reference the final element without an explicit capture."

---

### H10. Silently-swallowed catch-block contracts are untested

When a service-layer module wraps a non-critical side effect (audit log, cache refresh, metrics emission, telemetry) in a `try/catch` that logs and continues instead of rethrowing, the implicit contract — "the main operation succeeds even if this side effect fails" — is testable behavior. Usually it's *not* tested.

**Pattern shape:**

```ts
async function update(payload, userEmail) {
  const result = await Model.update(payload);
  try {
    await logCtrl.saveLog({ ... });  // ← contract: never aborts update
  } catch (err) {
    log.verror(err, '[controllers.X.update] failed to write audit log');
    // swallowed
  }
  try {
    await cache.refresh(payload.sourceId);  // ← same contract
  } catch (err) { log.verror(err, '...'); }
  return result;
}
```

**Detection:**
1. Grep for `catch` blocks in `src/controllers/`, `src/services/`, `src/lib/` that contain logging calls but no `throw`.
2. For each, look in the corresponding test file for a test that makes the swallowed call (e.g., `logCtrl.saveLog`) reject and asserts the outer function still resolves with the expected result.
3. If no such test exists, flag.

**Severity:** High when the swallowed effect is observable in production (audit-log loss, stale cache, missing telemetry). Medium when the failure is purely internal.

**Principle:** "A `try/catch` that intentionally swallows an error is a documented behavior. Behaviors that aren't tested aren't behaviors — they're accidents waiting to drift."

**Suggested fix shape:** add one negative test per swallowed catch: force the inner call to reject, assert the outer function still resolves correctly, assert the error was logged at the expected level.

---

## Medium — worth fixing

### M1. Snapshot density

```
toMatchSnapshot\(|toMatchInlineSnapshot\(
```

Count occurrences per file. For React/Vue component tests:
- Files with `toMatchSnapshot` ratio >50% of total `expect` calls → flag
- Files with >5 snapshots covering complex DOM trees → flag

**Verify:** Small, stable snapshot of a serialized config object is fine. The smell is large DOM snapshots that break on any markup change.

**Principle:** "Large DOM snapshots capture implementation details, break on refactors, and are updated blindly — masking real regressions."

---

### M2. Missing co-located test file

For each source file in scope, check if a sibling test file exists matching `<name>.{test,spec}.{ts,tsx,js,jsx}` or a `__tests__/<name>.{test,spec}.*`.

**Exclusions (do not flag):**
- Type-only files (`*.d.ts`, `types.ts`, `*.types.ts`)
- Barrel files (`index.ts` that only re-exports)
- Config files (`*.config.*`, `*.setup.*`)
- Generated code (`*.generated.*`, files in `dist/`, `build/`, `.next/`, `node_modules/`)
- Component story files (`*.stories.*`)
- Pure-constants files (only exports of literals)

**Verify:** Read the source file briefly. If it's <10 LOC of trivial re-exports or constants, skip.

**Principle:** "Co-located test files provide a static signal of intended coverage; their absence flags untested modules at structure-review time."

---

### M3. Aggressive describe-level setup with no teardown

```
beforeAll\(|beforeEach\(
```

In the same file, check if an `afterAll`/`afterEach` exists that cleans up. If `beforeEach` creates module state, mocks, or fixtures with no paired cleanup, flag.

**Principle:** "Setup hooks without paired teardown leak state across tests; failures cascade and isolation breaks."

---

### M4. Snapshot of non-deterministic data

In snapshot files (`__snapshots__/*.snap`), look for raw UUIDs, ISO timestamps, or `Date.now()` outputs that would change on every run.

**Patterns inside .snap files:**
```
"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
```

**Principle:** "Snapshots containing UUIDs, timestamps, or random values fail non-deterministically; teams update them blindly."

---

### M5. Faker without seed

```
import.*from\s*['"]@faker-js/faker['"]|faker\.
```

If Faker is imported anywhere in test code, look for `faker.seed(` in a setup file or `beforeAll`. If absent, flag.

**Principle:** "Unseeded random data generators produce different inputs each run; intermittent edge-case failures become irreproducible."

---

## Low — style/structure observations

Only include these when the user asked for a thorough audit. Skip for scoped requests.

### L1. Test files outside conventional location

Flag if tests are mixed: some co-located in `src/`, some in a top-level `tests/` or `__tests__/`. Inconsistency makes structural detectors unreliable.

### L2. Missing top-level `describe`

Files with only flat `test()` calls and no `describe` grouping. Mild — not a real bug.

### L3. Test names that describe code, not behavior

Names like `test('calls getUserById')`, `test('returns true')`. Behavior-oriented names (`test('rejects user under 18')`) signal intent.

---

## Suite-wide signals (always compute on exhaustive audits)

These are quantitative ratios across the *whole* suite, not per-file findings. Compute them once and surface a single headline metric in the Summary. They're cheap to grep and they land in a way file-by-file findings don't.

### S1. Assertion strength ratios

For the in-scope test files, count:

```
# Count "toHaveBeenCalled()" with no arguments
grep -rcE 'toHaveBeenCalled\(\s*\)' <test-dir> | awk -F: '{sum+=$2} END {print sum}'

# Count "toHaveBeenCalledWith(...)"
grep -rcE 'toHaveBeenCalledWith\(' <test-dir> | awk -F: '{sum+=$2} END {print sum}'

# Count "toThrow" / ".rejects"
grep -rcE '\.toThrow\(|\.rejects\.' <test-dir> | awk -F: '{sum+=$2} END {print sum}'
```

**Report these in the Summary as a single line.** Examples:

- "Assertion strength: 256 `toHaveBeenCalled()` (no args) vs 33 `toHaveBeenCalledWith(...)` — 8:1 ratio. Strong indicator that call-shape regressions are not caught."
- "Error-path coverage: 5 `.toThrow` / `.rejects` assertions across 87 test files. Error contracts (VError wrapping, NotFound, BadRequest) are effectively untested."

**Thresholds (rough):**
- A `toHaveBeenCalled : toHaveBeenCalledWith` ratio above 3:1 across a non-trivial suite is a high-confidence smell.
- Fewer than 1 `.toThrow`/`.rejects` per 10 test files is a high-confidence smell for any codebase with error-wrapping conventions.

**Principle:** "Single-line suite-wide metrics land in a way file-by-file findings don't. They give the reader a feel for the suite's overall assertion posture before they read any individual finding."

---

## Surviving-mutant signals (only if Stryker report provided)

If user provides `reports/mutation/mutation.json` or a Stryker HTML report:

- List the top 10 files by surviving-mutant count
- For each, show one example mutation that survived (`age >= 18` → `age > 18`)
- Flag any file with mutation score <60%

If the report includes "Killed" vs "Survived" vs "Timeout" vs "NoCoverage", treat NoCoverage as a coverage gap (M2 cross-reference), Timeout as ambiguous (do not flag), Survived as assertion-strength gap.

**Principle:** "Surviving mutants are direct evidence of assertion blind spots — tests passed against deliberately-broken code."

---

## Coverage-report signals (only if coverage file provided)

If user provides `coverage/coverage-summary.json` or `lcov.info`:

- List files with 0% coverage that exist (and aren't in M2 exclusion list)
- List files with <50% branch coverage and call them out as branch-gap candidates
- **Do not** report aggregate line coverage as a finding — it's a number, not a smell. Only report it in the Summary section.

**Principle:** "Branch coverage gaps reveal untested decision paths; line coverage on its own does not."
