# Synthesis guide

The scripts collect raw data (GitHub API, shallow clones, file parsing). **You write the knowledge.** This guide explains how to turn raw data into the kind of insight an experienced team member would have after a few weeks on the job.

---

## Reading `_synthesis_input.json`

This is your primary working document. For each repo it contains:

- `description` — GitHub repo description (often short/generic)
- `key_files` — structured content extracted from the repo's baseline context files:
  - `claude_md` — CLAUDE.md body (if it exists) — **highest priority**: written for AI consumption, often contains architecture notes, important constraints, team conventions
  - `agents_md` — AGENTS.md body — similar purpose
  - `readme` — first 2000 chars of README — human-facing entry point
  - `package_json` — name, description, scripts, main dependencies
  - `openapi` — API title, description, path list, tags (great for understanding what this service exposes)
  - `docker_compose` — services map (reveals what runtime dependencies this app has)
  - `contributing` / `architecture` — process and design docs when present
- `runbook` — detected commands (test_cmd, install_cmd, etc.) for Tier-1 repos
- `internal_deps` — other org repos listed as dependencies

**The CLAUDE.md/AGENTS.md content is gold.** If a repo has one, read it first before trying to infer anything — it's been written explicitly to describe the service's purpose, architecture, and quirks. Let it anchor your description and capability list.

## Domain synthesis (after scripts finish)

When `scan.py` finishes, domain files don't exist yet — you write them. Read `_synthesis_input.json` and for each domain, synthesize the domain file from the repo data.

### Inferring capabilities

Capabilities are the THINGS this domain is responsible for — the verbs and nouns of its business logic. Read in priority order:

1. **`key_files.claude_md` / `key_files.agents_md`** — if a CLAUDE.md or AGENTS.md exists, its description section usually names the service's responsibilities directly. Extract from there.
2. **`key_files.openapi.tags` and `.paths`** — a service exposing `/v1/payments/*`, `/v1/subscriptions/*` paths → capabilities: `payment-processing`, `subscription-management`
3. **`key_files.readme`** — look for "Features", "What this does", "Capabilities" sections
4. **Repo names and descriptions** — `payments-api` + "Handles card processing and refunds" → capabilities: `card-processing`, `refund-flow`
5. **`internal_deps`** — if `auth-sdk` is a dep of several repos in this domain, the domain probably handles authentication
6. **CI workflow names** — a `release-mobile-sdk.yml` workflow suggests an SDK publishing capability

Write capabilities as short, lowercase, hyphen-separated noun phrases (not sentences). 3–8 per domain is the right range — fewer means the domain is too vague, more means it should be split.

**Good:** `card-processing`, `subscription-management`, `invoice-generation`
**Bad:** `handles payments`, `PaymentService`, `billing stuff`

### Inferring cross-domain dependencies

Look at `internal_deps` fields in the Tier-1 repo files. If `payments-api` lists `auth-sdk` as an internal dep, and `auth-sdk` belongs to the `auth` domain, then `payments → auth` is an upstream dependency.

Map these bottom-up and write them into both domain files. The goal is to understand: which domains are foundational (many consumers) vs. leaf-level (few consumers)?

### Writing the domain description

The description field (frontmatter) and the first paragraph of the body should answer: "If someone new to the team asked 'what does the payments domain own and why does it exist?', what would you say?"

Be concrete. Reference actual repos. Use the business language that appears in READMEs.

**Weak:** "The payments domain handles payment-related services."
**Strong:** "Owns the full money movement stack — card processing, subscription lifecycle, refund flow, and the accounting ledger. The `payments-api` is the system of record; `payments-worker` handles async operations like settlement and reconciliation."

### Flagging critical domains

Mark a domain `critical: true` if:
- Multiple other domains depend on it (foundational)
- Its Tier-1 repos have `required_reviewers >= 2` or strict CODEOWNERS
- It handles money, auth, data privacy, or infrastructure
- Outages in this domain would break other services

---

## Repo body enrichment (Tier-1 repos)

After the script renders the repo file, check whether the runbook sections are populated. If any are `null` or `unknown`, consult `key_files` in `_synthesis_input.json`:

- `install_cmd: null` but `key_files.docker_compose` shows services → `docker compose up` is likely the dev entry point
- `release_method: unknown` but `key_files.readme` mentions "tag and push to release" → tag-push
- `approvers: []` → check if `key_files.claude_md` or `key_files.contributing` mentions review requirements
- `description` is generic → rewrite it using the opening paragraph of `key_files.claude_md` or `key_files.readme`
- `frameworks: []` → derive from `key_files.package_json.main_deps` (e.g. `express`, `fastify`, `nextjs` → framework names)
- `infra: []` → derive from `key_files.docker_compose.services` image names or `key_files.openapi.servers`

Also look at the repo's `key_files.openapi` — if it has a rich path list, add a `## API surface` section to the body that lists the major endpoint groups. This is uniquely useful for service-to-service connection mapping.

---

## Intelligent post-scan briefing

After a scan completes, don't just report stats. Give the user a 5–8 sentence briefing that answers:

1. **What domains did we find, and which matter most?** Rank by activity, flag any critical ones.
2. **What are the most active repos?** Name the top 3 Tier-1 repos and say what each does in one phrase.
3. **Are there interesting cross-repo connections?** Any domains that many others depend on? Any isolated clusters?
4. **Any surprises?** Lots of Tier-2/3 repos suggests lots of technical debt or old experiments. Very few domains suggests the org hasn't formalized team ownership yet.
5. **What should the user look at first?** Suggest the one domain file most worth reading for a newcomer.

**Good briefing example:**
> "Found 3 domains: `payments` (critical — 5 Tier-1 repos, everything depends on it), `checkout` (active — 2 Tier-1 repos, consumes payments), and `experiments` (12 archived repos, mostly Tier-3 stubs). The `payments-api` is clearly the load-bearing service — it shows up as an internal dep in 7 other repos. You have a lot of Tier-2 repos in the experiments domain; worth reviewing `domains.yml` to either formally claim them or denylist the ones nobody should touch."

---

## Domain clustering (when `_cluster_input.json` exists)

The script writes `_cluster_input.json` when repos couldn't be assigned by the heuristic cascade. Read it and:

1. **Try to assign to existing domains first.** Look at each repo's name, description, topics, and language against the existing domain list. A repo named `billing-pdf-service` with description "generates invoice PDFs" probably belongs to `payments`.

2. **Propose new domains only for groups of ≥2 clearly related repos.** Prefer combining into an existing domain over creating a new one — teams usually already know their domains, the automated signals just missed them.

3. **Don't over-fragment.** 15 domains in a 50-repo org is too many. Aim for 5–10 meaningful clusters.

4. **Write your clustering results to `_cluster_output.json`:**

```json
{
  "assignments": {
    "billing-pdf-service": "payments",
    "infra-terraform": "infra",
    "new-repo-a": "new-domain-name",
    "new-repo-b": "new-domain-name"
  },
  "new_domains": [
    {
      "name": "new-domain-name",
      "description": "What this domain owns and why it exists",
      "repos": ["new-repo-a", "new-repo-b"]
    }
  ],
  "ungrouped": ["singleton-repo-nobody-owns"]
}
```

New domains go into `domains.yml` with a `# auto-generated, review` comment.
