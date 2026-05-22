---
name: skill-use-audit
description: >
  Audit how well an installed skill performed in the current Claude Code
  session (or in a saved session log) and propose concrete improvements to
  the skill's SKILL.md. Reads the live session transcript, finds every
  invocation of the target skill, evaluates effectiveness against signals
  like trigger accuracy, post-invocation user steering, corrections,
  re-prompts, abandonment, and whether the user appeared satisfied with the
  outcome. Produces an assessment, a diff-style proposal for SKILL.md
  changes, asks for user approval, then writes the changes to wherever the
  skill lives on disk — and if the skill lives in a git repo, offers to
  stage and commit. Use this skill whenever the user says "/skill-use-audit",
  "audit a skill", "evaluate that skill", "how did /<name> do", "review the
  skill we just used", "evaluate effectiveness of <skill>", "check how
  <skill> performed", "grade the skill", or names a specific skill they
  want introspected (e.g. "/skill-use-audit /brainstorming", "audit
  /post-deploy-signal-check"). Also trigger when the user asks "why didn't
  X trigger when it should have" or "that skill needed too much hand-holding,
  what should we change" — those are skill-use-audit questions even without
  the literal phrase. Do NOT trigger for generic "review my code" requests
  (that's a code review), for creating new skills (that's /skill-creator),
  or for description-only triggering optimization (that's a separate flow
  inside /skill-creator).
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# /skill-use-audit — evaluate a skill's real-world performance and propose improvements

You are running a retrospective on a single named skill. The user has invoked it (or several skills, or none of the ones you'd expect) in a real conversation, and they want a grounded read on **how the skill actually performed in practice** — followed by surgical, evidence-backed improvements to the skill's `SKILL.md`.

This is not a vibes-only review. The conversation transcript is on disk, and you should read it directly. Speculation about "what the skill probably did" is the wrong move when the actual record is available.

## The four phases

1. **Locate** — find the target skill on disk AND the session transcript(s) to audit
2. **Extract** — pull every invocation of the target skill from the transcript, plus the surrounding context (the user message that triggered it, what came after, any corrections)
3. **Evaluate** — score the skill against a set of effectiveness signals, with citations back to the transcript
4. **Propose & apply** — present findings, propose specific edits to `SKILL.md`, get explicit user approval, write the changes, and offer to commit if the skill lives in a git repo

Each phase has clear inputs/outputs. Do not skip ahead. If a phase fails (e.g. you genuinely can't find the skill on disk), stop and ask the user rather than guessing.

---

## Phase 1: Locate

### Locate the skill on disk

The user typically passes the skill name as an argument: `/skill-use-audit /brainstorming`, `/skill-use-audit brainstorming`, `/skill-use-audit post-deploy-signal-check`. Normalize by stripping the leading `/`.

Search standard locations in order, stopping at the first definitive hit:

```
~/.claude/skills/<name>/SKILL.md
~/.claude/plugins/*/skills/<name>/SKILL.md
~/.claude/plugins/*/plugins/*/skills/<name>/SKILL.md
<current-project>/.claude/skills/<name>/SKILL.md
<current-project>/skills/<name>/SKILL.md
```

If the user works in a multi-repo skills workspace (e.g. the parent directory contains several `*-skills` folders), also check those. A quick `find ~/Documents -maxdepth 6 -path "*/skills/<name>/SKILL.md" 2>/dev/null` is fine as a fallback — keep depth bounded so it returns quickly.

If multiple matches: show all candidates to the user and ask which one to audit. Don't silently pick one — different copies may have diverged.

If zero matches: tell the user, list the paths you searched, and ask them to point at the SKILL.md directly.

Read the located `SKILL.md` in full. You'll need its current description and body to (a) judge whether invocations were appropriate per the stated triggers and (b) propose targeted edits later.

### Locate the session transcript(s)

Claude Code persists session transcripts as JSONL under `~/.claude/projects/<sanitized-cwd>/<session-id>.jsonl`. The sanitization rule is straightforward: the absolute cwd has `/` replaced with `-` and a leading `-` prefixed. For example, `/Users/alice/projects/foo` becomes `-Users-alice-projects-foo`.

Default behavior: audit **the current session**. The current session's JSONL is the most-recently-modified file in the project's transcript directory. Identify it like this:

```bash
# Most recent transcript for the current working directory
PROJECT_DIR=~/.claude/projects/$(pwd | sed 's|/|-|g; s|^|-|; s|-Users-|-Users-|')
ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1
```

If the user explicitly passes a different log path or session id, use that instead. Accepted forms:
- A full path to a `.jsonl` file
- A session id (find it under `~/.claude/projects/*/<session-id>.jsonl`)
- A range: "audit my last 5 sessions in this repo" — find the 5 most recent JSONLs in the project's transcript dir

If you can't find any transcript at all, stop and tell the user — don't fabricate invocations from memory of the conversation. The script below depends on the JSONL.

---

## Phase 2: Extract

Use the helper script to pull invocations out of the transcript(s):

```bash
python3 <skill-dir>/scripts/extract_invocations.py \
  --skill <skill-name> \
  --transcript <path-to-jsonl> \
  [--transcript <path-to-jsonl> ...]
```

The script emits a JSON document with this shape, one entry per invocation:

```json
{
  "skill": "brainstorming",
  "transcripts_scanned": 1,
  "invocations": [
    {
      "session_id": "...",
      "timestamp": "2026-05-21T15:55:38Z",
      "trigger_user_message": "<the user message immediately preceding the invocation>",
      "skill_args": "<the args passed to the Skill tool>",
      "subsequent_user_messages": ["...", "..."],
      "subsequent_tool_uses": ["Bash", "Edit", "Write"],
      "ended_with_user_correction": true,
      "correction_excerpts": ["no, that's not what I meant", "stop, back up"]
    }
  ],
  "near_misses": [
    {
      "timestamp": "...",
      "user_message": "<message that probably should have triggered the skill but didn't>",
      "what_was_used_instead": "<the tool/skill that actually ran, or 'nothing'>"
    }
  ]
}
```

Read the JSON carefully. If `invocations` is empty AND `near_misses` is empty, the audit reduces to "the skill didn't run and arguably didn't need to" — say so plainly and stop early rather than manufacturing findings.

For each invocation, the most important signal is **what happened after**. Read the transcript directly around each invocation timestamp — the script's summary fields are a starting point, not a substitute for the actual exchange. You'll need the raw context to judge whether the skill earned its keep.

---

## Phase 3: Evaluate

Use this rubric. Each axis gets a short verdict (one of: **strong**, **mixed**, **weak**, **n/a**) and one or two lines of evidence cited from the transcript.

1. **Trigger accuracy** — did the skill fire when it should have, and not when it shouldn't? Cross-reference the user messages against the skill's stated triggers in the description. Note both false positives (fired but shouldn't have) and false negatives (should have fired, didn't — these are the `near_misses` from the extractor).

2. **Steering required after invocation** — how much did the user have to redirect, clarify, or correct after the skill kicked in? Count user messages that read as corrections ("no", "that's wrong", "back up", "actually let's…", "stop"). A skill that needs heavy steering is either underspecified, overconfident, or both.

3. **Output acceptance** — did the user accept the skill's output, or rewrite/discard it? Look for follow-ups like "ok, do that" (accepted) vs. "let me write that myself" or extended re-prompting on the same task (rejected).

4. **Task completion** — did the skill see its work through to a sensible stopping point, or did it stall, loop, or abandon the task? Watch for: long tool-use chains with no resolution, repeated reads of the same file, the user manually finishing what the skill started.

5. **Triggering friction** — even when it did fire, was there an awkward handoff? E.g. the user typed `/skill-name` and the skill started by re-asking for info that was already obvious from context.

6. **Scope creep / scope under-shoot** — did the skill stay within its stated remit? Bleeding into adjacent skills' territory is a sign the description (or body) isn't drawing a clear enough boundary.

After scoring each axis, write a one-paragraph **overall assessment**. Be honest. If the skill performed well, say so and recommend no changes. If it performed poorly, name the specific failure modes.

See [references/eval-rubric.md](references/eval-rubric.md) for worked examples of each axis with transcript excerpts and the kinds of edits that follow from each diagnosis.

---

## Phase 4: Propose & apply

### Draft the improvement proposal

Based on the evaluation, draft a concrete set of edits to the located `SKILL.md`. Each edit must be tied to a specific finding from Phase 3. Vague suggestions ("make it clearer") are not acceptable — the user can't approve what they can't picture. Show the exact `old_string` → `new_string` you propose.

Common patterns:

- **False negatives** (skill should have triggered but didn't) → add the missing phrasing/trigger to the description. Be specific to the kind of user message you saw, not generic.
- **False positives** (skill triggered when it shouldn't have) → add a "Skip when…" clause to the description, or sharpen an existing one.
- **Heavy steering after trigger** → tighten the body's phase structure, add explicit "stop and ask" gates, or surface a constraint that was implicit.
- **Scope creep into another skill** → add a "Do NOT use this skill for X (use /other-skill)" line and link the boundary.
- **Output the user kept rewriting** → loosen overly rigid output templates, or constrain them where the skill was too freeform.

If you reach this point and have **no** concrete edits to propose, say so and end the audit — a skill that's working well doesn't need churn.

### Present the proposal

Show the user:

1. The overall assessment (one paragraph)
2. A bulleted list of findings, each with a one-line transcript citation
3. The proposed `SKILL.md` edits as a unified diff (old vs new), grouped by finding

Then ask explicitly: **"Apply these edits to `<path-to-SKILL.md>`?"** Wait for an explicit yes. Don't proceed on ambiguous answers.

### Apply the edits

After approval, use the Edit tool on the SKILL.md at the path located in Phase 1. Make the edits exactly as proposed — if the user said yes to the diff, the diff is what they approved.

### Offer to commit

After applying, check whether the SKILL.md lives in a git repo:

```bash
git -C <dir-of-SKILL.md> rev-parse --is-inside-work-tree 2>/dev/null
```

If yes, show the user the diff (`git -C <dir> diff -- SKILL.md`) and ask: **"Stage and commit these changes? If so, on what branch?"** Default behavior:

- If on `main` or `master`, refuse to commit there directly. Offer to branch off using a conventional name like `chore/skill-use-audit-<skill-name>` and commit there.
- Use a conventional commit message: `chore(skills): refine <skill-name> based on session audit` (or `fix(skills):` if the audit caught a real bug in the skill).
- Never push. Pushing is the user's job.
- Stage only `SKILL.md` (and any reference files you edited). Never `git add -A`.

If not in a git repo, just confirm the file was written and stop.

---

## Operating principles

- **The transcript is the truth.** If your memory of the session disagrees with the JSONL, the JSONL wins. Read it.
- **Cite evidence.** Every finding needs at least one transcript reference (timestamp + brief quote). Findings without evidence are speculation and shouldn't appear in the report.
- **Small, surgical edits.** This is `/unfuck`'s temperament applied to a skill file. A bad audit produces a bloated SKILL.md full of CYA clauses. A good audit produces three sharp edits that fix the actual observed failure modes.
- **Don't propose churn.** If the skill worked well, the right answer is "no changes needed" — say so cleanly.
- **Never write without explicit approval.** The user must see the diff and say yes before any file changes. The same gate applies to git operations: ask before staging, ask before committing.
- **Stay scoped to the named skill.** If you notice issues with adjacent skills, mention them briefly at the end as a separate "incidental observations" section — don't try to audit them in the same pass.

## Reference files

- [references/eval-rubric.md](references/eval-rubric.md) — Worked examples for each evaluation axis with transcript excerpts and example edits
- [scripts/extract_invocations.py](scripts/extract_invocations.py) — Pulls invocations + surrounding context out of one or more JSONL transcripts
