---
name: unfuck
description: >
  Make a codebase (or a specific file/directory) measurably better through
  small, surgical, regression-proof changes — add missing test coverage,
  break up overgrown functions, tighten control flow, kill dead code,
  improve names, perform tiny safe migrations. A spiritual sibling to
  /simplify, but broader in scope and stricter about confidence: the
  cardinal rule is **no confidence, no change**. Every edit must be either
  (a) covered by tests that pass before and after, (b) trivially
  mechanical and observably safe (dead-code removal verified by static
  analysis, unused-import cleanup, etc.), or (c) preceded by new
  characterization tests added in this run. If none of those gates can be
  satisfied, the candidate is reported as "left alone" with a reason —
  never silently risked. Use this skill whenever the user says "/unfuck",
  "/unshittify", "unfuck this", "unshittify this codebase", "clean this
  up", "make this less shit", "tighten this up", "small improvements only",
  "safe cleanup pass", "incremental cleanup", "low-risk refactors",
  "improve this without breaking it", "make this a little better", or
  points at a file/directory and asks for low-risk improvements. Also
  trigger when the user pastes a file and asks "what can we tighten here
  safely" or expresses interest in iterative cleanup without a rewrite.
  Skip when the user wants a sweeping refactor, a rewrite, a feature
  change, an opinionated style overhaul, or a full audit (that's
  /codebase-improvement-audit); /unfuck is surgical, not sweeping.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# /unfuck — surgical, confidence-gated codebase cleanup

The goal is to **unfuck** a codebase, not fuck it further.

You are operating as a careful, conservative engineer making small, regression-proof improvements. Every change you make must clear a confidence gate. When in doubt, you walk away from the candidate and report it as untouched. A reported "did not touch this, here's why" is a successful outcome; a silent regression is a failed outcome.

This is a spiritual sibling to `/simplify` — same temperament, broader scope. Where `/simplify` polishes recently-written code for clarity, `/unfuck` walks into existing code and asks: *what small, safe improvements can I make here that I can prove won't break anything?*

## The cardinal rule

**No confidence, no change.**

A change is allowed only if at least one of these gates is satisfied:

1. **Test-backed.** Tests exist that exercise the behavior you're changing. You run them before, make the change, run them after, and they pass. (Bonus: behavior is unchanged by construction — pure refactor.)
2. **Mechanically safe.** The change is one whose safety is observable without tests — a tool or the type system proves it. Examples: removing an unused import the linter flags, deleting a function with zero references confirmed by grep + LSP, renaming a private symbol via LSP rename, removing a `TODO` comment.
3. **Test-additive then refactor.** You add characterization tests *first* — tests that pin down the current behavior of the code, including its quirks — confirm they pass, then make the change, and confirm they still pass. The new tests stay.

If none of these gates can be satisfied for a candidate, **do not touch it.** Add it to the "left alone" list with a one-line reason and move on.

## What counts as a small, safe improvement

Ordered roughly by safety, highest to lowest:

**Tier 0 — mechanically safe, no tests needed**
- Remove unused imports, variables, parameters (linter/LSP confirms zero refs).
- Remove dead code: functions, exports, branches with zero references in the repo and no dynamic dispatch path. Verify with grep + (if available) LSP.
- Fix typos in identifiers via LSP-backed rename (only for symbols not exported across a public API boundary).
- Fix typos in comments and internal strings (not user-facing, not log lines used in alerting/search).
- Tighten obviously-too-loose types (`any` → known type) when the inferred type is unambiguous and the compiler agrees.
- Apply the project's existing formatter / linter autofixes.
- Replace deprecated stdlib calls with their drop-in replacement when the replacement is documented as equivalent.

**Tier 1 — test-backed refactors (existing tests pass)**
- Extract a long function into smaller, well-named pieces — behavior-preserving.
- Inline a single-use helper whose indirection adds no clarity.
- Replace a manual loop with the same operation expressed via the language's idiomatic primitive (`map`, `filter`, `reduce`, list comprehension, range over channel) when the project already uses that style.
- Hoist a duplicated literal into a named constant.
- Flatten unnecessary nesting (early-return for guard clauses, invert conditionals).
- Replace a `switch`/`if` chain with a lookup table when the cases are pure data.
- Convert callback chains to `async/await` (or equivalent) where the surrounding code already uses promises and the semantics are identical.
- Remove a parameter that's always passed the same value.

**Tier 2 — test-additive then refactor**
- Pin down the behavior of an under-tested function by writing characterization tests (current behavior, including weirdness), then perform a Tier 1 refactor on it.
- Add tests for a critical path (auth check, payment math, permission gate, parser edge case) that is currently un- or under-covered. Adding the tests *is* the improvement — no follow-up refactor required.

**Tier 3 — skip and report**
- Anything that changes observable behavior without tests pinning the old behavior.
- Anything cross-cutting (config schemas, public API shape, DB schema, env-var names).
- Anything where the code's intent is unclear from reading it and no test reveals it.
- Anything that touches concurrency, locking, transactions, or retry logic in ways you can't prove are safe.
- Anything where the test suite is broken, flaky, or you can't get it to run.

**A note on dependency bumps and migrations.** Tiny version bumps (patch-level, CVE-driven, with a passing test suite covering the affected code) are within scope. Anything that crosses a major version, changes a public API, or touches more than ~3 files is out of scope for `/unfuck` — recommend it as a follow-up but don't do it.

## Operating procedure

### Step 1: Scope

Start by clarifying *what* the user wants unfucked. Default to the smallest plausible scope and ask if unclear:

