"""
Incremental update — re-processes only dirty repos.
Usage:
  update.py --org <org> --output <dir>
  update.py --bundle <name> --bundle-file <path> --output <dir>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from scan import (
    list_org_repos, list_bundle_repos, fetch_commit_stats, check_recent_release,
    clone_and_infer, synthesize_domains, _write_scan_meta, _load_scan_meta,
    _log_failure, run_scan, MAX_CLONE_WORKERS,
)
from activity_score import RepoMeta, classify_tier, activity_score
from domain_assign import assign_domains, load_domains_yml
from render import render_and_write

NOW_ISO = datetime.now(timezone.utc).date().isoformat()


def run_update(
    org: str | None,
    output: Path,
    bundle_name: str | None = None,
    bundle_repos_list: list[str] | None = None,
) -> None:
    is_bundle = bundle_name is not None
    scope = "bundle" if is_bundle else "org"
    scope_name = bundle_name if is_bundle else org

    prev_meta = _load_scan_meta(output)
    if not prev_meta:
        print("[update] No prior scan found — running full scan.", flush=True)
        run_scan(org, output, bundle_name=bundle_name, bundle_repos_list=bundle_repos_list)
        return

    print(f"[update] Fetching current repo list for {scope_name} ...", flush=True)
    if is_bundle:
        repos = list_bundle_repos(bundle_repos_list or [])
    else:
        repos = list_org_repos(org)

    prev_repos = prev_meta.get("repos", {})
    domains_cfg = load_domains_yml(output / "domains.yml")

    dirty_repos: list[dict] = []
    clean_repos: list[dict] = []

    for r in repos:
        name = r["name"]
        prev = prev_repos.get(name)

        # Recompute tier (cheap — just metadata)
        pushed_at_str = r.get("pushed_at")
        pushed_at = None
        if pushed_at_str:
            try:
                pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        commits_30d, unique_authors_90d = fetch_commit_stats(
            r.get("org", org or ""), name, r.get("default_branch", "main")
        ) if prev is None or r.get("pushed_at") != prev.get("pushed_at") else (0, 0)

        has_release = check_recent_release(r.get("org", org or ""), name)

        domain_cfg = (domains_cfg.get("domains") or {})
        meta = RepoMeta(
            name=name,
            org=r.get("org", org or ""),
            pushed_at=pushed_at,
            archived=r.get("archived", False),
            open_prs=r.get("open_prs", 0),
            open_issues=r.get("open_issues", 0),
            commits_30d=commits_30d,
            unique_authors_90d=unique_authors_90d,
            has_release_180d=has_release,
            stars=r.get("stars", 0),
            previous_tier=prev.get("tier") if prev else None,
            in_allowlist=any(name in cfg.get("allowlist", []) for cfg in domain_cfg.values()),
            in_denylist=any(name in cfg.get("denylist", []) for cfg in domain_cfg.values()),
            pin_tier=next(
                (cfg.get("pin_tier", {}).get(name) for cfg in domain_cfg.values() if name in cfg.get("pin_tier", {})),
                None,
            ),
        )
        tier, reason = classify_tier(meta)
        score = activity_score(meta)
        r["_tier"] = tier
        r["_tier_reason"] = reason
        r["_activity_score"] = score
        r["_commits_30d"] = commits_30d
        r["_unique_authors_90d"] = unique_authors_90d
        r["_has_release"] = has_release

        # Dirty conditions
        tier_changed = prev and prev.get("tier") != tier
        pushed_changed = prev and r.get("pushed_at") != prev.get("pushed_at")
        is_new = prev is None
        is_disappeared = False  # handled separately below

        if tier_changed or pushed_changed or is_new:
            dirty_repos.append(r)
        else:
            # Keep previous domain assignment
            r["_domain"] = prev.get("domain", "ungrouped") if prev else "ungrouped"
            clean_repos.append(r)

    # Repos that disappeared (in prev but not in current listing)
    current_names = {r["name"] for r in repos}
    for name, prev in prev_repos.items():
        if name not in current_names:
            # Remove their files
            for glob_pat in [f"repos/{name}.md", f"archive/{name}.md"]:
                p = output / glob_pat
                if p.exists():
                    p.unlink()
                    print(f"  [remove] {glob_pat} (repo gone)", flush=True)

    print(f"[update] {len(dirty_repos)} dirty, {len(clean_repos)} unchanged", flush=True)

    if not dirty_repos:
        print("[update] Nothing to do.", flush=True)
        return

    # Domain assignments for dirty repos
    domain_assignments, llm_prompts = assign_domains(
        dirty_repos, org or (bundle_repos_list[0].split("/")[0] if bundle_repos_list else ""), domains_cfg
    )
    for r in dirty_repos:
        r["_domain"] = domain_assignments.get(r["name"], "ungrouped")

    if llm_prompts:
        for p in llm_prompts:
            if "_llm_prompt" in p:
                print(f"\n[LLM_CLUSTER_PROMPT_START]\n{p['_llm_prompt']}\n[LLM_CLUSTER_PROMPT_END]\n", flush=True)

    # Clone + runbook for dirty Tier-1 repos
    dirty_tier1 = [r for r in dirty_repos if r["_tier"] == 1]
    dirty_tier3 = [r for r in dirty_repos if r["_tier"] == 3]
    tier1_data: dict[str, dict] = {}

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=MAX_CLONE_WORKERS) as pool:
        futures = {pool.submit(clone_and_infer, r): r for r in dirty_tier1}
        for fut in as_completed(futures):
            name_done, data = fut.result()
            tier1_data[name_done] = data

    # Render updated repo files
    for r in dirty_tier1:
        rb = tier1_data.get(r["name"], {})
        repo_name = r["name"] if not is_bundle else f"{r.get('org', org)}___{r['name']}"
        ctx = {
            "schema_version": 1, "name": f"repo-{r['name']}", "type": "repo",
            "scope": scope, "scope_name": scope_name,
            "org": r.get("org", org or ""),
            "description": r.get("description") or f"{r['name']} service",
            "tags": r.get("topics", []) + [r.get("language", "").lower()],
            "updated": NOW_ISO, "repo": r["name"], "domain": r.get("_domain", "ungrouped"),
            "language": r.get("language"), "frameworks": [], "activity_score": r["_activity_score"],
            "tier": 1, "default_branch": r.get("default_branch", "main"),
            "infra": [], "internal_deps": [], "critical": False,
            "visibility": r.get("visibility", "private"), "monorepo": False, **rb,
        }
        render_and_write("repo-tier1.md.tpl", ctx, output / "repos" / f"{repo_name}.md")

    for r in dirty_tier3:
        stub_name = r["name"] if not is_bundle else f"{r.get('org', org)}___{r['name']}"
        ctx = {
            "schema_version": 1, "name": f"repo-{r['name']}", "type": "repo-stub",
            "scope": scope, "scope_name": scope_name, "org": r.get("org", org or ""),
            "description": f"Archived/stale: {r.get('description') or r['name']}",
            "tags": ["archived"] + r.get("topics", []),
            "updated": NOW_ISO, "repo": r["name"], "domain": r.get("_domain", "ungrouped"),
            "tier": 3, "archived": r.get("archived", False),
            "reason": r["_tier_reason"], "successor": None,
        }
        render_and_write("repo-stub.md.tpl", ctx, output / "archive" / f"{stub_name}.md")

    # Re-synthesize only affected domains
    all_repos = dirty_repos + clean_repos
    from collections import defaultdict
    repos_by_domain: dict[str, list[dict]] = defaultdict(list)
    for r in all_repos:
        repos_by_domain[r.get("_domain", "ungrouped")].append(r)

    dirty_domains = {r.get("_domain", "ungrouped") for r in dirty_repos}
    domains_to_regen = dirty_domains

    for domain in sorted(domains_to_regen):
        domain_repos = repos_by_domain.get(domain, [])
        synthesize_domains(
            {domain: domain_repos}, tier1_data, domains_cfg, output, scope, scope_name, is_bundle
        )

    # Update scan meta
    updated_meta = prev_meta.copy()
    updated_meta["domains_synthesized_at"] = NOW_ISO
    for r in all_repos:
        updated_meta["repos"][r["name"]] = {
            "pushed_at": r.get("pushed_at"),
            "last_scanned": NOW_ISO,
            "tier": r["_tier"],
            "previous_tier": r["_tier"],
            "activity_score": r["_activity_score"],
            "domain": r.get("_domain", "ungrouped"),
        }
    _write_scan_meta(output, updated_meta)
    print(f"\n[update] Done. {len(dirty_repos)} repos refreshed.", flush=True)


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
        run_update(None, output, bundle_name=args.bundle, bundle_repos_list=bundle_repos_list)
    elif args.org:
        run_update(args.org, output)
    else:
        print("ERROR: Provide --org or --bundle + --bundle-file", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
