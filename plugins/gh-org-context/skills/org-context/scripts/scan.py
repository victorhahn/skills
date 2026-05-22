"""
Full scan entrypoint.
Usage:
  scan.py --org <org> --output <dir>
  scan.py --bundle <name> --bundle-file <path> --output <dir>
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Local modules
sys.path.insert(0, str(Path(__file__).parent))
from activity_score import RepoMeta, classify_tier, activity_score
from domain_assign import assign_domains, load_domains_yml, save_domains_yml, _skeleton_domains_yml
from runbook_infer import infer_runbook, extract_key_files_from_clone, fetch_key_files_via_api
from render import render_and_write

NOW_ISO = datetime.now(timezone.utc).date().isoformat()
MAX_CLONE_WORKERS = 5


# ── GitHub API helpers ────────────────────────────────────────────────────────

def _gh(*args: str) -> bytes:
    return subprocess.check_output(["gh"] + list(args), stderr=subprocess.DEVNULL)


def _gh_json(*args: str) -> Any:
    return json.loads(_gh(*args))


def list_org_repos(org: str) -> list[dict]:
    """Fetch all repos for an org via GraphQL (one batched query)."""
    query = """
    query($org: String!, $cursor: String) {
      organization(login: $org) {
        repositories(first: 100, after: $cursor, orderBy: {field: PUSHED_AT, direction: DESC}) {
          pageInfo { hasNextPage endCursor }
          nodes {
            name
            description
            isArchived
            defaultBranchRef { name }
            primaryLanguage { name }
            pushedAt
            stargazerCount
            topics: repositoryTopics(first: 20) { nodes { topic { name } } }
            openIssues: issues(states: OPEN) { totalCount }
            openPRs: pullRequests(states: OPEN) { totalCount }
            visibility
          }
        }
      }
    }
    """
    repos: list[dict] = []
    cursor = None
    while True:
        variables = {"org": org, "cursor": cursor}
        resp = json.loads(_gh("api", "graphql",
                              "-f", f"query={query}",
                              "-F", f"org={org}",
                              *((["-F", f"cursor={cursor}"]) if cursor else [])))
        data = resp["data"]["organization"]["repositories"]
        for node in data["nodes"]:
            repos.append({
                "name": node["name"],
                "org": org,
                "description": node.get("description") or "",
                "archived": node["isArchived"],
                "default_branch": (node.get("defaultBranchRef") or {}).get("name", "main"),
                "language": (node.get("primaryLanguage") or {}).get("name"),
                "pushed_at": node.get("pushedAt"),
                "stars": node.get("stargazerCount", 0),
                "topics": [t["topic"]["name"] for t in (node.get("topics") or {}).get("nodes", [])],
                "open_issues": (node.get("openIssues") or {}).get("totalCount", 0),
                "open_prs": (node.get("openPRs") or {}).get("totalCount", 0),
                "visibility": node.get("visibility", "PRIVATE").lower(),
            })
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]
    return repos


def list_bundle_repos(bundle_repos: list[str]) -> list[dict]:
    """Fetch metadata for a specific list of 'owner/repo' slugs."""
    by_owner: dict[str, list[str]] = defaultdict(list)
    for slug in bundle_repos:
        owner, name = slug.split("/", 1)
        by_owner[owner].append(name)

    all_repos: list[dict] = []
    for owner, names in by_owner.items():
        # Fetch each in a small batch via REST (GraphQL filter-by-name is awkward)
        for name in names:
            try:
                r = _gh_json("api", f"repos/{owner}/{name}")
                all_repos.append({
                    "name": r["name"],
                    "org": owner,
                    "description": r.get("description") or "",
                    "archived": r.get("archived", False),
                    "default_branch": r.get("default_branch", "main"),
                    "language": r.get("language"),
                    "pushed_at": r.get("pushed_at"),
                    "stars": r.get("stargazers_count", 0),
                    "topics": r.get("topics", []),
                    "open_issues": r.get("open_issues_count", 0),
                    "open_prs": 0,  # expensive; skipped for bundles
                    "visibility": r.get("visibility", "private"),
                })
            except Exception as e:
                print(f"  [warn] could not fetch {owner}/{name}: {e}", flush=True)
    return all_repos


def fetch_commit_stats(org: str, repo: str, default_branch: str) -> tuple[int, int]:
    """Returns (commits_30d, unique_authors_90d). Falls back to 0 on error."""
    try:
        since_30 = (datetime.now(timezone.utc).replace(day=1)).isoformat()
        out = _gh("api", f"repos/{org}/{repo}/commits",
                  "--paginate",
                  "-F", "per_page=100",
                  "-F", f"since={since_30}")
        commits = json.loads(out) if out else []
        commits_30d = len(commits) if isinstance(commits, list) else 0
        # 90d authors
        from datetime import timedelta
        since_90 = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        out2 = _gh("api", f"repos/{org}/{repo}/commits",
                   "--paginate",
                   "-F", "per_page=100",
                   "-F", f"since={since_90}")
        c90 = json.loads(out2) if out2 else []
        authors = {c["commit"]["author"]["email"] for c in c90 if isinstance(c, dict) and "commit" in c}
        return commits_30d, len(authors)
    except Exception:
        return 0, 0


def check_recent_release(org: str, repo: str) -> bool:
    try:
        r = _gh_json("api", f"repos/{org}/{repo}/releases/latest")
        published = r.get("published_at") or ""
        if published:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - dt).days <= 180
    except Exception:
        pass
    return False


# ── Clone + runbook ───────────────────────────────────────────────────────────

def clone_and_infer(repo: dict, all_repo_names: set[str]) -> dict:
    """Shallow clone a Tier-1 repo, run runbook + dep + key-file inference."""
    org, name = repo["org"], repo["name"]
    tmpdir = tempfile.mkdtemp(prefix=f"ghctx_{name}_")
    try:
        subprocess.check_call(
            ["git", "clone", "--depth", "50", "--quiet",
             f"https://github.com/{org}/{name}.git", tmpdir],
            stderr=subprocess.DEVNULL,
        )
        root = Path(tmpdir)
        runbook = infer_runbook(root, org, name, repo.get("default_branch", "main"))
        runbook["internal_deps"] = _infer_internal_deps(root, all_repo_names - {name})
        runbook["_key_files"] = extract_key_files_from_clone(root, org, name)
        return runbook
    except Exception as e:
        return {"_clone_error": str(e)}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Internal dep detection ────────────────────────────────────────────────────

def _infer_internal_deps(root: Path, all_repo_names: set[str]) -> list[str]:
    deps: set[str] = set()
    manifest_files = [
        "go.mod", "package.json", "requirements.txt",
        "pyproject.toml", "Cargo.toml",
    ]
    for mf in manifest_files:
        text = (root / mf).read_text(errors="replace") if (root / mf).exists() else ""
        for repo_name in all_repo_names:
            if repo_name in text:
                deps.add(repo_name)
    return sorted(deps)


# ── Write helpers ─────────────────────────────────────────────────────────────

def _write_domains_yml_skeleton(output: Path, domains_cfg: dict) -> None:
    path = output / "domains.yml"
    if not path.exists():
        save_domains_yml(path, domains_cfg if domains_cfg else _skeleton_domains_yml())


def _write_scan_meta(output: Path, meta: dict) -> None:
    (output / ".scan-meta.json").write_text(json.dumps(meta, indent=2, default=str))


def _load_scan_meta(output: Path) -> dict:
    p = output / ".scan-meta.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def _log_failure(output: Path, repo: str, error: str) -> None:
    with open(output / ".failures.log", "a") as f:
        f.write(f"{NOW_ISO} {repo}: {error}\n")


# ── Domain synthesis ──────────────────────────────────────────────────────────

def synthesize_domains(
    repos_by_domain: dict[str, list[dict]],
    tier1_data: dict[str, dict],
    domains_cfg: dict,
    output: Path,
    scope: str,
    scope_name: str,
    is_bundle: bool,
) -> None:
    for domain, domain_repos in sorted(repos_by_domain.items()):
        tier1_repos = [r for r in domain_repos if r.get("_tier") == 1]
        all_capabilities: list[str] = []
        for r in tier1_repos:
            td = tier1_data.get(r["name"], {})
            all_capabilities.extend(td.get("capabilities", []))

        ctx = {
            "schema_version": 1,
            "name": f"domain-{domain}",
            "type": "domain",
            "scope": scope,
            "scope_name": scope_name,
            "org": scope_name if not is_bundle else (domain_repos[0].get("org", "") if domain_repos else ""),
            "description": (domains_cfg.get("domains", {}).get(domain, {}).get("description")
                            or f"{domain} domain repos"),
            "tags": [domain],
            "updated": NOW_ISO,
            "domain": domain,
            "teams": domains_cfg.get("domains", {}).get(domain, {}).get("teams", []),
            "repos": [r["name"] for r in domain_repos],
            "tier1_repos": [r["name"] for r in tier1_repos],
            "capabilities": sorted(set(all_capabilities)),
            "critical": domain in (domains_cfg.get("domains", {}).get(domain, {}).get("critical", False) or
                                   [d for d, cfg in (domains_cfg.get("domains") or {}).items()
                                    if cfg.get("critical")]),
            "upstream_deps": [],
            "downstream_consumers": [],
            "tier2_repos": [r["name"] for r in domain_repos if r.get("_tier") == 2],
            "domain_conventions": _domain_conventions(tier1_repos, tier1_data),
        }
        dest = output / "domains" / f"{domain}.md"
        render_and_write("domain.md.tpl", ctx, dest)
        print(f"  [domain] {domain} ({len(domain_repos)} repos)", flush=True)


def _domain_conventions(tier1_repos: list[dict], tier1_data: dict[str, dict]) -> dict:
    test_cmds = [tier1_data[r["name"]].get("test_cmd") for r in tier1_repos
                 if r["name"] in tier1_data and tier1_data[r["name"]].get("test_cmd")]
    release_methods = [tier1_data[r["name"]].get("release_method") for r in tier1_repos
                       if r["name"] in tier1_data]
    return {
        "common_test_cmd": test_cmds[0] if len(set(test_cmds)) == 1 else None,
        "release_methods": list(set(filter(None, release_methods))),
    }


# ── Main scan ─────────────────────────────────────────────────────────────────

def run_scan(
    org: str | None,
    output: Path,
    bundle_name: str | None = None,
    bundle_repos_list: list[str] | None = None,
) -> None:
    is_bundle = bundle_name is not None
    scope = "bundle" if is_bundle else "org"
    scope_name = bundle_name if is_bundle else org
    output.mkdir(parents=True, exist_ok=True)

    # Clear old failures log
    (output / ".failures.log").unlink(missing_ok=True)

    print(f"[scan] Fetching repo list for {scope_name} ...", flush=True)
    if is_bundle:
        repos = list_bundle_repos(bundle_repos_list or [])
    else:
        repos = list_org_repos(org)
    all_repo_names = {r["name"] for r in repos}
    print(f"[scan] {len(repos)} repos found", flush=True)

    # Load existing domains config
    domains_yml_path = output / "domains.yml"
    domains_cfg = load_domains_yml(domains_yml_path)
    _write_domains_yml_skeleton(output, domains_cfg)

    # Load previous scan meta for hysteresis
    prev_meta = _load_scan_meta(output)
    prev_repos = prev_meta.get("repos", {})

    # ── Phase 1: Enrich metadata and tier all repos ──
    print("[scan] Computing activity stats and tiers ...", flush=True)
    tier1: list[dict] = []
    tier2: list[dict] = []
    tier3: list[dict] = []

    for r in repos:
        name = r["name"]
        r_org = r.get("org", org or "")
        pushed_at_str = r.get("pushed_at")
        pushed_at = None
        if pushed_at_str:
            try:
                pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Fetch commit stats (cheap: just counts)
        commits_30d, unique_authors_90d = fetch_commit_stats(r_org, name, r.get("default_branch", "main"))
        has_release = check_recent_release(r_org, name)

        prev_tier = prev_repos.get(name, {}).get("tier")
        domain_cfg = (domains_cfg.get("domains") or {})
        in_allowlist = any(name in cfg.get("allowlist", []) for cfg in domain_cfg.values())
        in_denylist = any(name in cfg.get("denylist", []) for cfg in domain_cfg.values())
        pin_tier_val = next((cfg.get("pin_tier", {}).get(name) for cfg in domain_cfg.values()
                             if name in cfg.get("pin_tier", {})), None)

        meta = RepoMeta(
            name=name,
            org=r_org,
            pushed_at=pushed_at,
            archived=r.get("archived", False),
            open_prs=r.get("open_prs", 0),
            open_issues=r.get("open_issues", 0),
            commits_30d=commits_30d,
            unique_authors_90d=unique_authors_90d,
            has_release_180d=has_release,
            stars=r.get("stars", 0),
            previous_tier=prev_tier,
            in_allowlist=in_allowlist,
            in_denylist=in_denylist,
            pin_tier=pin_tier_val,
        )
        tier, reason = classify_tier(meta)
        score = activity_score(meta)
        r["_tier"] = tier
        r["_tier_reason"] = reason
        r["_activity_score"] = score
        r["_commits_30d"] = commits_30d
        r["_unique_authors_90d"] = unique_authors_90d
        r["_has_release"] = has_release

        if tier == 1:
            tier1.append(r)
        elif tier == 3:
            tier3.append(r)
        else:
            tier2.append(r)

    print(f"[scan] Tier 1: {len(tier1)}, Tier 2: {len(tier2)}, Tier 3: {len(tier3)}", flush=True)

    # ── Phase 1b: Fetch key files for Tier-2 repos via API (no clone) ──
    # Tier-1 repos get richer context from their shallow clone.
    # Tier-2 gets CLAUDE.md, AGENTS.md, README, package.json, OpenAPI, docker-compose
    # via the GitHub contents API — enough for Claude to write meaningful domain synthesis.
    if tier2:
        print(f"[scan] Fetching key context files for {len(tier2)} Tier-2 repos (no clone) ...", flush=True)

        def fetch_tier2_keys(r: dict) -> tuple[str, dict]:
            r_org = r.get("org", org or "")
            return r["name"], fetch_key_files_via_api(r_org, r["name"])

        with ThreadPoolExecutor(max_workers=MAX_CLONE_WORKERS) as pool:
            futures = {pool.submit(fetch_tier2_keys, r): r for r in tier2}
            tier2_key_files: dict[str, dict] = {}
            for fut in as_completed(futures):
                name, key_files = fut.result()
                tier2_key_files[name] = key_files
                if key_files:
                    found = list(key_files.keys())
                    print(f"  [T2] {name}: {', '.join(found)}", flush=True)
    else:
        tier2_key_files = {}

    # ── Phase 2: Domain assignment ──
    print("[scan] Assigning domains ...", flush=True)
    domain_assignments, unassigned_repos = assign_domains(
        repos,
        org or (bundle_repos_list[0].split("/")[0] if bundle_repos_list else ""),
        domains_cfg,
    )

    # Write cluster input for Claude to handle (repos the heuristic cascade couldn't assign)
    if unassigned_repos:
        cluster_input = {
            "org": org or scope_name,
            "existing_domains": {
                d: cfg.get("description", "")
                for d, cfg in (domains_cfg.get("domains") or {}).items()
            },
            "unassigned_repos": [
                {
                    "name": r["name"],
                    "description": r.get("description") or "",
                    "topics": r.get("topics") or [],
                    "language": r.get("language"),
                    "tier": r.get("_tier", 2),
                }
                for r in repos if r["name"] in {u["name"] for u in unassigned_repos}
            ],
            "instruction": (
                "Assign each unassigned repo to an existing domain if it fits, "
                "or propose new domains for groups of ≥2 related repos. "
                "Write results to _cluster_output.json — see references/synthesis-guide.md."
            ),
        }
        (output / "_cluster_input.json").write_text(json.dumps(cluster_input, indent=2))
        print(f"[scan] {len(unassigned_repos)} repos need domain clustering — wrote _cluster_input.json", flush=True)

    # Group repos by domain
    repos_by_domain: dict[str, list[dict]] = defaultdict(list)
    for r in repos:
        domain = domain_assignments.get(r["name"], "ungrouped")
        r["_domain"] = domain
        repos_by_domain[domain].append(r)

    # ── Phase 3: Clone Tier-1 repos and infer runbooks ──
    print("[scan] Processing Tier-1 repos (shallow clone + runbook) ...", flush=True)
    tier1_data: dict[str, dict] = {}

    def process_tier1(r: dict) -> tuple[str, dict]:
        print(f"  [T1] {r['name']} ({r['_tier_reason']})", flush=True)
        runbook = clone_and_infer(r, all_repo_names)
        if "_clone_error" in runbook:
            _log_failure(output, r["name"], runbook["_clone_error"])
            return r["name"], {}
        return r["name"], runbook

    with ThreadPoolExecutor(max_workers=MAX_CLONE_WORKERS) as pool:
        futures = {pool.submit(process_tier1, r): r for r in tier1}
        for fut in as_completed(futures):
            name, data = fut.result()
            tier1_data[name] = data

    # ── Phase 4: Render repo files ──
    print("[scan] Rendering repo files ...", flush=True)
    for r in tier1:
        rb = tier1_data.get(r["name"], {})
        _repo_name = r["name"] if not is_bundle else f"{r.get('org', org)}___{r['name']}"
        ctx = {
            "schema_version": 1,
            "name": f"repo-{r['name']}",
            "type": "repo",
            "scope": scope,
            "scope_name": scope_name,
            "org": r.get("org", org or ""),
            "description": r.get("description") or f"{r['name']} service",
            "tags": r.get("topics", []) + [r.get("language", "").lower()],
            "updated": NOW_ISO,
            "repo": r["name"],
            "domain": r.get("_domain", "ungrouped"),
            "language": r.get("language"),
            "frameworks": [],
            "activity_score": r["_activity_score"],
            "tier": 1,
            "default_branch": r.get("default_branch", "main"),
            "infra": [],
            "internal_deps": [],
            "critical": False,
            "visibility": r.get("visibility", "private"),
            "monorepo": False,
            **rb,
        }
        dest = output / "repos" / f"{_repo_name}.md"
        written = render_and_write("repo-tier1.md.tpl", ctx, dest)
        if written:
            print(f"  [write] repos/{_repo_name}.md", flush=True)

    for r in tier3:
        _stub_name = r["name"] if not is_bundle else f"{r.get('org', org)}___{r['name']}"
        ctx = {
            "schema_version": 1,
            "name": f"repo-{r['name']}",
            "type": "repo-stub",
            "scope": scope,
            "scope_name": scope_name,
            "org": r.get("org", org or ""),
            "description": f"Archived/stale repo: {r.get('description') or r['name']}",
            "tags": ["archived"] + (r.get("topics", [])),
            "updated": NOW_ISO,
            "repo": r["name"],
            "domain": r.get("_domain", "ungrouped"),
            "tier": 3,
            "archived": r.get("archived", False),
            "reason": r["_tier_reason"],
            "successor": None,
        }
        dest = output / "archive" / f"{_stub_name}.md"
        render_and_write("repo-stub.md.tpl", ctx, dest)

    # ── Phase 5: Write synthesis input for Claude ──
    # Domain files and ORG.md are written by Claude (synthesis pass), not by templates.
    # This JSON gives Claude everything it needs: repo metadata, README excerpts,
    # runbook data, domain groupings, and stats for the frontmatter.
    print("[scan] Writing synthesis input for Claude ...", flush=True)

    bundle_purpose = ""
    if is_bundle:
        bf = output / "bundle.yml"
        if bf.exists():
            bd = yaml.safe_load(bf.read_text()) or {}
            bundle_purpose = bd.get("purpose", "")

    synthesis_repos = []
    for r in repos:
        entry = {
            "name": r["name"],
            "org": r.get("org", org or ""),
            "description": r.get("description") or "",
            "domain": r.get("_domain", "ungrouped"),
            "tier": r["_tier"],
            "tier_reason": r["_tier_reason"],
            "activity_score": r["_activity_score"],
            "language": r.get("language"),
            "topics": r.get("topics", []),
            "visibility": r.get("visibility", "private"),
            "stars": r.get("stars", 0),
            "open_prs": r.get("open_prs", 0),
            "commits_30d": r.get("_commits_30d", 0),
            "pushed_at": r.get("pushed_at"),
            "archived": r.get("archived", False),
        }
        # Tier-1: full runbook + key files from clone
        t1 = tier1_data.get(r["name"])
        if t1:
            entry["key_files"] = t1.pop("_key_files", {})
            entry["internal_deps"] = t1.get("internal_deps", [])
            entry["runbook"] = {k: v for k, v in t1.items()
                                if not k.startswith("_") and k != "internal_deps"}
            entry["repo_file"] = f"repos/{r['name']}.md"
        # Tier-2: key files from API (no clone)
        elif r["_tier"] == 2:
            entry["key_files"] = tier2_key_files.get(r["name"], {})
        synthesis_repos.append(entry)

    synthesis_input = {
        "schema_version": 1,
        "scope": scope,
        "scope_name": scope_name,
        "org": org or "",
        "updated": NOW_ISO,
        "is_bundle": is_bundle,
        "bundle_purpose": bundle_purpose,
        "stats": {
            "repo_count": len(repos),
            "tier1_count": len(tier1),
            "tier2_count": len(tier2),
            "tier3_count": len(tier3),
        },
        "domains": {
            d: [r["name"] for r in rs]
            for d, rs in sorted(repos_by_domain.items())
        },
        "domain_config": domains_cfg.get("domains", {}),
        "repos": synthesis_repos,
        "cluster_needed": (output / "_cluster_input.json").exists(),
        "instructions": (
            "Use this file to write domain .md files and ORG.md (or BUNDLE.md). "
            "See references/synthesis-guide.md for how to infer capabilities, "
            "cross-domain deps, and write meaningful descriptions. "
            "Domain files go in domains/, summary file is ORG.md or BUNDLE.md."
        ),
    }
    (output / "_synthesis_input.json").write_text(json.dumps(synthesis_input, indent=2, default=str))
    print(f"[scan] Wrote _synthesis_input.json ({len(synthesis_repos)} repos)", flush=True)

    # ── Phase 7: Save scan meta ──
    meta_repos = {
        r["name"]: {
            "pushed_at": r.get("pushed_at"),
            "last_scanned": NOW_ISO,
            "tier": r["_tier"],
            "previous_tier": r["_tier"],
            "activity_score": r["_activity_score"],
            "domain": r.get("_domain", "ungrouped"),
        }
        for r in repos
    }
    _write_scan_meta(output, {
        "org_scanned_at": NOW_ISO,
        "domains_synthesized_at": NOW_ISO,
        "scope": scope,
        "scope_name": scope_name,
        "repos": meta_repos,
    })

    print(f"\n[scan] Done. Context written to {output}", flush=True)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--org")
    parser.add_argument("--output", required=True)
    parser.add_argument("--bundle")
    parser.add_argument("--bundle-file")
    args = parser.parse_args()

    output = Path(args.output)

    if args.bundle:
        bundle_repos_list: list[str] = []
        if args.bundle_file and Path(args.bundle_file).exists():
            bd = yaml.safe_load(Path(args.bundle_file).read_text()) or {}
            bundle_repos_list = bd.get("repos", [])
        if not bundle_repos_list:
            print("ERROR: Bundle file missing or has no repos.", file=sys.stderr)
            sys.exit(1)
        run_scan(None, output, bundle_name=args.bundle, bundle_repos_list=bundle_repos_list)
    elif args.org:
        run_scan(args.org, output)
    else:
        print("ERROR: Provide --org or --bundle + --bundle-file", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
