---
name: visualize
description: >
  Produce a single-file, self-contained interactive HTML artifact instead of
  markdown prose whenever HTML would communicate more clearly — and fire
  proactively, without waiting to be asked. Also invoked explicitly via
  /visualize, "visualize this", "make this a page", "give me an artifact".
  Output shapes: comparison grids, dashboards, architecture diagrams, plan
  pages, PR diffs, decision matrices, kanbans, tunable-knobs tools,
  calculators, reference docs, FAQs, code walkthroughs, timelines, ERDs,
  flowcharts, slide decks, mindmaps, interactive tables. Template at
  assets/template.html ships card/grid primitives, CSS variables, dark/light
  toggle, and a sticky Copy-state-as-JSON export bar. Heuristic: if the
  answer would take >30 seconds to scan as markdown, an artifact almost
  certainly serves it better. Skip for short factual answers (<3 sentences),
  single code snippets, conversational back-and-forth, or when the user says
  "keep it simple".
---

# Visualize

The artifact is part of the conversation, not the deliverable. A page the user can open, scroll, click through, and screenshot closes the loop in a way another wall of bullets can't. Build to *think with* the user — if the artifact is wrong, the next prompt rewrites it.

For the deeper *why*, principles, and anti-patterns, see `references/philosophy.md`. Load it when in doubt about whether to build, what shape to pick, or whether the page is doing too much.

## When to fire (proactively)

Don't wait for `/visualize`. If any of these match the conversation, build the artifact:

- Explaining a multi-step process or tutorial
- Presenting structured data, comparisons, or metrics
- Generating a report with multiple navigable sections
- Creating a tool, calculator, or interactive widget
- Showing code with annotations or syntax highlighting
- Timelines, dashboards, FAQs, accordions, reference docs
- Anything where a visual layout beats a wall of bullets

The 30-second rule: if scanning the markdown version would take more than 30 seconds, build the artifact instead.

## When to skip

Not everything wants to be a page. Skip when:

- The answer fits in 2–3 sentences.
- It's a single command, a one-line fact, a yes/no, or a definition.
- The user is mid-debug and wants the next move, not a deliverable.
- The user explicitly says "just markdown" or "keep it simple".
- You'd have to invent structure that isn't really there.

A bad artifact is worse than a clear paragraph. If you find yourself padding to fill a page, just answer.

## How to build one

**Start from `assets/template.html`** (sibling to this file). The defaults are tuned for "elevated modern SaaS" — Linear / Vercel / Stripe-adjacent. It gives you:

- **Type:** Geist + Geist Mono via Google Fonts, tight tracking on display sizes, tabular numerals on data primitives.
- **Palette:** cool-neutral zinc-family in both light and dark, considered indigo accent used sparingly. CSS variables for every color and dimension so restyling is one block of overrides.
- **Theme:** toggle (top-right, lucide icon), `prefers-color-scheme` honored, FOUC-free.
- **Primitives:**
  - `.card` / `.card.elevated` / `.card.interactive` — flat hairline by default, optional shadow or hover-lift variant
  - `.grid.grid-2/3/4` — responsive columns
  - `.section-head` with `.label` eyebrow — Stripe/Vercel docs-style section heading
  - `.pill` with `.good/.warn/.bad/.accent` — mono uppercase status pills with status dot
  - `.stat` — large numeric display with delta indicator
  - `.kbd` — keyboard hint
  - `.btn` / `.btn.primary` / `.btn.ghost`
  - `.divider`, styled `<details>` disclosures, hover-rowed tables
- **Frosted, sticky export bar** with `Copy state as JSON` wired to `window.__artifactState`.
- **a11y:** `:focus-visible` outlines, `aria-label`s on framework controls, `prefers-reduced-motion` respected.

Copy the template, replace the title block and content slot, set `window.__artifactState` from any interactive widgets. Restyle as needed (see Creative latitude below).

### Visual system — keep these, flex everything else

