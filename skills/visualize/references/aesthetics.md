# Aesthetic anchors

Eight curated starting points. Each is a *direction* with concrete typography and palette — not a template, not a house style. Reach for one when the content has a clear tone; remix or ignore when you have a stronger idea.

The rule that matters most: **don't default to the same look across artifacts.** Default-modern-SaaS on everything is the AI-generated-page tell. Pick deliberately.

---

## editorial-longform

For plans, specs, longform reference, post-mortems, RFCs, anything essay-shaped. The artifact wants to *be read*, not scanned.

- **Type**: Serif body — Crimson Pro, Source Serif Pro, EB Garamond, or Lora. 17–18px body. Generous line-height (1.65+). One display weight for headings (semibold, not bold).
- **Palette**: Cream / warm-white background (`#fdfcf9` or `#faf9f6`), deep ink (`#1a1a1a`). Single restrained accent (deep teal `#0d5c5c`, oxblood `#7a2222`, or muted ochre `#8a6d3b`) for links and pull quotes.
- **Rhythm**: Wide gutters, narrow measure (60–72ch), pull quotes as marginalia. Sticky sidebar nav for sections.
- **What makes it distinctive**: Reads like a Stratechery post or a New Yorker piece, not a Notion doc.

---

## ops-terminal

For status dashboards, observability pages, audits, technical reference — anything where the operator is glancing at it during incident response or to make a fast decision.

- **Type**: Mono everywhere or near-everywhere — JetBrains Mono, Berkeley Mono, IBM Plex Mono, Geist Mono. 13–14px. Numbers tabular.
- **Palette**: Deep black background (`#08080a` or `#0d1117` GitHub-dark), pale ink (`#e6e6ea`). Severity-coded only: green `#34d399`, amber `#fbbf24`, red `#f87171`. No decorative accent.
- **Rhythm**: Dense, gridded. 1px borders. Inline sparklines, status pips, deploy badges. No animation except subtle status pulses.
- **What makes it distinctive**: Looks like Grafana / Datadog / k9s, not a SaaS landing page. The reader trusts it to be accurate.

---

## pitch-display

For lightning talks, slide decks, pitch pages, manifestos, "why we should X" arguments. Wants energy and commitment.

- **Type**: Display sans for headings — Space Grotesk, Inter Tight (weight 800+), Fraunces, Cal Sans, DM Serif Display. Tight letter-spacing on display sizes (-0.03em). Body in a clean sans (Inter, Geist).
- **Palette**: Commit to a strong palette. Dark mode is often right: deep base (`#0a0a0f`, `#0d0d18`) with a saturated accent (electric indigo `#7c6bf0`, neon teal `#00d9b2`, sunset coral `#ff6b6b`). Or invert: cream base with oversized black type and one violent accent color.
- **Rhythm**: Oversized type (60–120px headings). Generous slide-level whitespace. Each section commits to a single idea.
- **What makes it distinctive**: The audience knows you cared. Won't be confused for a generic deck template.

---

## audit-restrained

For security reviews, compliance docs, postmortems-as-deliverable, anything where restraint is the credibility signal. The artifact says "I'm serious; only the findings carry color."

- **Type**: Serif body (Source Serif Pro, EB Garamond) or restrained sans (IBM Plex Sans, Source Sans Pro). 14–15px. Mono for IDs / CVE refs / paths.
- **Palette**: Off-white background (`#f7f6f3`), graphite ink (`#212121`), warm grey supporting tones. Severity badges are the only loud color: critical `#b91c1c`, high `#d97706`, medium `#0d4a8a`, info `#525252`.
- **Rhythm**: Print-feeling. Numbered sections. Clear severity pills. Tables with hairline rules.
- **What makes it distinctive**: Looks like a Big Four audit report or an OWASP doc, not a Linear ticket.

---

## whimsy-kitchen

For personal pages, gifts for partners/family, recipe cards, hobby guides, anything warm and human. The artifact says "I made this for you."

