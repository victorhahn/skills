# Rendering Checklist

Correctness pass before opening the artifact. None of this is about taste — it's about the page actually rendering and being usable.

## HTML hygiene

- **Straight quotes only in attributes.** `"` not `“` `”`. Smart quotes (from a paste, from a code-block round-trip) break attribute parsing silently.
- **Close every tag.** Especially `<script>`, `<style>`, `<svg>`, `<details>`. An unclosed `<script>` swallows the rest of the page.
- **Unique IDs.** No two elements share an `id`. If you're generating elements in a loop, suffix with the index or a slug.
- **Avoid inline event handlers.** `addEventListener` over `onclick="..."` — easier to debug, easier to remove, plays nicely with CSP.
- **One `<h1>` per page.** Use `<h2>`/`<h3>` for sections.

## SVG

- **`xmlns="http://www.w3.org/2000/svg"` on every root `<svg>`.** Without it, the browser may treat it as HTML and nothing renders.
- **`viewBox` set explicitly.** Don't rely on width/height alone — `viewBox` is what makes SVG scale.
- **No CSS custom properties referenced from inline SVG attribute values.** They don't always inherit. Use them in `<style>` blocks or on the element's `style="..."` attribute.
- **`<title>` inside `<svg>` for non-decorative graphics.** Screen readers use it.

## Accessibility

- **`aria-label` on icon-only buttons.** Theme toggle, export buttons, close buttons — anything without visible text.
- **`:focus-visible` outline on interactive elements.** Keyboard users need to see where they are.
- **WCAG AA contrast** — 4.5:1 for normal text, 3:1 for large text. Check `--muted` against every background it appears on (page bg *and* card surface).
- **Tab order matches visual order.** If you reorder with CSS grid/flex, verify Tab still flows sensibly.
- **`prefers-reduced-motion` respected.** Wrap animations in `@media (prefers-reduced-motion: no-preference) { ... }`.

## Interactivity

- **State persists where it should.** Kanban order in `localStorage`, form drafts in `sessionStorage`. Don't make the user redo work on refresh.
- **`window.__artifactState` populated.** Any artifact where the user edits something must set this so the Copy-state-as-JSON button works.
- **Drag-and-drop tested with keyboard, too.** A11y-friendly DnD libraries exist; if you roll your own, provide arrow-key reordering.

## JS

- **No top-level `await` in classic `<script>` blocks.** Use `<script type="module">` if you need it.
- **Defensive selectors.** `document.querySelector('.foo')?.addEventListener(...)` — don't crash the whole page on a missing node.
- **Console clean.** Mentally open devtools before declaring done. A red console means the page is broken even if it looks fine.

## Final pass

- Open the file in a browser. Click everything that should be clickable. Tab through the page. Print preview if there's a Print button.
- If anything looks broken or feels brittle, fix it before handing back. The artifact is the message.
