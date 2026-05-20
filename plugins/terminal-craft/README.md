# terminal-craft

A Claude Code plugin for building production-grade terminal tools — both the **agent-friendly CLI** (composable, JSON-stable, durable) and the **human-facing TUI** (Ink 7 + React 19, design-grounded in real-world precedent).

Three skills, coordinated:

| Skill | What it does | When it triggers |
|---|---|---|
| **`cli-creator`** | Builds a Node/TypeScript CLI that future Claude Code sessions can invoke by name. JSON contract, `doctor`, composable verbs, raw escape hatch, companion skill. Stack is pnpm-first, Node 20+ (or 22+ if Ink), `tsup` build, `vitest` tests, `biome` lint. | "build a CLI", "wrap this API", "turn these curls into a tool", "CLI from OpenAPI". |
| **`tui-design`** | Universal TUI design principles — framework-agnostic. Layout paradigm selector, semantic color tiers, focus management, animation rules, accessibility checklist. Includes a full Ink 7 / React 19 implementation reference at `references/ink-implementation.md`. | "TUI design", "terminal UI layout", "Ink components", "keyboard navigation", "TUI color palette". |
| **`tui-patterns`** | Pattern catalog from 18 reference TUIs (lazygit, k9s, claude-code, harlequin, btop, yazi, helix, …). Three direction archetypes — **Studio** (persistent multi-panel), **Atelier** (borderless / background-layered), **Concourse** (top-tab with which-key). Ranked anti-patterns. Cross-cutting non-negotiables. | "how does lazygit handle X", "Studio vs Atelier vs Concourse", "TUI anti-patterns", "precedent for Y". |

## How the skills compose

```
User wants to build a terminal tool
            │
            ▼
┌──────────────────────────────────────┐
│         cli-creator                  │   "I need a tool to do X"
│  (agent surface: JSON, doctor, …)    │   ──────────────────────►
└──────────────────────────────────────┘
            │
            │ Does it also need a polished interactive surface?
            ▼ yes
┌──────────────────────────────────────┐
│         tui-patterns                 │   "Which direction is right
│  (Studio / Atelier / Concourse +     │    for this tool's shape?"
│   anti-patterns from 18 real TUIs)   │
└──────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│         tui-design                   │   "Apply the universal
│  (universal principles +             │    design system + Ink 7
│   Ink 7 / React 19 implementation)   │    component recipes."
└──────────────────────────────────────┘
```

The three skills are cross-linked so a future Claude Code session naturally pulls in the related ones.

## Why this stack

- **Node 22 + TypeScript 5** — native `fetch`, native `crypto`, top-level await, ESM. Minimal dependency surface, smaller CVE footprint.
- **pnpm everywhere** — strict, fast, content-addressable. No `npm`/`npx` fallbacks; `pnpm dlx` for one-shot execution.
- **Ink 7 + React 19** — verified against the [Ink readme](https://github.com/vadimdemedes/ink). Yoga flexbox, hooks-based focus/animation/window-size, `incrementalRendering` for flicker-free output, kitty keyboard protocol for proper key disambiguation.
- **One binary, two surfaces** — the same tool serves `--json` to agents and renders an Ink TUI to humans. Ink is loaded lazily so the agent path never pays the React boot cost.

## Conventions baked in

- **Agent CLI side** — every command supports `--json`; `doctor` always exits 0 and reports missing setup; resolve commands turn names into stable IDs; writes are narrow-ID and `--dry-run`-friendly.
- **TUI side** — one accent color; locked status triad (success/warning/error); state-bearing borders or none at all; three-layer discoverability (footer / `?` which-key / `:` palette) all derived from one keymap table; async I/O off the render thread with panel-header spinners.

## Skills in this plugin

```
terminal-craft/
├── .claude-plugin/plugin.json
├── README.md
└── skills/
    ├── cli-creator/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── agent-cli-patterns.md
    │   │   └── node-defaults.md
    │   └── evals/
    ├── tui-design/
    │   ├── SKILL.md
    │   └── references/
    │       ├── app-patterns.md
    │       ├── visual-catalog.md
    │       └── ink-implementation.md       ← Ink 7 / React 19 recipes
    └── tui-patterns/
        ├── SKILL.md
        └── references/
            ├── cluster-a-devops.md          ← lazygit, lazydocker, gitui, k9s, atuin, zellij
            ├── cluster-b-modern.md          ← claude-code, aider, posting, harlequin, glow, presenterm
            └── cluster-c-monitors.md        ← btop, bottom, yazi, helix, ranger, tig
```

## Versions verified

This plugin's recipes are pinned to (at minimum) the versions below. Re-verify the `latest` tag on npm before scaffolding a new project — Ink moves through majors fairly often.

```bash
curl -s https://registry.npmjs.org/ink | jq -r '."dist-tags".latest'
curl -s https://registry.npmjs.org/ink | jq -r '.versions[."dist-tags".latest] | {peerDependencies, engines}'
```

Current as of 2026-05:

- `ink` ^7.0 (Node ≥22, React ≥19.2)
- `react` ^19.2
- `ink-text-input` ^6.0
- `ink-select-input` ^6.2
- `ink-spinner` ^5.0
- `ink-testing-library` ^4.0

## Credits

The 18-tool TUI research in `tui-patterns/references/cluster-{a,b,c}-*.md` was originally compiled for the `wsm` (workspace-manager) redesign project. Some passages still reference "workspace-manager" or "wsm" as a concrete case study; the lessons generalize.
