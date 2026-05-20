---
name: cli-creator
description: >
  Build a durable, installable Node/TypeScript CLI that Claude Code can run by command
  name from any working directory. Use this skill whenever the user wants to create a
  production-grade command-line tool from API docs, an OpenAPI spec, curl examples, an
  SDK, an internal web app, or an existing script — and wants it to expose composable
  commands, return stable JSON, manage auth cleanly, and pair with a companion skill.
  Trigger on: "build a CLI for X", "create a command-line tool", "turn these curls into
  a CLI", "wrap this API", "make a durable command I can run from anywhere", "CLI from
  OpenAPI", "installable tool for X", "package this script as a command", or any request
  to turn a workflow into a persistent binary. This is for durable tools, not one-off
  scripts — if a short script in the current repo solves the task, write it there
  instead. Pairs with the `tui-design` and `tui-patterns` skills when the same tool also
  needs an interactive Ink-based TUI surface.
---

# CLI Creator

Build a real Node/TypeScript CLI that future Claude Code sessions can invoke by name from any working directory.

This skill assumes the **Node/TypeScript + Ink** stack: agent-friendly JSON output from the same binary that can render a polished interactive TUI when invoked without `--json`. Sister skills `tui-design` and `tui-patterns` cover the interactive surface.

## Step 1 — Clarify Intent

Before touching code, identify three things:

- **Source** — where the API surface comes from: API docs, OpenAPI JSON/YAML, SDK, curl
  examples, browser DevTools network capture, existing script, or working shell history.
- **Jobs** — the literal reads/writes the CLI must do, phrased as verb phrases:
  `list failed deployments`, `download job logs`, `search messages`, `upload media`.
- **Install name** — a short shell-friendly binary name: `dd-cli`, `slack-logs`, `gh-dash`.

Default install location: `~/code/clis/<tool-name>/` for personal tools with no named repo.

Check for conflicts before scaffolding:
```bash
command -v <tool-name> || true
```
If occupied, propose a clearer name.

## Step 2 — Confirm the Toolchain

```bash
command -v node pnpm tsx || true
node --version
```

**Always use `pnpm`.** It's the project default — strict by design (no phantom deps), fast, content-addressable. If pnpm is missing, install it via `corepack enable && corepack prepare pnpm@latest --activate` rather than falling back to `npm`. Use **`pnpm dlx`** instead of `npx` for any one-shot package execution. Commit `pnpm-lock.yaml`; never commit `package-lock.json` or `yarn.lock`.

Use **tsx** for dev (zero-config TS execution), **tsup** for builds (ESM + DTS). Stick with the platform: native `fetch`, native `crypto`, native `fs/promises` — no extra dependencies where a built-in works.

