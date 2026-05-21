# Composable CLI Patterns

Reference for designing command surfaces that Claude Code can reliably chain across sessions.

---

## Canonical Surface Shape

Every CLI should follow this shape:

```
<tool> --help                          # full capability list
<tool> --json doctor                   # health check (auth, config, reachability)
<tool> init [--api-key KEY]            # store config (when env-only is painful)

# Discovery — find containers
<tool> list-projects                   # accounts, workspaces, teams, queues, orgs
<tool> list-pipelines --project ID

# Resolve — name → stable ID (avoid re-searching in scripts)
<tool> resolve-pipeline "my-pipeline" --project ID

# Read — exact fetch + collection search
<tool> get-pipeline PIPELINE_ID        # exact object
<tool> list-builds --pipeline ID --limit 20
<tool> search-builds --status failed --limit 10

# Write — one action per command, narrow IDs
<tool> trigger-build PIPELINE_ID [--dry-run]
<tool> cancel-build BUILD_ID
<tool> upload-artifact BUILD_ID --file ./out.zip

# Raw escape hatch
<tool> request GET /v2/pipelines       # read-only first
<tool> request POST /v2/builds --body '{"pipeline_id":"..."}'
```

---

## JSON Output Contract

Under `--json`, output must be:

**Success:**
```json
{ "data": { ... } }            // single object
{ "data": [...], "meta": { "total": 42, "cursor": "xyz" } }  // paginated list
```

**Error:**
```json
{ "error": { "code": "not_found", "message": "Build BUILD_ID not found", "status": 404 } }
```

Rules:
- Exit code 0 for success, non-zero for errors — always.
- Never mix human-readable prose into `--json` output.
- Never include credentials, tokens, or session cookies in any output path.
- `cursor`/`next_page` fields enable Claude Code to paginate without parsing prose.
- Command shape is stable: the same command with the same flags produces the same JSON structure across versions.

Without `--json`, human-readable output is fine — tables, colored status, prose summaries.

---

## `doctor` Contract

`<tool> --json doctor` is the first command Claude Code should run in a new session.
It must always exit 0 and return a machine-readable health report:

```json
{
  "version": "1.2.0",
  "auth": {
    "present": true,
    "source": "env",           // "env" | "config" | "flag" | "missing"
    "token_prefix": "bkua_"   // first few chars only; never the full token
  },
  "config": {
    "path": "/Users/me/.buildkite/config.toml",
    "org": "acme"
  },
  "reachability": {
    "api_base": "https://api.buildkite.com",
    "ok": true,
    "latency_ms": 142
  },
  "offline_mode": false,
  "missing_setup": []          // list of strings describing what's wrong
}
```

If `missing_setup` is non-empty, the CLI is not ready. Claude Code reads this before
proceeding to any other command.

---

## Resolve Pattern

Discovery returns names; downstream commands need stable IDs. Without a resolve command,
Claude Code must re-run discovery every session. With one:

```bash
# Session 1: discover + resolve
<tool> list-pipelines --project acme
<tool> resolve-pipeline "Deploy API" --project acme
# → PIPELINE_ID = pipe_abc123

# Session 2+: skip discovery entirely
<tool> get-pipeline pipe_abc123
```

Resolve commands should:
- Accept names, URLs, slugs, and permalinks
- Return the canonical stable ID in `--json` mode: `{ "id": "pipe_abc123" }`
- Be idempotent (passing an ID through resolve returns the same ID)

---

## Pagination

For `list`/`search` commands:

- Always support `--limit N` with a documented default (suggest 20–50).
- Prefer cursor-based pagination; fall back to page/offset if the API requires it.
- Include `"meta": { "cursor": "...", "has_more": true }` in `--json` output so Claude
  Code can loop without parsing prose.
- Never silently truncate — if results were limited, say so.

---

## Write Command Safety

- Every write command should support `--dry-run` (or `--draft`/`--preview`) when the
  service allows it. This lets Claude Code verify intent before committing.
- Accept the narrowest stable resource ID as the primary argument. Avoid accepting names
  (which are ambiguous) for destructive operations.
- Do not name write commands after broad outcomes (`fix`, `debug`, `auto`, `sync`). Name
  them after the exact action: `create-webhook`, `update-env-var`, `delete-pipeline`.
- For destructive actions (delete, purge, force-cancel), require an explicit flag
  (`--confirm` or `--force`) even outside `--dry-run` mode.

---

## Anti-Patterns

| Anti-pattern | Better alternative |
|---|---|
| Only a generic `request` command | High-level verbs + raw escape hatch |
| Human-readable prose in `--json` output | Strict JSON structure |
| Accepting API key as positional arg | `--api-key` flag or env var |
| Silently truncating list results | `--limit` with `has_more` in output |
| Write commands that accept names | Resolve to ID first, write by ID |
| `doctor` that exits 1 when auth missing | Always exit 0; report in `missing_setup` |
| Tokens or secrets in error output | Redact to prefix only |
| Binary only works inside source dir | Smoke-test from `/tmp` after install |
