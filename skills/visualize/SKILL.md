---
name: visualize
description: >
  Build a single-file, self-contained HTML artifact instead of markdown prose
  whenever a rendered page would communicate the answer more clearly — and
  fire proactively, without waiting to be asked. Also invoked explicitly via
  /visualize, "visualize this", "make this a page", "give me an artifact",
  "turn this into a page". Output shapes range freely: comparison grids,
  dashboards, plan/spec pages, architecture diagrams, decision matrices,
  kanbans, slide decks, mockups, wireframes, ERDs, flowcharts, mindmaps,
  timelines, FAQs, tutorials, calculators, status pages, code walkthroughs,
  reference docs. Heuristic: if the answer would take more than 30 seconds
  to scan as markdown, an artifact almost certainly serves it better. Skip
  for short factual answers (under 3 sentences), single code snippets,
  conversational back-and-forth, or when the user says "keep it simple".
---

# Visualize

The artifact is part of the conversation, not the deliverable. A page the user can open, scroll, click through, and screenshot closes the loop in a way a wall of bullets can't. Build to *think with* them — if the artifact is wrong, the next prompt rewrites it.

There's no template here on purpose. The most distinctive artifacts come from picking the right shape for the content and committing to an aesthetic that fits — not from filling in a house template. Trust your judgement; reach for `references/aesthetics.md` when the content has a clear tone and you want a concrete starting point.

## When to fire (proactively)

Don't wait for `/visualize`. Build the artifact when any of these match:

- Comparing options, approaches, or designs
- Presenting structured data, metrics, or anything tabular-ish
- A multi-step process, tutorial, or sequence
- A report or plan with multiple navigable sections
- A tool, calculator, slider, or interactive widget the user can play with
- Code with annotations, diagrams, or syntax-highlighted blocks
- Timelines, dashboards, FAQs, accordions, reference docs, slide decks
- Anything where a visual layout beats a wall of bullets

**30-second rule**: if scanning the markdown version would take more than 30 seconds, build the artifact instead.

## When to skip

- The answer fits in 2–3 sentences.
- It's a single command, a one-line fact, a yes/no, a definition.
- The user is mid-debug and wants the next move, not a deliverable.
- The user said "just markdown" or "keep it simple".
- You'd have to invent structure that isn't really there.

A bad artifact is worse than a clear paragraph. If you find yourself padding to fill a page, just answer.

## Principles

- **Density beats decoration.** Use HTML's layout — grids, columns, sticky elements, disclosure. If you're pasting markdown into a `<div>`, you should have written markdown.
- **Match aesthetic to content.** A pitch deck wants energy. A security audit wants restraint. A wireframe wants intentional roughness. A whimsical personal page wants personality. The default-modern-SaaS look on every artifact is the AI-generated-page tell — actively avoid it. See `references/aesthetics.md` for curated anchors when taste calibration matters.
- **Color encodes meaning** — status, severity, category, identity — not vibe.
- **Interactivity earns its keep.** Add a slider only if moving it teaches something. Add drag-and-drop only if reordering is the point. A static page that loads fast beats a clever one that feels brittle.
- **Accessibility floor**: keyboard-navigable, `aria-label` on icon-only controls, `:focus-visible` outlines, WCAG AA contrast, respect `prefers-reduced-motion`.
- **Self-contained, single file.** External `<script src>` and `<link rel="stylesheet">` to pinned CDN versions are fine; no split local files of your own. Chart.js / D3 / `<canvas>` don't read CSS custom properties — pass explicit hex/rgba matched to the theme.

## Pick the shape

Most requests imply a shape. Some common ones (mix freely, invent your own):

| The user is trying to… | Likely shape |
|---|---|
| Compare N options | Grid of N panels, shared attribute rows |
| Understand a system | Annotated architecture diagram (SVG with labeled arrows + callouts) |
| Read a plan or spec | Long-form page: goals, mockups, snippets, open questions |
| Review a PR / diff | Diff with margin annotations + severity color-coding |
| Decide between things | Decision matrix — rows × criteria, colored cells |
| Prioritize work | Kanban (Now / Next / Later / Cut), drag-and-drop, `localStorage` |
| Tune a system | Sliders / knobs that update SVG / chart / computed value live |
| Look at data | Dashboard — KPI tiles, charts, filter controls, sortable table |
| Trace a sequence | Mermaid sequence diagram embedded in a page |
| Mock a UI | High-fidelity mockup with realistic data |
| Sketch a UI | Wireframe, grayscale, intentionally rough |
| Model data | ERD with entities, attributes, PK/FK, cardinality |
| Present | Slide deck (Reveal.js), one section per slide |
| Show time | Timeline / Gantt (horizontal for projects, vertical for stories) |
| Riff off live | Reference page with diagrams + key data + jump-to sections |
| Explore hierarchy | Mindmap, radial from center, collapsible branches |
| Reference / cheatsheet | Sticky sidebar nav + sectioned long-form, anchor links |
| Tutorial | Progress indicator + step-by-step reveal + prev/next |
| FAQ | Collapsible Q&A, one open at a time |

