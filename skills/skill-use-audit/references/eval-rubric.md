# Eval rubric — worked examples

Each axis below: what the signal looks like in a transcript, what diagnosis it points to, and the kind of edit it should produce in `SKILL.md`. Use these as anchors, not as a checklist to mechanically apply.

---

## 1. Trigger accuracy

### False negative (should have fired, didn't)

**What it looks like in the transcript:** A user message clearly within the skill's stated remit, followed by the assistant doing the work freehand (via Bash/Read/Edit) without consulting the skill. The `near_misses` array from the extractor is your starting point — but verify each one by reading context, since the heuristic catches the skill name appearing in any context.

> User: "ok let's design a new internal tool for tracking PR review SLAs — what should the surface look like?"
> Assistant (no skill invocation): proceeds to ask three implementation questions without surfacing the underlying brainstorm.

**Diagnosis:** the description's triggers don't cover this phrasing. The user said "let's design" — a clear `brainstorming` signal — but the description over-indexed on the literal word "brainstorm."

**Edit pattern:** add the missing trigger phrase to the description, ideally clustered with similar phrasings:

```diff
- Use this skill whenever the user says "let's brainstorm", "help me think through", ...
+ Use this skill whenever the user says "let's brainstorm", "let's design", "let's figure out",
+   "help me think through", "what should X look like", ...
```

### False positive (fired but shouldn't have)

**What it looks like:** the skill ran on a message that was already well-specified, leading to obvious churn — the skill re-asks for info that was clear, or the user immediately overrides with "no, just do X."

**Edit pattern:** sharpen a "Skip when…" clause, or move ambiguous trigger phrases into a "soft trigger" zone that requires the request to also be underspecified.

---

## 2. Steering required after invocation

**Signal:** the `subsequent_user_messages` for an invocation are dominated by corrections — "no", "actually", "back up", "that's not what I meant", "stop." Two or three corrections in a row strongly suggests the skill's behavior diverged from intent right out of the gate.

**Diagnoses, in rough order of likelihood:**

- The skill's body assumes a workflow the user didn't want. Often the body's first instruction is too prescriptive ("First, do X, then Y, then Z…") and the user wanted a different sequence.
- The skill is over-asking. The user wanted action, the skill wanted clarification first.
- The skill is under-asking. The user expected a clarifying question and got an unwanted action instead.

**Edit pattern:** introduce an explicit "stop and ask" or "stop and act" gate based on what the transcript shows the user actually wanted. Example:

```diff
+ ## Before you start
+ If the user's request already names a specific file, function, or commit, skip the
+ discovery phase and go straight to action. Discovery is only valuable when the target
+ is ambiguous — when it isn't, the discovery questions are friction.
```

---

## 3. Output acceptance

**Signal:** the user discards or rewrites the skill's output. Look for "let me just do that myself", or the user pasting a completely different version, or a long silence followed by a new prompt that ignores what the skill produced.

**Diagnoses:**

- The output format is too rigid (e.g. a fixed markdown template that doesn't fit the user's intent).
- The output is too freeform (the user wanted a specific shape and got prose).
- The skill produced the wrong artifact entirely — e.g. wrote code when the user wanted a design doc.

**Edit pattern:** clarify the output contract. Sometimes that means *removing* a rigid template; sometimes it means *adding* one. Let the failure mode tell you which.

---

## 4. Task completion

**Signal:** long chains of `subsequent_tool_uses` (Read, Bash, Read, Bash, …) without a resolving action, or repeated reads of the same file. The skill is spinning rather than completing.

**Diagnoses:**

- The skill body doesn't define a stopping condition.
- The skill body has too many phases and the model is dutifully running through each even when earlier ones already resolved the task.
- The skill's instructions encourage exhaustive search instead of "search until you find enough."

**Edit pattern:** add an explicit completion gate. Example:

```diff
+ ## When to stop
+ Stop as soon as you have enough evidence to answer the user's question. Reading more
+ files past that point is friction, not thoroughness — every additional read pushes
+ useful signal further down in the user's view.
```

---

## 5. Triggering friction

**Signal:** the user invokes `/skill-name`, the skill's first action is to ask a question that's already answered by the user's original message or visible in the file selection / cwd.

**Edit pattern:** pull context discovery up front. Tell the skill to *read* before *asking*.

```diff
- ## Phase 1: gather context from the user
- Ask the user: what file? what behavior? what's expected?
+ ## Phase 1: gather context
+ Check the user's message and IDE selection first. If the file path, function name,
+ or specific behavior is already named — use it. Only ask if the information is
+ genuinely missing.
```

---

## 6. Scope creep / scope under-shoot

**Signal:** the skill did meaningful work that another, more specialized skill should own — or it bailed early on work that was clearly within scope.

**Edit patterns:**

- For creep: add an explicit boundary line, ideally with a pointer to the right alternative. ("Do NOT use this skill for X — use /other-skill instead.")
- For under-shoot: remove an overly-narrow caveat. The skill was being too cautious.

---

## Writing the report

When you assemble findings into the report shown to the user, organize by axis. For each finding:

- **The axis** (e.g. "Trigger accuracy — false negative")
- **The evidence** (one short transcript quote with timestamp)
- **The diagnosis** (one sentence)
- **The proposed edit** (a real diff hunk against `SKILL.md`)

Keep findings under ~5 unless the skill is in genuinely bad shape. The goal is surgical improvement, not a rewrite. If you have 12 findings, group them by theme and pick the 3-4 that would move the needle most.