- **Compose with the primitives.** New shape? Combine existing classes before inventing new ones. The primitives carry the family resemblance and the export/theme/print mechanics.
- **Override CSS variables** to flex the surface (different accent, denser/airier, alt type, dark-default). Don't fight variables with overrides on every element.
- **Hierarchy by type, not size alone.** H1 → H2 → H3, mono uppercase `.label` for eyebrows, body 14px, mono 11–13px for meta. Resist arbitrary font sizes.
- **Tabular numerals for any aligned numeric column.** Already on for tables, pills, stats — extend it where you add data.
- **Color encodes meaning.** `good/warn/bad/accent` are semantic. Don't repurpose them for vibe.
- **Hairline > heavy.** 1px borders + minimal shadow is the elevation language. Reach for shadow only on hover / floating surfaces.

### Contextual libraries (CDN, pinned versions)

Pull these in only when the shape needs them. Single-file constraint allows external `<script src>`, just no split files of your own.

| Library | CDN | Use for |
|---|---|---|
| Chart.js 4 | `https://cdn.jsdelivr.net/npm/chart.js@4` | Standard charts: bar, line, pie, scatter |
| D3 v7 | `https://d3js.org/d3.v7.min.js` | Custom viz, force graphs, heatmaps, bespoke shapes |
| Mermaid 11 | `https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js` | Sequence, flow, ER, gantt, mindmap diagrams |
| Reveal.js 5 | `https://cdn.jsdelivr.net/npm/reveal.js@5` | Slide decks |
| highlight.js 11 | `https://cdn.jsdelivr.net/npm/highlight.js@11` | Code syntax highlighting |
| Prism.js | `https://cdn.jsdelivr.net/npm/prismjs@1/prism.min.js` | Alternative code highlighting (plus per-language components) |
| lucide | `https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js` | Icon system |
| MathJax 3 | `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js` | Math rendering |
| Tailwind CDN | `https://cdn.tailwindcss.com` | Utility classes (use sparingly — primitives cover most cases) |
| Google Fonts | `https://fonts.googleapis.com/css2?family=...` | Typeface — pick one that fits the artifact |

For Chart.js / D3 / `<canvas>`: those libs don't read CSS custom properties. Use explicit `rgba()`/hex matched to the active theme.

**Where to save it.** Default to the **current working directory** with a meaningful filename. Use the shape as a prefix when it's obvious: `./comparison-auth-options.html`, `./arch-payment-flow.html`, `./kanban-q2-roadmap.html`. Otherwise `./visualize-<topic-slug>.html` is fine. Kebab-case throughout. The artifact lives next to the work it's about — the user can `git add` it if it matters, `.gitignore` it if not, or just delete it. Don't write to `/tmp/` (files get GC'd) or a global cache (divorces the artifact from its project). If the file already exists *and* the user didn't ask for a fresh one, **read and modify it in place** (see Input handling). Only suffix with `-2` when the user has explicitly asked for a new version alongside.

**Open it immediately.** Run `open ./<filename>.html` (macOS) or `xdg-open` (Linux) with `dangerouslyDisableSandbox: true` on the first try — `open` uses LaunchServices XPC which the Claude Code sandbox blocks (same fundamental Darwin limitation as `gh`). No `permissions.allow` entry fixes this; bypass the sandbox directly. Don't wait for the user to ask — the artifact lands in their browser as part of your reply. That's the loop.

## Input handling

- **Source file path** ("visualize this `schema.prisma`", "show me what's in `api.go`"): read and analyze the source first, then build the artifact from what you found. Don't visualize the *file*; visualize the *thing the file describes*.
- **Existing artifact path** ("update `visualize-auth-flow.html`", "tweak the kanban from earlier"): read the existing file and modify in place. Don't recreate from scratch — the user's edits and state live in it. Suffix with `-2` only when the user explicitly asks for a fresh start.
- **Natural language only**: infer the shape from the conversation. If genuinely ambiguous between two very different shapes, ask one targeted question.

## Pick the artifact shape

Match the conversation to a shape. Most real requests compose several — mix freely.

