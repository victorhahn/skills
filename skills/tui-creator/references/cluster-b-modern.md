# Cluster B — Modern / Sparse / Textual+Ink lineage

**About this file:** Per-tool research on six TUIs in the borderless, sparse, modern lineage (Textual / Ink / Bubbletea / rich-based). Grounds the "Atelier" direction archetype. Each tool covers concrete UI behaviors, weaknesses, and patterns worth stealing or avoiding.

> Some passages reference "workspace-manager" or "wsm" as a concrete case study from the project where these notes were originally compiled. Treat those passages as illustrative; the lessons generalize. The "Steal" / "Avoid" callouts are the generalizable takeaways.

## claude-code (Anthropic)

- **Framework / lang:** Ink (React-on-terminal) initially; Anthropic later rewrote the renderer in TypeScript while keeping React as the component model. Closed source; GitHub mirrors and reverse-engineering posts confirm a custom React reconciler, a pure-TS Yoga layout port, and a full ANSI/CSI/DEC/OSC parser stack.
- **Active:** Feb 2025 – present; the dominant agentic CLI of 2025–26.

**Strengths**

1. **Single named brand-accent token (`claude`) drives the spinner, the assistant label, the prompt-border accent, and nothing else.** Mode borders use their own tokens (`planMode`, `autoAccept`, `bashBorder`, `fastMode`) so the prompt box visually morphs as the agent's permission state changes — the user reads state from a single chrome element, not a status string.
2. **"Good terminal citizen" rendering** — the default mode does *not* take over the alt-screen. It carefully diffs the bottom region of the buffer so scrollback is preserved. Fullscreen (`/tui fullscreen`, `CLAUDE_CODE_NO_FLICKER=1`) is opt-in for users who want flat memory and mouse scrolling. Most coding agents converged on alt-screen by default; Claude Code's split-mode default is a deliberate counter-trend.

**Weakness / controversial choice**

- The default inline (non-fullscreen) renderer is the source of the now-famous "signature flicker" that pushed Anthropic to rewrite Ink's reconciler. Long sessions in some terminals still tear visibly. The team accepted this cost to stay out of alt-screen.

**Steal:** the **mode-coloured prompt border**. The input box itself encodes agent state — plan mode, auto-accept, bash, fast — by recoloring its single-line border. Zero status-bar real estate, instantly legible. Map directly onto `wsm` workspace modes (read-only / pending writes / branched).

**Avoid:** the **eight subagent colors** (`<color>_FOR_SUBAGENTS_ONLY`). Eight differentiated hues in one transcript collapses the rest of the palette into noise. For `wsm`, never use more than two accents simultaneously.

**Sentiment**

- Praise (Anthropic docs / palo_alto_ai on dev.to): "*Most of what Claude Code outputs is English … on a busy session my screen is maybe 20% syntax-highlighted code.*" The themes are tuned for prose readability via APCA contrast, not for syntax — a deliberate inversion of normal terminal-theme priorities.
- Critique (steipete.me, "The Signature Flicker"): "*Over the last year, most new coding agents have converged on alt-screen TUIs — often after fighting flicker — but the results haven't been great.*" The implication: Claude Code's inline-render bet is technically harder and the visible cost is still flicker.

## aider

- **Framework / lang:** Python; uses `prompt_toolkit` + `rich`. Not a true alt-screen TUI — a streaming chat with rich diffs in the normal scrollback.
- **Active:** mid-2023 – present. ~30k+ GitHub stars.

**Strengths**

1. **Diff-as-output, not diff-as-modal.** Aider never opens a panel for proposed changes — it streams a unified diff with green/red background fills directly into the conversation, then a yes/no prompt sits below. Reviewing N edits is "scroll up," not "navigate a tree."
2. **Aggressive use of `rich`'s 24-bit syntax-highlighted code blocks inside chat turns** with a thin left rule (1-char vertical bar) instead of full borders. Each turn reads as a quoted block without visually fragmenting into panels.

**Weakness**

- The interface is essentially "a smarter REPL." No persistent panels, no file tree, no in-flight task indicator beyond a spinner. Once context windows grow, scrollback becomes the only navigation, and users report losing track of which file Aider has touched in a session.

