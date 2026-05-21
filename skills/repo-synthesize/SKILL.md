---
name: repo-synthesize
description: >
  Deep-read one or more repos and produce structured Markdown documentation
  covering both structure and capabilities. Use whenever the user says
  "synthesize this repo", "document this project", "what does this codebase do",
  "deepwiki X", "analyze this workspace", "create docs for this project", or
  points at a folder of related repos and wants to understand how they fit
  together. Works on a single repo OR a multi-repo workspace (a parent folder
  containing several related repos — app + infra + libs, frontend + backend,
  etc.). Runs a deliberate three-phase Recon → Delta Plan → Write workflow with
  an explicit human approval gate before writing anything. For workspaces,
  always produces at least one synthesis page covering how the repos
  interconnect.
---

# Repo Synthesize

You are doing a thorough read of one or more repos and producing structured documentation that captures both *structure* (what it's made of) and *capabilities* (what it lets people do).

## The Two Axes: Structure AND Capabilities

A code project has two distinct things worth documenting, and you must cover both deliberately. The most common failure mode is over-indexing on the first and missing the second.

| Axis | Question it answers | Where the evidence lives |
|---|---|---|
| **Structure** | What is this project made of? | Repos, sub-services, manifests, infra config, deployment topology |
| **Capabilities** | What does this project *do* for someone? | Routes, handlers, public APIs, UI features, jobs, migrations, recent commits, tests |

Structure is easier to extract — it's right there in `package.json`, `docker-compose.yml`, the workspace layout. Capabilities take more work because they're spread across the surface of the code: an HTTP route, a database migration, a Lambda handler name, a CHANGELOG entry, a test file describing a behavior. **You must actively hunt for capability signal.** Documentation that lists "service X has a UI, a Lambda, and a datastore" without saying what those things actually *let people do* is half-done.

Concrete capability prompts to keep in your head during recon:

- **What does a user / consumer do with this?** Submit a form? Pull a quote? Run an experiment? Configure a flag? Get a webhook?
- **What features have shipped recently?** Commit messages, CHANGELOG, recent migration filenames, recent route additions.
- **What's the public API surface?** OpenAPI/swagger, GraphQL schema, protos, exported SDK functions, page routes for a UI.
- **What background work happens?** Cron jobs, queue consumers, scheduled Lambdas, ETL pipelines.
- **What's the data model in user terms?** Not the table list — the entities users think in.

When you write pages in Phase 3, every project overview and most satellite pages should have an explicit **capabilities** section answering "what can this do?" — not just a structure dump.

## Before You Start

1. **Identify the target.** The user will name a project, a folder, or a workspace. Resolve it to an absolute path. If unclear, ask one targeted question — don't guess.
2. **Detect repo mode** by inspecting the target path:
   - `.git/` at the root → **single-repo mode**.
   - Multiple immediate subdirectories that each contain `.git/` (or look like repos — `package.json`, `go.mod`, `*.tf`, etc.) → **workspace mode**.
   - Mixed (top-level repo plus nested ones) → workspace mode, but flag the structure to the user.
3. **Git branch gate.** Before touching any files, check the current branch for each repo: `git -C <path> rev-parse --abbrev-ref HEAD`. If any repo is on a branch other than `main` or `master`, pause and surface it:

   > "You're on `<branch>` in `<repo>`. Synthesis is usually most useful against the source-of-truth state on main — feature branches may have in-progress work that doesn't reflect the real shape of the project. Proceed on `<branch>`, or should I switch to main with a fresh pull first?"

   Wait for explicit confirmation before proceeding. If the user says to use main: run `git -C <path> checkout main && git -C <path> pull --ff-only` in each affected repo, then continue. If the user confirms the feature branch (e.g., they specifically want to document an in-progress feature), continue as-is.

   In workspace mode, collect all non-main branches across repos and ask once in aggregate rather than per-repo.

   Skip this check when HEAD is detached (specific tag or commit) — the user clearly knows what ref they want.

## Capture User Context

**If the user's initial prompt is sparse** (e.g. just a path with no description of what the project does, how the repos interact, or what's changed), pause before recon and ask one focused question: **"What should I know about how these repos interact and what's changed?"** Their answer captures context you can't reliably infer — planned deprecations, ownership shifts, why one repo is "legacy", who owns what. This question is required when context is sparse; skip it only when the user has already provided a paragraph or two of framing.

If the user gives you nothing (or says "just infer it"), proceed with inference — but mark every cross-repo wiring claim with `^[inferred]` until proven by code. Don't make this a long interview; one question, then move on.

## Phase 1 — Recon (read-only)

