"""
Infer runbook information from a shallow-cloned repo:
  - install / dev / test commands
  - release method and workflow
  - CI workflows (names, triggers, jobs)
  - approvers (CODEOWNERS)
  - required reviewers (branch protection)
  - package managers, containerization

Also provides key-file extraction (CLAUDE.md, AGENTS.md, README, package.json,
OpenAPI specs, docker-compose) either from disk (Tier-1 clone) or via GitHub
Contents API (Tier-2, no clone needed).
"""
from __future__ import annotations

import base64
import json
import re
import subprocess
from pathlib import Path
from typing import Any


def _read(path: Path) -> str | None:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return None


def _gh(args: list[str]) -> Any:
    try:
        out = subprocess.check_output(["gh"] + args, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return None


# ── Package manager detection ─────────────────────────────────────────────────

def detect_package_managers(root: Path) -> list[str]:
    indicators = {
        "package-lock.json": "npm",
        "pnpm-lock.yaml": "pnpm",
        "yarn.lock": "yarn",
        "go.sum": "go-mod",
        "go.mod": "go-mod",
        "Cargo.lock": "cargo",
        "Cargo.toml": "cargo",
        "Pipfile.lock": "pipenv",
        "poetry.lock": "poetry",
        "uv.lock": "uv",
        "requirements.txt": "pip",
        "pyproject.toml": "pyproject",
        "Gemfile.lock": "bundler",
        "pubspec.lock": "pub",
        "Package.resolved": "spm",
    }
    found: list[str] = []
    seen: set[str] = set()
    for fname, pm in indicators.items():
        if (root / fname).exists() and pm not in seen:
            found.append(pm)
            seen.add(pm)
    return found


def detect_containerization(root: Path) -> tuple[bool, bool]:
    containerized = any((root / f).exists() for f in ["Dockerfile", "Dockerfile.dev", ".dockerfile"])
    compose = any((root / f).exists() for f in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"])
    return containerized, compose


# ── Makefile / justfile parsing ───────────────────────────────────────────────

def _parse_makefile_targets(root: Path) -> dict[str, str]:
    text = _read(root / "Makefile") or _read(root / "makefile") or ""
    targets: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([a-zA-Z0-9_\-]+)\s*:", line)
        if m:
            targets[m.group(1).lower()] = f"make {m.group(1)}"
    return targets


def _parse_justfile_targets(root: Path) -> dict[str, str]:
    text = _read(root / "justfile") or _read(root / "Justfile") or ""
    targets: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([a-zA-Z0-9_\-]+)\s*:", line)
        if m:
            targets[m.group(1).lower()] = f"just {m.group(1)}"
    return targets


def _parse_package_json_scripts(root: Path) -> dict[str, str]:
    text = _read(root / "package.json")
    if not text:
        return {}
    try:
        data = json.loads(text)
        scripts = data.get("scripts", {})
        return {k.lower(): f"npm run {k}" for k in scripts}
    except json.JSONDecodeError:
        return {}


# ── README extraction ─────────────────────────────────────────────────────────

def _extract_readme_commands(root: Path) -> dict[str, str]:
    readme = None
    for name in ["README.md", "README.rst", "README.txt", "README"]:
        readme = _read(root / name)
        if readme:
            break
    if not readme:
        return {}

    heading_pattern = re.compile(
        r"(?:^|\n)#{1,3}\s*(.+?)\s*\n([\s\S]*?)(?=\n#{1,3}\s|\Z)",
        re.MULTILINE,
    )
    code_pattern = re.compile(r"```(?:\w+)?\n([\s\S]*?)```")
    install_keys = re.compile(r"install|setup|getting.?started|bootstrap", re.I)
    dev_keys = re.compile(r"run.?local|development|dev.?server|start", re.I)
    test_keys = re.compile(r"test|testing|run.?test", re.I)

    result: dict[str, str] = {}
    for match in heading_pattern.finditer(readme):
        heading = match.group(1)
        body = match.group(2)
        code_match = code_pattern.search(body)
        if not code_match:
            continue
        first_line = code_match.group(1).strip().splitlines()[0].strip()
        if not first_line:
            continue
        if install_keys.search(heading) and "install" not in result:
            result["install"] = first_line
        elif dev_keys.search(heading) and "dev" not in result:
            result["dev"] = first_line
        elif test_keys.search(heading) and "test" not in result:
            result["test"] = first_line

    return result


# ── CI workflow analysis ──────────────────────────────────────────────────────

def _parse_workflow(path: Path) -> dict | None:
    try:
        import yaml
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            return None
    except Exception:
        return None

    on_triggers = data.get("on") or data.get(True)  # yaml parses 'on' as True
    if isinstance(on_triggers, dict):
        triggers = list(on_triggers.keys())
    elif isinstance(on_triggers, list):
        triggers = on_triggers
    elif isinstance(on_triggers, str):
        triggers = [on_triggers]
    else:
        triggers = []

    jobs = list((data.get("jobs") or {}).keys())
    return {
        "name": path.name,
        "triggers": triggers,
        "jobs": jobs,
    }


def infer_ci_workflows(root: Path) -> list[dict]:
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return []
    workflows = []
    for wf_file in sorted(wf_dir.glob("*.yml")):
        parsed = _parse_workflow(wf_file)
        if parsed:
            workflows.append(parsed)
    for wf_file in sorted(wf_dir.glob("*.yaml")):
        parsed = _parse_workflow(wf_file)
        if parsed:
            workflows.append(parsed)
    return workflows


def _extract_ci_test_commands(root: Path) -> list[str]:
    """Pull actual test commands run in CI workflows."""
    commands: list[str] = []
    for wf in infer_ci_workflows(root):
        wf_path = root / ".github" / "workflows" / wf["name"]
        text = _read(wf_path) or ""
        # Find 'run:' lines in test jobs
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("run:"):
                cmd = stripped[4:].strip()
                if re.search(r"\btest\b", cmd, re.I) and cmd not in commands:
                    commands.append(cmd)
    return commands


# ── Release detection ─────────────────────────────────────────────────────────

def infer_release_method(root: Path) -> dict:
    wf_dir = root / ".github" / "workflows"
    release_workflow: str | None = None
    release_method = "unknown"

    # semantic-release
    pkg = _read(root / "package.json")
    if pkg:
        try:
            deps = json.loads(pkg).get("devDependencies", {}) | json.loads(pkg).get("dependencies", {})
            if "semantic-release" in deps:
                release_method = "semantic-release"
        except json.JSONDecodeError:
            pass
    for cfg in [".releaserc", ".releaserc.json", ".releaserc.yml", "release.config.js"]:
        if (root / cfg).exists():
            release_method = "semantic-release"
            break

    # goreleaser
    if any((root / f).exists() for f in [".goreleaser.yml", ".goreleaser.yaml", "goreleaser.yml"]):
        release_method = "tag-push"  # goreleaser is invoked by tag push
        release_workflow = ".goreleaser.yml"

    # release-please
    if (root / ".release-please-manifest.json").exists() or (root / "release-please-config.json").exists():
        release_method = "release-please"

    # Scan workflow files for tag-push or release triggers
    if wf_dir.is_dir():
        for wf_file in list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml")):
            text = _read(wf_file) or ""
            if re.search(r"push:\s*\n\s+tags:", text) or re.search(r"tags:\s*\[", text):
                if release_workflow is None:
                    release_workflow = f".github/workflows/{wf_file.name}"
                if release_method == "unknown":
                    release_method = "tag-push"
            if re.search(r"on:\s*release:", text) or re.search(r"release:\s*\n\s+types:", text):
                if release_method == "unknown":
                    release_method = "manual-workflow"
                if release_workflow is None:
                    release_workflow = f".github/workflows/{wf_file.name}"

    return {
        "release_method": release_method,
        "release_workflow": release_workflow,
    }


# ── CODEOWNERS ────────────────────────────────────────────────────────────────

def infer_approvers(root: Path) -> list[str]:
    for path in [
        root / ".github" / "CODEOWNERS",
        root / "CODEOWNERS",
        root / "docs" / "CODEOWNERS",
    ]:
        text = _read(path)
        if text:
            owners: list[str] = []
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[0] == "*":
                    # root-level catch-all
                    owners.extend(parts[1:])
                elif len(parts) >= 2:
                    owners.extend(parts[1:])
            # Deduplicate preserving order
            seen: set[str] = set()
            unique: list[str] = []
            for o in owners:
                if o not in seen:
                    unique.append(o)
                    seen.add(o)
            return unique[:10]  # cap at 10 for readability
    return []


def infer_required_reviewers(org: str, repo: str, default_branch: str) -> dict:
    data = _gh(["api", f"repos/{org}/{repo}/branches/{default_branch}/protection"])
    if not data or not isinstance(data, dict):
        return {"required_reviewers": None}
    pr_reviews = data.get("required_pull_request_reviews") or {}
    return {
        "required_reviewers": pr_reviews.get("required_approving_review_count"),
        "require_code_owner_reviews": pr_reviews.get("require_code_owner_reviews", False),
        "dismiss_stale_reviews": pr_reviews.get("dismiss_stale_reviews", False),
        "required_status_checks": [
            c for c in ((data.get("required_status_checks") or {}).get("contexts") or [])
        ],
    }


# ── Key-file extraction ───────────────────────────────────────────────────────
# These files are high-signal baselines: CLAUDE.md / AGENTS.md give AI-native
# architecture context, README is the human entry point, package.json reveals
# tech stack and scripts, OpenAPI shows the API surface, docker-compose shows
# the runtime service graph.

_CLAUDE_PATHS = ["CLAUDE.md", "claude.md", ".github/CLAUDE.md", "docs/CLAUDE.md"]
_AGENTS_PATHS = ["AGENTS.md", "agents.md", ".github/AGENTS.md", "docs/AGENTS.md"]
_OPENAPI_PATHS = [
    "openapi.yaml", "openapi.json", "openapi.yml",
    "swagger.yaml", "swagger.json", "swagger.yml",
    "api/openapi.yaml", "api/openapi.json",
    "docs/openapi.yaml", "docs/api.yaml",
    "src/openapi.yaml", "api-spec.yaml", "api-spec.json",
]
_COMPOSE_PATHS = [
    "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml",
    "docker-compose.dev.yml", "docker-compose.local.yml",
]


def _fetch_file_via_api(org: str, repo: str, path: str) -> str | None:
    """Fetch a single file from GitHub contents API. Returns decoded text or None."""
    data = _gh(["api", f"repos/{org}/{repo}/contents/{path}"])
    if not data or not isinstance(data, dict):
        return None
    encoded = data.get("content", "")
    if not encoded:
        return None
    try:
        return base64.b64decode(encoded).decode("utf-8", errors="replace")
    except Exception:
        return None


def _try_paths_via_api(org: str, repo: str, candidates: list[str]) -> tuple[str | None, str | None]:
    """Try candidate paths in order; return (path_that_worked, content) or (None, None)."""
    for path in candidates:
        content = _fetch_file_via_api(org, repo, path)
        if content:
            return path, content
    return None, None


def _parse_package_json_structured(content: str) -> dict:
    """Extract the meaningful parts of package.json for synthesis context."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {"raw": content[:500]}

    # Top prod deps by name (skip internal/workspace packages)
    all_deps = {**data.get("dependencies", {}), **data.get("peerDependencies", {})}
    # Filter out scoped private packages that are likely workspace deps
    external_deps = [k for k in all_deps if not k.startswith("@") or "/" in k][:20]

    return {
        "name": data.get("name"),
        "description": data.get("description"),
        "version": data.get("version"),
        "scripts": {k: v for k, v in (data.get("scripts") or {}).items()
                    if k in {"dev", "start", "build", "test", "lint", "typecheck", "check"}},
        "main_deps": list(all_deps.keys())[:20],
        "type": "module" if data.get("type") == "module" else "commonjs",
    }


def _parse_openapi_structured(content: str, path: str) -> dict:
    """Extract summary info from an OpenAPI/Swagger spec."""
    try:
        if path.endswith(".json"):
            data = json.loads(content)
        else:
            import yaml  # optional; guarded
            data = yaml.safe_load(content) or {}
    except Exception:
        return {"raw_excerpt": content[:500]}

    info = data.get("info") or {}
    paths = list((data.get("paths") or {}).keys())
    tags = [t.get("name") for t in (data.get("tags") or []) if isinstance(t, dict)]
    servers = [(s.get("url") or s.get("description", "")) for s in (data.get("servers") or [])][:3]

    return {
        "title": info.get("title"),
        "version": info.get("version"),
        "description": (info.get("description") or "")[:300],
        "paths": paths[:50],  # cap to avoid huge lists
        "path_count": len(data.get("paths") or {}),
        "tags": tags,
        "servers": servers,
        "spec_file": path,
    }


def _parse_docker_compose_structured(content: str) -> dict:
    """Extract service names and image references from a compose file."""
    try:
        import yaml
        data = yaml.safe_load(content) or {}
    except Exception:
        return {"raw_excerpt": content[:400]}

    services = data.get("services") or {}
    service_info = {}
    for svc_name, svc in (services.items() if isinstance(services, dict) else []):
        service_info[svc_name] = {
            "image": svc.get("image") if isinstance(svc, dict) else None,
            "ports": svc.get("ports", []) if isinstance(svc, dict) else [],
        }
    return {"services": service_info}


def extract_key_files_from_clone(root: Path, org: str, repo: str) -> dict:
    """
    Read high-signal context files from a cloned repo on disk.
    Returns a dict keyed by a canonical name (claude_md, agents_md, readme, etc.)
    with content or structured data as the value.
    """
    result: dict = {}

    # CLAUDE.md / AGENTS.md — highest priority; read full content (usually short)
    for key, candidates in [("claude_md", _CLAUDE_PATHS), ("agents_md", _AGENTS_PATHS)]:
        for cand in candidates:
            text = _read(root / cand)
            if text:
                result[key] = {"path": cand, "content": text.strip()}
                break

    # README
    for rname in ["README.md", "README.rst", "README.txt", "README"]:
        text = _read(root / rname)
        if text:
            result["readme"] = {"path": rname, "content": text[:2000].strip()}
            break

    # package.json — structured
    pkg_text = _read(root / "package.json")
    if pkg_text:
        result["package_json"] = _parse_package_json_structured(pkg_text)

    # OpenAPI spec — structured
    for opath in _OPENAPI_PATHS:
        text = _read(root / opath)
        if text:
            result["openapi"] = _parse_openapi_structured(text, opath)
            break

    # docker-compose — structured
    for cpath in _COMPOSE_PATHS:
        text = _read(root / cpath)
        if text:
            result["docker_compose"] = _parse_docker_compose_structured(text)
            break

    # CONTRIBUTING.md — dev process context
    for cname in ["CONTRIBUTING.md", "CONTRIBUTING.rst", ".github/CONTRIBUTING.md"]:
        text = _read(root / cname)
        if text:
            result["contributing"] = {"path": cname, "content": text[:800].strip()}
            break

    # ARCHITECTURE.md / docs/architecture — explicit arch docs
    for aname in ["ARCHITECTURE.md", "docs/ARCHITECTURE.md", "docs/architecture.md", "DESIGN.md"]:
        text = _read(root / aname)
        if text:
            result["architecture"] = {"path": aname, "content": text[:1500].strip()}
            break

    return result


def fetch_key_files_via_api(org: str, repo: str) -> dict:
    """
    Fetch high-signal context files via GitHub Contents API (no clone needed).
    Used for Tier-2 repos. Costs ~5-8 API calls per repo.
    Returns same shape as extract_key_files_from_clone().
    """
    result: dict = {}

    # CLAUDE.md / AGENTS.md
    for key, candidates in [("claude_md", _CLAUDE_PATHS), ("agents_md", _AGENTS_PATHS)]:
        path, content = _try_paths_via_api(org, repo, candidates)
        if content:
            result[key] = {"path": path, "content": content.strip()}

    # README
    path, content = _try_paths_via_api(org, repo, ["README.md", "README.rst", "README.txt", "README"])
    if content:
        result["readme"] = {"path": path, "content": content[:2000].strip()}

    # package.json
    content = _fetch_file_via_api(org, repo, "package.json")
    if content:
        result["package_json"] = _parse_package_json_structured(content)

    # OpenAPI spec
    path, content = _try_paths_via_api(org, repo, _OPENAPI_PATHS)
    if content and path:
        result["openapi"] = _parse_openapi_structured(content, path)

    # docker-compose
    path, content = _try_paths_via_api(org, repo, _COMPOSE_PATHS)
    if content:
        result["docker_compose"] = _parse_docker_compose_structured(content)

    return result


# ── Orchestrator ──────────────────────────────────────────────────────────────

def infer_runbook(
    root: Path,
    org: str,
    repo: str,
    default_branch: str,
) -> dict:
    """Run all inference on a shallow-cloned repo root. Returns flat runbook dict."""
    make_targets = _parse_makefile_targets(root)
    just_targets = _parse_justfile_targets(root)
    npm_scripts = _parse_package_json_scripts(root)
    readme_cmds = _extract_readme_commands(root)
    ci_test_cmds = _extract_ci_test_commands(root)

    def _best(*candidates: str | None) -> str | None:
        return next((c for c in candidates if c), None)

    install_cmd = _best(
        make_targets.get("install") or just_targets.get("install") or npm_scripts.get("install"),
        readme_cmds.get("install"),
    )
    dev_cmd = _best(
        make_targets.get("dev") or just_targets.get("dev") or npm_scripts.get("dev")
        or make_targets.get("run") or just_targets.get("run") or npm_scripts.get("start"),
        readme_cmds.get("dev"),
    )
    # CI-derived test command takes priority over Makefile (it's what actually runs)
    test_cmd = _best(
        ci_test_cmds[0] if ci_test_cmds else None,
        make_targets.get("test") or just_targets.get("test") or npm_scripts.get("test"),
        readme_cmds.get("test"),
    )

    # Determine source confidence
    if ci_test_cmds:
        runbook_source = "ci-workflow"
    elif make_targets.get("test") or just_targets.get("test") or npm_scripts.get("test"):
        runbook_source = "makefile" if make_targets.get("test") else ("justfile" if just_targets.get("test") else "package-json")
    else:
        runbook_source = "readme"

    release_info = infer_release_method(root)
    ci_workflows = infer_ci_workflows(root)
    approvers = infer_approvers(root)
    reviewer_info = infer_required_reviewers(org, repo, default_branch)
    pkg_managers = detect_package_managers(root)
    containerized, docker_compose = detect_containerization(root)

    return {
        "install_cmd": install_cmd,
        "dev_cmd": dev_cmd,
        "test_cmd": test_cmd,
        "runbook_source": runbook_source,
        **release_info,
        "ci_workflows": ci_workflows,
        "approvers": approvers,
        **reviewer_info,
        "package_managers": pkg_managers,
        "containerized": containerized,
        "docker_compose": docker_compose,
    }