**Steal:** **stream changes into scrollback with a one-char left rule instead of a box border**. For `wsm`, hook output and script output can use this pattern so they read as quoted history, not as ephemeral panels.

**Avoid:** **no persistent visual model of state.** A workspace manager whose UI is purely a scrolling chat would be unusable. Aider's minimalism is right for *its* domain (one project, one diff at a time) and wrong for ours (N repos, N scripts, branch state).

**Sentiment**

- Praise (NxCode 2026 comparison): users describe Aider as "*calmer and more in control than browser-based chat assistants.*"
- Critique (multiple comparisons to OpenCode): "*OpenCode's TUI is a step above … vim-style navigation with a richer TUI, multi-session management … Aider's interface is straightforward and minimal.*" Translation: minimal is being read as *under-built* in 2026.

## posting (Darren Burns)

- **Framework / lang:** Python, Textual. ~7k stars. Active since mid-2024; 2.0 shipped scripting + keymaps.

**Strengths**

1. **The "PRODUCTION" header** — when the active collection is flagged production, a single full-width band renders as `[black on #ff0000 bold blink]PRODUCTION[/]`. One element, terrifying, unmissable. This is the entire warning system; there is no modal, no confirmation, no second indicator.
2. **Jump mode** — press one key (`v` by default), every interactive surface in the visible viewport gets a two-character overlay label, type the two chars to focus. Borrowed from Vimium. It collapses Tab/Shift-Tab navigation drudgery and works regardless of how panels are laid out today.

**Weakness**

- HN feedback (item 40926211) captured a recurring confusion: arrow-key navigation requires Enter to actually activate a request, and Ctrl+C wasn't documented as the exit. Textual's default focus model is keyboard-rich but unobvious; Posting inherits that.

**Steal:** **Jump-mode overlays.** For `wsm`, this lets one binding (`f` perhaps) put 2-letter labels on every repo, script, and link without us pre-assigning shortcuts per workspace.

**Avoid:** **the "Metadata tab" naming.** Users couldn't find request rename because it lived under Metadata. Generic tab names that look like cosmetic toggles hide commands. Tab labels in `wsm` should be the noun the user already says ("Repos," "Scripts," "Links," "Health").

**Sentiment**

- Praise (waylonwalker.com): "*Darren is really getting into a groove, and textual is getting to a place that is allowing him to really make these beautiful.*"
- Critique (HN, multiple): "*how do I exit?*" and "*counterintuitive to have to hit Enter*" on row activation. The polish is real; the discoverability lags it.

## harlequin (Ted Conbeer)

- **Framework / lang:** Python, Textual. ~6.1k stars. Active since late 2023; v1.0 hit #2 on HN.

**Strengths**

1. **Three-pane layout with no visible borders between panes — separation is purely a single-cell gutter and a slight background lift on the focused pane.** Catalog (left), editor (top-right), results (bottom-right). The focused pane shifts its background ~1 step lighter; everything else stays on the base surface. No box-drawing characters at all in the default theme.
2. **Horizontally-animated column scrolling on the results table.** Pressing right doesn't snap-jump columns — it scrolls smoothly. HN's top comment (item 38882526): "*The horizontal scroll animation on the query results table is fascinating. Never seen animations like that in a TUI app.*" The animation makes a 200-column result set feel like a spreadsheet.

**Weakness**

- The default `harlequin` theme leans heavily on pink-purple accent text on dark bg. Several users in the HN thread asked for "more themes" before v1 — the in-house theme reads as opinionated rather than neutral. Harlequin now ships gruvbox, catppuccin-mocha, tokyo-night, textual-light as bundled alternates.

**Steal:** **focus-via-background-lift, not border-color-change.** This is the single most important visual technique in the cluster. For `wsm`, define `bg.surface` (panel default) and `bg.elevated` (focused panel) ~3–5% L\* apart in OKLab. No `accent.primary` borders on focus.

**Avoid:** **shipping with one strongly-flavored theme as the only default.** Ship a neutral default plus 2–3 bundled named themes; let users opt into flavor.

**Sentiment**

- Praise (HN, item 38882526): "*Wow, this is really good. I can't believe how good terminal app is now.*"
- Critique (HN, same thread): a developer noted true SQL-IDE status requires "*integrated view of database design, data entry/inspection, custom querying … and report generation*" — Harlequin's polish has outpaced its feature surface. UI fidelity ≠ product completeness.

