---
name: tui-creator
description: >
  Design and implement interactive terminal user interfaces (TUIs) — layout, color,
  focus, keybindings, animation, accessibility, and real-world precedent. Framework-
  agnostic patterns (Ratatui, Ink, Textual, Bubbletea, gocui) plus deep Ink 7 / React 19
  implementation recipes. Use this skill whenever the user is designing, building, or
  critiquing a terminal interactive surface. Trigger on: "design a TUI", "build a
  terminal UI", "TUI layout", "split panes", "panel layout", "terminal dashboard",
  "keybinding design", "TUI color palette", "focus management", "modal dialogs",
  "terminal accessibility", "Ink components", "Ratatui layout", "Textual widgets",
  "Bubbletea views", "Studio vs Atelier vs Concourse", "TUI anti-patterns", "how does
  lazygit / k9s / btop / yazi / helix / claude-code / harlequin / posting / glow / tig
  handle X", "what's the precedent for Y in a TUI", "pick a TUI direction". Also fires
  on any critique of an existing TUI's discoverability, density, color choices, or
  responsiveness. If the same tool also needs an agent-friendly JSON command surface
  (the non-interactive side of a CLI binary), also invoke `cli-creator` for the binary
  structure, JSON contract, auth handling, and lazy-loading the TUI from the same entry
  point.
---

# TUI Creator

Design and implement exceptional terminal user interfaces. Framework-agnostic principles with grounded precedent from 18 reference TUIs, plus an Ink 7 / React 19 implementation track when the target is Node/TypeScript.

**Core philosophy:** TUIs earn their power through spatial consistency, keyboard fluency, and information density that respects human attention. Design for the expert's speed without abandoning the beginner's discoverability.

## How to use this skill

Skim this file once at the start of any TUI work. It's the synthesis layer — the decisions you'll make before any code is written. Depth lives in references:

- [`references/design-principles.md`](references/design-principles.md) — Full universal design system: responsive layout, four-layer keybinding design, color tiers (16 ANSI / 256 / true color), semantic color slots, data viz widgets, animation rules, the seven principles, accessibility checklist. Read after picking a direction here.
- [`references/cluster-a-devops.md`](references/cluster-a-devops.md) — Bordered persistent-multi-panel TUIs (lazygit, lazydocker, gitui, k9s, atuin, zellij). Full strengths/weaknesses/source quotes per tool.
- [`references/cluster-b-modern.md`](references/cluster-b-modern.md) — Modern sparse Textual/Ink/Bubbletea lineage (claude-code, aider, posting, harlequin, glow, presenterm).
- [`references/cluster-c-monitors.md`](references/cluster-c-monitors.md) — Dashboards, file managers, editors (btop, bottom, yazi, helix, ranger, tig).
- [`references/ink-implementation.md`](references/ink-implementation.md) — Ink 7 / React 19 component and hook recipes. The concrete how-to once you've picked your design direction. Read when writing Node/TS TUI code.
- [`references/app-patterns.md`](references/app-patterns.md) — Real-world TUI app design analysis and inspiration.
- [`references/visual-catalog.md`](references/visual-catalog.md) — Unicode character reference tables and border style gallery.

## The design process

```
What are you building?
       ↓
Pick a direction (Studio / Atelier / Concourse)
       ↓
Pick a layout paradigm (Persistent Multi-Panel / Miller Columns / Drill-Down / Widget Dashboard / IDE Three-Panel / Overlay / Header+List)
       ↓
Design the interaction model (keybindings, focus, search, help, dialogs)
       ↓
Define the visual system (color tiers, semantic slots, typography, borders)
       ↓
Validate against the ranked anti-patterns
       ↓
Ship it
```

The direction is your spine — it governs the next four choices. The layout paradigm constrains your interaction model. Color and motion serve content, not the other way around.

---

## 1. Pick a Direction

Three internally-consistent design directions emerge from the 18-tool catalog. Pick one as your spine; mix in primitives from the others where they fit.

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

---

## 2. Pick a Layout Paradigm

Direction governs the spine; the paradigm governs the floor plan. Pick by what you're building:

