# Subagent Frontmatter Reference

Complete reference for every supported field in subagent YAML frontmatter, with usage guidance. Only `name` and `description` are required.

## Required fields

### `name`
Lowercase, hyphenated identifier. Must be unique within its scope. Used as the agent's invocation handle (`@code-reviewer`).

```yaml
name: code-reviewer
```

Bad: `CodeReviewer` (case), `reviewer` (too generic and likely to collide), `code_reviewer` (underscores not idiomatic).

### `description`
The triggering text. See SKILL.md §3.2 for the full design rules. Single most important field.

```yaml
description: Expert code review specialist. Use proactively after writing or modifying code, especially before committing or creating a pull request.
```

For agents whose triggering is subtle, embed `<example>` blocks in the description (XML-style). Several real agents in the Claude Code ecosystem do this — see `templates/reviewer.md`.

## Tool surface

### `tools`
Allowlist. If specified, the agent can use *only* these tools. If omitted, inherits everything from the parent.

```yaml
tools: Read, Grep, Glob, Bash
```

Special syntax for spawning other subagents (only relevant when this agent runs as the main thread via `claude --agent`):

```yaml
tools: Agent(worker, researcher), Read, Bash
```

The `Agent(...)` form allowlists which subagent types this orchestrator can spawn. If `Agent` is omitted entirely, the agent cannot spawn anything. Subagents themselves cannot spawn — this only applies to the main-thread case.

### `disallowedTools`
Denylist. Removes tools from the inherited or allowlisted set.

```yaml
disallowedTools: Write, Edit
```

Useful when you want "everything except writes" without enumerating every other tool. Applied first if both `tools` and `disallowedTools` are set.

## Model

### `model`
What model the agent runs on. Accepts an alias (`sonnet`, `opus`, `haiku`), a full ID (`claude-sonnet-4-6`), or `inherit`.

```yaml
model: sonnet
```

Default is `inherit` if omitted. Prefer aliases over pinned IDs unless the user has a reason to pin (reproducibility, known regression, etc.).

### `effort`
Effort level when this agent is active. Overrides the session effort. Options depend on the model: `low`, `medium`, `high`, `xhigh`, `max`.

Rare to need. Use only when the user has a specific reason (cost ceiling for an Opus agent that runs often, max-effort agent for security review).

## Permissions and isolation

### `permissionMode`
How the agent handles permission prompts.

| Mode | Use case |
| :--- | :--- |
| `default` | Standard prompts. Inherit unless reason to override. |
| `acceptEdits` | Auto-accept file edits and common filesystem ops in the working dir. Good for trusted builders that edit a lot. |
| `auto` | Background classifier reviews each command. Inherits if parent uses it (and overrides ignored). |
| `dontAsk` | Auto-deny prompts. Useful for hardened agents where you trust the `tools` list completely. |
| `bypassPermissions` | Skip prompts. Use only when tool surface is locked down and the user has explicitly opted in. |
| `plan` | Read-only plan mode. Useful for research agents. |

Parent's mode takes precedence if it's `bypassPermissions`, `acceptEdits`, or `auto` — your override is ignored in those cases.

### `isolation`
```yaml
isolation: worktree
```

Runs the agent in a temporary git worktree. Use for parallel experiments, agents that might leave the tree in a messy state, or "what-if" exploration. Auto-cleaned if the agent makes no changes.

### `maxTurns`
Cap on agentic turns before the agent stops. Backstop, not a primary control. Set when you want a hard ceiling on cost/runtime for a runaway agent.

## Memory

### `memory`
Persistent directory across sessions.

```yaml
memory: project   # or user, local
```

| Scope | Path | Use when |
| :--- | :--- | :--- |
| `user` | `~/.claude/agent-memory/<name>/` | Knowledge applies across all projects |
| `project` | `.claude/agent-memory/<name>/` | Project-specific, sharable via git |
| `local` | `.claude/agent-memory-local/<name>/` | Project-specific, not in git (gitignored typically) |

When set, Read/Write/Edit are auto-enabled (the agent needs them to manage memory) and the first ~200 lines of `MEMORY.md` are injected at startup.

If you enable memory, **include explicit instructions in the body** for what to record and what to skip. Otherwise the agent hoards trivia or skips the useful stuff.

## Skills

### `skills`
Preload skill content into the agent's context at startup.

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

The full skill body is injected — not made invokable, *injected*. Subagents do not inherit skills from the parent; you must list them explicitly.

Cannot preload skills with `disable-model-invocation: true`.

## MCP servers

### `mcpServers`
Scope MCP server access to this agent. Either reference an existing server by name (string) or define one inline (full server config).

```yaml
mcpServers:
  - playwright:                  # inline definition, scoped to this agent only
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  - github                       # reference to a server already configured in the session
```

Two reasons to use this:

1. The MCP server is only relevant to this agent — defining it inline keeps its tool descriptions out of the main thread's context.
2. The agent needs an MCP that the rest of the session shouldn't touch.

## Hooks

### `hooks`
Lifecycle hooks scoped to this agent. Only run while the agent is active; cleaned up when it finishes. All standard hook events supported. Most common:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
```

When the agent runs as a subagent (not the main session), a `Stop` hook in frontmatter is automatically converted to `SubagentStop`.

`PreToolUse` hooks let you do conditional gating finer than `tools`/`disallowedTools` allow — e.g., Bash allowed but only for SELECT statements.

> Note: plugin subagents cannot use `hooks`, `mcpServers`, or `permissionMode` for security reasons. If a plugin agent needs these, copy it into `~/.claude/agents/` or `.claude/agents/`.

## Background and concurrency

### `background`
```yaml
background: true
```

Always run this agent in the background (concurrent with main thread). Default: `false` (Claude decides per invocation).

Background agents need permissions pre-approved at launch — they can't prompt mid-flight. Choose this for agents that run long and shouldn't block the user.

### `initialPrompt`
First user-turn message when this agent runs as the main session via `--agent` or the `agent` setting. Slash commands and skills inside it are processed.

```yaml
initialPrompt: /agents
```

Only relevant for main-thread agent mode, not for typical subagents.

## Display

### `color`
Background color in the UI. Useful for visually distinguishing concurrent subagents.

Accepts: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`.

```yaml
color: green
```

Cosmetic but helpful in workflows with parallel agents.

## Field interaction gotchas

- **`tools` + `disallowedTools` together**: `disallowedTools` is applied first against the inherited pool, then `tools` is resolved. A tool listed in both is removed.
- **Parent permissionMode wins** in some cases (see Permission section above).
- **`memory` auto-grants Read/Write/Edit** even if you tried to restrict tools — the agent needs them to manage its memory dir.
- **Subagents do NOT inherit skills from the parent**. List them explicitly in `skills:` or the agent won't have them.
- **Subagents do NOT inherit `CLAUDE.md`** the same way — the agent's body is its system prompt. CLAUDE.md context goes to the parent. If your agent needs project conventions, either preload a skill or summarize them in the body.
- **Subagent files are loaded at session start.** A new file isn't picked up until you restart the session or run `/agents` to reload.