- **Type**: Handwritten or display serif for headings — Caveat, Patrick Hand, Shadows Into Light, Fraunces, Playfair Display. Paired with a friendly sans (Lato, Quicksand, DM Sans) for body. Don't go all-handwritten; that's hard to read.
- **Palette**: Warm cream/butter background (`#faf3e6`, `#fdf8f3`), espresso ink (`#3d2817`), caramel/amber accents (`#c08552`, `#d4a373`), muted sage or rose as secondary.
- **Rhythm**: Recipe-card layout. Numbered steps with hand-drawn-feeling SVG illustrations. Small playful animations (steam from a cup, a gently bobbing element) — gated on `prefers-reduced-motion`.
- **What makes it distinctive**: Reads as personal, not corporate. Feels handmade.

---

## brutalist-newsprint

For opinion pieces, strong takes, "here's the thing" pages, anything that wants to feel uncompromising. The artifact says "look at this, no apologies."

- **Type**: Times-style serif (`Times New Roman`, `Georgia`, `Source Serif Pro`) at large display sizes, OR Helvetica/Inter at heavy weights (900) and extreme sizes. Oversized headlines (80–160px). Body at 16–18px.
- **Palette**: Pure black on off-white (`#fafaf7`), or pure white on pure black. A single violent accent (signal red `#dc2626`, electric yellow `#facc15`) used sparingly for emphasis.
- **Rhythm**: Sharp grid. Big-headline-then-block-of-body. Asymmetric layouts. Minimal borders, generous whitespace, no shadows, no rounded corners.
- **What makes it distinctive**: Looks like Bloomberg Businessweek covers or Vignelli's NYC Subway map. Or an architecture firm's portfolio site. Confident.

---

## technical-schematic

For ERDs, architecture diagrams, API specs, RFCs, hardware datasheets, formal technical documents. Wants to feel precise without being austere.

- **Type**: IBM Plex Sans + IBM Plex Mono. Or Inter + JetBrains Mono. 13–14px. Mono for identifiers, types, paths.
- **Palette**: Cool neutral background (`#f8fafc`), slate ink (`#0f172a`). Zone-coded colors for service categories: sky for frontend, indigo for backend, emerald for data, amber for external. Used as muted backgrounds, not on text.
- **Rhythm**: Labeled SVG diagrams with protocol annotations on arrows (`HTTP+JSON`, `gRPC`, `Kafka: events.v1`). Callout bubbles for non-obvious decisions. Code blocks with line numbers and syntax highlighting.
- **What makes it distinctive**: Reads like an RFC or an IBM Redbook. Precise without being airless.

---

## consumer-warm

For onboarding pages, tutorials, friendly explainers, "getting started" guides. The audience is a real human who may be intimidated. Wants approachability.

- **Type**: Rounded sans for headings — DM Sans, Plus Jakarta Sans, Nunito (semibold). Friendly sans for body — Inter, Geist. 15–16px body. Generous line-height (1.6).
- **Palette**: Warm-leaning background (`#fff8f3`, `#fef9f4`), soft ink (`#2d2a26`). Two coordinated accents: a "primary" (sunset orange `#f97316`, warm coral `#fb7185`, golden `#f59e0b`) and a "supporting" (soft sage `#86b29a`, dusty blue `#7ba8c4`).
- **Rhythm**: Rounded corners (12–16px radius). Generous padding. Illustrative empty states. Light shadows. Progress indicators for multi-step flows. Friendly microcopy ("Nice — you're set!").
- **What makes it distinctive**: Feels like a Duolingo / Linear-onboarding / Notion-template moment, not enterprise software.

---

## How to use these

- **Read just one anchor** — the one that fits the content's tone. Don't load all eight; you'll dilute the signal.
- **Concrete is the point.** Use the actual fonts and hex colors named — these have been chosen to feel distinctive together. If you swap a font, swap toward an anchor in the same family (Source Serif Pro ↔ Crimson Pro is fine; Source Serif Pro → Comic Sans is not).
- **Remix when content asks for it.** A pitch deck that's also an audit can blend pitch-display headings with audit-restrained body. A whimsical onboarding page might mix whimsy-kitchen warmth with consumer-warm rhythm. Use the anchors as ingredients, not boxes.
- **Skip them entirely if you have a stronger idea.** These are scaffolding for moments when taste calibration matters. If the conversation has already established a specific aesthetic ("make it look like the NYT election needle"), follow that.