You are not writing anything yet. You are building a mental model of what each repo *is* and *does* right now. The order is **breadth first, then depth** — get a structural skeleton, then aggressively hunt for capability signal, then dive into specific files only when a question demands it. **Stop when you can answer both "what is this?" and "what does it let people do?" with concrete examples — not before.**

### Structural skeleton (do this first, fast)

1. **High-signal docs**: `README.md`, `docs/`, `CLAUDE.md`, `AGENTS.md`, `swimm/`, `ARCHITECTURE.md`, `DESIGN.md`, `CHANGELOG.md`. These describe intent and often list features explicitly.
2. **Project manifests**: `package.json`, `pnpm-workspace.yaml`, `go.mod`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `Gemfile`, `*.csproj`. The `scripts:` or task entries often reveal capability (e.g. `generate:api`, `seed:demo`, `run:worker`).
3. **Ownership and deployment signal**: `CODEOWNERS`, `.github/workflows/`, `Makefile`, `Dockerfile`. Workflows tell you what's deployed, where, and how.

### Capability hunt (do this next, deliberately)

This is the step that's easy to skip and most often missed. Spend real budget here.

4. **Public API surface** — the single richest capability source:
   - `openapi.yaml` / `openapi.json` / Swagger — every operation is a capability.
   - GraphQL schema files (`*.graphql`, `schema.graphql`).
   - gRPC/proto files (`*.proto`).
   - Exported SDK functions if it's a library.
5. **Route tables and handlers** — read enough to enumerate the verbs:
   - Express/Fastify/Koa: route registration files, `router.*` calls.
   - Next.js: `pages/api/` or `app/*/route.ts` directory listings.
   - Go: HTTP mux registrations, `cmd/*/main.go`.
   - Frontend pages: `pages/`, `app/`, route configs — what screens exist?
   - Lambda: handler names + their SAM/Serverless event sources (HTTP, SNS topic, cron, S3, DynamoDB stream).
6. **Background work**: cron specs, queue consumers, scheduled events, ETL job definitions. Each is a capability that doesn't show up in a route table.
7. **Migration / schema history**: `migrations/`, `db/migrations/`, Prisma/Drizzle schema files. Migration filenames are a free changelog of features.
8. **Recent commit signal**: `git log --oneline -50` in each repo. Look for `feat:` / `feature/` / `add ` commits.
9. **Test names as a behavior spec**: `*.spec.ts`, `*_test.go`, `tests/**` filenames and top-level `describe`/`it` strings often read like a feature list.

### Infrastructure & cross-repo wiring (only if relevant)

10. **Infrastructure-as-Code repos** specifically:
    - If a *live* IaC config (per-environment compositions): which modules each environment composes, what providers/regions are pinned, what big-bucket resources exist.
    - If a *module* library: only the modules the project actually consumes upstream.
11. **Cross-repo wiring**: configs that reference other repos (URLs, queue names, deployed endpoint names, shared package names). Raw material for the synthesis page.

**Always skip**: `node_modules`, `dist`, `build`, `.next`, `.pnpm-store`, `vendor`, `target`, `.venv`, `__pycache__`, `.git`, `coverage`, generated SDKs, lock files (unless you need a pinned version).

**Track as you go**: keep a running list of `(repo, file_path, fact_extracted)`. You'll need it to know which claims are `extracted` vs `inferred`.

**Capture HEAD commit per repo during recon.** Run `git -C <repo> rev-parse --short HEAD` for each repo. These hashes go into Phase 3 metadata. Doing this upfront avoids re-walking repos later.

Do not summarize the repo to the user in long-form during this phase. Take notes silently. The deliverable is Phase 2's plan.

## Phase 2 — Delta Plan (present, then wait)

Now compare recon findings to any existing documentation state. **Output a structured plan and stop. Do not write anything yet.**

Present a fresh topology proposal based on what recon found.

**Present the plan in this format**:

```
## Recon summary
- <repo-1>: <one-line "what it is"> — <one-line "what it does">
- <repo-2>: ...

## Capabilities I found
Group by repo or domain, whichever reads more naturally. Each bullet should be
something a person could *use* or *do* — not architecture.

- <repo>: exposes a `/quotes` POST endpoint that triggers an appraisal workflow
- <repo>: runs a nightly cron at 02:00 UTC that recomputes user audiences
- <repo>: admin UI lets ops users create/edit experiments and flip flag rollouts

If a repo's capabilities are unclear or uniformly internal, say so explicitly.

## Proposed file structure

## Proposed synthesis page (workspace mode only)
- <filename> — <one-sentence purpose>

## Open questions for you
- <anything ambiguous to confirm before writing>
```

The "Capabilities I found" block is required.

### Proposed file structure

Use this scaffold — skip sections with no evidence, add any the repo demands:

