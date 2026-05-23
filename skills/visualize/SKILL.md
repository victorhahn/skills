---
name: visualize
description: >
  Build a single-file, self-contained interactive HTML artifact and open
  it in the browser. Invoke via /visualize, "visualize this", "generate a
  visual artifact", or "make this into a page". Output shapes: comparison
  grids, architecture diagrams, scrollable plan/spec pages, PR diffs with
  annotations, decision matrices, draggable kanbans, dashboards, tunable
  knobs pages, mockups, wireframes, ERDs, flowcharts, slide decks,
  timelines, mindmaps, interactive tables. Template at assets/template.html
  provides card/grid primitives, CSS variables, dark/light toggle, and a
  sticky export bar with Copy State as JSON. Skip for text
  explanations, single mermaid blocks, debug next-steps, or answers that
  fit in a few sentences.
---

# Visualize

The artifact is part of the conversation, not the deliverable. A page the user can open, scroll, click through, and screenshot closes the loop in a way another wall of bullets can't. Build to *think with* the user — if the artifact is wrong, the next prompt rewrites it.

For the deeper *why*, principles, and anti-patterns, see `references/philosophy.md`. Load it when in doubt about whether to build, what shape to pick, or whether the page is doing too much.

## When to skip

Not everything wants to be a page. Skip when:

- The answer fits in 2–3 sentences.
- It's a single command, a one-line fact, a yes/no, or a definition.
- The user is mid-debug and wants the next move, not a deliverable.
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

**Where to save it.** Default to the **current working directory** with a meaningful filename. Use the shape as a prefix when it's obvious: `./comparison-auth-options.html`, `./arch-payment-flow.html`, `./kanban-q2-roadmap.html`. Otherwise `./visualize-<topic-slug>.html` is fine. Kebab-case throughout. This matches the Anthropic-canonical pattern from the `codebase-visualizer` example — the artifact lives next to the work it's about, so the user can `git add` it if it matters, `.gitignore` it if not, or just delete it. Don't write to `/tmp/` (files get GC'd) or a global cache (divorces the artifact from its project). If the file already exists *and* the user didn't ask for a fresh one, **read and modify it in place** (see Input handling). Only suffix with `-2` when the user has explicitly asked for a new version alongside.

**Open it immediately** with `open ./<filename>.html` (macOS) or `xdg-open` (Linux). Don't wait for the user to ask — the artifact lands in their browser as part of your reply. That's the loop.

If the artifact genuinely needs something the template doesn't cover (a charting library, mermaid, drag-and-drop), pull in a CDN script — single-file constraint allows external `<script src>`, just no split files of your own. See `references/shapes.md` for the pinned CDN shortlist.

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

The grid-of-N panels is the signature move. When a request is even loosely about comparing, options, or "show me the differences," default to it.

For per-shape implementation hints (what makes a good ERD vs a good mockup vs a good dashboard), see `references/shapes.md`.

## Creative latitude

The template's palette is a *starter*, not a uniform. Match aesthetic to artifact.

A debugging dashboard wants flat, data-dense neutrality. A pitch deck wants energy and contrast. A wireframe wants sketchiness. A security audit wants severity-coded restraint. A brainstorm page can be playful — different typeface, looser layout, color used expressively. Slides especially are the one shape where the neutral defaults are usually wrong: pick a typeface, pick a palette, commit to a look.

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
- `references/shapes.md` — per-shape implementation hints (mockup vs wireframe, ERD specifics, kanban DnD, etc.) and the pinned CDN library shortlist.
- `references/rendering-checklist.md` — correctness pass before opening. Smart quotes, SVG xmlns, ARIA, contrast, console-clean.
- `assets/template.html` — the starting point. Don't reinvent its primitives; restyle them.
