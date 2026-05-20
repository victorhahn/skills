# Cluster C — Monitors, File Managers, Editors, Status-Lines

**About this file:** Per-tool research on six TUIs spanning dashboards, file managers, editors, and status-line ergonomics. Focus areas: dashboard widgetry, Miller-column previews, post-modal discoverability, async I/O as UX.

> Some passages reference "workspace-manager" or "wsm" as a concrete case study from the project where these notes were originally compiled. Treat those passages as illustrative; the lessons generalize. The "Steal" / "Avoid" callouts are the generalizable takeaways.

## btop (C++ / custom ncurses-style renderer)

- **Stats**: ~32.3k stars; first stable release Sep 2021 (continuation of `bashtop`/`bpytop`); written in C++23.
- **Strength 1 — Braille sparklines as the polish ceiling.** btop's CPU/memory/network graphs use Unicode Braille (U+2800–U+28FF) which packs a 2×4 dot grid into a single cell, giving graphs roughly 8× the resolution of half-block characters on the same row count. A 3-line CPU widget actually conveys micro-spikes. The author exposes this as an explicit tri-mode setting (`braille` / `block` / `tty`) so users on fontless TTYs degrade gracefully — that fallback contract is what makes the high-end look bold rather than fragile.
- **Strength 2 — "Game-inspired menu" framing and presets.** btop deliberately treats its config screen, theme selector, and preset switcher as a stylized in-app menu rather than a separate `--config` flag. The result is that "configuration" is an interactive surface, not an external file ritual. Mouse + keyboard work everywhere.
- **Weakness / controversy — refresh rate honesty.** The default minimum is 100 ms and the README now recommends `update_ms = 2000` "for better sample times for graphs." Anything faster makes input laggy (input is processed only on tick) and worsens reported accuracy (see issue [#793](https://github.com/aristocratos/btop/issues/793) and discussion [#421](https://github.com/aristocratos/btop/discussions/421)). The fact that the most visually impressive TUI on the market quietly recommends throttling itself is a real signal: there is a CPU/polish tradeoff and naïve "60fps TUI" is a trap.
- **Steal**: Treat sparklines as a first-class semantic widget with `braille | block | tty` rendering tiers, and let theme/tier auto-detect (`NO_COLOR`, `*256color*`, `COLORTERM=truecolor`). We already do this for color; do it for glyph density too.
- **Avoid**: Animating things faster than 1 Hz when they don't need to. Workspace health does not change at 30 fps; pretending it does just burns battery.
- **Sentiment**: Praise — "the htop alternative" framing dominates roundups; *terminal.guide* calls it "beautiful TUI resource monitor." Critique — HN thread [45254907](https://news.ycombinator.com/item?id=45254907) leads with "you might want to decrease the btop refresh rate" — i.e., the community's top tip is "the defaults are too aggressive."

## bottom (Rust / tui-rs → ratatui)

- **Stats**: ~13.3k stars; written in Rust; uses tui-rs / ratatui (per the official `ratatui/awesome-ratatui` list); active since 2019.
- **Strength 1 — Layout is data.** bottom's killer feature is its TOML-driven widget layout: users describe a grid of rows/columns with widget types and ratios, and the renderer obeys. This is the same primitive Ratatui exposes (`Layout::default().constraints(...)`), surfaced to end users. The implication for wsm: if our panel layout is data (TOML), users can build their own dashboards without forking the binary.
- **Strength 2 — Per-widget expand (`e` key).** Any widget can be "zoomed" to full-screen and back, preserving keyboard context. This is the killer pattern for dense dashboards: dense overview by default, focus mode on demand, single keystroke between them.
- **Weakness — configuration sprawl.** "Higher resource usage than minimal tools and configuration can be complex" is the recurring critique in roundups. Every widget has its own keybindings, and the config surface is large enough that most users live with defaults forever.
- **Steal**: The "expand current panel to full screen" affordance. Studio/Atelier/Concourse all have multi-panel layouts — we need a one-key zoom (`z` or `Enter`) on the focused panel.
- **Avoid**: Per-widget keymap dialects. wsm should have ONE keymap that means the same thing in every panel; bottom's "press `?` again, the help is different now" model is a learnability tax.
- **Sentiment**: Praise — *LinuxBlog.io* notes the "polished" customization. Critique — Ubuntu manpage discussion and OSTechNix reviews both single out the config curve.

## yazi (Rust / Ratatui)

- **Stats**: ~38.2k stars; first public release ~2023; Rust + Lua plugin system; explicitly built on async I/O (tokio).
- **Strength 1 — Miller columns + hot-rendered preview.** Three-column layout (parent / current / preview). The third column renders images natively via Kitty graphics protocol, iTerm2 inline images, Sixel, and Konsole's kitty-old protocol, with Überzug++/Chafa fallbacks. The crucial detail: preview rendering is async — moving the cursor never blocks the UI, the preview just *catches up*.
- **Strength 2 — Async-everywhere as a design constraint.** From the README: "All I/O operations are asynchronous, CPU tasks are spread across multiple threads." On HN [37531434](https://news.ycombinator.com/item?id=37531434): *"the UI stays responsive while a file copy happens in the background."* This is the single biggest UX delta vs ranger — it isn't a feature, it's an architectural invariant.
- **Weakness — discoverability.** From the same HN thread: *"even figuring out that you can press `?` to open the help panel took me way too long."* 38k stars and still no inline hint surface; the project is fast but mute.
- **Steal**: A right-pane preview that hot-renders `CLAUDE.md` (or `.wsm/config.toml`) for whichever workspace is selected in the sidebar. Render asynchronously so cursor movement is never gated on file I/O. Use a small spinner glyph in the preview header while loading.
- **Avoid**: Yazi's silence about its own bindings. Whatever else we do, the workspace list needs a visible hint row (`enter open · c create · d delete · ? more`).
- **Sentiment**: Praise — *"the performance is excellent…the code is really good in this. It's super simple to read"* (HN). Critique — *"could use better documentation / quick-start guide"* (same thread).

## helix (Rust / custom TUI)

- **Stats**: ~44.4k stars; first release ~2021; Rust; tree-sitter built in; no plugin system (yet).
- **Strength 1 — The space-popup is the discoverability primitive.** Pressing `Space` (or `g`, or any minor-mode prefix) opens a popup listing every next key with a short description. From the *terminal.guide* review: *"Helix has a very discoverable UI, which is quite rare for a terminal application…when entering space, match or goto modes a popup appears, with the further bindings and a small explanation."* You learn the editor by exploring it; no `:help` required.
- **Strength 2 — Selection-first grammar with infobar feedback.** Helix shows your current selection state in the statusline (mode, register, selection count) so multi-cursor edits are never ambient — they're always visible. The infobar is the single source of truth for "what mode am I in and what just happened."
- **Weakness — no `marks`, no Vim muscle memory.** Felix Knorr's [1.5-year review](https://felix-knorr.net/posts/2025-03-16-helix-review.html): *"the repeat command only repeats the last action, not the motion before that, which makes it much less useful…it feels like driving and steering left, but your car turns right."* The post-modal grammar is principled but loses Vim refugees.
- **Steal**: A which-key popup for wsm. Press `?` (or hold a leader key) and a translucent panel slides in listing every legal next key with a one-line description, grouped by category. This is *the* answer to "how do users discover the command palette without reading docs."
- **Avoid**: Designing a brand-new grammar from first principles. Our users will arrive with muscle memory from `lazygit`, `k9s`, `git`. Match those defaults; don't invent new verbs for the same nouns.
- **Sentiment**: Praise — *"you basically don't need to configure Helix"* (rushter.com). Critique — Felix Knorr again: *"I can't agree that this keymap is more effective"* than Vim's action-scope model. Discoverability is loved; the underlying grammar is contested.

## ranger (Python / curses)

- **Stats**: ~17.2k stars; project dates to 2009; pure Python on curses.
- **Strength 1 — Miller columns as a canonical pattern.** Ranger is *the* reference implementation of three-pane Miller columns in a terminal. Every modern file manager (yazi, lf, nnn, joshuto) is positioned against it. The pattern works because peripheral vision picks up the parent column without focus.
- **Strength 2 — `scope.sh` as a plugin contract.** Previews are produced by an external shell script (`scope.sh`) that dispatches on mime type. Anyone can edit it; no recompilation. The contract — stdout becomes the preview — is dead simple and has outlived every Python-API plugin system.
- **Weakness — blocking everything.** Issues [#928](https://github.com/ranger/ranger/issues/928), [#2121](https://github.com/ranger/ranger/issues/2121), [#2717](https://github.com/ranger/ranger/issues/2717): image preview can freeze the entire terminal; large directories load slowly; `w3mimgdisplay` leaks memory until the box hangs. Synchronous Python on curses cannot win against yazi's async tokio runtime in 2026.
- **Steal**: The `scope.sh` philosophy. Let users drop a `~/.config/workspace-manager/preview.sh` that takes a workspace path and writes preview text to stdout. Default implementation reads `CLAUDE.md`; advanced users can run `glow`, `bat`, whatever.
- **Avoid**: Synchronous file I/O on the render path. We're picking Ink (Node) not Rust — single-threaded — so async-everywhere matters even more.
- **Sentiment**: Praise — *"vim-like, scriptable, hackable"* (Hund's blog). Critique — Slant: *"enabling file previews makes it even slower…has a steeper learning curve."* Lovable but visibly aging.

## tig (C / ncurses)

- **Stats**: ~13.2k stars; first release 2006; pure C on ncurses; latest release tig-2.6.0 (Sep 2025) — twenty years old and still cut.
- **Strength 1 — View stack as the navigation model.** Tig's views (`main`, `log`, `diff`, `tree`, `blob`, `blame`, `refs`, `status`, `stage`) are a stack: open one with `Enter`, pop back with `q`. There is no "modal dialog" concept; everything is a view that pushes on a stack. The mental model is identical to a web browser back-button and is instantly intuitive.
- **Strength 2 — `tigrc` as a small, well-scoped DSL.** Keybindings are scoped per-view with a clean fallthrough hierarchy: view bindings → generic keymap → built-ins. From the docs: *"keys are mapped by first searching the keybindings for the current view, then the keybindings for the generic keymap, and last the default keybindings."* No global key conflicts; everything is local-by-default.
- **Weakness — discoverability is "press `h` and read."** No popup, no hint row, no command palette. You either know the keys or you read the help screen. By 2026 standards this is austere.
- **Steal**: View-stack navigation. `Enter` drills into a workspace's repo list / scripts / links / hooks; `Esc`/`q` pops back. No floating modals for navigation — modals are reserved for confirmations and pickers.
- **Avoid**: "press `h` for help" as the only discoverability surface.
- **Sentiment**: Praise — *"quicker and less resource-intensive…suitable for remote environments"* (Slant). Critique — same Slant entry: *"has a steeper learning curve than GUI clients which are usually more intuitive."* HN [30706467](https://news.ycombinator.com/item?id=30706467) reads as a wholesale defection to lazygit's visual model.

---

## Cluster C synthesis

### Dashboard widgets raise the polish ceiling — but only at the right cadence

btop and bottom prove that **a single well-rendered sparkline outranks ten plain status lines** for perceived polish. The mechanism is Unicode Braille (8 dots/cell) and the constraint is refresh rate: btop's own defaults capping at 100 ms and recommending 2000 ms is the design lesson. For wsm, this means: small braille-rendered widgets on the dashboard panel (recent activity per workspace, last-N-days commit counts, healthcheck rolling status) that update on file-change events or once a minute — not on a tick. The polish comes from glyph density, not framerate.

### Status-line patterns: hint-row beats which-key beats nothing

Three patterns ranked by discoverability ROI:

1. **helix's contextual popup** (best). Press a leader, a translucent panel appears listing legal next keys with descriptions. This is the gold standard and the *terminal.guide* review calls it out explicitly: *"discoverability is important — if users don't know a feature exists, they won't use it."* For wsm: implement a `?` popup grouped by category (`workspace`, `repo`, `worktree`, `view`).
2. **bottom's persistent footer hint strip** (good). Always-visible row showing `[?] help [q] quit [tab] cycle [e] expand`. Costs one row; pays back forever. This is the floor — wsm should already have this.
3. **tig's "press h for help"** (insufficient by 2026). Hidden discoverability is now a defect.

helix's space popup *is* a which-key implementation — call it that internally. Pair it with the always-visible footer hint strip; the two are not redundant (footer = current-context hints, popup = full discovery on demand).

### Animation: subtraction, not addition

The honest answer from this cluster: **the most polished tool here (btop) explicitly recommends slowing itself down**. Yazi achieves "feels fast" through async I/O, not through animation. tig has zero animation and is universally praised as snappy. The takeaway for wsm:

- **No transition animations** between panels or modals — flicker > slide-in in a TUI.
- **Spinners only at I/O boundaries** (loading workspace metadata, running `wsm doctor`). Single braille spinner glyph.
- **Throttled updates** for health/status indicators (1 Hz max, ideally on event).
- One small allowance: a 100–150 ms fade-in on the which-key popup so it doesn't strobe. That's it.

### Preview panes for our use case

The Miller-column third pane is **directly applicable to wsm**. The mapping:

| ranger/yazi  | workspace-manager                                |
|--------------|--------------------------------------------------|
| parent dir   | category / tag / group sidebar                   |
| current dir  | workspace list                                   |
| preview pane | rendered `CLAUDE.md` + `.wsm/config.toml` digest |

Render the preview pane async (yazi pattern, not ranger pattern) — never block cursor movement on file reads. Use `bat`-style syntax highlighting for the TOML, and dim/wrap the CLAUDE.md so it reads as documentation, not as a wall. The `scope.sh` lesson from ranger: make the preview renderer pluggable via a user script so power users can swap in `glow`, `mdcat`, or `bat`.

### Discoverability for keyboard-first UX

Helix's contribution to the genre is that **modal/keyboard-first does not have to mean hidden**. Three layers, all simultaneously visible at the right moment:

1. **Footer hint strip** — current-context legal keys, always visible (cost: 1 row).
2. **Which-key popup on leader** — full menu of next-keys with descriptions (cost: opens on `?` or `Space`-equivalent).
3. **Command palette** — fuzzy search over every action (cost: opens on `:`, `Ctrl-P`).

All three exist in Helix. Yazi and tig have only #3 (or weaker). btop has none — it relies on the "game menu" aesthetic instead, which works in btop's narrow domain (one screen, ~20 keys) but won't scale to wsm's surface (workspaces × repos × scripts × hooks × links).

**Recommendation for the visual prototype phase**: regardless of whether we land on Studio / Atelier / Concourse, all three layers above should be in scope. The direction choice is about *density and chrome*; discoverability is a cross-cutting requirement that all three directions must meet.