| The user is trying to… | Artifact shape |
|---|---|
| Compare N approaches / options / designs | Grid of N panels, one column per option with a shared row of attributes |
| Understand a system or flow | Annotated architecture — layered SVG with labeled arrows + callouts |
| Read a plan or spec | Long-form single page: goals, mockups, data flow, snippets, open questions |
| Review a PR / diff | Rendered diff with margin annotations, severity color-coding |
| Decide between things | Decision matrix — rows × criteria, colored cells, optional weighted score |
| Explain a concept | Storyboard — numbered panels, one idea per panel, SVG between text |
| Prioritize work | Draggable kanban (Now / Next / Later / Cut) — persist to `localStorage` |
| Edit something interactively | Form-based editor with live preview side-by-side |
| Tune a system | Sliders / knobs that update an SVG, chart, or computed value live |
| Look at data | Dashboard — KPI tiles, chart per question, filter controls, sortable table |
| Trace a sequence | Mermaid sequence diagram embedded *in* a page (not as the whole output) |
| Mock a UI | High-fidelity mockup with realistic data, device frame if it adds context |
| Sketch a UI | Low-fidelity wireframe, sketch aesthetic, grayscale |
| Model data | ERD with entities, attributes, PK/FK marks, cardinality labels |
| Map a flow | Flowchart — start/decision/process node semantics, branch conditions on edges |
| Present | Slide deck (Reveal.js), one section per slide, speaker notes optional |
| Show change over time | Timeline (horizontal for projects, vertical for stories), Gantt for schedules |
| Explore a hierarchy | Mindmap, radial from center, collapsible branches |
| Browse rows | Interactive table — sortable headers, filter input, optional pagination |
| Reference / cheat sheet | Sticky sidebar nav + sectioned long-form, anchor links |
| Tutorial / multi-step | Progress indicator at top, step-by-step reveal, prev/next controls |
| FAQ / accordion | Collapsible Q&A list, one open at a time |

The grid-of-N panels is the signature move. When a request is even loosely about comparing, options, or "show me the differences," default to it.

For per-shape implementation hints (what makes a good ERD vs a good mockup vs a good dashboard), see `references/shapes.md`.

## Creative latitude

The template's palette is a *starter*, not a uniform. Match aesthetic to artifact.

| Content tone | Suggested direction |
|---|---|
| Technical / data-dense / neutral | Default palette. Maybe denser spacing. |
| Creative / expressive / pitch | Pick a typeface with personality, bolder accent, more whitespace |
| Professional dark / ops dashboard | Dark-default theme, restrained accents, terminal-adjacent mono |
| Friendly / consumer / onboarding | Warmer palette, rounder shapes, illustrative empty states |
| Serious / audit / report | Restrained palette, severity-coded badges as the only loud color |
| Editorial / longform | Serif body, generous line-height, wider gutters |

A debugging dashboard wants flat, data-dense neutrality. A pitch deck wants energy and contrast. A wireframe wants sketchiness. A security audit wants severity-coded restraint. A brainstorm page can be playful. Slides especially are the one shape where the neutral defaults are usually wrong: pick a typeface, pick a palette, commit to a look.

Override CSS variables; pick a typeface that fits (one Google Font is fine, two max — heading + body); change spacing and rhythm if the content asks for it. Restyle the surface — just keep the *primitives* (`.card`, `.grid-N`, `.pill`, `.btn`, the export bar, the theme toggle) so artifacts feel like part of the same family and the export/print/dark-mode mechanics keep working.

**Guardrails:**

- Accessibility floor: keyboard-navigable, `aria-label` on icon-only controls, `:focus-visible` outlines, WCAG AA contrast on every text/background pair. Respect `prefers-reduced-motion`.
- Density beats decoration.
- Color encodes meaning.
- Keep the primitives and the export hatch working.
- Run through `references/rendering-checklist.md` before opening.

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

## References

- `references/philosophy.md` — the deeper *why*, principles, and anti-patterns. Load when in doubt about whether to build or what shape fits.
- `references/shapes.md` — per-shape implementation hints (mockup vs wireframe, ERD specifics, kanban DnD, etc.).
- `references/rendering-checklist.md` — correctness pass before opening. Smart quotes, SVG xmlns, ARIA, contrast, console-clean.
- `assets/template.html` — the starting point. Don't reinvent its primitives; restyle them.
