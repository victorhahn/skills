# Artifact Shapes

The shape table in `SKILL.md` picks the format. This file gives implementation hints once a shape is picked. Real artifacts compose multiple shapes — these are starting points, not boxes to force a request into.

Tone hints below each shape are *suggestions*, not rules. The shape's content drives aesthetic choices; see "Creative latitude" in `SKILL.md`.

---

## Comparison grid (the signature move)

- N panels in a `.grid-N` row, one per option.
- Shared row of attributes across panels — same order, same labels — so eyes can sweep horizontally.
- Color-code only what encodes meaning (recommendation, status). Decoration in shared cells just adds noise.
- Optional summary row at the bottom: totals, recommendation, weighted score.
- **Tone:** clean, neutral, data-forward. Let the comparison do the work; don't dress it up.

## Architecture diagram

- Layered SVG: Frontend / Backend / Data / External. Top-to-bottom for request flow, left-to-right for data flow.
- Label arrows with the protocol and shape (HTTP+JSON, gRPC, Kafka topic name, S3 path).
- Callout bubbles for non-obvious decisions: why this lives here, what fails if it goes down, where the bottleneck is.
- Zoom/pan only if the diagram is genuinely large — most aren't.
- **Tone:** structural, slightly technical. Monospace for service names is fine. Color-code zones, not boxes.

## Plan / spec page

- Anchor sidebar or sticky tabs for navigation past ~3 sections.
- Inline mockups (SVG, `<img>`, or live HTML) right next to the prose that describes them.
- "Open questions" section at the bottom — explicitly invites pushback. This is what makes it a working doc, not a deliverable.
- Code snippets in `<pre>` with monospace; syntax highlighting via highlight.js for non-trivial blocks.
- **Tone:** readable, document-flavored. Serif body is welcome here if the content is essay-shaped.

## PR / diff review

- Two-column or unified diff with margin annotations.
- Severity color-coding (info / warn / blocker) using the template's pill classes.
- Header summarizes what changed and why — link to ticket/PR if known.
- **Tone:** terminal-adjacent. Monospace, restrained palette, severity as the only loud color.

## Decision matrix

- Rows: options. Columns: criteria.
- Cell colors encode rating; optional weighted score column on the right.
- Click row to highlight; sort by column header.
- **Tone:** spreadsheet-clean. Dense is fine — that's the point.

## ERD

- Entity boxes with attribute lists; mark PK and FK distinctly (icon, color, or position).
- Relationship lines labeled with cardinality (1:1, 1:N, N:M).
- If draggable: relationship lines must reflow on drag (D3 force layout or manual edge recalculation).
- **Tone:** technical, schematic. Color used sparingly for entity grouping.

## Flow / sequence

- Node types carry meaning: circle (start/end), rectangle (process), diamond (decision).
- Directional arrows; branch conditions on the connection line.
- Sequence-of-events → Mermaid sequence diagram. Branching logic → custom SVG or Mermaid flowchart.
- **Tone:** schematic. Same restraint as architecture diagrams.

## Chart / dashboard

- Auto-pick chart type from data shape: bar for categorical, line for time series, scatter for correlation, pie only for ≤5 slices summing to a whole, stacked area when composition over time matters.
- Axis labels include units. Hover tooltips for precision values.
- Dashboard: KPI tiles at top, charts below, filter controls global. Clicking one chart filters the others.
- **Tone:** clean and data-dense. If the dashboard is for ops, lean Bloomberg-terminal; if for a stakeholder readout, breathe more.

## Mockup

- Realistic placeholder data — names, prices, dates that match the domain. No Lorem ipsum.
- Device frame (phone, tablet, browser chrome) only if it communicates context.
- Multiple screens side-by-side with labels, or tabs/swipe for transitions.
- **Tone:** match the *product* being mocked. A fintech mockup and a children's app mockup should not look the same.

## Wireframe

- Sketch aesthetic — slightly irregular lines (`stroke-dasharray` or a hand-drawn web font like Excalifont/Caveat).
- Grayscale; reserve color for callouts.
- Text blocks as gray rectangles, not filler text.
- Focus on layout and information hierarchy, not visual polish.
- **Tone:** low-fidelity, intentionally rough. The roughness signals "this is a draft."

## Slides

- Reveal.js (CDN) — one section per slide, fragments for emphasis.
- Speaker notes (`<aside class="notes">`) toggleable with `S`.
- Code blocks highlighted via highlight.js.
- **Tone:** expressive. Slides are the one shape where the template's neutral defaults are usually wrong — pick a typeface, pick a palette, commit to a look.

## Timeline / Gantt

- Horizontal for project schedules, vertical for storytelling history.
- Event nodes with date labels; bars for ranges.
- Zoom/scroll for long periods; otherwise fixed scale.
- **Tone:** depends on direction. Project Gantt → operational neutral. Historical timeline → editorial, can lean illustrative.

## Mindmap

- Radial layout from center; collapsible branches.
- Mermaid mindmap for static, custom SVG/D3 for interactive.
- **Tone:** playful is fine. This is a thinking shape, not a delivery shape.

## Kanban

- Columns customizable. Default Now / Next / Later / Cut or TODO / Doing / Done.
- Drag-and-drop between columns; persist to `localStorage`.
- Labels/tags on cards using pill classes.
- `window.__artifactState` mirrors current column ordering so Copy-state works.
- **Tone:** workmanlike. Pills carry the color load.

## Interactive table

- Sortable headers — click cycles asc / desc / off.
- Filter input at top; debounced.
- Pagination or virtual scroll past ~200 rows.
- Row selection for bulk actions if the table is editable.
- **Tone:** dense, terminal-adjacent for technical data; airier for stakeholder views.

---

## CDN shortlist

Pin versions. Don't reach for these unless pure SVG / CSS won't do it.

| Library | CDN | Use for |
|---|---|---|
| Mermaid 11 | `https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js` | Sequence, flow, ER, gantt, mindmap |
| D3 v7 | `https://d3js.org/d3.v7.min.js` | Custom viz, force graph, heatmap, anything bespoke |
| Chart.js 4 | `https://cdn.jsdelivr.net/npm/chart.js@4` | Standard charts (bar, line, pie, scatter) |
| Reveal.js 5 | `https://cdn.jsdelivr.net/npm/reveal.js@5` | Slide decks |
| highlight.js 11 | `https://cdn.jsdelivr.net/npm/highlight.js@11` | Code-block syntax |
| Tailwind play CDN | `https://cdn.tailwindcss.com` | Heavy utility classes — usually the template's primitives are enough |
| Google Fonts | `https://fonts.googleapis.com/css2?family=...` | Pick a typeface that fits the artifact, not Inter-by-default |

If you need something not on this list, add it — just pin the version.
