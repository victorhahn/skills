"""
Domain assignment cascade:
  1. domains.yml explicit mappings  (user truth)
  2. CODEOWNERS / GitHub team membership
  3. GitHub repo topics matched against topic_map
  4. Name-prefix heuristics (prefix on ≥3 repos)
  5. LLM clustering for unassigned leftovers
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

import yaml


def _gh(args: list[str]) -> dict | list | None:
    """Run gh api ... and return parsed JSON, or None on error."""
    try:
        out = subprocess.check_output(["gh"] + args, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def load_domains_yml(path: Path) -> dict:
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def save_domains_yml(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True))


def _skeleton_domains_yml() -> dict:
    return {
        "domains": {},
        "overrides": {"ungrouped_action": "prompt"},
    }


# ── Step 1: explicit mappings from domains.yml ───────────────────────────────

def assign_from_domains_yml(
    repos: list[dict], domains_cfg: dict
) -> dict[str, str]:
    """Return {repo_name: domain} for repos explicitly listed."""
    assignments: dict[str, str] = {}
    for domain, cfg in (domains_cfg.get("domains") or {}).items():
        for repo in cfg.get("allowlist", []):
            assignments[repo] = domain
        # also handle any explicit `repos:` list if present
        for repo in cfg.get("repos", []):
            assignments[repo] = domain
    return assignments


# ── Step 2: CODEOWNERS / team membership ─────────────────────────────────────

def _fetch_team_repos(org: str) -> dict[str, str]:
    """Return {repo_name: team_slug} via GitHub teams API."""
    teams = _gh(["api", f"orgs/{org}/teams", "--paginate"]) or []
    repo_to_team: dict[str, str] = {}
    if not isinstance(teams, list):
        return {}
    for team in teams:
        slug = team.get("slug", "")
        team_repos = _gh(["api", f"orgs/{org}/teams/{slug}/repos", "--paginate"]) or []
        if isinstance(team_repos, list):
            for r in team_repos:
                name = r.get("name", "")
                if name and name not in repo_to_team:
                    repo_to_team[name] = slug
    return repo_to_team


def _team_to_domain(team_slug: str, domains_cfg: dict) -> str | None:
    for domain, cfg in (domains_cfg.get("domains") or {}).items():
        if team_slug in (cfg.get("teams") or []):
            return domain
    # Heuristic: strip common suffixes and see if the result is a known domain
    stem = re.sub(r"[-_](eng|platform|team|svc|services?)$", "", team_slug)
    if stem in (domains_cfg.get("domains") or {}):
        return stem
    return None


def assign_from_teams(
    repos: list[dict], org: str, domains_cfg: dict, assigned: dict[str, str]
) -> dict[str, str]:
    unassigned = [r for r in repos if r["name"] not in assigned]
    if not unassigned:
        return {}
    team_map = _fetch_team_repos(org)
    new: dict[str, str] = {}
    for r in unassigned:
        team = team_map.get(r["name"])
        if team:
            domain = _team_to_domain(team, domains_cfg)
            if domain:
                new[r["name"]] = domain
    return new


# ── Step 3: GitHub repo topics ───────────────────────────────────────────────

def assign_from_topics(
    repos: list[dict], domains_cfg: dict, assigned: dict[str, str]
) -> dict[str, str]:
    topic_map: dict[str, str] = {}
    for domain, cfg in (domains_cfg.get("domains") or {}).items():
        for topic in cfg.get("topic_map", []):
            topic_map[topic.lower()] = domain

    new: dict[str, str] = {}
    for r in repos:
        if r["name"] in assigned:
            continue
        for topic in (r.get("topics") or []):
            domain = topic_map.get(topic.lower())
            if domain:
                new[r["name"]] = domain
                break
    return new


# ── Step 4: name-prefix heuristics ───────────────────────────────────────────

def _common_prefix(name: str) -> str | None:
    parts = re.split(r"[-_]", name)
    return parts[0] if len(parts) > 1 else None


def assign_from_prefix(
    repos: list[dict], domains_cfg: dict, assigned: dict[str, str]
) -> dict[str, str]:
    unassigned = [r for r in repos if r["name"] not in assigned]
    prefix_counts: Counter[str] = Counter()
    for r in unassigned:
        p = _common_prefix(r["name"])
        if p:
            prefix_counts[p] += 1

    # Only use prefixes that cover ≥3 repos and map to a known domain
    known_domains = set((domains_cfg.get("domains") or {}).keys())
    valid_prefixes = {p for p, cnt in prefix_counts.items() if cnt >= 3 and p in known_domains}

    new: dict[str, str] = {}
    for r in unassigned:
        p = _common_prefix(r["name"])
        if p and p in valid_prefixes:
            new[r["name"]] = p
    return new


# ── Step 5: LLM clustering (via Claude) ──────────────────────────────────────

def get_unassigned(
    repos: list[dict], assigned: dict[str, str]
) -> list[dict]:
    """Return repos that the heuristic cascade could not assign to a domain."""
    return [r for r in repos if r["name"] not in assigned]


# ── Orchestrator ──────────────────────────────────────────────────────────────

def assign_domains(
    repos: list[dict],
    org: str,
    domains_cfg: dict,
) -> tuple[dict[str, str], list[dict]]:
    """
    Run the heuristic cascade (steps 1–4). Returns (assignments, unassigned_repos).
    unassigned_repos contains repos the cascade couldn't place — caller writes
    _cluster_input.json for Claude to handle as step 5.
    """
    assigned: dict[str, str] = {}

    assigned.update(assign_from_domains_yml(repos, domains_cfg))
    assigned.update(assign_from_teams(repos, org, domains_cfg, assigned))
    assigned.update(assign_from_topics(repos, domains_cfg, assigned))
    assigned.update(assign_from_prefix(repos, domains_cfg, assigned))

    # Apply denylist overrides
    for domain, cfg in (domains_cfg.get("domains") or {}).items():
        for repo in cfg.get("denylist", []):
            assigned.pop(repo, None)

    unassigned = get_unassigned(repos, assigned)
    return assigned, unassigned