## glow (Charm / Bubbletea)

- **Framework / lang:** Go, Bubbletea + Lipgloss. ~18k stars. Active since 2020.

**Strengths**

1. **Borderless file browser with a left-edge selection cursor** — the currently-highlighted markdown file gets a single-color filled bar in column 0 (one cell wide, full row height) and a slight bg lift across the rest of the row. No box, no underline, no `>` glyph. The cursor *is* the selection indicator.
2. **Pager keystrokes mirror `less` exactly** (`j`/`k`/`gg`/`G`/`/`/`n`/`N`). Glow refuses to invent new bindings where a 40-year-old standard exists. The result is zero learning cost for anyone who's read a man page.

**Weakness**

- The stash feature (encrypted cloud-sync of markdown) was always optional and is now de-emphasized; the TUI still carries UI affordances for it that most users never use. Vestigial product surface that confused new users on HN (item 24810312).

**Steal:** **left-edge color bar as selection indicator.** Cheap, theme-friendly, works on 16-color terminals. For `wsm`, the sidebar's selected workspace can be marked with one filled cell of `accent.primary` and a small bg lift across the row.

**Avoid:** **multi-purpose stash-like features in a tool that's primarily a viewer.** Don't bolt browser-tab "open links" UI onto a workspace manager whose core job is repo management. Keep links as a flat list, not a synced collection.

**Sentiment**

- Praise (HN item 24810312, multiple): "*Charm makes the prettiest CLIs.*" The visual identity is so consistent across `glow`, `gum`, `soft-serve`, `wishlist` that "looks like a Charm app" is a recognizable aesthetic.
- Critique (same HN thread): users wanted plain reading without account signup for stash. Charm's product-coupling drew skepticism even as the visual design earned universal praise.

## presenterm (Manuel Fontanini)