| App Type           | Paradigm                 | Examples            | Direction fit     |
| ------------------ | ------------------------ | ------------------- | ----------------- |
| File manager       | Miller Columns           | yazi, ranger        | Studio            |
| Git / DevOps tool  | Persistent Multi-Panel   | lazygit, lazydocker | Studio            |
| System monitor     | Widget Dashboard         | btop, bottom, oxker | Studio/Atelier    |
| Data browser / K8s | Drill-Down Stack         | k9s, diskonaut      | Concourse         |
| SQL / HTTP client  | IDE Three-Panel          | harlequin, posting  | Atelier/Concourse |
| Shell augmentation | Overlay / Popup          | atuin, fzf          | Atelier           |
| Log / event viewer | Header + Scrollable List | htop, tig           | Studio            |

Brief notes — see `references/design-principles.md` §1 for full ASCII sketches, when-to-use, and key rules.

- **Persistent Multi-Panel** — All panels visible simultaneously; focus shifts between them. Users build spatial memory. Panels stay fixed across sessions.
- **Miller Columns** — Three-pane past/present/future navigation. Parent (left), current (center), preview (right). Preview adapts to selection type.
- **Drill-Down Stack** — `Enter` descends, `Esc` ascends. Browser-like through deep hierarchies. Always show the current navigation path as a breadcrumb. `:resource` command-mode for direct jumps.
- **Widget Dashboard** — Self-contained widget panels with independent data streams. Each widget has its own title. Braille/block characters for density.
- **IDE Three-Panel** — Sidebar (left), editor/main (center), detail/output (bottom). Tab bar along top. Sidebar toggles with a single key.
- **Overlay / Popup** — TUI appears on demand over the shell, disappears after use. Configurable height. Never disrupt scrollback.
- **Header + Scrollable List** — Fixed header with meters/stats, scrollable data below, function bar at bottom. Sort by the most actionable dimension by default.

---

## 3. The Seven Cross-Cutting Patterns

These recur across all three clusters with broad community validation. They generalize beyond their originating tools.

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

## 4. Cross-direction Non-Negotiables

Regardless of which direction you pick, these belong to all three:

- **Three-layer discoverability**: footer hint strip + `?` which-key popup + `:` command palette. All from the same `keymap` table.
- **Async-everywhere I/O**: every shell-out off the render thread; panel headers show spinner during load.
- **One accent token + locked status triad.**
- **Event-driven / throttled (≤1 Hz) status updates** — no per-tick animation.
- **View-stack navigation** for drill-in (`Enter` opens, `Esc`/`q` pops back) — never a popup for navigation.
- **Inline confirmations** with explicit-choice labels for destructive actions, not `y/n` modal popups.
- **Tier-1 must be 16-color ANSI**; truecolor is enhancement, never load-bearing.
- **Keyboard-first, mouse-optional** — every feature reachable via keyboard. `Shift+click` bypasses mouse capture for text selection.
- **Spatial consistency** — panels stay in fixed positions; users build mental maps.

---

## 5. Ranked Anti-Patterns

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
| 9   | **Aggressive refresh rates.**                                         | Event-driven or ≤1 Hz. btop itself recommends 2000ms.                         |
| 10  | **Per-widget keymap dialects.**                                       | One keymap, same meanings everywhere. Help is global, not per-panel.          |
| 11  | **Resource-taxonomy leak into UI.**                                   | Progressive disclosure. Don't expose ~80 entities via `:` from minute one.    |
| 12  | **Modal popups for decisions instead of inline yes/no.**              | Modals for forms only. Decisions go inline with explicit-choice labels.       |
| 13  | **Polish that doesn't degrade gracefully.**                           | Tier-1 = 16-color ANSI. Truecolor enhances; sixel/Kitty are bonus, not core.  |
| 14  | **Border decoration without state-bearing.**                          | If a border is there, it means something. Otherwise background-layer.         |
| 15  | **Colors break on different terminals.**                              | Use 16 ANSI as foundation. Test 3+ emulators + light/dark themes.             |
| 16  | **Flickering / full redraws.**                                        | Double buffer + synchronized output + batched writes. Overwrite, never clear. |
| 17  | **Broken on Windows / WSL.**                                          | Test on Windows Terminal. Avoid advanced Unicode beyond box-drawing.          |
| 18  | **No accessibility support.**                                         | Respect `NO_COLOR`, provide monochrome mode, never color-only meaning.        |

---

## 6. The Reference Catalog (18 tools, compressed)

