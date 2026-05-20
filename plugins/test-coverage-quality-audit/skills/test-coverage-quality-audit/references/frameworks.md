# Framework-specific detectors

Load the section(s) matching the stack detected from `package.json`/`go.mod`. Skip the rest.

These detectors layer on top of the generic catalog in `detectors.md`. When a framework-specific finding overlaps with a generic one, prefer the framework citation — it's more actionable.

---

## React + Testing Library

### R1. Asserting on implementation details

Tests querying by `className`, `data-testid` proliferation, or component instance internals (`wrapper.instance()`, `enzyme`-style).

**Patterns:**
```
\.querySelector\(['"]\.[a-z]   # class-based queries
data-testid=                    # heavy use suggests poor semantic queries
container\.firstChild
wrapper\.instance\(\)|wrapper\.state\(
```

**Verify:** `data-testid` is fine *sometimes* (3rd-party components, ambiguous semantics). Heavy use (>5 per file) signals avoidance of accessible queries.

**Severity:** Medium.

**Principle:** "Querying by class or test-id couples tests to markup; accessible queries (getByRole, getByLabelText) match how users interact."

---

### R2. `waitFor` with side effects

```
waitFor\(\s*(?:async\s*)?\(\s*\)\s*=>\s*\{[^}]*(?:dispatch|setState|userEvent|fireEvent)
```

`waitFor` retries its callback. If the callback has side effects (dispatches an event, calls an API), each retry fires it — leading to N requests instead of 1.

**Severity:** High.

**Principle:** "waitFor retries its callback until assertion passes; side effects inside waitFor fire repeatedly."

---

### R3. Manual `act()` around `render` / `userEvent`

Already covered by H4 in detectors.md. Cross-reference here.

---

### R4. Server Component testing in jsdom

If `next` is in deps and you find tests for `app/**/page.tsx` or `app/**/route.ts` running in a jsdom environment, flag — server components can't execute in jsdom without `vitest-plugin-rsc` or a server runtime.

**Patterns to verify:**
- vitest config `environment: 'jsdom'` AND tests under `app/`
- jest config `testEnvironment: 'jsdom'` AND tests under `app/`
- Absence of `vitest-plugin-rsc` in deps

**Severity:** Medium — if the tests still pass, they likely test only the client portion. Flag as "RSC server logic likely untested by these tests."

---

## Vue + Vue Test Utils / Testing Library Vue

### V1. Pinia store leak between tests

Already in detectors.md (H3). Vue-specific manifestation:

```
import .* from\s+['"]pinia['"]
useUserStore|useAuthStore|defineStore
```

In each test file using a Pinia store, look for `setActivePinia(createPinia())` inside `beforeEach`. Absent = flag.

---

### V2. Missing `flushPromises` or `nextTick` after reactive change

After mutating reactive state, tests that immediately assert on the DOM without yielding to Vue's microtask queue will see stale output.

**Patterns:**
```
wrapper\.setData\(|wrapper\.setProps\(|store\.[a-zA-Z]+\(
# followed by immediate expect(wrapper.html()) or expect(wrapper.find(...).text())
```

**Verify:** Read the test. If an assertion on DOM follows a state change with no `await wrapper.vm.$nextTick()`, `await flushPromises()`, or `await nextTick()`, flag.

**Severity:** Medium.

**Principle:** "Vue batches DOM updates into the microtask queue; assertions running synchronously after state changes see pre-update output."

---

### V3. Shallow mount used by default

```
shallowMount\(
```

Shallow mounting stubs child components — useful for isolation but hides integration bugs. Flag heavy reliance (>50% of test files using `shallowMount`) as a structural smell.

**Severity:** Low. This is a style preference more than a bug.

---

### V4. Composable tested without component context

```
useOnlineStatus|use[A-Z]\w+\s*\(\s*\)   # bare composable invocation
```

In test files: composables that use `onMounted`, `onUnmounted`, or `inject` won't work when called outside a component setup context. If you see a composable test that just calls `useFoo()` and asserts on the returned ref without a host component, flag.

**Severity:** Medium if the composable uses lifecycle hooks (read the source to verify), Low otherwise.

**Principle:** "Composables using lifecycle hooks or inject require a Vue component context; bare invocation in tests silently no-ops those hooks."

---

## Node.js (Express / Fastify)

