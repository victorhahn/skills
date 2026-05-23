# Why visualize exists

Markdown made sense when context was scarce and output had to be light. That era is over. A single self-contained HTML file is now the most useful thing the agent can produce in many situations — denser than markdown, more interactive than mermaid, more shareable than a Notion doc, and cheap to throw away.

The deeper point: **the artifact is part of the conversation, not the deliverable.** A page the user can open, scroll, click through, and screenshot closes the loop in a way another wall of bullets can't. Build artifacts to *think with the user*, not to hand off polished work. If the artifact is wrong, the next prompt rewrites it — that's the loop.

This is why mermaid-as-final-output is usually the wrong move. A diagram alone is a thin slice of one shape. A page can hold the diagram, the surrounding context, the comparison, the open questions, and an export button — all in one place, opened with one `open` command.

## Principles

- **Density beats decoration.** Markdown shies away from density because it can't lay things out. HTML can. Use grids, tabs, columns, sticky headers, and `<details>` disclosure to fit more on screen without losing scannability.
- **Communicate, don't decorate.** Color encodes meaning (status, side, severity, category) — not vibe. The template's accent / good / warn / bad pills already do this; reach for them before inventing new colors.
- **Aesthetic earns the room it takes.** Within the guardrails (accessibility, communicability, the primitives), the artifact's look should fit its purpose. A pitch deck is allowed to be expressive; a security audit isn't. Don't default to the same look every time — that's the AI-generated-page tell. See `SKILL.md` → Creative latitude.
- **Interactivity earns its keep.** Add a slider only if moving it teaches something. Add drag-and-drop only if reordering is the point. A static page that loads fast beats a clever one that feels brittle.
- **The export hatch is non-negotiable for editable state.** Any artifact where the user edits something (kanban, matrix, config, prompt) needs the Copy-state-as-JSON button working — set `window.__artifactState` from your widgets and the template handles the rest. Without it, the work the user does in the artifact is trapped.
- **Low-commitment is fine.** This is scaffolding, not a product. The file lives in the user's CWD — they own the keep/delete/commit decision. If the next prompt invalidates it, build a new one alongside.

## Anti-patterns

- **ASCII diagrams.** If it deserves a picture, it deserves SVG or Mermaid inside HTML.
- **Mermaid as the entire output for things that want layout.** A complex architecture as a single mermaid blob is unreadable. Lay it out in HTML and use mermaid only as an inset for the part where a sequence is the right primitive.
- **The 600-line scroll-of-doom.** If the page won't fit on a laptop screen after one expand, it's the wrong shape — switch to tabs, an index sidebar, or split into a grid.
- **Pasting markdown into a `<div>`.** If you're not using HTML's layout capabilities, you should've just written markdown.
- **Forgetting the export button.** Trapped state is wasted work.
- **Reinventing every CSS rule from scratch.** If you throw out the primitives entirely, artifacts across one session feel unrelated and the Copy-state mechanics get lost. Override variables and add new classes; don't blow away the base.
