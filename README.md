# skills

[![skills.sh](https://skills.sh/b/victorhahn/skills)](https://skills.sh/victorhahn/skills)

A personal collection of Claude Code skills and plugins, dual-published as a **Claude Code marketplace**, a **Cursor team marketplace**, and a **`skills` CLI** registry. Install the whole bundle or pick individual skills.

## Install (Claude Code — recommended)

Add the marketplace once:

```shell
/plugin marketplace add victorhahn/skills
```

Then install any skill by name:

```shell
/plugin install aws-solutions-architect@victorhahn-skills
/plugin install brainstorming@victorhahn-skills
/plugin install cli-creator@victorhahn-skills
/plugin install codebase-improvement-audit@victorhahn-skills
/plugin install contract-first-backend@victorhahn-skills
/plugin install kubernetes-specialist@victorhahn-skills
/plugin install repo-synthesize@victorhahn-skills
/plugin install skill-use-audit@victorhahn-skills
/plugin install subagent-architect@victorhahn-skills
/plugin install test-coverage-quality-audit@victorhahn-skills
/plugin install tui-creator@victorhahn-skills
/plugin install typescript-expert@victorhahn-skills
/plugin install unfuck@victorhahn-skills
/plugin install visualize@victorhahn-skills
/plugin install gh-org-context@victorhahn-skills
```

To add the marketplace automatically for everyone working in a repo, drop this into `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "victorhahn-skills": {
      "source": {
        "source": "github",
        "repo": "victorhahn/skills"
      }
    }
  }
}
```

## Install (Cursor)

This repo is also a [Cursor team marketplace](https://cursor.com/docs/plugins#team-marketplaces). On a Team or Enterprise plan, import it via **Dashboard → Settings → Plugins → Team Marketplaces → Import**, pasting this repo's GitHub URL. Individual skills then appear as installable plugins in the Cursor marketplace panel.

> Plugin installation is only supported in the Cursor IDE — the Cursor CLI does not support plugins.

## Install (any agent — via `skills` CLI)

Skills here are installable into any agent supported by the [`skills` CLI](https://github.com/vercel-labs/skills) (Claude Code, Codex, OpenCode, Cline, and ~50 others).

```shell
# Install everything
pnpm dlx skills add victorhahn/skills

# List skills without installing
pnpm dlx skills add victorhahn/skills --list

# Install specific skills
pnpm dlx skills add victorhahn/skills --skill typescript-expert --skill visualize
```

(Works with `npx` too — substitute `npx` for `pnpm dlx`.)

## Install (local dev / from a clone)

If you've cloned this repo and want to install skills directly into `~/.agents/skills`:

```shell
./install.sh
```

The installer backs up any existing skills directory, copies each skill into the flat `~/.agents/skills/<skill-name>/` layout, and works for both Claude Code and Cursor.

## Skills

| Skill | What it does |
|---|---|
| [`aws-solutions-architect`](skills/aws-solutions-architect/SKILL.md) | AWS service selection, architecture patterns, cost optimization, and Terraform AWS provider implementation. |
| [`brainstorming`](skills/brainstorming/SKILL.md) | Turn vague ideas into approved designs through one-question-at-a-time dialogue before any code is written. |
| [`cli-creator`](skills/cli-creator/SKILL.md) | Build durable, installable Node/TypeScript CLIs from API docs, OpenAPI specs, curl examples, or existing scripts. |
| [`codebase-improvement-audit`](skills/codebase-improvement-audit/SKILL.md) | Audit a codebase for real improvement opportunities — security, compliance, modernization, dead code, test gaps, dep drift — and produce a prioritized, regression-safe iteration plan. |
| [`contract-first-backend`](skills/contract-first-backend/SKILL.md) | Bootstrap and work with contract-first TypeScript/Express backends where `openapi.yaml` is the source of truth and all types, validation, and clients are generated. |
| [`kubernetes-specialist`](skills/kubernetes-specialist/SKILL.md) | Deploy and manage Kubernetes workloads — manifests, RBAC, NetworkPolicies, Helm, debugging, right-sizing, GitOps. |
| [`repo-synthesize`](skills/repo-synthesize/SKILL.md) | Deep-read one or more repos and produce structured Markdown docs covering both structure and capabilities. Runs a Recon → Delta Plan → Write workflow with an approval gate. |
| [`skill-use-audit`](skills/skill-use-audit/SKILL.md) | Audit how well an installed skill performed in the current Claude Code session — reads the live transcript, finds every invocation, evaluates effectiveness, and proposes diff-style improvements to `SKILL.md`. |
| [`subagent-architect`](skills/subagent-architect/SKILL.md) | Design Claude Code subagents and multi-agent workflows — when a subagent is the right tool, what shape it should take, and how it fits the rest of the workflow. |
| [`test-coverage-quality-audit`](skills/test-coverage-quality-audit/SKILL.md) | Audit a codebase for test coverage *quality* — tautological assertions, snapshot abuse, over-mocking, and framework anti-patterns in JS/TS and Go. |
| [`tui-creator`](skills/tui-creator/SKILL.md) | Design and implement interactive terminal UIs — layout, color, focus, keybindings, accessibility, and real-world precedent. Framework-agnostic plus Ink 7 / React 19 recipes. |
| [`typescript-expert`](skills/typescript-expert/SKILL.md) | TypeScript and JavaScript expert — type-level programming, performance, monorepos, migrations, modern tooling. |
| [`unfuck`](skills/unfuck/SKILL.md) | Make a codebase measurably better through small, surgical, regression-proof changes — coverage adds, dead-code removal, control-flow tightening, safe renames. Cardinal rule: no confidence, no change. |
| [`visualize`](skills/visualize/SKILL.md) | Produce rendered Mermaid diagrams and self-contained HTML visuals when the answer should be a diagram, not prose. |

## Plugins

Plugins bundle slash commands (and optionally skills) into a single installable unit. They live at `plugins/<name>/`.

| Plugin | What it does |
|---|---|
| [`gh-org-context`](plugins/gh-org-context/) | Distills a GitHub org (or curated repo list) into dense, structured context for downstream skills — tech stack, domains, runbooks, cross-repo connections, team ownership, release process. Ships the `org-context` skill and supporting slash commands. |

## Layout & contributing

Each skill carries its own `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json` so it can be installed independently. The top-level `.claude-plugin/marketplace.json` lists every installable plugin (skill or bundle) — keep it in sync when adding, renaming, or removing skills.

See [AGENTS.md](AGENTS.md) for layout rules and the `scripts/new-skill.sh` scaffold.
