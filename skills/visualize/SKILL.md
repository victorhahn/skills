---
name: visualize
description: >
  Build a single-file, self-contained interactive HTML artifact when the
  answer wants to be a page you can scroll, click, and share — not more
  prose. Triggers — (1) explicit: "visualize", "make an HTML", "build me
  a page / one-pager for this", "diagram this", "draw the flow", "I can't
  picture it"; (2) comparison: "show me N approaches side-by-side", "lay
  them out so I can compare them", "give me options to scan"; (3)
  planning / spec / review: "turn this plan into something I can read",
  "review this PR as an HTML", "rendered diff with margin annotations",
  "show me the architecture"; (4) interactive exploration: "let me play
  with X", "build me a quick editor", "make me a dashboard", "draggable
  cards / kanban", "knobs to tune Y"; (5) sharing intent: user wants
  something to send to a teammate, drop in a chat, put on a wiki, or
  show a stakeholder. The artifact is scaffolding for the conversation —
  build it freely, low commitment to keep it. Mermaid, SVG, and charts
  are primitives inside the page. Every artifact with editable state ends
  with a "Copy state as JSON" button so the work flows back into chat.
  Skip for one-line answers, single commands, factual lookups, and live
  debugging where the user needs a next move, not a page.
---

# Visualize

## Why this skill exists

Markdown made sense when context was scarce and output had to be light. That era is over. A single self-contained HTML file is now the most useful thing the agent can produce in many situations — it's denser than markdown, more interactive than mermaid, more shareable than a Notion doc, and cheap to throw away.

The deeper point: **the artifact is part of the conversation, not the deliverable.** A page the user can open, scroll, click through, and screenshot closes the loop with the agent in a way that another wall of bullets can't. Build artifacts to *think with the user*, not to hand off polished work. If the artifact is wrong, the next prompt rewrites it — that's the loop.

This is why mermaid-as-final-output is usually the wrong move now. A diagram alone is a thin slice of one shape. A page can hold the diagram, the surrounding context, the comparison, the open questions, and an export button — all in one place, opened with one `open` command.

## When to skip

Not everything wants to be a page. Skip when:

- The answer fits in 2–3 sentences.
- It's a single command, a one-line fact, a yes/no, or a definition.
- The user is mid-debug and wants the next move, not a deliverable.
- You'd have to invent structure that isn't really there.

A bad artifact is worse than a clear paragraph. If you find yourself padding to fill a page, just answer.

## How to build one

**Start from `assets/template.html`** (sibling to this file). It has:

- Neutral palette and system font stack as CSS variables — restyle by changing variables, not by adding new ones.
- `.card`, `.grid-2/3/4`, `.pill`, and table primitives that compose into most artifact shapes.
- A sticky export bar with `Print/PDF` and `Copy state as JSON` buttons already wired to `window.__artifactState`.
- Print styles that hide the export bar so PDF/screenshot output looks clean.

Copy the template, replace the title block and the content slot, and set `window.__artifactState` from any interactive widgets.

**Where to save it.** Default to the **current working directory** with a meaningful filename: `./visualize-<topic-slug>.html` (kebab-case, e.g. `./visualize-auth-flow.html`). This matches the Anthropic-canonical pattern from the `codebase-visualizer` docs example — the artifact lives next to the work it's about, so the user can `git add` it if it turns out to matter, `.gitignore visualize-*.html` if they don't want it tracked, or just delete it. Don't write to `/tmp/` (files get GC'd and the user loses their work) or a global cache directory (divorces the artifact from its project context). If the file already exists, suffix with `-2`, `-3`, etc. — never overwrite silently. If the user explicitly asks for a different path ("save it in `docs/`", "put it in the repo at X"), respect it.

**Open it immediately** with `open ./visualize-<topic-slug>.html` (macOS) or `xdg-open` (Linux). Don't wait for the user to ask — the artifact is meant to land in their browser as part of your reply. That's the loop the article is about.

If the artifact genuinely needs something the template doesn't cover (a charting library, mermaid, drag-and-drop), pull in a CDN script — single-file constraint allows external `<script src>`, just no split files of your own. Mermaid: `<pre class="mermaid">…</pre>` plus `https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js` and an init call.

