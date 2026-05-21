---
name: brainstorming
description: Turn vague ideas into approved designs through collaborative dialogue — one question at a time. Use this whenever the user wants to "build", "design", "add", "explore", or "figure out" something non-trivial, even if they don't explicitly ask to brainstorm. Especially use when scope is unclear, multiple approaches are viable, or the request could mean several different things. Skip only for typo fixes, mechanical refactors with obvious shape, or when the user explicitly says "just do it".
---

# Brainstorming

Help turn ideas into validated designs through natural, one-question-at-a-time dialogue. The goal is shared understanding *before* anything gets built — not exhaustive specs, just enough clarity that the next step has a sound foundation.

## When this is the right move

Brainstorm whenever the *shape* of the work is unclear:
- "Let's add a feature that does X" — what's the surface, what's the boundary?
- "Build a tool for Y" — single utility, or a whole subsystem?
- "Refactor this module" — what problem are we actually solving?
- "Wire up service A to service B" — what contract, what failure modes?

Don't brainstorm when the work is already shaped:
- "Fix this typo." → just fix it.
- "Rename `getUser` to `fetchUser` across the repo." → just do it.
- "The build is broken, investigate." → that's debugging, not designing.

When in doubt, lean toward brainstorming. The cost of one good clarifying question is much smaller than the cost of building the wrong thing.

## Anti-pattern: "this is too simple to need a design"

A todo app, a single helper function, a config tweak — they all benefit from a single round of clarifying questions. "Simple" is where unexamined assumptions hide. The design can be three sentences, but state it explicitly and get a nod before building. This is the cheapest insurance you can buy.

## The Loop

1. **Orient.** Read what's already there before asking anything: relevant files, recent commits, the README, any existing notes. Cold questions feel lazy when the answer is sitting in the repo.

2. **Check scope.** If the request describes multiple independent subsystems ("a platform with auth + billing + dashboards + notifications"), call that out before drilling in. Help the user decompose: what are the independent pieces, what depends on what, what's the first slice? Then brainstorm the first slice through the normal loop.

3. **Ask, one question at a time.** Prefer multiple choice or A/B/C — easier to answer than open-ended. Focus on purpose, constraints, and what "done" looks like. Do not stack questions. One question per turn, even if it means a few extra turns. The signal from a focused answer is much higher than from a wall of choices.

4. **Propose 2-3 approaches.** Once you have enough context, sketch a couple of viable directions with tradeoffs. Lead with your recommendation and the why. The user usually has good instincts — give them something concrete to react to.

5. **Present the design in sections.** Architecture, components, data flow, error handling, testing — whichever apply. Scale each section to its weight (one line if obvious, a paragraph if nuanced). Pause after each section: "does that match what you had in mind?" Iterate before moving on.

6. **Get explicit approval before building.** This is the one hard rule. Writing code, scaffolding files, running migrations, anything irreversible — all of it waits until the user has said yes to the design. Why: a five-minute correction at the design stage avoids a five-hour rewrite at the code stage. There's no scenario where skipping this step pays off.

7. **Hand off cleanly.** When the design is approved, pick the next step based on the shape of the work:
   - **Trivial / single-file / mechanical** — implement directly.
   - **Multi-file, ordered steps, or anything where the approval surface matters** — enter Plan mode (`EnterPlanMode`) and present the implementation steps for approval before executing.

   If it's a coin flip, ask the user which they prefer.

## Optional: write the design down

For anything that spans more than a single session or involves more than one person, save the design somewhere durable before implementing — usually a short markdown file in the repo's `docs/` (or wherever the repo already keeps design notes). The file should answer: what are we building, why, what are the main components, what's out of scope. A page or less is plenty for most things.

For one-shot, single-session work, the conversation itself is enough — no doc needed. Don't manufacture paperwork for its own sake.

If you do write a doc, give it a quick fresh-eyes pass before handoff:
- Any TODOs, "TBD", or hand-wavy bits? Resolve or remove.
- Internal contradictions? Does the architecture match the components?
- Ambiguity that could be read two ways? Pick one and say so explicitly.
- Scope creep? Pull it back to what was actually agreed.

Then ask the user to skim it before kicking off implementation.

## How to ask good questions

- **Multiple choice beats open-ended** when there's a clear option space. "A: keep it in-process. B: extract to a service. C: split per environment. Which fits?" is easier and faster than "how do you want to structure this?"
- **Ask the smallest question that unblocks the next step.** Don't ask about error handling before you know the happy path.
- **State your guess.** "I'd assume X — does that match?" gets to the answer faster than a fully open question, and gives the user something to push back on.
- **One per turn.** Stacking three questions in one message gets you one mediocre answer and two ignored ones.

## Working in existing codebases

Look at the code before proposing the change. Match conventions — naming, file structure, where things live, how errors flow. If the surrounding code has a problem that directly affects this work (a file that grew too big, a tangled boundary), fold a targeted improvement into the design. Don't propose unrelated cleanup — stay focused on what serves the current goal.

## Design for understandability

Break the work into units where each one has a clear job, a defined interface, and can be understood without reading its internals. The test: can someone use this unit knowing only what it does, how to call it, and what it depends on? If not, the boundaries need work.

This isn't just for the human readers. You reason better about code you can hold in your head — when a file or function grows past that, your edits get less reliable. Smaller, well-bounded units are easier on everyone.

## Principles

- **One question at a time.** No stacking.
- **Multiple choice beats open-ended** when an option space exists.
- **YAGNI by default.** If a feature isn't requested, leave it out.
- **Explore alternatives.** Always sketch 2-3 directions before settling.
- **Validate incrementally.** Each section gets a quick check before the next.
- **Be willing to revise.** If something doesn't make sense, back up and clarify — don't paper over.
- **Explain the why.** Both in dialogue and when you write things down. A design without rationale ages badly.