Node baseline: **Node 20+** for the pure agent CLI, **Node 22+** if Ink (TUI) is included (Ink 7's requirement).

State your runtime choices in one sentence: confirm pnpm is available, build tool, anything non-default.

## Step 3 — Design the Command Surface

**Before writing code**, sketch the full command surface in chat and get alignment.
Read [references/agent-cli-patterns.md](references/agent-cli-patterns.md) for the
canonical composable CLI shape, JSON conventions, and common anti-patterns.

The surface must include:

- `<tool> --help` — every major capability visible
- `<tool> --json doctor` — checks config, auth, version, endpoint reachability, missing setup
- Discovery commands — find top-level containers (projects, workspaces, queues, channels)
- Resolve commands — turn names/URLs/slugs into stable IDs so downstream commands don't re-search
- Read commands — fetch exact objects; `list`/`search` with a bounded `--limit` or cursor
- Write commands — one named action each (`create`, `update`, `delete`, `upload`, `retry`);
  accept narrow stable IDs; support `--dry-run` or `--draft` where the service allows
- `--json` flag — stable machine-readable output on every command
- Raw escape hatch — `request`, `api`, or `tool-call`; read-only first

Never expose only a generic `request` — give Claude Code high-level verbs for repeated jobs.

Document the JSON contract in the README: API pass-through vs. CLI envelope, success shape,
error shape, one example per command family. Errors under `--json` must be machine-readable
and must never contain credentials.

### The agent/human dual surface

A well-designed CLI serves two audiences from one binary:

- **Agent path** — `<tool> --json <verb>` returns strict JSON, exits with a code, prints nothing else. This is what Claude Code chains together across sessions.
- **Human path** — `<tool> <verb>` without `--json` may render a rich interactive surface (table, prompts, or full Ink TUI). When the same data flows through both paths, the agent and human stay in sync.

If the tool warrants a full TUI (more than a row table — multi-panel, live updates, navigation), invoke the [`tui-design`](../tui-design/SKILL.md) and [`tui-patterns`](../tui-patterns/SKILL.md) skills to design that surface. They cover layout, color, focus, animation, and real-world precedent across 18 reference TUIs.

## Step 4 — Auth and Config

Support in this precedence order:

1. **Environment variable** — service's standard name (`GITHUB_TOKEN`, `DATADOG_API_KEY`)
2. **User config** — `~/.<tool-name>/config.toml` or another simple, documented path
3. **Flag** (`--api-key`, `--token`) — only for explicit one-off use; flags leak into shell
   history and process listings

Never print full tokens. `doctor --json` must report: token present/absent, auth source
(`env`, `config`, `flag`, or `missing`), and the exact missing setup step.

**For internal web apps sourced from DevTools curls:** before implementing, write sanitized
endpoint notes (resource name, method/path, headers, auth mechanism, CSRF, request body,
response ID fields, pagination, errors, one redacted sample response). Never commit cookies,
bearer tokens, customer secrets, or full production payloads.

## Step 5 — Build

1. **Research** — inventory resources, auth, pagination, ID shapes, media flows, rate limits,
   and dangerous writes. Download/inspect OpenAPI before naming commands.
2. **Sketch commands** — present in chat; short, shell-friendly names; get alignment.
3. **Scaffold** — project structure + README with JSON contract docs.
4. **Implement** — `doctor`, discovery, resolve, read commands, one `--dry-run` write path
   if requested, raw escape hatch.
5. **Install on PATH** — so `<tool-name> ...` works from any directory.
6. **Smoke test outside the source tree** — run from `/tmp` or another repo:
   `command -v <tool-name>`, `<tool-name> --help`, `<tool-name> --json doctor`.
7. **Test suite** — format, typecheck/build, unit tests for request/pagination builders,
   no-auth `doctor`, help output, and at least one fixture or live read-only call.

For a live write: ask first; keep it reversible or draft-only.

See [references/node-defaults.md](references/node-defaults.md) for the exact packages,
project layout, install patterns, and Makefile targets to use. Versions in that file are
verified against the npm registry; re-check `dist-tags.latest` for `ink` and `react`
before scaffolding if it's been a while.

## Step 6 — Companion Skill

After the CLI is installed and smoke-tested, create a companion skill at
`~/.claude/skills/<tool-name>/SKILL.md`.

Write it in the order a future Claude Code session should use the CLI — not as a feature
tour. Cover:

1. How to verify the command exists (`command -v <tool-name>`)
2. Which command to run first
3. How auth is configured
4. Which discovery command finds the common ID
5. The safe read path
6. The intended draft/write path
7. The raw escape hatch
8. What not to do without explicit user approval
9. Three copy-pasteable command examples

Keep API reference details in the CLI README or a `references/` file inside the skill.
Keep the skill itself focused on ordering, safety, and examples.

Frontmatter template:
```yaml
---
name: <tool-name>
description: >
  Use the <tool-name> CLI to <what it does>. Trigger when the user asks to <key jobs>.
  Before any write command, verify with --dry-run or confirm intent explicitly.
---
```

## Companion Skills

- [`tui-design`](../tui-design/SKILL.md) — Universal TUI design principles. Layout paradigm selector, semantic color system, focus management, animation rules, accessibility. Read when the CLI also needs a polished interactive surface.
- [`tui-design/references/ink-implementation.md`](../tui-design/references/ink-implementation.md) — Ink 7 / React 19 component and hook recipes. The concrete how-to once you've picked your design direction.
- [`tui-patterns`](../tui-patterns/SKILL.md) — Real-world precedent from 18 reference TUIs (lazygit, k9s, claude-code, harlequin, btop, yazi, helix, …). Three direction archetypes (Studio/Atelier/Concourse) and ranked anti-patterns. Read before committing to a TUI direction.