## Pick the artifact shape

Match the conversation to one of these. Most real requests are a mix — compose freely.

| The user is trying to… | Artifact shape |
|---|---|
| Compare N approaches / options / designs | Grid of N panels, one column per option with a shared row of attributes |
| Understand a system or flow | Annotated architecture — layered SVG with labeled arrows + callout bubbles for non-obvious decisions |
| Read a plan or spec | Long-form single page: goals, mockups, data flow, code snippets, open questions, with anchor links or tabs |
| Review a PR / diff | Rendered diff with inline margin annotations, severity color-coding, header summarizing what changed and why |
| Decide between things | Decision matrix — rows are options, columns are criteria, cells colored, optional weighted score |
| Explain a concept | Storyboard — numbered panels, one idea per panel, SVG illustrations between text |
| Prioritize work | Draggable kanban (Now / Next / Later / Cut) — persist to `localStorage`, export to JSON |
| Edit something interactively | Form-based editor with live preview side-by-side, validation hints |
| Tune a system | Page with sliders / knobs that update an SVG, chart, or computed value live |
| Look at data | Dashboard — KPI tiles, chart per question, filter controls, sortable table |
| Trace a sequence | Mermaid sequence diagram embedded in the page (not as the whole output) |

The grid-of-N panels is the article's signature move. When a request is even loosely about comparing, options, or "show me the differences," default to it. When you genuinely can't tell which shape fits, ask one targeted question rather than guessing — but usually the conversation tells you.

## Philosophy

A few principles to lean on instead of rote rules. The template encodes the defaults; these explain *why* and when to deviate.

- **Density beats decoration.** Markdown shies away from density because it can't lay things out. HTML can. Use grids, tabs, columns, sticky headers, and `<details>` disclosure to fit more on screen without losing scannability.
- **Communicate, don't decorate.** Color encodes meaning (status, side, severity, category) — not vibe. The template's accent / good / warn / bad pills already do this; reach for them before inventing new colors.
- **Interactivity earns its keep.** Add a slider only if moving it teaches something. Add drag-and-drop only if reordering is the point. A static page that loads fast beats a clever one that feels brittle.
- **The export hatch is non-negotiable for editable state.** Any artifact where the user edits something (kanban, matrix, config, prompt) needs the `Copy state as JSON` button working — set `window.__artifactState` from your widgets and the template handles the rest. Without it, the work the user does in the artifact is trapped.
- **Low-commitment is fine.** This is scaffolding, not a product. The file lives in the user's CWD — they own the keep/delete/commit decision. If the next prompt invalidates it, build a new one alongside.

## Anti-patterns

- **ASCII diagrams.** If it deserves a picture, it deserves SVG or Mermaid inside HTML.
- **Mermaid as the entire output for things that want layout.** A complex architecture as a single mermaid blob is unreadable. Lay it out in HTML and use mermaid only for an inset where a sequence is the right primitive.
- **The 600-line scroll-of-doom.** If the page won't fit on a laptop screen after one expand, it's the wrong shape — switch to tabs, an index sidebar, or split into a grid.
- **Pasting markdown into a `<div>`.** If you're not using HTML's layout capabilities, you should've just written markdown.
- **Forgetting the export button.** Trapped state is wasted work.
- **Reinventing the template's CSS.** Every divergent restyle makes future artifacts feel inconsistent. Change CSS variables, not the whole sheet, unless the request specifically asks for a custom look.

## Communication style

One sentence before the artifact — name the shape and why. Then build it, save it, open it. Don't ask permission unless the request is genuinely ambiguous between two very different shapes.

**Good:**
> "Laying these four approaches out as a grid so the tradeoffs are scannable — opening it now."
> `[writes file, runs open ...]`

**Good:**
> "Turning the plan into a single-page HTML with mockups inline and an open-questions section at the bottom."

**Too much:**
> "I'll create an HTML visualization to help you compare these approaches. The page will show each approach with its tradeoffs and let you scan them side by side. Let me know if you'd like a different layout. Here it is: ..."

After producing it, don't summarize what's on the page. If there's a meaningful simplification ("I omitted the retry path — happy to add it"), one sentence. Let the artifact do the work.
