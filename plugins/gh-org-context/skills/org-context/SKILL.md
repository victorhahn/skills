---
name: org-context
description: Builds and queries a structured knowledge base for a GitHub org or repo bundle — tech stack, domains, runbooks, cross-repo connections, team ownership, release process, test commands, and approvers. Use this skill whenever a user asks how to understand, navigate, or work within a large multi-repo codebase; when they're confused about which repos matter or how services connect; when they need to know who owns something or how to run/test/release a service; when any other skill needs org or repo context to do its job (it should trigger this skill to load the knowledge base rather than re-deriving from scratch). This is the "onboarded engineer" context layer — build it once, use it everywhere.
allowed-tools: Bash, Read, Write, Edit
---

# org-context

The goal is a knowledge base that captures what an experienced team member knows after a few weeks on the job: which repos matter, how domains connect, how to work in each service, and who owns what. Scripts handle the data collection (GitHub API, file parsing, shallow clones). **You write the knowledge** — the synthesis, the narrative, the domain insight.

## Data layout

```
${CLAUDE_PLUGIN_ROOT}/context/
  orgs/<org>/
    ORG.md               # org overview
    domains/<name>.md    # one per team/capability area
    repos/<repo>.md      # Tier-1 repos — full runbooks and connections
    archive/<repo>.md    # Tier-3 stubs — archived/stale
    domains.yml          # editable config; survives scans
  bundles/<bundle>/
    BUNDLE.md
    ... same structure, repos named <owner>__<repo>.md
```

## Slash commands

- `/org-scan <org>` — full scan of a GitHub org
- `/org-update [<org>]` — incremental refresh (only re-processes changed repos)
- `/repos-scan <bundle> <owner/repo>...` — curated cross-org bundle
- `/repos-update [<bundle>]` — incremental bundle refresh

## Your role: data collection vs. synthesis

The scripts handle everything deterministic: GitHub API calls, tiering, shallow clones, runbook field detection, file rendering.

What they **can't** do is understand context. That's your job:

| What scripts produce | What you add |
|---|---|
| `capabilities: []` in every domain | Infer from repo names, descriptions, README features, dep names |
| `upstream_deps: []` / `downstream_consumers: []` | Map by reading `internal_deps` across repos |
| `description: "payments-api service"` (generic) | Write something specific: what it actually owns and why it exists |
| Skeleton bodies with placeholder text | Fill in the narrative sections with real insight |
| `_cluster_input.json` when repos couldn't be auto-assigned | Read it and perform domain clustering yourself |

Read `references/synthesis-guide.md` before doing any enrichment — it covers capability inference, cross-domain mapping, clustering, and the post-scan briefing format.

## Tiering (scripts decide this automatically)

| Tier | Condition | Output |
|------|-----------|--------|
| 1 | High activity — commits, PRs, recent releases, or allowlisted | Full repo file with runbook, deps, CI |
| 2 | Moderate — not stale, not highly active | Mentioned in domain file only, no own file |
| 3 | Archived / dormant | One-line stub in `archive/` |

## Domain inference (scripts run this, you handle leftovers)

The script runs a cascade: `domains.yml` → CODEOWNERS/team ownership → GitHub topics → name-prefix heuristics. Repos that fall through write `_cluster_input.json` for you to handle. See `references/synthesis-guide.md` → "Domain clustering."

## Schema reference

Full frontmatter schema for all file types: `references/frontmatter-schemas.md`

Key fields for quick filtering:
- `type` — `org-summary | bundle-summary | domain | repo | repo-stub`
- `tier` — `1 | 2 | 3`
- `domain` — team/capability slug
- `critical` — `true | false`
- `test_cmd`, `install_cmd`, `dev_cmd` — runbook commands
- `approvers`, `required_reviewers` — ownership/review info
- `internal_deps` — other org repos this depends on

## Downstream consumer pattern

For any skill that needs to query this data: `references/consumer-pattern.md`

Check if context exists before querying:
```bash
test -f "$PLUGIN_ROOT/context/orgs/<org>/ORG.md" || echo "Run /org-scan <org> first"
```

## Setup

- `gh` CLI installed and authenticated (`gh auth login`)
- Token scopes: `read:org`, `repo`
- Python 3.9+ (venv bootstrapped automatically on first run via slash commands)

## Phase 2 (not yet implemented)

Confluence, Jira, Notion, Slack channel topics. The `scope`, `schema_version`, and `org` frontmatter fields are sized to survive this addition.
