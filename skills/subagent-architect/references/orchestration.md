# Multi-Agent Orchestration Patterns

When you have a system of subagents, the control flow lives in the main thread or in a top-level orchestrator. **Subagents cannot spawn other subagents** — that constraint shapes every pattern below.

This file covers four patterns plus the cross-cutting decision of subagents-vs-agent-teams.

## Pattern 1: Parallel research (fan-out, no orchestrator)

Main thread spawns N independent investigators in **one turn** (one message with multiple Agent tool calls). Each works in its own context window. Results return to main, which synthesizes.

### Use when
- Investigations don't depend on each other.
- Each path produces verbose output (search results, file dumps) the main thread doesn't need.
- The synthesis step itself is small.

### Don't use when
- Investigation paths depend on each other ("first find X, then trace through Y based on what you found").
- You'd spawn more than ~5 — synthesis cost dominates.

### Example: investigate auth changes across modules

In one turn, main thread issues three Agent tool calls:

```
Agent(subagent_type=Explore, prompt="Trace authentication module: where login handlers live, session token issuance, refresh flow. Report file paths and key functions.")
Agent(subagent_type=Explore, prompt="Trace authorization module: permission checks, role definitions, middleware. Report file paths and key functions.")
Agent(subagent_type=Explore, prompt="Trace session storage: where sessions are persisted, TTL configuration, invalidation. Report file paths and key functions.")
```

Each returns ~200-token summaries. Main thread reads all three, then has the full mental model in its own context.

### Anti-pattern
Spawning the three calls across three separate turns. They run sequentially and you waste the parallelism entirely.

## Pattern 2: Sequential chain

Research → plan → implement → review. Each agent runs fresh, each output feeds the next.

### Use when
- Phases want different tool surfaces (read-only research, then full-edit implementation, then read-only review).
- Phases want different model tiers (Opus for design, Sonnet for implementation, Haiku for sanity check).
- The handoff is clean and each output is small enough to be the next prompt.

### Don't use when
- The phases are really one cohesive task with branches — that's better as one agent with a structured prompt.
- The handoff loses too much context. Each fresh agent re-establishes context, which has cost.

### Example: feature implementation chain

1. **`code-explorer`** (read-only, Sonnet) → maps the existing feature and returns a structured summary
2. **Main thread** consumes the summary, drafts a plan, asks the user
3. **`code-architect`** (read-only, Opus) → produces the implementation blueprint
4. **Main thread** writes the code (or delegates to `builder`)
5. **`code-reviewer`** (read-only, Sonnet) → reviews the diff

Notice: the orchestration lives in the main thread between steps. Each subagent is fresh, focused, and returns one structured payload.

## Pattern 3: Fan-out/fan-in via orchestrator agent

A top-level agent run via `claude --agent <orchestrator>` with `tools: Agent(specialist-1, specialist-2, ...)`. The orchestrator's prompt encodes the dispatch logic.

### Use when
- The orchestration logic itself is non-trivial and benefits from a focused system prompt.
- You want the user to be able to drop into "orchestrator mode" with `claude --agent` and have the orchestrator's prompt drive the whole session.
- You want the `tools: Agent(...)` allowlist to enforce *which* specialists can be spawned.

### Don't use when
- A few-line orchestration in the main thread would do the job. Don't promote main-thread logic to an orchestrator agent unless it earns its keep.
- The dispatch decision is trivial (always run all specialists, every time). If the orchestrator's prompt boils down to "spawn these three in parallel and concatenate their output," skip the orchestrator and have the main thread issue the three Agent calls directly. Orchestrators earn their keep when classification, conditional dispatch, or non-trivial synthesis lives in their prompt.
- Inputs already arrive pre-classified (e.g., your support tooling tags reports with service + severity before they reach Claude). The classification step the orchestrator would run is then wasted overhead.

### Example: a `triage` orchestrator

```yaml
---
name: triage
description: Triages incoming bug reports across the stack. Use when a customer-reported issue lands without diagnosis. Will spawn appropriate specialists based on the report.
tools: Agent(log-searcher, code-explorer, datadog-investigator), Read, Bash
model: opus
---

You are the on-call triage lead. Given a bug report, you:

1. Categorize the report (frontend, backend, data pipeline, infra).
2. Spawn parallel specialists:
   - log-searcher: pull recent logs for the affected service
   - code-explorer: trace the user-flow described in the report
   - datadog-investigator: pull metrics for the affected window
3. Synthesize findings into a triage doc with: likely root cause, files to look at, severity assessment, recommended owner.

Run the three specialists in parallel — they don't depend on each other.
```