### N1. Mocking the framework instead of using supertest

Tests that construct mock `Request`/`Response` objects manually to test route handlers.

**Patterns:**
```
const req = \{ body:|const res = \{ status:|jest\.fn\(\)\s*\.mockReturnThis
mockResponse|mockRequest
```

This is the smell *and* a downstream symptom of business-logic-in-controllers (H7). If you flag this, cross-reference H7.

**Severity:** Medium. (Tests work, they're just brittle and verbose.)

**Principle:** "Manually-mocked req/res objects don't exercise middleware, routing, or serialization; supertest against the real app catches integration bugs these miss."

---

### N2. `jest.mock` on ESM-native packages without `unstable_mockModule`

If `package.json` has `"type": "module"` and you see `jest.mock(...)` without `jest.unstable_mockModule(...)`, the mock is likely silently broken.

**Verify:** Confirm `package.json` has `"type": "module"` and there's no Babel CJS transformation step in `jest.config`.

**Severity:** High. Likely a silently-broken test.

**Principle:** "Native ESM resolves imports statically before jest.mock() executes; mocks register too late to intercept."

---

### N3. `supertest` without MSW for outbound calls

If `supertest` is used (good) but the routes under test make outbound HTTP calls without MSW intercepting, the tests hit real services or fail unpredictably.

**Verify:** Look for `supertest` usage. If the routes call `fetch`/`axios` and `msw` isn't set up in the test file, flag.

**Severity:** High.

---

## Go

### G1. Loop variable not captured before `t.Parallel()`

Covered by H9 in detectors.md. Cross-reference here.

**Go 1.22+ caveat:** Loop variable semantics changed in Go 1.22. Check `go.mod` for `go 1.22` (or later) — if present, this bug is no longer possible at the language level. Do not flag.

---

### G2. `gomock` over hand-rolled fakes

```
//go:generate mockgen
import\s+\"github.com/golang/mock/gomock\"
```

Idiomatic Go favors hand-rolled fakes satisfying minimal interfaces. Heavy gomock usage isn't *wrong* but is a style flag.

**Severity:** Low. Only include in thorough audits.

**Principle:** "Hand-rolled fakes for narrow interfaces are more readable and refactor-stable than generated mocks."

---

### G3. Missing table-driven tests for branching logic

Look for test functions with repeated `t.Run("case_name", ...)` calls that have nearly identical bodies — candidates for table-driven refactor. Or: functions with multiple branches whose test file has a flat sequence of `TestFoo_CaseA`, `TestFoo_CaseB`, ... functions.

**Severity:** Low. Structural suggestion, not a bug.

**Principle:** "Table-driven tests reduce boilerplate, make adding cases trivial, and keep assertions consistent across scenarios."

---

### G4. `t.Errorf` where `t.Fatalf` is needed

`t.Errorf` continues execution; subsequent code that dereferences a nil from the previous step will panic.

**Pattern:**
```
err := .*\nif err != nil \{\s*t\.Errorf
```

If the next line dereferences `result` or accesses fields, the test will panic on nil instead of cleanly failing.

**Severity:** Medium.

**Principle:** "t.Errorf logs and continues; t.Fatalf halts. Use Fatalf when the rest of the test depends on the previous step succeeding."

---

## Playwright / Cypress

### P1. `page.waitForTimeout` / `cy.wait(<ms>)`

Hard-coded sleeps. Flaky by definition.

**Patterns:**
```
page\.waitForTimeout\(\d+\)
cy\.wait\(\d+\)
```

**Severity:** High. Hard-coded waits are one of the top causes of CI flake.

**Principle:** "Fixed timeouts hide race conditions and cause flake under load; wait for state, not for clocks."

---

### P2. E2E tests asserting on DOM internals

Same smell as R1 but in E2E. Querying `.btn-primary` or `[data-cy=...]` over user-facing selectors makes tests fragile.

**Severity:** Medium.

---

### P3. Shared auth state across spec files

Playwright/Cypress tests that log in via UI in every `beforeEach` instead of using storage state / session caching. Slow and a polluter pattern.

**Severity:** Low (perf), Medium if it causes flake.

---

## Cross-stack note

When the user invokes this skill on a polyglot repo, run each stack's detectors against only the directories matching that stack. Don't apply React detectors to a Go service directory.
