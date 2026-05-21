# Cluster A — Devops / persistent-multi-panel TUIs

**About this file:** Per-tool research on six TUIs in the bordered, persistent-multi-panel lineage — tools that show many boxes at once and keep them on screen. Each tool covers framework, strengths, weaknesses, what to steal, what to avoid, and primary-source sentiment.

> Some passages reference "workspace-manager" or "wsm" as a concrete case study from the project where these notes were originally compiled. Treat those passages as illustrative; the underlying lessons generalize to any TUI in this style. The "Steal" / "Avoid" callouts are the generalizable takeaways.

Stars and version numbers are as of May 2026.

## lazygit

- **Framework / language:** Go + gocui (jesseduffield's own fork of gocui); JSX-free, hand-rolled view system. Active since 2018.
- **Stars:** ~78k. Current v0.61.1 (Apr 2026), 179 releases.
- **Strength 1 — Contextual footer that adapts per panel.** Each focused panel rewrites the bottom hint row with only the keys relevant to that panel; pressing `?` opens a full keymap modal that is also context-scoped. This means users never see the full keymap unless they ask, but never lose access to it either.
- **Strength 2 — Inline confirmation modals with binary-choice framing.** Destructive operations (force push, hard reset, discard) interrupt with a centered modal that names the exact divergence ("upstream has 3 commits you don't have") and offers two labeled choices rather than a y/n prompt. This is the single most-cited UX win in reviews — it inverts "memorize the consequences" into "the tool explains what will happen."
- **Weakness / controversial choice:** Inconsistent global keybindings — the maintainer himself filed [issue #1712](https://github.com/jesseduffield/lazygit/issues/1712) noting that `R` does different things across panels, that `d` is the only deletion key (no Backspace), and that hard-reset requires "g then down twice then enter." He's explicit that newcomer accessibility and long-term-user speed pull in opposite directions and lazygit hasn't fully resolved the tension.
- **Steal:** The context-scoped footer + `?` overlay pattern. It's the cleanest answer to "discoverability without permanent visual cost" we'll see in this cluster.
- **Avoid:** Letting the same key glyph mean different things in different panels. For a workspace manager, `o` (open) and `d` (delete) must mean the same thing everywhere or muscle memory rebels.
- **Sentiment:**
  - Praise (bwplotka, [The (lazy) Git UI](https://www.bwplotka.dev/2025/lazygit/), 2025): *"if you forget important keybindings for actions, it's quick to check them on the footer or with `?`"* — captures the killer feature succinctly.
  - Critique (jesseduffield himself, [1 million downloads, one embarrassment at a time](https://jesseduffield.com/Embarrassment/)): the author concedes the original release shipped with `echo 'alias lg=lazygit' > ~/.zshrc` in the README — clobbering user zshrc files — and that the v1 process "consumed 100% CPU when left running." His framing: *"the greater the value, the greater the embarrassment."*

## lazydocker

- **Framework / language:** Go + gocui, same author as lazygit. Active since 2019.
- **Stars:** ~51k. Current v0.25.2 (Apr 2026), 47 releases — slower cadence than lazygit.
- **Strength 1 — Five-pane always-on dashboard.** Containers, services, images, volumes, configuration are always visible in a left rail; the right pane swaps content (logs / stats / config / top) without ever hiding the rail. This is the prototypical "spatial memory" layout — your hands know where containers live without looking.
- **Strength 2 — Streaming log pane with bounded buffer.** The detail pane tail-follows logs but caps memory; scrolling up pauses the follow, hitting `G` resumes. The mode indicator ("FOLLOWING" vs "PAUSED") is a single-word footer chip — minimal visual cost, complete state disclosure.
- **Weakness / controversial choice:** Performance against remote Docker daemons degrades sharply — logs lag, stats jitter, navigation can hang. Per [XDA's review](https://www.xda-developers.com/the-laziest-way-to-manage-container-stack/): *"navigation can at times feel sluggish... lazydocker often times out or behaves unpredictably depending on your network setup."* It assumes a local fast socket.
- **Steal:** The "rail of nouns + swappable detail" pattern. Maps perfectly to workspace-manager: workspaces are the rail, repos/scripts/links/status are the swappable details.
- **Avoid:** Treating every information stream as worth streaming. lazydocker tails logs by default, which is the right call for Docker; for a workspace manager, defaulting to "show me everything live" would just produce flicker.
- **Sentiment:**
  - Praise (HN, [2019 launch thread](https://news.ycombinator.com/item?id=20315973)): consistently lauded for "everything in one terminal window with every common command living one keypress away."
  - Critique ([XDA, 2025](https://www.xda-developers.com/the-laziest-way-to-manage-container-stack/)): scope-limited — "it still falls short of Portainer's custom templates, registry management, and stack management, and it won't let you edit or manage Compose files."

## gitui

- **Framework / language:** Rust + tui-rs / Ratatui. Active since 2020.
- **Stars:** ~22k. Current v0.28.1 (Mar 2026).
- **Strength 1 — Async git ops with no UI freezes.** Long git operations (log walk on a 900k-commit Linux tree) run on background threads and stream into the panel; the UI never blocks. Their own benchmark: 24s + 0.17 GB memory parsing Linux history vs lazygit/tig freezing. This is the design lesson, not the number: any I/O the workspace manager does (scanning .git/HEAD across many repos) must be off the render thread.
- **Strength 2 — Light/dark theme adaptation that actually works.** The bundled theme uses semantic slots that resolve to different terminal palette indexes based on detected background. Most TUIs ignore light terminals; gitui's contrast holds up on both Solarized Light and Dracula.
- **Weakness / controversial choice:** Feature-parity gap with lazygit on interactive rebase. [Issue #2584](https://github.com/gitui-org/gitui/issues/2584) is a long-running request for commit reordering and amending non-latest commits — the Rust async architecture made these harder, not easier. README still labels the project "beta" five years in.
- **Steal:** Off-main-thread I/O with a visible "loading" affordance in the panel header. Workspace scans (`git status` across N repos) should never block input.
- **Avoid:** Letting an architectural choice (async-first) drive feature triage. Users don't care that interactive rebase is hard in an async model — they care that lazygit has it.
- **Sentiment:**
  - Praise (HN [#39666727](https://news.ycombinator.com/item?id=39666727)): *"I've been using gitui after lazygit was getting a bit slow with larger repo history"* — the canonical migration story.
  - Critique (multiple GitHub issues): gitui is *fast* but *thin*. The README leans on benchmarks because it can't lean on features.

## k9s

- **Framework / language:** Go + tview (rivo/tview). Active since 2019.
- **Stars:** ~33.6k. 257 releases, very active.
- **Strength 1 — Vim-style `:` command mode as the universal entry point.** Typing `:pod` switches to pods, `:deploy` to deployments, `:ctx` to contexts. The header breadcrumbs (toggleable via Ctrl-G) show your nav stack. This collapses what would be a deep menu hierarchy into a single text field — the whole resource taxonomy is one keystroke away.
- **Strength 2 — Per-row color coding tied to lifecycle state, not just severity.** New rows briefly pulse yellow, modified rows flash, error rows hold red. The color isn't decorative; it encodes *change recency*, which is what an operator actually scans for. Skins (Dracula default, many bundled) let teams pin a context-specific palette — production red, staging blue ([issue #3414](https://github.com/derailed/k9s/issues/3414)).
- **Weakness / controversial choice:** Resource taxonomy leaks into the UI. k9s exposes ~80 Kubernetes resource kinds via the same `:` mechanism, which is great for power users and overwhelming for newcomers. There's no progressive disclosure — `:` accepts everything from the start.
- **Steal:** The colon-prefix command mode is a clean alternative to a modal palette. For workspace-manager: `:repo`, `:open`, `:script <name>` could all be the same mechanism.
- **Avoid:** Per-row pulse animations triggered by polling. k9s pulses are cheap because the watch API is event-driven; if workspace-manager polled git status every second to drive pulses, it would burn CPU and feel jittery.
- **Sentiment:**
  - Praise ([Palark](https://palark.com/blog/k9s-the-powerful-terminal-ui-for-kubernetes/)): *"the experience is as smooth as editing files with Vim — full keyboard control, real-time feedback, and one-key access to everything."*
  - Critique ([kagent issue #1494](https://github.com/kagent-dev/kagent/issues/1494) calling out k9s as inspiration): the resource taxonomy assumes Kubernetes literacy. Newcomers see colors they don't know how to interpret.

## atuin

- **Framework / language:** Rust + Ratatui (mostly — some recent eye-declare exploration in the org). Active since 2021.
- **Stars:** ~29.8k.
- **Strength 1 — Full-history search as a single dense table with semantic columns.** Time, duration, exit code, command — each is a column with its own format, and the row is the unit of selection. Fuzzy-match highlights are applied per column. The whole search is one rectangle, no separate input pane vs results pane.
- **Strength 2 — Filter modes are sticky and labelled in the footer.** `Ctrl-R` cycles through *session / directory / global*; the current filter is a single word in the footer. This is the cleanest "what scope am I querying?" disclosure in the cluster — one word, always visible, one keystroke to change.
- **Weakness / controversial choice:** Default `up-arrow` rebinding launches a full-screen TUI for what is usually a one-line correction. [HN #39460148](https://news.ycombinator.com/item?id=39460148) is full of complaints: *"having a full screen pop-up appear whenever I hit up was really jarring."* The fix exists (`--disable-up-arrow`) but the default is wrong.
- **Steal:** Sticky filter mode labelled in the footer. Workspace-manager filter mode (active / archived / branched-only) should follow this pattern — single word, footer-anchored, one key to cycle.
- **Avoid:** Hijacking a keystroke users have decades of muscle memory for, then putting a maximalist UI behind it. The corollary for workspace-manager: don't take over `Enter` to launch something heavyweight when the user expected a row-action.
- **Sentiment:**
  - Praise ([Ellie's Notes](https://ellie.wtf/projects/atuin/)): the timing data + sync story is the killer feature, not the TUI per se.
  - Critique ([HN #39460148](https://news.ycombinator.com/item?id=39460148)): *"the search functionality is not on par with fzf, I found myself several times going `cat ~/.zsh_history | fzf`"* — atuin's TUI loses to a pipe.

## zellij

- **Framework / language:** Rust, custom rendering (not Ratatui — own VTE-aware compositor); plugin runtime is Wasm. Active since 2020.
- **Stars:** ~32.7k. Current v0.44.3 (May 2026), very active.
- **Strength 1 — Mode-aware status bar that rewrites itself.** Press `Ctrl-p` (pane mode) and the bar lists pane-relevant keys; `Ctrl-t` (tab mode) rewrites for tabs. The bar is a teaching surface, not just a status line. The compact variant exists for users who've internalized the modes.
- **Strength 2 — Floating panes that persist across tab switches.** A floating pane (background process, scratch shell) survives tab navigation and can be summoned with one keystroke. The visual treatment — drop-shadow, dimmed parent — is one of the few cases where TUI decoration actually carries information.
- **Weakness / controversial choice:** Default status bar is loudly criticized as overlong and visually noisy. [Issue #3771](https://github.com/zellij-org/zellij/issues/3771): *"the status bar has too much text, but it doesn't conceptually convey a lot of information to justify how long it gets"* — the left rail repeats "Ctrl" seven times. Memory consumption is the other recurring complaint ([HN](https://news.ycombinator.com/item?id=39258823)): *"it literally eats 500mb and has to be killed."*
- **Steal:** Mode-aware footer rewriting. Workspace-manager could have a "filter mode" / "script mode" / "branch mode" where the footer entirely retargets — preserves the single-row footer budget while still teaching modes.
- **Avoid:** Spelling out every modifier on every key. `Ctrl+g › LOCK Ctrl+p › PANE Ctrl+t › TAB` is unreadable. Use a single-letter mnemonic with the modifier implied by context.
- **Sentiment:**
  - Praise ([HN #39258823](https://news.ycombinator.com/item?id=39258823)): *"simplicity and predictability are big priorities. It shows everywhere in the project."*
  - Critique (same thread): *"unusable for me because of memory consumption"* — the most-upvoted top-level comment.

## Cluster A synthesis

**Density.** Every tool in this cluster lands at the high-density end of the spectrum — typically 3–6 always-on panels plus a header and footer. The community sentiment is *not* "this is too dense"; it's "the density only works if every panel earns its slot." lazygit's five panels earn it (files, branches, commits, stash, status) because each represents an independent piece of git state. Zellij's default status bar gets criticized not for density per se but for redundancy — repeating "Ctrl" seven times spends pixels without buying information. Lesson for workspace-manager: high density is fine; redundant density is not.

**Border conventions.** All six default to single-line box-drawing characters (`┌─┐`) with a title segment embedded in the top edge (`┌─ Files ─┐`). Focus is indicated by either border color change (lazygit, gitui, k9s) or border weight swap to double-line (lazydocker, some zellij themes). Critics on Reddit and HN consistently dislike ASCII fallbacks (`+--+`) and double-line everywhere — too 1995. The convention worth adopting: rounded corners (`╭─╮`) plus accent-color border on focus, single-weight everywhere.

**Modals, forms, palettes.** Three patterns recur. (1) k9s and recent gitui use a **colon command mode** — type `:something`, no separate palette. (2) lazygit uses **centered modals with explicit labeled choices** ("Force push" / "Cancel"), not y/n. (3) Zellij and lazydocker mostly avoid modals entirely, preferring **mode shifts** that retarget the whole screen. None of the six use a fully separate "search box" UI element — search is either the command mode (k9s, gitui), a `/` slash-overlay on the focused panel (lazygit), or the entire screen (atuin). For workspace-manager, the colon + slash combo (k9s + lazygit) lets us avoid a heavyweight palette modal entirely.

**Animation and feedback.** Reviewers single out as **polished**: k9s row-state pulse on resource change, lazygit's spinner during background fetch, zellij's drop-shadow on floating panes. They single out as **overdone**: zellij's verbose mode-switch animations, atuin's full-screen takeover on up-arrow, k9s default skin's heavy color saturation. The pattern: animate state *changes*, not state *presence*. A spinner during a 300ms git fetch is fine; a spinner that's always running because something is always polling is jittery.

**Status / footer / help disclosure.** The clearest pattern across the cluster: **footer = context-scoped key hints, `?` = full keymap modal, header = identity (workspace name / cluster / repo path)**. lazygit pioneered the contextual footer; everyone else copies. The footer should compress under narrow widths — k9s drops descriptions and keeps glyphs, lazygit truncates labels, zellij is criticized for *not* compressing well. Help disclosure is universally `?` (every tool in this cluster honors it). For workspace-manager: contextual footer, `?` full modal, header shows workspace name + repo count, and the footer must have a sub-100-col compression strategy from day one.

**One overarching lesson.** This cluster's reputation rests on *consistency under load* — five panels feel coherent when border-style, focus-indication, key-glyph meanings, and color semantics are uniform. The criticisms (zellij's status bar, lazygit's inconsistent global keys, k9s's resource-taxonomy leak) are all consistency failures, not density failures. Studio direction is viable for workspace-manager if and only if we hold the consistency line everywhere — semantic theme tokens, never raw colors; one key glyph, one meaning, across all panels; footer always uses the same column slots in the same order.
