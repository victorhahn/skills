# Subagent Anti-patterns

Catalog of common mistakes. When you spot one in a user's request or existing agent, name it briefly and propose the fix.

## Description-level

### "Helps with code"
Description so generic that Claude can't tell when to invoke it. Result: never triggers, or triggers on everything.

**Fix**: lead with a specific noun ("Expert code review specialist"), state when to use ("after writing code, before commits"), include keywords the user would actually say ("review", "PR", "pull request", "code review").

### Description that doesn't say when to use
Description tells you what the agent IS but not when to delegate. Auto-delegation underperforms.

**Fix**: add an explicit "Use when ___" or "Use proactively after ___" sentence. The phrase "use proactively" especially matters.

### Description identical to a sibling agent
Two agents with overlapping descriptions confuse the router. One always wins, the other is dead code.

**Fix**: in each description, name what makes it *different* from neighbors. "Focuses on auth, secrets, injection — separate from general code review."

## Tool surface

### Inherits all tools when it should be read-only
A research/review agent inheriting Edit and Write can hallucinate edits or "fix" things it shouldn't.

**Fix**: explicit `tools: Read, Grep, Glob, Bash` allowlist. Prompts saying "don't edit files" are not enforcement.

### `Bash` granted when only `BashOutput` is needed
Agent only needs to read output of a long-running command — it doesn't need to start new processes. Granting full Bash adds unnecessary capability.

**Fix**: use `BashOutput` for read-only access to background command output.

### MCP server scoped session-wide for a single agent
If only one agent uses Slack/Playwright/etc, scoping the server inline in that agent's frontmatter keeps tool descriptions out of main context.

**Fix**: move the server config from `.mcp.json` to `mcpServers:` inline in the agent file.

## Model selection

### Opus for trivial tasks
Using Opus to extract a value from a JSON file. Slow and expensive.

**Fix**: Haiku for narrow, well-defined tasks. Sonnet is the default. Opus only for tasks where bad reasoning costs hours.

### Haiku for hard reasoning
Using Haiku for security review or architecture analysis. The agent will miss things.

**Fix**: match tier to reasoning complexity, not author preference for fast/cheap.

### Pinned model ID without a reason
`model: claude-opus-4-7` instead of `model: opus`. Locks the agent to one version; doesn't follow improvements.

**Fix**: use the alias unless you have a specific reason to pin (reproducibility, known issue with newer version).

## System prompt body

### 200-line `MUST`/`NEVER` walls
Long lists of strict commands. Modern Claude often does worse with this style — it skims, ignores edge cases.

**Fix**: explain *why*, use imperative voice without all-caps. Save `MUST`/`NEVER` for genuine safety constraints.

### No output structure when the caller will parse it
Agent returns prose; main thread has to extract values. Brittle.

**Fix**: define an output template in the body. If it's machine-consumed, JSON or fixed markdown headers. If human-consumed, scannable structure.

### Agent doesn't know what input to expect
"You will receive a task" with no further detail. The calling agent has to figure out the input shape.

**Fix**: state explicitly what the agent expects ("Input: a git diff or file paths. Default to `git diff` if not specified.").

### No calibration for noisy domains
Code reviewer flags every minor style nit. User stops trusting the agent.

**Fix**: add explicit confidence thresholds or signal/noise rules. "Only flag issues with confidence ≥ 80." "Skip nits, focus on bugs and explicit convention violations."

### Body explains *what* but not *why*
"Run linter. Report results." Agent has no model of the goal, can't make judgment calls.

**Fix**: include the why. "Lint errors that block CI matter; warnings on changed lines are worth reporting; warnings on untouched lines are noise."

## Architecture-level

### Subagent for a 5-second inline task
Spawning an agent to add a single import or rename a variable. Subagent overhead dwarfs the work.

**Fix**: just do it inline.

### Subagent that needs to ask the user clarifying questions
Subagents are fire-and-forget. They cannot prompt the user mid-flight (background subagents auto-deny `AskUserQuestion`; foreground ones can pass it through but the design is fragile).

**Fix**: do the work in the main thread, or use a fork (which can pass prompts through to terminal), or have the calling thread gather all clarifications upfront and pass them in the prompt.

### Subagent that spawns subagents in its body
Subagents cannot spawn other subagents. The Agent tool isn't available to them. Body that says "delegate to the X agent" doesn't work.

**Fix**: lift orchestration to main thread or to an explicit orchestrator agent run with `claude --agent`.

### Three-step chain where each step is one prompt
Splitting a cohesive task into a chain because it "feels modular." Handoffs lose context, fresh agents re-establish, latency adds up.

**Fix**: collapse to one agent with a structured multi-step prompt. Use a chain only when phases want different tool surfaces or model tiers.

### Fan-out with too many agents
Spawning ten parallel investigators. Synthesis cost eats the parallelism benefit; main context fills with summaries.

**Fix**: cap parallelism at ~3-5. If you need more, use agent teams.

### Fan-out with no synthesis
Five investigators all dump their findings into main context unstructured. Defeats the context-preservation point.

**Fix**: have main (or an orchestrator) synthesize before continuing.

### Sequential calls that should be parallel
Three independent Agent calls issued across three turns. They run sequentially.

**Fix**: one turn, multiple Agent calls in the same message.

## Memory

### Memory enabled with no record-vs-skip guidance
Agent hoards everything (memory bloats fast) or records nothing.

**Fix**: in the body, explicitly say what kinds of things to record and what to skip. "Record recurring conventions and architectural decisions. Skip one-off bugs and trivia."

### Memory enabled for a one-shot agent
A test runner with `memory: project`. Test runs don't compound; memory is dead weight.

**Fix**: drop the field.

### Memory at user scope when knowledge is project-specific
Reviewer learns React conventions in one project and applies them to a Vue project elsewhere.

**Fix**: `memory: project` (or `local` if shouldn't be in git).

## Permissions

### `bypassPermissions` without locked-down tools
Agent has Edit, Write, Bash all enabled, plus `bypassPermissions: true`. No prompts, no restrictions. Anything goes.

**Fix**: either narrow the tool surface first, or use `default`/`acceptEdits` and let the prompts protect the user.

### `permissionMode: plan` on a builder
Agent that's supposed to write code, but in plan mode (read-only). Will fail to make changes.

**Fix**: `plan` is for researchers. Builders need `default` or `acceptEdits`.

## Placement

### Personal agent in the plugin cache directory
File at `~/.claude/plugins/cache/.../agents/foo.md`. Plugin update wipes it.

**Fix**: personal agents go in `~/.claude/agents/`. Project agents in `.claude/agents/`. Distributable agents in a plugin you build, not the cache.

### Project agent that should be user-scoped
Agent that has nothing project-specific in it, copied into every repo's `.claude/agents/`. Maintenance burden.

**Fix**: `~/.claude/agents/`.

### Agent file edited but not reloaded
Subagent files are loaded at session start. Editing the file in the current session doesn't take effect.

**Fix**: `/agents` to reload, or restart the session.
