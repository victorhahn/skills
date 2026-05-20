---
name: tui-patterns
description: >
  Real-world TUI design patterns distilled from 18 reference applications across three
  clusters — devops/persistent-multi-panel (lazygit, lazydocker, gitui, k9s, atuin,
  zellij), modern/sparse (claude-code, aider, posting, harlequin, glow, presenterm), and
  dashboards/file managers/editors (btop, bottom, yazi, helix, ranger, tig). Use this
  skill whenever the user is designing or critiquing a TUI and wants grounded precedent
  instead of abstract principle: "how does lazygit handle X", "what's the precedent for
  Y", "show me how real tools do Z", "I'm picking a TUI layout", "Studio vs Atelier vs
  Concourse", "TUI anti-patterns", "what mistakes do TUIs make". Also pair this with the
  `tui-design` skill (universal design principles) and `cli-creator` skill (the agent CLI
  side of a tool) for any non-trivial TUI build. This skill is precedent and synthesis —
  read it before committing to a layout/color/keybinding direction.
---

# TUI Patterns — Real-World Precedent

A pattern catalog grounded in 18 reference TUIs. Pair with `tui-design` (universal principles) and `cli-creator` (the agent CLI side).

**When to read this:** before committing to a layout paradigm, before picking color/border treatment, before designing keybindings, or when critiquing a TUI you're already building. The synthesis sections (the three directions, the seven cross-cutting patterns, the ranked anti-patterns) compress the catalog so you can make informed choices without re-reading 18 tool postmortems.

---

## The Reference Catalog (compressed)

| Tool          | Framework             | Cluster | Steal                                                                  | Avoid                                                                          |
| ------------- | --------------------- | ------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| lazygit       | Go / gocui            | A       | Context-scoped footer + `?` keymap modal                                | Same key glyph meaning different things across panels                          |
| lazydocker    | Go / gocui            | A       | Rail-of-nouns + swappable-detail layout                                 | Default-on streaming of everything                                             |
| gitui         | Rust / Ratatui        | A       | Off-main-thread I/O with a "loading" affordance in panel headers        | Letting an architecture choice (async-first) drive feature triage              |
| k9s           | Go / tview            | A       | Vim `:` command mode as universal entry point                           | Resource-taxonomy leak into UI (no progressive disclosure)                     |
| atuin         | Rust / Ratatui        | A       | Sticky filter mode labeled in the footer (one word, one key to cycle)   | Hijacking universal keystrokes for a heavyweight UI                            |
| zellij        | Rust / custom         | A       | Mode-aware footer that rewrites for each mode                           | Spelling every modifier on every key                                           |
| claude-code   | Ink / TS / React      | B       | Mode-colored prompt border (state in chrome, zero status-bar real estate) | Eight differentiated accent hues (subagent colors); too many accents at once |
| aider         | Python / rich         | B       | Stream diffs into scrollback with a 1-char left rule instead of a box   | No persistent visual model of state                                            |
| posting       | Python / Textual      | B       | Jump-mode 2-char overlays on every interactive surface                  | Generic tab names ("Metadata") that hide commands                              |
| harlequin     | Python / Textual      | B       | Focus-via-bg-lift, not border-color-change                              | Shipping with one strongly-flavored theme as the only default                  |
| glow          | Go / Bubbletea        | B       | Left-edge color bar (1 cell × full row) as selection indicator          | Bolting tangential features onto a viewer                                      |
| presenterm    | Rust / crossterm      | B       | Frontmatter-pinned theme per-document                                   | Terminal-protocol-dependent visual fidelity for core UX                        |
| btop          | C++ / custom          | C       | Braille glyph density (2×4 dots/cell) with `braille → block → tty` tiers | Animating things faster than 1 Hz when they don't need it                    |
| bottom        | Rust / Ratatui        | C       | Per-widget `e` to expand any panel to full-screen and back              | Per-widget keymap dialects                                                     |
| yazi          | Rust / Ratatui        | C       | Async preview rendering — cursor movement never blocks on I/O           | Silence about your own bindings                                                |
| helix         | Rust / custom         | C       | The space-popup / which-key surface — discoverability primitive          | Inventing brand-new grammar from first principles                              |
| ranger        | Python / curses       | C       | `scope.sh` plugin contract (stdout → preview)                           | Synchronous file I/O on the render path                                        |
| tig           | C / ncurses           | C       | View-stack navigation (`Enter` drills, `q` pops) instead of modals      | "Press `h` for help" as the only discoverability surface                       |