The grid-of-N panels is the signature move for comparisons. Beyond that, pick what fits — and if the conversation suggests a *hybrid* shape (a reference page with an embedded diagram and a mockup), build the hybrid. Don't force a request into one shape because the table says so.

## Aesthetic — pick deliberately

`references/aesthetics.md` has 8 curated anchors (editorial-longform, ops-terminal, pitch-display, audit-restrained, whimsy-kitchen, brutalist-newsprint, technical-schematic, consumer-warm). Each names specific Google Fonts, a palette with hex values, and when to reach for it. **Consult it whenever the content has a clear tone** — read just the anchor that fits. Remix, blend, ignore — these are starting points, not house styles.

The one rule: don't default to the same look across artifacts. Default-modern-SaaS on everything is the AI tell.

## Tools

Vanilla HTML/CSS/JS is the default — fast, predictable, lets the aesthetic shine. Reach for libraries only when the shape genuinely needs them; pin CDN versions:

- Charts → `https://cdn.jsdelivr.net/npm/chart.js@4`
- Custom viz → `https://d3js.org/d3.v7.min.js`
- Diagrams → `https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js`
- Slides → `https://cdn.jsdelivr.net/npm/reveal.js@5` (+ matching CSS)
- Code highlight → `https://cdn.jsdelivr.net/npm/highlight.js@11`
- Icons → `https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js`
- Math → `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js`
- Google Fonts → `https://fonts.googleapis.com/css2?family=...`

Don't reach for Tailwind/daisyUI by default — utility-class soup tends to flatten artifacts into looking the same. Use them only when the artifact's shape genuinely benefits.

## Input handling

- **Source file path** ("visualize this `schema.prisma`"): read and analyze the source first, then build the artifact from what you found. Visualize the *thing the file describes*, not the file.
- **Existing artifact path** ("update `visualize-auth-flow.html`"): read it and modify in place. The user's edits and state live in it. Suffix with `-2` only when explicitly asked for a fresh start.
- **Natural language only**: infer the shape from the conversation. If genuinely ambiguous between two very different shapes, ask one targeted question.

## Where to save it

Default to the **current working directory** with a meaningful kebab-case filename: `comparison-auth-options.html`, `arch-payment-flow.html`, `kanban-q2-roadmap.html`. Otherwise `visualize-<topic-slug>.html`. The artifact lives next to the work it's about — the user can `git add` it, `.gitignore` it, or delete it. Don't write to `/tmp/` (GC'd) or a global cache (divorces the artifact from its project).

## Open it immediately

Run `open ./<filename>.html` (macOS) or `xdg-open` (Linux) **with `dangerouslyDisableSandbox: true`** on the first try — `open` uses LaunchServices XPC which the Claude Code sandbox blocks. No `permissions.allow` entry fixes this; bypass the sandbox directly. The artifact lands in the user's browser as part of your reply. That's the loop.

## Communication style

One sentence before the artifact — name the shape and the aesthetic direction. Then build it, save it, open it. Don't summarize what's on the page after; let the artifact do the work. If you made a meaningful simplification ("I omitted the retry path — happy to add it"), one sentence. Otherwise stay quiet.

**Good:**
> "Laying these four approaches out as a comparison grid with an editorial-longform feel — opening it now."
> `[writes file, runs open ...]`

**Too much:**
> "I'll create an HTML visualization to help you compare these approaches. The page will show each approach with its tradeoffs and let you scan them side by side. Let me know if you'd like a different layout. Here it is: ..."

## Before opening — quick correctness pass

None of this is taste; it's whether the page renders.

- Straight quotes in attributes (`"`, not smart quotes from a paste).
- Close every tag — unclosed `<script>` swallows the rest of the page.
- Unique IDs.
- `xmlns="http://www.w3.org/2000/svg"` on every root `<svg>`, with explicit `viewBox`.
- No top-level `await` in classic `<script>` blocks.
- Use `document.createElement` + `textContent` for any DOM-building done after page load — setting raw HTML strings at runtime trips Claude Code's security hook (and is XSS-risky).
- Mentally open devtools before declaring done. A red console means the page is broken even if it looks fine.