The user runs `claude --agent triage`, pastes a bug report, and the orchestrator's prompt drives the whole flow.

## Pattern 4: Fork (experimental)

A fork inherits the entire main conversation. Same system prompt, same tools, same message history, same model. The fork's own tool calls stay out of main context — only its final result returns.

Requires `CLAUDE_CODE_FORK_SUBAGENT=1`.

### Use when
- Re-explaining the conversation context to a fresh subagent would be wasteful.
- "Try several approaches in parallel from the same starting point."
- A side task during a long-running session ("draft tests for what we just discussed").

### Don't use when
- The task benefits from a fresh, focused prompt without main-thread baggage.
- You want strict tool restriction on the side task — forks inherit everything.

### Example
```
/fork draft unit tests for the parser changes so far
```

The fork has the entire conversation up to that point, runs in the background, returns a final message.

## Designing for synthesis: aligning specialist outputs

When multiple specialists feed one synthesizer (orchestrator or main thread), their output formats need to line up — otherwise the synthesizer spends effort reconciling shapes instead of meaning. Three rules:

1. **Same time format across specialists.** Pick one (UTC ISO 8601 is the right default) and put it in every specialist's "Standards you hold yourself to" section. Mixed timezones turn correlation into a puzzle.
2. **Same citation format.** `path/to/file.ts:42` for code, `https://app.datadoghq.com/...` for dashboards, monitor IDs as `<id>`. The synthesizer should be able to grep across specialist outputs for citations.
3. **Same role boundary.** Every specialist's body should explicitly say "don't speculate about root cause — that's the synthesizer's job." If two specialists each propose conflicting root causes, the synthesizer can't tell which to trust. Specialists characterize; one role synthesizes.

Beyond format, design the prompts the orchestrator sends to each specialist as a typed-ish contract: state in the orchestrator's body what fields it will pass (service name, time window with timezone, symptom statement, correlators), and state in each specialist's "Inputs you can expect" section the same set. Mismatches there are the most common source of "the specialist returned something useless" bugs.

## Cross-cutting decision: subagents vs agent teams

| Question | Subagent | Agent team |
| :--- | :--- | :--- |
| Lifetime | One session | Across sessions, days/weeks |
| Communication | Single return value | Bidirectional messaging |
| Concurrency | Up to ~handful in parallel | Sustained parallelism with shared workspace |
| Right for | "Run this side task and report back" | "These five agents collaborate on this initiative for two weeks" |

If the user describes work that lives across sessions and involves agents passing tasks back and forth over time, that's an agent team. Point at https://code.claude.com/docs/en/agent-teams and stop building subagents.

## Resuming subagents within a session

Each Agent tool call creates a fresh subagent instance. To continue a previous one's work without restarting, use `SendMessage` with the previous agent's ID as `to`. The subagent picks up with full conversation history.

This requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Useful when:
- A reviewer should follow up on its own previous review with new files
- A researcher should drill deeper into something it already explored

Resumption works *within a session*. Subagent transcripts are stored in `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` and persist for `cleanupPeriodDays` (default 30). After a session restart, you can resume the session and the subagents resume with it.

## Common orchestration anti-patterns

- **Three agents to do one cohesive task.** Each handoff loses context and adds latency. If the agents share intent, collapse to one.
- **Trying to spawn nested subagents.** A subagent calling Agent → not allowed. If you find yourself wanting this, lift orchestration to the main thread or to an explicit orchestrator agent.
- **Sequential calls that should be parallel.** If three investigators don't depend on each other, issue them in one main-thread turn with multiple Agent calls.
- **Fan-out without a synthesis step.** Spawning five investigators and dumping their raw output into the conversation defeats the context-preservation purpose. Have the main thread (or an orchestrator) synthesize.
- **Orchestrator agent with no `tools: Agent(...)` allowlist.** Then any subagent can be spawned, including unintended ones. Always allowlist.
- **Subagent that asks the user a clarifying question.** It can't. Redesign as fork or main thread.
