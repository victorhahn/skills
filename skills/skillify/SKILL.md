---
name: skillify
description: Turn a source artifact — a URL, article, blog post, talk transcript, paper, doc page, or pasted context — into a fully functioning Claude Code skill. Use when the user invokes /skillify, says "make a skill out of this", "skillify this article", "turn this into a skill", "extract learnings from X into a skill", or hands over a link/snippet and asks for a reusable skill built from it. Ingests the source, distills key learnings, proposes a skill design, gates on user approval after clarifying questions, then scaffolds and writes the final skill.
allowed-tools: Bash, Read, Write, Edit, WebFetch, WebSearch, Grep, Glob
---

# Skillify

Turn one source — a URL, article, transcript, paper, doc page, or pasted blob — into a real, installable Claude Code skill. The job is *not* to mechanically transcribe the source; it is to extract the durable, reusable learnings and shape them into a triggerable skill that future-Claude can actually use.

You are doing four things, in order: **ingest**, **distill**, **shape**, **build**. Stop and get approval after *shape* — never write the skill file until the user has greenlit the design.

## When to fire

Trigger on:

- `/skillify <url-or-context>` — explicit invocation, with or without a URL.
- "Make a skill out of this article / post / talk / doc."
- "Turn the learnings from X into a skill."
- "Skillify this." (with attached content, a URL, or recent conversation context).
- "Extract a skill from this transcript / paper / thread."

Skip when:

- The user wants to *use* an existing skill — that's not skillify.
- The source has no transferable lessons — a one-off announcement, a changelog with nothing to operationalize, a product page. Say so and stop.
- The user already knows exactly what skill they want and has no source to ingest — just scaffold a skill directly, no need for this skill.

## Step 1 — Ingest the source

Figure out what kind of input you're working with and pull the content:

| Input type | How to fetch |
| :--- | :--- |
| URL (http/https) | `WebFetch` with a prompt asking for the full article text, not a summary. Follow obvious "read more" / canonical links if the first fetch returns a landing page. |
| Local file path | `Read` the file. |
| Pasted text in the message | Use what's already in context. |
| Recent conversation as the source ("/skillify what we just talked about") | Treat the prior turns as the source — no fetch needed. |
| Multiple URLs/files | Ingest each; treat as one combined corpus, but note which insights came from which source for citation later. |

If the source is huge (paper, long transcript), do a first read to identify the durable sections, then re-read those targeted sections. Don't load 30k tokens of source content when 5k is enough.

If `WebFetch` returns 403 / paywalled / login-walled, say so explicitly and ask the user to paste the content. Don't fabricate from the URL alone.

## Step 2 — Distill the learnings

Read the source as a *practitioner*, not a transcriber. You're looking for:

- **Patterns** — repeatable techniques, mental models, decision frameworks ("when X, prefer Y because Z").
- **Tactics** — concrete moves: commands to run, structures to follow, checks to perform.
- **Anti-patterns** — things to avoid, with the reasoning so an edge case can be judged.
- **Triggers** — situations or symptoms that should make someone reach for this knowledge.
- **Worked examples** — small enough to embed; large enough to anchor the abstraction.

Explicitly *discard*:

- Marketing language, "we're excited to announce", author bios, footer noise.
- Anything tied to a specific time/version that won't generalize (unless the skill is explicitly versioned).
- Restatements of common knowledge — if the source spends three paragraphs on "what is git", that's not skill material.

Hold the distillation in your head (or in scratch notes) — do not write a separate distillation file. The output of this step is what feeds Step 3.

## Step 3 — Shape the skill (and gate on approval)

This is the load-bearing step. You're proposing a skill design and stopping for the user to sanction or redirect it. Don't write any files yet.

Present the proposed design as a short, scannable block covering all of:

1. **Name** — lowercase, hyphenated, action-oriented. Concrete enough that `@<name>` reads well.
2. **One-line description** — what the skill IS and when to use it. This is the triggering text Claude uses to decide whether to fire the skill in future sessions; treat it like the most important sentence in the skill. Pack it with the natural-language phrases a user might say, the situations that should fire it, and what makes it distinct from neighbors.
3. **Trigger phrases** — 4-8 natural-language phrases that should fire it ("how do I X", "review my Y", "/foo bar"). The richer this list, the more reliably the skill fires.
4. **Scope** — what the skill DOES, and equally important, what it explicitly DOES NOT do (the "skip when" list).
5. **Shape** — is this a knowledge skill (Claude reads it and applies the patterns inline), a workflow skill (steps the user runs), or a producer skill (generates artifacts)? Different shapes need different bodies.
6. **Where it goes** — propose a destination based on the user's working directory and the skill's audience. Common options to consider:
   - Project-local (`.claude/skills/<name>/` in the current repo) — tied to this codebase, shared with collaborators via version control.
   - User-global (`~/.claude/skills/<name>/`) — personal, available across all the user's projects, not shared.
   - A dedicated skills repo the user maintains — if you can detect one (a repo with existing `skills/<name>/SKILL.md` siblings, a `scripts/new-skill.sh`, or a `.claude-plugin/` registry), surface it as an option and follow its conventions.
   - A distribution channel (marketplace, plugin bundle) — only if the user explicitly wants to publish.

   Brainstorm potential clarifying questions about audience before recommending. If you see signals of internal/proprietary content in the source, flag that the destination choice matters (public vs. private) and confirm before defaulting.

