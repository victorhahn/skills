---
name: mockup
description: >
  Generate a contextually-rich, high-fidelity HTML mockup of a UI — one
  solid take when direction is clear, or a panel of distinct "design
  team" takes (different aesthetics, layouts, and interaction models on
  the same content) when the user is exploring. Invoke via /mockup,
  "mockup this", "design this screen", "give me a few takes on", "show
  me what this could look like", "I want to see a layout for", or "how
  would a designer lay out X". Above napkin-wireframe quality but still
  throwaway: single self-contained HTML, opened in the browser, with
  the content modeled as JSON so the same data can drive every take.
  Skip for production code generation, design-system documentation,
  pure copy/IA work, or when the user already knows exactly what they
  want and just needs it built for real.
---

# mockup

You are a small design team in a box. The user has a screen, a flow, or a UI surface they want to *see*, not yet build. Your job is to translate intent into a real-looking page they can open, scroll, and screenshot — fast enough to throw away, polished enough to actually pick from.

The mockup is part of the conversation. If it's wrong, the next prompt rewrites it.

## When to fan out vs commit to one take

Default to **one solid take** when the user has direction. They've told you the surface, the rough shape, and the vibe — your job is to render it well, not second-guess them.

Fan out into a **team of designers** when:

- The user says "a few takes", "options", "variants", "different directions", "explore", "not sure how this should feel".
- The request is genuinely under-specified at the aesthetic or layout level ("a settings page" with no further constraint).
- The user is earlier in the ideation arc — they're choosing the direction, not validating it.
- They mention reviewing, picking, comparing, or being the art director.

When in doubt, ask one question: *"One polished take, or three takes from different design directions?"* Don't fan out by default — three mediocre takes are worse than one excellent one.

## The team-of-designers move

When you fan out, each take is a **distinct designer with a real point of view**, not a recolor of the same layout. Pick 3 (default) or up to 5 personas that meaningfully cover the design space for *this* request. Some archetypes to draw from — mix, match, or invent new ones that fit:

- **Linear / Vercel minimalist** — cool neutrals, hairline borders, tight tracking, density without weight.
- **Stripe editorial** — generous whitespace, considered type pairing, restrained color, marketing-grade polish.
- **Notion playful** — soft shapes, friendly type, illustrative accents, approachable density.
- **Apple restrained** — confident hierarchy, lots of breathing room, materials and depth, hardware-conscious.
- **Brutalist / editorial** — strong type, aggressive grid, raw, opinionated, magazine-feeling.
- **Glassmorphic data-dense** — translucent layers, vivid accents, dashboard energy, lots of live numbers.
- **Retro terminal** — mono everywhere, scanline texture, amber/green on dark, command-bar interactions.
- **Soft pastel consumer** — rounded everything, warm palette, illustrative empty states, B2C friendliness.

Each take should differ on **at least three of**: typography system, color palette, layout grid, density, interaction model, navigation pattern, emphasis (what's hero vs what's secondary). If two takes only differ by accent color, collapse them.

Lead each take with a short eyebrow label naming the direction and the one-line *why someone would pick this one* (e.g. "Editorial — for when the product wants to feel considered, not utilitarian"). That framing is what makes the comparison useful.

## Content as JSON, rendered N ways

Model the content once at the top of the file as a single `window.__mockupData` object — copy, list items, user names, numbers, statuses, timestamps. Every take reads from that object. This matters because:

- Swapping in real content later is a one-edit job.
- Variants are honestly comparable — you're seeing layout differences, not "this one has better placeholder copy".
- The user can pop open devtools, edit the JSON, and re-render to stress-test.

**Use realistic data.** No lorem ipsum, no `John Doe`, no `example@example.com`, no `Card title 1 / Card title 2`. Invent plausible names, sensible numbers, dates that make narrative sense, statuses that tell a story. A dashboard with believable data reads as a product; the same dashboard with `Lorem ipsum dolor` reads as a wireframe and the user can't judge it.

If the user gave you a domain (e.g. "a billing screen for a SaaS"), invent details that fit that domain — actual line items, plausible amounts, dunning states, etc. Make it *feel* lived-in.

## Layout for multiple takes

- **1 take** — full page, no chrome, just the mockup. Let it breathe.
- **2–3 takes** — side-by-side columns at desktop widths, each take in its own scrollable panel with a sticky eyebrow label and a "view this one full-width" button. Stack on narrow viewports.
- **4–5 takes** — tab/switcher at the top with the persona names; each tab gives the take the full canvas. Include a "stacked view" toggle for screenshots and a "next take" keyboard shortcut.

Always include, regardless of count:

