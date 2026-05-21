# victorhahn-skills

Personal Claude Code skills and plugins.

## Installation

```bash
# npm
npx skills add victorhahn/victorhahn-skills

# pnpm
pnpm dlx skills add victorhahn/victorhahn-skills
```

## Skills

Flat skills live at `skills/<name>/`.

| Skill | What it does |
|---|---|
| [`aws-solutions-architect`](skills/aws-solutions-architect/SKILL.md) | AWS service selection, architecture patterns, cost optimization, and Terraform AWS provider implementation. |
| [`brainstorming`](skills/brainstorming/SKILL.md) | Turn vague ideas into approved designs through one-question-at-a-time dialogue before any code is written. |
| [`cli-creator`](skills/cli-creator/SKILL.md) | Build durable, installable Node/TypeScript CLIs from API docs, OpenAPI specs, curl examples, or existing scripts. |
| [`codebase-improvement-audit`](skills/codebase-improvement-audit/SKILL.md) | Audit a codebase for real improvement opportunities — security, compliance, modernization, dead code, test gaps, dep drift — and produce a prioritized, regression-safe iteration plan. |
| [`contract-first-backend`](skills/contract-first-backend/SKILL.md) | Bootstrap and work with contract-first TypeScript/Express backends where `openapi.yaml` is the source of truth and all types, validation, and clients are generated. |
| [`kubernetes-specialist`](skills/kubernetes-specialist/SKILL.md) | Deploy and manage Kubernetes workloads — manifests, RBAC, NetworkPolicies, Helm, debugging, right-sizing, GitOps. |
| [`repo-synthesize`](skills/repo-synthesize/SKILL.md) | Deep-read one or more repos and produce structured Markdown docs covering both structure and capabilities. Runs a Recon → Delta Plan → Write workflow with an approval gate. |
| [`subagent-architect`](skills/subagent-architect/SKILL.md) | Design Claude Code subagents and multi-agent workflows — when a subagent is the right tool, what shape it should take, and how it fits the rest of the workflow. |
| [`test-coverage-quality-audit`](skills/test-coverage-quality-audit/SKILL.md) | Audit a codebase for test coverage *quality* — tautological assertions, snapshot abuse, over-mocking, and framework anti-patterns in JS/TS and Go. |
| [`tui-creator`](skills/tui-creator/SKILL.md) | Design and implement interactive terminal UIs — layout, color, focus, keybindings, accessibility, and real-world precedent. Framework-agnostic plus Ink 7 / React 19 recipes. |
| [`typescript-expert`](skills/typescript-expert/SKILL.md) | TypeScript and JavaScript expert — type-level programming, performance, monorepos, migrations, modern tooling. |
| [`visualize`](skills/visualize/SKILL.md) | Produce rendered Mermaid diagrams and self-contained HTML visuals when the answer should be a diagram, not prose. |

## Plugins

Plugins bundle slash commands (and optionally skills) into a single installable unit. They live at `plugins/<name>/`.

| Plugin | What it does |
|---|---|
| [`gh-org-context`](plugins/gh-org-context/) | Distills a GitHub org (or curated repo list) into dense, structured context for downstream skills — tech stack, domains, runbooks, cross-repo connections, team ownership, release process. Ships the `org-context` skill and supporting slash commands. |

## Layout & contributing

This repo stays compatible with two formats simultaneously: **skills.sh** (public CLI registry) and **Claude Code plugins** (`.claude-plugin/` schema). See [AGENTS.md](AGENTS.md) for layout rules, the two-registry sync requirement, and the `scripts/new-skill.sh` scaffold.