- **Framework / lang:** Rust, Ratatui-style direct terminal control (uses `crossterm`, not technically Ratatui's widget set in all paths). ~4k+ stars. Active since 2022.

**Strengths**

1. **Frontmatter-defined themes with full code-highlighting palettes** (catppuccin, gruvbox, terminal-default, etc.) settable per-presentation via a single `theme: catppuccin-mocha` YAML key. The theme isn't a runtime toggle — it's per-document, version-controlled, predictable for the speaker.
2. **Selective code highlighting** — within a code block, the author can mark which lines are "live" for each slide step, dimming the rest. The dimmed lines drop to ~40% luminance, the live lines stay full. One block, multiple progressive reveals, no second slide.

**Weakness**

- Image rendering quality is bound to terminal protocol support (Kitty/iTerm2/WezTerm/Ghostty for full fidelity, Sixel for partial, ASCII fallback for the rest). On a "wrong" terminal a slide that's gorgeous becomes garbled. Visual polish is non-portable.

**Steal:** **frontmatter-pinned theme** (in our case `.wsm/config.toml` workspace-level `theme` key, with a global default in the central registry). A workspace can declare its preferred theme so a shared workspace dir reads the same on every dev's machine.

**Avoid:** **terminal-protocol-dependent visual fidelity for core UX.** Sixel images and Kitty graphics are great extras but cannot be load-bearing. `wsm` must look correct on tier-1 ANSI 16-color terminals; truecolor is a progressive enhancement.

**Sentiment**

- Praise (ssp.sh / ElnurBDa blog): "*simply beautiful*" — multiple developers report abandoning Keynote/Reveal.js for `presenterm` after one talk.
- Critique (GitHub issues): users on terminals without graphics protocol support hit a quality cliff. Polish doesn't gracefully degrade.

## Cluster B synthesis

**How they achieve "polished/GUI-like" without heavy borders.** Across all six, the dominant technique is **background layering, not box-drawing**. Harlequin, Glow, and Claude Code (fullscreen mode) all separate panes by a single-cell gutter and a 3–5% background lightness step rather than `┌─┐` chrome. The eye reads "two surfaces" from the lightness boundary; borders feel coarse by comparison. Where borders *are* used (Claude Code's prompt input, posting's panel headings), they are single-line, single-color, and state-bearing — never decorative.

**Role of background layering (bg.surface → bg.elevated).** This is the load-bearing primitive. The pattern is a two-level stack: `bg.surface` (everything default) and `bg.elevated` (the focused or selected element). Glow's selection-row, Harlequin's focused pane, Posting's selected list item, and Claude Code's fullscreen-mode user-message background are all `bg.elevated`. A *third* level (`bg.overlay`) appears only for modals (Posting's command palette, Harlequin's keybinding cheatsheet). Crucially, none of them use more than three background layers — depth comes from semantic meaning, not from a Material Design ramp.

**Modals, forms, palettes.** Three patterns recur:

1. **Floating centered palette** for command/jump — Posting and Harlequin both use a ~60% width, 40% height centered box on `bg.overlay` with a faint border. Always invoked by `ctrl+p` or similar.
2. **Slide-in side panel** for inspector/detail — Claude Code's `/usage`, Posting's request editor expansion. Lives on the right, 30–40% width, replaces no scrollback.
3. **Inline confirmation** rather than modal — Aider and Claude Code both prefer a yes/no prompt rendered into the normal scrollback over a popup dialog. Modals are reserved for *navigation* (palette, help), not for *decisions*.

**Color philosophy.** Every tool in the cluster converges on **monochrome + single accent + status triad**. The accent is one color (Claude Code's `claude` token, Charm's pink-magenta, Harlequin's pink-purple, Posting's cyan), used sparingly for the brand element and active focus. Status colors (`success`/`error`/`warning`) are a separate, semantically locked triad that *never* doubles as accent. The notable outlier is Claude Code's eight subagent colors, which is also Claude Code's most-criticized palette decision. Lesson for `wsm`: one accent, three status colors, two text shades, three background layers — eleven semantic tokens cover the entire surface.

**Animations and transitions worth keeping.** The cluster is restrained: no fade-ins, no easing on focus changes, no spinning skeumorphic loaders. The animations that *do* exist are all motion-of-content rather than motion-of-chrome:

- Harlequin's horizontal column scroll (content motion, ~120ms, ease-out)
- Claude Code's spinner with its shimmer-gradient brand-accent token (one element, never global)
- Presenterm's selective-highlight dimming (instant, but the *appearance* of progression is animation enough)
- Glow's scrollbar fade (appears on scroll, fades after ~600ms idle)

Gratuitous animations the cluster avoids: panel slide-in/out (Harlequin doesn't animate panel focus, just snaps the bg lift), modal fade (Posting's palette appears instantly), border-color cross-fades, mode-change transitions. The implicit rule: **animate content, never chrome.**

**Net guidance for `wsm`.** Build the visual hierarchy on two background tiers plus one overlay; one accent token plus a locked success/error/warning triad; borders only where they encode state (prompt mode, focus rules in lieu of full-pane chrome are usually better); a centered command palette and a right-side detail slide-in as the only two modal patterns; animation reserved for content motion. The Atelier direction is well-supported by this cluster — but with the explicit warning from Aider that *too minimal* reads as *under-built* in 2026. Surfacing state (mode borders, focus lift, status badges) is the difference between sparse and empty.

Sources: Anthropic Claude Code docs ([terminal-config](https://code.claude.com/docs/en/terminal-config), [theme tokens](https://blog.vincentqiao.com/en/posts/claude-code-theme/)); steipete.me ["The Signature Flicker"](https://steipete.me/posts/2025/signature-flicker); dev.to ["Terminal themes optimize for code"](https://dev.to/palo_alto_ai/terminal-themes-optimize-for-code-claude-code-isnt-code-54n7); [Claude Code Internals Part 11](https://kotrotsos.medium.com/claude-code-internals-part-11-terminal-ui-542fe17db016); HN [Posting v1](https://news.ycombinator.com/item?id=40926211), [Harlequin v1](https://news.ycombinator.com/item?id=38882526), [Glow](https://news.ycombinator.com/item?id=24810312); [darren.codes Posting 2.0](https://darren.codes/posts/posting2/); [harlequin.sh/docs/themes](https://harlequin.sh/docs/themes); [Charm Bubble Tea](https://github.com/charmbracelet/bubbletea) / [Lipgloss](https://github.com/charmbracelet/lipgloss); [presenterm README](https://github.com/mfontanini/presenterm); [aider.chat](https://aider.chat/); NxCode 2026 Aider vs OpenCode comparison.