Full strengths, weaknesses, sentiment quotes, and source citations for each tool live in:

- [`references/cluster-a-devops.md`](references/cluster-a-devops.md) — bordered persistent-multi-panel TUIs
- [`references/cluster-b-modern.md`](references/cluster-b-modern.md) — modern sparse Textual/Ink/Bubbletea lineage
- [`references/cluster-c-monitors.md`](references/cluster-c-monitors.md) — dashboards, file managers, editors

Read the relevant cluster file when you need depth on a specific tool's UI behavior, the exact source quotes, or the community-cited tradeoffs.

---

## The Seven Cross-Cutting Patterns

These are the patterns that recur across clusters with broad community validation. They generalize beyond their originating tools.

### 1. Density is earned, not avoided

The high-density end (Cluster A — lazygit, k9s) is not criticized for being dense. It's criticized for **redundant density** — zellij's status bar repeating "Ctrl" seven times. The sparse end (Cluster B — claude-code, posting) is praised when state is visibly surfaced (mode-bordered prompt, PRODUCTION banner) but criticized when minimalism reads as **under-built** (aider in 2026 vs OpenCode).

**Rule:** every visible element must earn its slot; every implicit element must surface its state somewhere. Pick density or sparseness based on what the user needs to see — never as an aesthetic default.

### 2. One accent, locked status triad

Strongest cross-cluster convergence. Across claude-code, glow, harlequin, posting, k9s, lazygit: **exactly one brand-accent color**, used for focus/selection/spinner/single brand element. Status colors (success/error/warning) are a semantically locked triad that **never** doubles as the accent. Claude-code's eight subagent colors is the cited outlier and the cited mistake.

**Rule:** one accent token. Never let `accent.primary` mean both "focused pane" and "warning." Status colors are reserved for status meaning, not decoration.

### 3. Borders — state-bearing or absent

Three modes across the catalog:

- **State-bearing single-line borders** — claude-code's mode-colored prompt; lazygit/k9s/gitui focused-pane border.
- **Background-layering instead of borders** — harlequin, glow, claude-code fullscreen. `bg.surface` ↔ `bg.elevated` 3–5% lightness step + 1-cell gutter reads as two panes without chrome.
- **Hybrid** — zellij's drop-shadow on floating panes (chrome only where it encodes elevation).

Critics consistently dislike: ASCII fallback borders (`+--+`), double-line borders, decorative borders that don't encode state.

**Rule:** rounded single-line borders (`╭─╮`) where a border encodes focus/state. Background layering everywhere else. No purely decorative chrome.

### 4. Modals, forms, palettes — three patterns

The whole catalog uses one of:

1. **Colon command mode** (k9s, vim, helix) — `:` opens a single-line input at the footer; type a verb. No separate modal element.
2. **Centered floating palette** (posting, harlequin) — ~60% width × 40% height; `Ctrl-P` or `:`. Fuzzy search over actions.
3. **Inline confirmation** (lazygit explicit-choice modal; aider yes/no in scrollback) instead of `y/n` prompts; never a popup for navigation.