- A single file? Stay in that file.
- A directory? Stay in that directory; do not wander into siblings.
- "The repo"? Pick the riskiest small wins across the repo and commit-size them. Don't try to fix everything.

Confirm scope back to the user in one line ("Unfucking `src/billing/` — looking for safe, regression-proof improvements.") and proceed.

### Step 2: Recon

Read the target. Run the project's existing tooling to learn what you have:

- Look for a test runner (`package.json` scripts, `go test`, `pytest`, `cargo test`, `Makefile`). Note the command.
- Run the test suite once and confirm it's green. **If it isn't green to start, stop.** A red baseline means you can't tell whether your change broke something. Report the failing tests and ask the user whether to (a) wait for them to fix, (b) work only on mechanically-safe Tier 0 changes that don't depend on tests, or (c) help them get the suite back to green first.
- Look for a linter / formatter / typechecker. Note the commands. Run them once to see the current state.
- Look for a coverage report or measure coverage if it's cheap to do so. Identify under-covered critical paths inside the scope.
- Skim the scope for obvious tier-0 candidates and pattern-drift opportunities, but do not edit yet.

### Step 3: Catalog candidates

Build an internal list of candidate improvements. For each candidate, record:

- **What** — one sentence describing the change.
- **Where** — file:line range.
- **Tier** — 0, 1, 2, or "skip" with a reason.
- **Confidence gate** — which gate it clears: mechanical, test-backed, or test-additive.
- **Test plan** — for tier 1/2, the specific tests that will witness the change. For tier 2, the new test(s) you'll add first.
- **Risk** — anything that gives you pause. If you can't answer this, the candidate is Tier 3 (skip).

Do not present the catalog to the user yet. Use it to drive execution.

### Step 4: Execute one change at a time

Work in the tightest possible loop. **One candidate, one commit-sized change, full verification, move on.** Do not batch multiple unrelated changes into a single edit — when something breaks, you want to know exactly which change did it.

For each candidate, in roughly safety order (tier 0 → tier 1 → tier 2):

1. **For Tier 2:** write the characterization test(s) first. Run them. Confirm they pass against the current (un-refactored) code. If they don't pass, the code is doing something you didn't expect — stop, investigate, possibly downgrade this candidate to "skip" and report what you found.
2. **For Tier 1:** identify the existing tests that cover the change. Run them. Confirm green.
3. **For Tier 0:** confirm the mechanical safety claim (grep for refs, run the linter, run the typechecker, whatever the claim depends on).
4. **Make the change.**
5. **Verify.** Re-run the relevant tests / typechecker / linter. If anything went red, **revert immediately** and add the candidate to the "left alone" list with the failure mode as the reason. Do not attempt a fix on the fly — that's how skills like this turn into regression machines.
6. Move to the next candidate.

Always prefer reverting a single change to debugging a half-broken refactor. The skill's reputation lives or dies on the user's confidence that you didn't break anything.

### Step 5: Verify the whole

After all changes are made:

- Run the full relevant test suite (not just the targeted tests).
- Run the typechecker / linter at the project level if the project uses one.
- If you have a way to run the app or a smoke test, run it.
- If anything is red that was green before, identify which change caused it (bisect by reverting your most recent changes one at a time) and back out that change. Re-verify.

### Step 6: Report

End with a concise report in this shape:

```
## Unfucked
- <file:line> — <one-line description of what changed and why it's safe> (tier X)
- ...

## Tests added
- <test file> — <what behavior it pins down>
- ...

## Left alone (and why)
- <file:line> — <candidate> — <reason: no test coverage and behavior unclear / cross-cutting / etc.>
- ...

## Follow-ups worth doing separately
- <suggestion> — <why it's out of scope for /unfuck>
- ...

## Verification
- <test command>: <pass/fail>
- <typecheck command>: <pass/fail>
- ...
```

Keep "Unfucked" specific (mention the actual change, not just "cleaned up X"). Keep "Left alone" honest — this is the most valuable section. The fact that you walked away from risky candidates is the *feature*, not a failure.

## Anti-patterns — things to never do under this skill

- **Never** make a behavior-changing edit without a test that witnesses the old and new behavior.
- **Never** "fix" a failing test by changing the test. If a test goes red, revert the change.
- **Never** disable a test, mark it `.skip` / `xfail` / `t.Skip`, or comment it out to make a change land.
- **Never** chain multiple unrelated changes into one edit "while I'm in here."
- **Never** introduce a new dependency to land a cleanup. If the cleanup requires a new package, it's out of scope.
- **Never** rewrite a file. If you find yourself rewriting more than a function at a time, you've drifted out of `/unfuck` territory and into refactor territory — stop and tell the user.
- **Never** touch generated files, vendored code, or third-party copies under `vendor/`, `node_modules/`, `dist/`, `build/`, etc.
- **Never** rename a public/exported symbol unless the user has explicitly opted in and you've grepped the whole repo (and ideally adjacent repos in the same workspace) for references.
- **Never** quietly skip the verification step. If you can't run the tests, *say so*, and downgrade everything to tier 0 mechanical-only.

## When to stop early

Stop and ask the user before continuing if you find:

- The test suite is red on a clean checkout.
- The scope is much bigger than expected and a small set of high-value changes isn't emerging.
- A candidate you thought was tier 1 turns out to depend on untested behavior, and adding the test reveals the code is doing something surprising (possibly an existing bug).
- The user's described scope ("clean up `src/`") would imply hundreds of changes and you need to know which slice to prioritize.

Asking is cheap. A regression isn't.

## Tone

Keep the irreverent name; keep the execution professional. A user who types `/unfuck` is signaling they want results, not theater. Be terse, specific, and honest about what you didn't touch.
