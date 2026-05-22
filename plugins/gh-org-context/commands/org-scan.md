---
name: org-scan
description: Full scan of a GitHub org — builds or rebuilds the complete distilled context under context/orgs/<org>/
allowed-tools: Bash, Read, Write, Edit
---

# /org-scan <org>

Build the "onboarded engineer" knowledge base for GitHub org `<org>`. This runs in two phases: **Data collection** (scripts fetch GitHub metadata, clone repos, detect runbooks) and **Synthesis** (you read the raw data and write the domain knowledge files).

## Phase 1 — Preflight

Resolve `PLUGIN_ROOT` as the absolute path of the directory containing `commands/` (this file's parent). Everything goes under `$PLUGIN_ROOT/context/orgs/<org>/`.

Run:
```
bash $PLUGIN_ROOT/skills/org-context/scripts/gh_preflight.sh <org>
```

Handle exit codes conversationally:
- **10**: `gh` not installed → "Install with `brew install gh` or visit https://cli.github.com, then retry."
- **20**: Not authenticated → "Run `gh auth login` (GitHub.com → HTTPS → browser). Do NOT run it yourself — it needs an interactive TTY."
- **30**: Missing scopes → "Run `gh auth refresh -s read:org,repo`."
- **40**: Org not found or SSO blocked → "You may not be an org member, or your token needs SSO enabled at https://github.com/settings/tokens."
- **50**: Rate limit low → report remaining and reset time, ask whether to wait.
- **0**: Proceed.

## Phase 2 — Data collection (scripts)

Bootstrap venv if needed and run the data collection script:

```bash
cd $PLUGIN_ROOT/skills/org-context
python3 -m venv scripts/.venv 2>/dev/null || true
scripts/.venv/bin/pip install -q -r scripts/requirements.txt
scripts/.venv/bin/python scripts/scan.py \
  --org <org> \
  --output $PLUGIN_ROOT/context/orgs/<org>
```

The script will:
- Fetch all repos, tier them (1/2/3) based on activity
- Shallow-clone Tier-1 repos to detect runbook commands, CI workflows, approvers
- Render Tier-1 repo .md files (these are deterministic — runbook fields, tech stack, etc.)
- Render Tier-3 archive stubs
- Write `_synthesis_input.json` — structured data for your synthesis pass
- Write `_cluster_input.json` if any repos couldn't be automatically domain-assigned

Tell the user the script is running and may take a few minutes for large orgs.

## Phase 3 — Domain clustering (if needed)

If `$PLUGIN_ROOT/context/orgs/<org>/_cluster_input.json` exists after the script finishes, read it. It contains repos that fell through the automatic assignment cascade (domains.yml → CODEOWNERS → topics → prefix).

Perform the clustering yourself. Read `references/synthesis-guide.md` → "Domain clustering" for the approach. Write your assignments to `_cluster_output.json` in the same directory. The synthesis step (below) picks it up.

## Phase 4 — Synthesis (your most important job)

Read `$PLUGIN_ROOT/context/orgs/<org>/_synthesis_input.json`. It contains all the collected repo data including README excerpts. Now write the knowledge files:

**For each domain, write `domains/<domain>.md`:**

Use the template shape from `references/frontmatter-schemas.md` but write the CONTENT yourself — don't generate placeholder text. Specifically:
- `capabilities`: infer from repo names, descriptions, README excerpts, internal_deps names
- `description` (frontmatter and body): one sharp sentence + a paragraph that answers "what does this domain own and why does it exist?" Reference actual repos by name.
- `upstream_deps` / `downstream_consumers`: derive from `internal_deps` fields across repos — if `payments-api` depends on `auth-sdk` and `auth-sdk` lives in the `auth` domain, then `payments → auth`
- `critical`: set to true if multiple domains depend on it, or it handles auth/money/infra
- `## Domain conventions`: summarize common test/release patterns across the domain's Tier-1 repos

**Write `ORG.md`:**

Write this yourself too — don't template-render it. The frontmatter needs the stat fields (repo_count, tier1_count, etc.) from `_synthesis_input.json`. The body should read like a 5-minute orientation for a new engineer: which domains matter most, what the most active repos are, any notable cross-domain dependencies, what the org's general tech stack and release culture look like.

Read `references/synthesis-guide.md` → "Domain synthesis" and "Intelligent post-scan briefing" for guidance on both.

## Phase 5 — Update domains.yml

If domain clustering created new domains, add them to `domains.yml` under `domains:` with a `# auto-generated, review` comment. The user should ratify these.

## Phase 6 — Briefing

Give the user a 5–8 sentence briefing (not a file dump). Cover:
1. What domains you found and which ones matter most
2. The top 2–3 most active repos and what each does
3. Any interesting cross-repo connections or dependencies
4. Anything that stood out (lots of archived repos = technical debt; fragmented domain ownership; unusually complex CI setup)
5. The one domain file most worth reading first for a newcomer

Then point them to `context/orgs/<org>/` and suggest `/org-update <org>` for incremental refreshes going forward.

## Notes

- If `<org>` is missing from the invocation, ask before doing anything.
- Never dump file contents verbatim into the conversation — summarize and point to paths.
- If the script fails on individual repos, those are logged in `.failures.log` — mention the count but don't enumerate every failure.