Avoid: slide-in side panels for navigation (claude-code uses them for read-only inspectors only); modal dialogs for *decisions* (those go inline); nested modals (use view-stack navigation — tig's `Enter` drills, `q` pops — instead).

**Rule:** combine `:` palette + `/` filter (k9s + lazygit pattern). Reserve floating-modal chrome for forms (Create/Edit/Delete) and the Help popup. Use inline-explicit-choice ("Force delete" / "Cancel") for confirmations. View-stack navigation, not nested modals.

### 5. Three-layer discoverability stack

The strongest single recommendation across all three clusters. Three layers, all present at once:

1. **Footer hint strip** (lazygit, bottom, helix, every Cluster A tool). 1 row, always visible, context-scoped to current panel/mode.
2. **Which-key popup** (helix's space-popup is the gold standard). Press `?` (or a leader) and a translucent panel lists every legal next key with a short description, grouped by category.
3. **Command palette** (k9s `:`, posting `Ctrl-P`). Fuzzy search over the full action surface.

Tools with only one layer (yazi, tig) consistently get "discoverability lags polish" critiques.

**Rule:** all three layers, regardless of direction. Footer is context-scoped. `?` opens helix-style which-key. `:` opens palette. **All three derive from the same `keymap` table so they cannot disagree.**

### 6. Animation — motion of content, never chrome

The most-praised tool in the dashboard cluster (btop) explicitly **recommends throttling itself** — its README suggests `update_ms = 2000`. The most-praised tool in the modern cluster (harlequin) has one animation: horizontal column scroll on the results table (content motion). Tig has zero animations and is universally called "snappy."

Animation patterns that earn their keep: braille spinners at I/O boundaries (300ms+); 100–150ms fade-in for which-key popup so it doesn't strobe; harlequin-style horizontal content scroll; subtle scrollbar fade-out after idle.

Animation patterns that don't earn it: panel slide-in/out, modal fade, border color cross-fades, mode-switch animations (zellij criticized).

**Rule:** spinners only at I/O boundaries, capped at 1 Hz for status indicators, no chrome animation. One allowed flourish: a 100–150ms fade-in on the which-key popup. Otherwise, snap. Throttle status indicators to event-driven updates or 1 Hz max — never poll on a tick.

### 7. Async I/O is a UX feature, not an implementation detail

gitui (Cluster A) wins migrations from lazygit on large repos because git operations stream in without blocking the UI. yazi (Cluster C) wins against ranger because preview rendering is async — cursor movement never blocks on file reads. The HN top comments for both single this out: *"the UI stays responsive while [I/O] happens in the background."*

**Rule:** every shell-out, file read, or network call must run off the render thread. Show a panel-header spinner while loading. Cursor movement, filter typing, and tab switching must never gate on file or subprocess I/O.

---

## Three Direction Archetypes

Three internally-consistent design directions emerge from the catalog. Pick one as the spine of your TUI; mix in primitives from the others where they fit.

### Direction A — Studio

Inherits from **lazygit, lazydocker, gitui, k9s.** Bordered persistent multi-panel; context-scoped footer; rounded single-line borders with focus encoded in border color; rail-of-nouns + swappable-detail layout.

Viable only if **consistency holds across every panel**. Same key glyph = same action everywhere. Footer compresses gracefully under 100 cols. One accent. No per-panel keymap dialects. The cluster A overarching lesson is that the criticisms in this lineage are *consistency failures*, not density failures.

**Use when:** the tool surfaces several independent pieces of state that the user needs to compare or cross-reference simultaneously (git state, container state, k8s resources). Spatial memory is the payoff.

### Direction B — Atelier

Inherits from **claude-code, harlequin, glow, posting.** Borderless; background-layering via `bg.surface` ↔ `bg.elevated`; one accent; state-bearing chrome where used (mode-colored prompt border).

Pure minimalism is **insufficient** in 2026 (Aider critique). Atelier must compensate for the missing border chrome with **explicit state surfacing** — mode-colored prompt borders (claude-code), focus-via-bg-lift (harlequin), small dashboard widgets (btop sparklines, throttled), badges for state counts. The discipline is **"calm but never silent."**

**Use when:** the tool centers on one primary workflow (a chat, a query editor, a document) and other state is supporting. Aesthetic ceiling is high; the trap is under-disclosure of state.

### Direction C — Concourse

Inherits from **k9s** (`:` command mode, breadcrumbs), **helix** (space-popup which-key), **tig** (view-stack navigation), **zellij** (mode-aware footer).

The top-tab metaphor implicitly demotes the workspace/file list to a sidebar or popup. Items become *documents* you switch between; the tab strip carries state per item; the detail pane fills the canvas. Sidebar is opt-in. Discoverability handled fully via which-key popup + palette since the visible footer chip count is smaller.

**Use when:** the tool's central abstraction is "a thing you switch between and work inside" (editors, REPLs, document browsers). Commits to the workspace-as-document metaphor.

### Cross-direction non-negotiables

Regardless of which direction you pick, these belong to all three:

- **Three-layer discoverability**: footer hint strip + `?` which-key popup + `:` command palette. All from the same `keymap` table.
- **Async-everywhere I/O**: every shell-out off the render thread; panel headers show spinner during load.
- **One accent token + locked status triad.**
- **Event-driven / throttled (≤1 Hz) status updates** — no per-tick animation.
- **View-stack navigation** for drill-in (`Enter` opens, `Esc`/`q` pops back) — never a popup for navigation.
- **Inline confirmations** with explicit-choice labels for destructive actions, not `y/n` modal popups.
- **Tier-1 must be 16-color ANSI**; truecolor is enhancement, never load-bearing.

---

## Ranked Anti-Patterns

Ordered by how badly they hurt community reception across the surveyed tools.

| #   | Anti-Pattern                                                          | Concrete fix                                                                  |
| --- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1   | **Same key meaning different things across panels.**                  | One global keymap. Panel-specific verbs use distinct keys, not overloaded ones. |
| 2   | **"Press `h` for help" as the only discoverability surface.**         | All three discoverability layers (footer / `?` popup / `:` palette).          |
| 3   | **Synchronous I/O on the render path.**                               | Async everywhere; panel-header spinners. yazi vs ranger is the cautionary tale. |
| 4   | **Hijacking universal keystrokes (Enter, Up, Ctrl-C) for heavy UI.**  | Atuin's up-arrow takeover; never bind a key users have decades of muscle for. |
| 5   | **Pure minimalism that doesn't surface state.**                       | If you go Atelier, compensate with state-bearing chrome (mode borders, badges). |
| 6   | **Multiple competing accents.**                                       | One accent. Status triad never doubles as accent.                             |
| 7   | **Spelling out every modifier on every key.**                         | Mnemonic single letters; modifiers implied by context.                        |
| 8   | **Generic tab names that hide commands.**                             | Tab/section names are *what you do here*, not *what kind of data*.            |
| 9   | **Aggressive refresh rates.**                                         | Event-driven or ≥1 Hz. btop itself recommends 2000ms.                         |
| 10  | **Per-widget keymap dialects.**                                       | One keymap, same meanings everywhere. Help is global, not per-panel.          |
| 11  | **Resource-taxonomy leak into UI.**                                   | Progressive disclosure. Don't expose ~80 entities via `:` from minute one.    |
| 12  | **Modal popups for decisions instead of inline yes/no.**              | Modals for forms only. Decisions go inline with explicit-choice labels.       |
| 13  | **Polish that doesn't degrade gracefully.**                           | Tier-1 = 16-color ANSI. Truecolor enhances; sixel/Kitty are bonus, not core.  |
| 14  | **Border decoration without state-bearing.**                          | If a border is there, it means something. Otherwise background-layer.         |

---

## How to Use This Skill

1. **Starting a TUI design.** Read the three direction archetypes. Pick one as your spine. Read the relevant cluster file for the tools that inherit into that direction.
2. **Stuck on a specific decision (color, border, modal, keybinding).** Jump to the relevant cross-cutting pattern (sections 1–7). Each pattern names the originating tools — read those entries in the cluster files for depth.
3. **Critiquing an existing TUI.** Walk the anti-pattern list. Tools usually fail two or three at the same time. Fix the top-ranked one first.
4. **Designing the agent CLI side of the same tool.** Use `cli-creator`. The Node/TS + Ink stack is the assumed surface for the human-facing side.
5. **Implementing the patterns.** Use `tui-design` (universal principles) and `tui-design/references/ink-implementation.md` (Ink 7 / React 19 component recipes).

---

## What This Skill is NOT

- Not a framework reference. The patterns apply to Ink, Ratatui, Textual, Bubbletea, gocui — anywhere.
- Not a substitute for testing in real terminal emulators (tmux, alacritty, iTerm2, Windows Terminal).
- Not exhaustive. 18 tools is a deep sample, not a complete one. When in doubt, look at how a tool you admire solved the same problem and ask whether its constraints match yours.
- Not opinionated about the *which* (Studio vs Atelier vs Concourse). It's opinionated about the *how* — once you pick a direction, the cross-cutting patterns and anti-patterns apply equally.