| File | Create when you see |
|---|---|
| `overview.md` | Always — project summary, who it serves, what it does |
| `architecture.md` | Multiple services, significant abstractions, non-trivial deployment shape |
| `data-model.md` | Migrations, schema files, Prisma/Drizzle models, ER-worthy entities |
| `api-surface.md` | OpenAPI spec, route tables, exported SDK functions, GraphQL schema |
| `frontend.md` | `pages/`, `app/`, UI components, screen-level routes |
| `background-jobs.md` | Crons, queue consumers, scheduled Lambdas, ETL jobs |
| `deployment.md` | Dockerfiles, Makefiles, CI workflows, Terraform modules consumed |
| `configuration.md` | Non-trivial env var surface, feature flags, external config schema |
| `synthesis.md` | Workspace mode only — how repos interconnect |

Each entry in the proposal should name the source evidence that justifies it (e.g. "api-surface.md — `openapi.yaml` found, 23 operations"). This gives the user a clear basis for pruning before you write.

**Then stop and wait for approval.** This gate is the whole point of the skill.

## Phase 3 — Write

Write the approved files to `<project>-synthesis/` in the **current working directory**, unless the user specified a different output location. Never place the synthesis directory next to or inside the source repos.

### Content rules

**Structure + capabilities on every page.** A workable default outline:

```markdown
# <Project / Repo / Topic>

One paragraph: what this is, who it serves.

## What it does
Bullet list of capabilities — verbs the user/consumer cares about. Each bullet
notes where in the code it lives (file/path or endpoint).

## How it's built
Structure: sub-services, deps, deployment shape, key abstractions.

## Related
Links to other pages in the synthesis set.
```

Adapt the labels to the topic. Every page should answer "what does it do?" before "what is it made of?" If a topic genuinely has no user-facing capability axis (e.g. a shared logging library), say so up front and lean structural.

**Diagrams.** For architecture, data flow, request lifecycle, deployment topology, or component relationships — default to Mermaid, not prose.

- `graph TD` — component topology, dependency graphs, service maps. Always top-down.
- `sequenceDiagram` — request/response flows, event handling, async message passing.
- `erDiagram` — data models, schema relationships.
- `flowchart TD` — decision trees, process flows, state transitions.

Keep node labels to 3–4 words max. Derive diagrams only from what you actually read — don't invent topology. Follow every diagram with a one-sentence explanation and cite the source files.

**Tables for structured data.** When a section covers more than ~4 entries of the same kind:

| Use a table for | Columns |
|---|---|
| API endpoints | Method, Path, Description, Auth required |
| Config options / env vars | Key, Type, Default, Description |
| Data model fields | Field, Type, Nullable, Description |
| Background jobs / crons | Name, Schedule, What it does |
| Lambda handlers | Handler name, Trigger source, Output |

**Don't paste code.** Distill the knowledge. "The Lambda is triggered by SNS topic X, processes events with the Y handler, and writes to DynamoDB table Z" is worth documenting. Pasting the handler function is not.

**Provenance markers.** Mark uncertain claims:
- Default (no marker) = extracted directly from source.
- `^[inferred]` — you reasoned to this claim (cross-repo wiring, design rationale, "why" statements).
- `^[ambiguous]` — README and code disagree, or there's a visible in-progress migration.

### Synthesis page (workspace mode)

Always produce one for workspace mode. The shape depends on the workspace:

- App + infrastructure → "How <project> deploys" — which modules back which services, data flow.
- Multiple services → "<project> service map" — how they call each other, shared schemas, event flow.
- Library + consumers → "<project> dependency graph" — what depends on what, version skew.

The synthesis page is the high-leverage artifact — it answers questions no single repo's README can.

### Optional: rendered HTML

A helper script ships with the skill: `scripts/render.mjs` takes the synthesis directory and produces a self-contained HTML wiki. Requires Node 18+ and pnpm. Run it only if the user asks for a browsable rendered output.

```bash
node skills/repo-synthesize/scripts/render.mjs <project>-synthesis/
```

## Working Heuristics

- **Lead with capabilities, follow with structure.** Structure is the answer to "how"; capabilities are the answer to "what".
- **Be conservative about claims.** When in doubt, mark `^[inferred]`.
- **Synthesis is the high-leverage output.** A user can read a README. They cannot easily read three READMEs and know how the pieces fit.
- **One synthesis page is enough.** If the workspace has multiple disconnected concerns, propose them in Phase 2 and let the user pick.
- **A short capability list beats a long one.** Aim for the 5–10 capabilities a teammate would actually need to know.

## When Not to Use This Skill

This skill earns its keep when there's a named project area and at least one repo (often several) worth doing a thorough read on. Skip it for one-off questions, single-file investigations, or anything that doesn't justify the recon + plan + write overhead.