| Tool        | Framework        | Cluster | Steal                                                                     | Avoid                                                                          |
| ----------- | ---------------- | ------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| lazygit     | Go / gocui       | A       | Context-scoped footer + `?` keymap modal                                  | Same key glyph meaning different things across panels                          |
| lazydocker  | Go / gocui       | A       | Rail-of-nouns + swappable-detail layout                                   | Default-on streaming of everything                                             |
| gitui       | Rust / Ratatui   | A       | Off-main-thread I/O with a "loading" affordance in panel headers          | Letting an architecture choice (async-first) drive feature triage              |
| k9s         | Go / tview       | A       | Vim `:` command mode as universal entry point                             | Resource-taxonomy leak into UI (no progressive disclosure)                     |
| atuin       | Rust / Ratatui   | A       | Sticky filter mode labeled in the footer (one word, one key to cycle)     | Hijacking universal keystrokes for a heavyweight UI                            |
| zellij      | Rust / custom    | A       | Mode-aware footer that rewrites for each mode                             | Spelling every modifier on every key                                           |
| claude-code | Ink / TS / React | B       | Mode-colored prompt border (state in chrome, zero status-bar real estate) | Eight differentiated accent hues (subagent colors); too many accents at once   |
| aider       | Python / rich    | B       | Stream diffs into scrollback with a 1-char left rule instead of a box     | No persistent visual model of state                                            |
| posting     | Python / Textual | B       | Jump-mode 2-char overlays on every interactive surface                    | Generic tab names ("Metadata") that hide commands                              |
| harlequin   | Python / Textual | B       | Focus-via-bg-lift, not border-color-change                                | Shipping with one strongly-flavored theme as the only default                  |
| glow        | Go / Bubbletea   | B       | Left-edge color bar (1 cell × full row) as selection indicator            | Bolting tangential features onto a viewer                                      |
| presenterm  | Rust / crossterm | B       | Frontmatter-pinned theme per-document                                     | Terminal-protocol-dependent visual fidelity for core UX                        |
| btop        | C++ / custom     | C       | Braille glyph density (2×4 dots/cell) with `braille → block → tty` tiers  | Animating things faster than 1 Hz when they don't need it                      |
| bottom      | Rust / Ratatui   | C       | Per-widget `e` to expand any panel to full-screen and back                | Per-widget keymap dialects                                                     |
| yazi        | Rust / Ratatui   | C       | Async preview rendering — cursor movement never blocks on I/O             | Silence about your own bindings                                                |
| helix       | Rust / custom    | C       | The space-popup / which-key surface — discoverability primitive           | Inventing brand-new grammar from first principles                              |
| ranger      | Python / curses  | C       | `scope.sh` plugin contract (stdout → preview)                             | Synchronous file I/O on the render path                                        |
| tig         | C / ncurses      | C       | View-stack navigation (`Enter` drills, `q` pops) instead of modals        | "Press `h` for help" as the only discoverability surface                       |

Full strengths, weaknesses, sentiment quotes, and source citations live in the three cluster files in `references/`.

---

## 7. Implementation Track

Once you've picked a direction and a layout:

- **General implementation guidance** (responsive resize handling, keybinding layers, focus management, color tier detection, semantic color slots, data viz widgets, animation timing, the compatibility checklist) → `references/design-principles.md`.
- **Ink 7 / React 19 specifics** (Yoga flexbox mapping for each paradigm, `useFocus`/`useFocusManager` recipes, the theme module pattern, `borderStyle`/`borderColor` driven by state, the flicker fix, status throttling, footer/which-key/palette implementation, inline-explicit-choice confirmation, accessibility hooks) → `references/ink-implementation.md`.
- **Ratatui / Textual / Bubbletea / gocui specifics** are not bundled — the design principles and the cluster files cover the cross-framework patterns; framework-specific component APIs live in those projects' own docs.

If the same binary also exposes an agent-friendly JSON command surface, `cli-creator` covers the non-interactive side (binary structure, JSON contract, auth, lazy-loading the TUI from the CLI entry).

---

## What this skill is NOT

- Not a framework-specific API reference for non-Ink toolkits. The patterns generalize; the components don't.
- Not an excuse to over-decorate terminal tools. Borders and colors serve content, not ego. The content IS the interface.
- Not a substitute for testing in real terminal emulators (tmux, alacritty, iTerm2, Windows Terminal, zellij, screen).
- Not exhaustive. 18 tools is a deep sample, not a complete one. When in doubt, look at how a tool you admire solved the same problem and ask whether its constraints match yours.
- Not opinionated about the *which* (Studio vs Atelier vs Concourse). It's opinionated about the *how* — once you pick a direction, the cross-cutting patterns and anti-patterns apply equally.