7. **Source attribution** — how the skill will reference the original source. Usually a single line at the bottom of the SKILL.md (`Source: <url> — <title>, <author>`). If the source is paywalled or proprietary, ask before linking it publicly.

Then **ask the user clarifying questions, one at a time** — never stack. The point is to brainstorm direction with the user before committing; an A/B/C multiple-choice question almost always beats an open-ended one. Default order:

- Q1: "Does the proposed name + description fit, or should we narrow/broaden the scope?"
- Q2 (if scope is ambiguous): "I see two reasonable directions for this — A: <option>, B: <option>. Which?"
- Q3 (if destination is unclear): "Where should this live — project-local, user-global, or somewhere else?"
- Q4 (if there are clearly multiple skills hiding in the source): "The source actually contains two distinct skills — X and Y. Build both, just one, or fold them together?"

Stop asking once the design is clear. Don't manufacture questions to seem thorough.

**Hard rule: no files are written until the user has explicitly approved the design.** Approval looks like "yes", "go", "ship it", "looks good, build it" — not silence and not "ok I see". If the user redirects, loop back to Step 3 and re-present.

## Step 4 — Build the skill

Once approved, scaffold and write. Match the destination's conventions:

### Detect existing conventions first

Before creating files, look around for what already exists:

- Are there sibling skills under `skills/<name>/` or `.claude/skills/<name>/`? Read one to understand the layout.
- Is there a `scripts/new-skill.sh` or equivalent scaffold script? Use it — it likely patches registries atomically.
- Is there an `AGENTS.md`, `CLAUDE.md`, `README.md`, or `.claude-plugin/` registry at the destination root that describes layout rules? Read it and follow it.
- Are there per-skill manifests (`.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`) on sibling skills? If yes, the new skill probably needs them too.
- Is there a registry file (`marketplace.json`, root `plugin.json`, a README skills table) that lists every skill? If yes, the new skill needs to be added.

If any of these exist, follow them exactly. If none exist, fall back to the minimal layout below.

### Minimal layout (no existing conventions detected)

Create `<destination>/<skill-name>/SKILL.md` with frontmatter (`name`, `description`, optionally `allowed-tools`) and the body. Nothing else is strictly required.

### Writing the SKILL.md body

The body should encode the distilled learnings as imperative, actionable guidance — not a recap of the source. A reader of the SKILL.md should be able to apply the lessons without reading the source.

Strong structure:

1. **Frontmatter**: `name`, `description` (rich, trigger-laden — pack natural-language triggers and situations into it, since this is what Claude matches against in future sessions), `allowed-tools` (narrowest list that works).
2. **One-paragraph identity**: what this skill IS and the standard it holds itself to. Not a summary of the source.
3. **When to fire / when to skip**: triggering signals and explicit exclusions.
4. **The body**: patterns, tactics, anti-patterns from the distillation. Use numbered steps for workflows, tables for decision matrices, bullets for principles.
5. **Anti-patterns**: a short section calling out the mistakes the source warned against.
6. **Checklist** (optional, useful for workflow skills): end-of-task gates the skill should self-verify.
7. **Source line** at the bottom: `Source: <url> — <title>` so the lineage is preserved.

Length target: **80–250 lines**. Push past 250 only if the domain genuinely demands it; if so, split secondary content into `references/<topic>.md` and link from the body.

If sibling skills exist at the destination, read one or two before writing — match their voice, structure, and section conventions.

## Step 5 — Confirm and hand off

After writing, tell the user:

1. The file path(s) created and any registries patched.
2. How to invoke the skill (natural language matching the description, or the trigger phrases you encoded).
3. That marketplace- or plugin-installed skills typically become available next session or via reload, but skills written directly to a local skills directory are usable immediately.
4. Anything that needs manual follow-up (README row, marketplace description sync, etc., based on what conventions you detected).

Don't write a long summary. Path + how-to-invoke + any TODOs is enough.

## Anti-patterns

- **Transcribing the source instead of distilling it.** A SKILL.md that reads like the article is a failure. Future-Claude wants imperative guidance, not exposition.
- **Skipping the approval gate.** Writing the skill before the user has greenlit the design wastes their time when the framing is off.
- **Asking five questions in one turn.** One question at a time, A/B/C beats open-ended.
- **Building one skill from a source that's clearly two.** If the article has two unrelated themes, ask whether to split before scaffolding.
- **Putting potentially sensitive content in a publicly-distributed destination without checking.** Once it's public it's public forever. When in doubt, ask.
- **Forgetting source attribution.** The lineage matters for both credibility and future updates if the source changes.
- **Ignoring the destination's existing conventions.** If sibling skills have a layout, manifests, or a scaffold script, use them — don't invent a new shape.

## End-of-task checklist

Before declaring done:

- [ ] Source was ingested in full (not just a summary or snippet).
- [ ] Distilled learnings are actionable, not narrative.
- [ ] Design was presented and explicitly approved before any file was written.
- [ ] `name` + `description` are consistent across `SKILL.md` and any per-skill manifests or registry entries.
- [ ] Destination conventions were followed (scaffold script used if present, registries patched, sibling-skill style matched).
- [ ] Source attribution line is present in the new SKILL.md.
- [ ] User knows how to invoke the skill and where it lives.
