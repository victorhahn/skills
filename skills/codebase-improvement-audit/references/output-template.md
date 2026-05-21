# Inline Output Templates

These templates describe the chat output for the audit. **Nothing is written to disk.** Print directly to chat in the format below, sized to match the dispatch mode.

---

## Mode 0 — Compact inline (solo, narrow ask)

Aim for ~30-60 lines of terminal output. No tables, no tiers, no methodology section. If 2-3 findings, just list them. If zero real findings, say so plainly with what you checked.

```markdown
**Audit — <one-line scope>** (solo, no specialists)

**Headline:** <1-2 sentences. The most important thing to hear.>

**Findings**

1. **<Title>** — Impact <1-5> · Effort <1-5> · Risk <Low/Med/High>
   <2-3 lines of evidence (files, lines, versions) + suggested approach.>

2. **<Title>** — Impact … · Effort … · Risk …
   <evidence + approach>

3. **<Title>** — …
   <evidence + approach>

**Ruled out**
- <one-line: what + why it's not worth it>
- <one-line>

**Suggested next step:** <one sentence — usually item #1 and how to apply it>
```

If zero findings:

```markdown
**Audit — <one-line scope>** (solo)

Looked at <list paths/areas>. Nothing actionable surfaced that meets the
evidence+impact bar.

**What I checked and ruled out**
- <one-liner>
- <one-liner>
- <one-liner>

If you want me to go deeper or broaden the lens, say the word.
```

---

## Modes 1, 2, 3 — Full inline (focused or broad)

Use this when one specialist (Mode 1), a fan-out (Mode 2), or the canonical roster (Mode 3) ran. Include only the sections that apply — if compliance context wasn't detected, omit the compliance section; if a tier is empty, omit it.

```markdown
**Codebase Improvement Audit**

- **Scope:** <repo / paths / what was excluded>
- **Mode:** <Focused: $domain | Focused fan-out: $domain | Broad>
- **Stack:** <one line — primary languages, frameworks, versions>
- **Specialists run:** <names, comma-separated>

## Headline

<3-5 sentences. What's the top theme, top risk, top opportunity. A reader
skimming this should know whether to invest the next sprint in modernization,
security hardening, test coverage, or none of the above.>

## Compliance posture
<Include this section only when HIPAA or SOC 2 context was detected.>

- **HIPAA-relevant findings:** <count>, top concerns: <one line>
- **SOC 2-relevant findings:** <count>, mapped controls: <CC6, CC7, etc.>
- **Disclaimer:** This audit surfaces engineering-visible gaps. It does not
  constitute a formal HIPAA Security Rule assessment or SOC 2 attestation.

## Tier 1 — Quick wins  (Impact ≥ 3, Effort ≤ 2, Risk = Low)

| # | Title | Impact | Effort | Risk | Category | Compliance |
|---|-------|--------|--------|------|----------|------------|
| 1.1 | ... | 4 | 1 | Low | Security | none |
| 1.2 | ... | 3 | 2 | Low | Deps | SOC 2 CC6 |

**Suggested order:** <one line>

For each Tier 1 item:

**1.1 <Title>**
- **Evidence:** <files, lines, versions>
- **Why it matters:** <1-2 sentences>
- **Approach:** <2-3 sentences, test-first when applicable>
- **Validation:** <which tests/typechecks/lint runs prove no regression>

(repeat for 1.2, 1.3…)

## Tier 2 — Solid investments  (Impact ≥ 3, Effort ≤ 3, Risk ≤ Med)

<Same table + per-item details. Omit section if empty.>

## Tier 3 — Larger initiatives  (Impact ≥ 4, Effort ≥ 4 OR Risk = High)

<Same table + per-item details, plus a "Sequencing / dependencies" line
per item. Omit section if empty.>

## Iterative rollout plan

The first three PRs to ship if you act on this.

**PR 1 — <Title>** (Tier 1 batch)
- Scope: <items>
- Validation: <how we know nothing regressed>
- Effort: <S/M>

**PR 2 — <Title>**
- Scope: …
- Validation: …
- Effort: …

**PR 3 — <Title>**
- Scope: …
- Validation: …
- Effort: …

## Findings ruled out

- <one-line item> — <why dropped>
- <one-line item> — <why dropped>

## Methodology

- Specialists run: <list>
- Scope: <paths included / excluded>
- Confidence threshold: Med and High only; Low-confidence dropped.
```

---

## Output sizing guidance

| Mode | Findings expected | Output length |
|------|------------------|----------------|
| 0 — solo narrow | 0-5 | ~30-60 lines |
| 1 — single specialist | 3-8 | ~80-150 lines |
| 2 — domain fan-out | 8-15 | ~150-250 lines |
| 3 — broad roster | 10-25 | ~200-400 lines |

If you're producing significantly more than this, you're padding. Cut to the highest-value findings and move the rest to "ruled out / lower priority" one-liners.

## When the user asks for a saved copy

Only if they explicitly say "write this to a file" / "save the report" — then write to `CODEBASE_AUDIT.md` (or `<repo>/docs/CODEBASE_AUDIT_<YYYY-MM-DD>.md` if a previous file exists). Otherwise: chat only.
