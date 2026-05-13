# Consumer pattern for downstream skills

This is the reference for skills that want to query org-context data.

## Data root

```
${CLAUDE_PLUGIN_ROOT}/context/
  orgs/<org>/
    ORG.md                    # top-level org summary
    domains/<domain>.md       # one per inferred domain
    repos/<repo>.md           # Tier-1 repos with full runbooks
    archive/<repo>.md         # Tier-3 stubs
    domains.yml               # editable domain config
  bundles/<bundle>/
    BUNDLE.md
    domains/<domain>.md
    repos/<owner>__<repo>.md  # cross-org; owner+repo in filename
```

## Finding context from a skill

The fastest pattern is to scan frontmatter first, then load bodies only when relevant:

```python
import pathlib, yaml

def find_context(plugin_root: str, org: str, **filters) -> list[dict]:
    """
    Returns list of {path, frontmatter} dicts matching all filters.
    Filters: type=, domain=, tier=, critical=, tags_include=[]
    """
    root = pathlib.Path(plugin_root) / "context" / "orgs" / org
    results = []
    for md in root.rglob("*.md"):
        text = md.read_text(errors="replace")
        if not text.startswith("---"):
            continue
        try:
            end = text.index("---", 3)
            fm = yaml.safe_load(text[3:end]) or {}
        except (ValueError, yaml.YAMLError):
            continue
        if _matches(fm, filters):
            results.append({"path": md, "frontmatter": fm})
    return results

def _matches(fm: dict, filters: dict) -> bool:
    if "type" in filters and fm.get("type") != filters["type"]:
        return False
    if "domain" in filters and fm.get("domain") != filters["domain"]:
        return False
    if "tier" in filters and fm.get("tier") != filters["tier"]:
        return False
    if "critical" in filters and fm.get("critical") != filters["critical"]:
        return False
    if "tags_include" in filters:
        tags = fm.get("tags") or []
        if not any(t in tags for t in filters["tags_include"]):
            return False
    return True
```

## Common query patterns

**"What's the test command for repo X?"**
```python
results = find_context(plugin_root, org, type="repo")
for r in results:
    if r["frontmatter"].get("repo") == "payments-api":
        print(r["frontmatter"].get("test_cmd"))
```

**"What domains exist and which are critical?"**
```python
results = find_context(plugin_root, org, type="domain")
critical = [r["frontmatter"]["domain"] for r in results if r["frontmatter"].get("critical")]
```

**"Who owns repo X / who approves PRs?"**
```python
results = find_context(plugin_root, org, type="repo")
for r in results:
    if r["frontmatter"].get("repo") == "payments-api":
        print(r["frontmatter"].get("approvers"))
        print(r["frontmatter"].get("required_reviewers"))
```

**"Load full runbook for a repo"**
```python
# Load body only after frontmatter confirms it's the right file
path = results[0]["path"]
body = path.read_text()
# Body has ## Runbook section with install/dev/test/release details
```

## Bash one-liners (for use in shell-based skills)

```bash
# Find all Tier-1 repos in the payments domain
grep -l 'domain: payments' $PLUGIN_ROOT/context/orgs/<org>/repos/*.md

# Get test command for a specific repo
python3 -c "
import yaml, pathlib
text = pathlib.Path('$PLUGIN_ROOT/context/orgs/<org>/repos/payments-api.md').read_text()
fm = yaml.safe_load(text.split('---')[1])
print(fm.get('test_cmd', 'unknown'))
"

# List all critical domains
grep -l 'critical: true' $PLUGIN_ROOT/context/orgs/<org>/domains/*.md
```

## Checking if org context exists before using it

```python
def org_context_available(plugin_root: str, org: str) -> bool:
    return (pathlib.Path(plugin_root) / "context" / "orgs" / org / "ORG.md").exists()
```

If context isn't available, tell the user to run `/org-scan <org>` first.

## Frontmatter field quick reference

| Field | Where | What it tells you |
|-------|-------|-------------------|
| `type` | all | file type — filter first on this |
| `description` | all | one-sentence summary for quick relevance check |
| `domain` | repo, repo-stub | which team/capability this belongs to |
| `tier` | repo, repo-stub | 1=full context, 2=metadata only (no file), 3=stub |
| `critical` | domain, repo | high-stakes; warrants extra care |
| `test_cmd` | repo | the exact command to run tests |
| `install_cmd` | repo | how to install/bootstrap |
| `dev_cmd` | repo | how to run locally |
| `approvers` | repo | CODEOWNERS — who reviews PRs |
| `required_reviewers` | repo | minimum approval count from branch protection |
| `internal_deps` | repo | other repos in the same org this depends on |
| `release_method` | repo | tag-push / semantic-release / release-please / unknown |
| `capabilities` | domain | what business functions this domain owns |
| `upstream_deps` | domain | domains this one consumes |
| `downstream_consumers` | domain | domains that depend on this one |