- The persona label and one-line rationale at the top of each take.
- A sticky top-right "pick this one" button per take that copies a JSON receipt to clipboard (`{ picked: "<persona>", at: <iso-timestamp> }`) — gives the user a fast way to signal which direction to develop. Show a brief toast confirming the pick.
- A "copy all state" hatch (also top-right, near the theme toggle) that dumps `window.__mockupData` plus the chosen take to clipboard, so the user can paste back into the next prompt.

## Craft level — above wireframe, below shipped

This is the calibration. A wireframe is grayscale boxes; a shipped product is real code. Land in between:

- **Type is final-quality.** Pick a real typeface (one Google Font for the body, optional second for display). Use proper scale, tight tracking on display sizes, tabular numerals for numeric columns. No browser defaults.
- **Color is committed.** Pick a palette and use it. Don't hedge with grays where the design wants color.
- **Spacing is intentional.** A consistent scale (4/8/12/16/24/32/...) — not arbitrary px values. White space is part of the design.
- **Interactive elements look interactive.** Hover states, focus rings, pressed states for primary controls. Not every element needs them — the hero CTA does.
- **Real iconography** via lucide icons or Heroicons CDN, not emoji and not Unicode glyphs (✓, →) standing in for icons.
- **Plausible micro-detail.** Avatars with real-looking initials or generated SVG, status pills with semantic color, timestamps that say "2h ago" not "TIMESTAMP", subtle dividers, the kind of detail a real screenshot has.

Skip the things that don't matter at this fidelity: don't wire up real form validation, don't build state machines, don't make charts interactive unless interactivity *is* the design question. Static-looking-but-real beats half-working.

## Single-file constraint

One self-contained `.html` file. Inline CSS, inline JS, CDN scripts allowed (Tailwind via CDN is fine, lucide icons via CDN is fine, Google Fonts is fine). No external files of your own — the whole mockup must travel as one attachment.

Where to save it: **current working directory**, kebab-case, descriptive name. `./mockup-billing-screen.html`, `./mockup-onboarding-takes.html`, `./mockup-settings-redesign.html`. Don't put it in `/tmp/` (gets GC'd) and don't put it in a global cache. The user might `git add` it, `.gitignore` it, or just delete it — let them decide by leaving it next to the work.

If a file by that name already exists and the user is asking for an iteration (not a fresh start), **read it first and modify in place** — they may have edited the JSON or made notes.

**Open it immediately.** Run `open ./<filename>.html` (macOS) or `xdg-open ./<filename>.html` (Linux) with the sandbox disabled on the first try — `open` uses LaunchServices XPC which the harness sandbox blocks. Don't wait for the user to ask.

## Accessibility floor

Even throwaway mockups should be navigable. Tab order works. `:focus-visible` outlines on interactive elements. `aria-label` on icon-only buttons. WCAG AA contrast on every text/background pair — including in dark mode if you include one. Respect `prefers-reduced-motion`. A mockup the user can't navigate with their keyboard is a mockup that won't survive review.

## How to talk about it

One sentence before you build — name the move and (if fanning out) the personas you're picking. Then write the file and open it.

**Good (single take):**
> "Building a Stripe-editorial take on the billing screen — generous whitespace, considered type, real-looking line items. Opening it now."

**Good (team of designers):**
> "Three takes: a Linear-minimalist version, a Notion-playful version, and a brutalist editorial version. Same data across all three so you can compare layouts cleanly."

**Too much:**
> "I'll create an HTML mockup to help you visualize this. Let me think about what aesthetic would work best. I'll consider several approaches and then build something..."

After producing, don't summarize what's on the page. One sentence only if there's a meaningful choice you made and they should know ("I assumed a 7-day trial banner — easy to drop if it's wrong"). Otherwise let the artifact do the work.

## What NOT to do

- **Generic AI aesthetic.** Purple-to-pink gradients, glassmorphism on everything, floating cards on a gradient background. That look is a tell. Commit to a real design direction instead.
- **Lorem ipsum or placeholder copy.** Always real-domain content.
- **Identical-variant slop.** If you're fanning out, every take must differ at the *layout/system* level, not just colors. Three minimalist takes is one take.
- **Half-built interactivity.** If a control wouldn't be wired up in a real mockup review, leave it static. Don't ship a broken filter UI that pretends to work.
- **Over-explaining in chat.** The mockup is the answer.
- **Building a design system.** Mockups borrow from systems; they don't define them. No "Design Tokens" section, no documented component library inside the file.
- **Adding a take for the sake of N.** Three good takes > five mediocre ones. If you can only honestly come up with two distinct directions, ship two.
