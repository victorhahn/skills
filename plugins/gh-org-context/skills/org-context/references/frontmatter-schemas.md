# Frontmatter schemas

Every generated file begins with YAML frontmatter. Downstream skills parse frontmatter to decide relevance before loading the body.

## Common fields (all types)

```yaml
---
schema_version: 1
name: <kebab-case slug = filename without .md>
type: org-summary | bundle-summary | domain | repo | repo-stub
scope: org | bundle
scope_name: <org-login or bundle-name>
org: <github-org-login>
description: <one sentence, <160 chars, self-contained>
tags: [lowercase, hyphen-separated]
updated: <ISO 8601 date of last body-changing scan>
---
```

## `type: org-summary` — `ORG.md`

```yaml
domains: [payments, auth, infra]
repo_count: 147
tier1_count: 23
critical_domains: [payments, auth]
```

## `type: bundle-summary` — `BUNDLE.md`

```yaml
orgs: [acme-corp, acme-tools]
bundle_purpose: "Platform team's owned services"
domains: [payments, infra]
repo_count: 12
tier1_count: 8
critical_domains: [payments]
```

## `type: domain` — `domains/<domain>.md`

```yaml
domain: payments
teams: [payments-platform, billing-eng]
repos: [payments-api, payments-worker, billing-ui]
tier1_repos: [payments-api]
capabilities: [card-processing, refunds, ledger]
critical: true
upstream_deps: [auth, identity]
downstream_consumers: [checkout, dashboard]
```

## `type: repo` — `repos/<repo>.md`

```yaml
repo: payments-api
domain: payments            # list if monorepo spans multiple domains
language: go
frameworks: [grpc, postgres]
activity_score: 0.87        # 0–1, weighted normalized
tier: 1
last_release: 2026-04-22
default_branch: main
infra: [kubernetes, aws-ecs]
internal_deps: [auth-sdk, ledger-proto]
critical: true
visibility: public
monorepo: false
# runbook
install_cmd: "make install"
dev_cmd: "make dev"
test_cmd: "make test"
runbook_source: ci-workflow  # ci-workflow | makefile | package-json | justfile | readme
release_method: tag-push     # tag-push | manual-workflow | semantic-release | release-please | unknown
release_workflow: .github/workflows/release.yml
ci_workflows:
  - name: ci.yml
    triggers: [push, pull_request]
    jobs: [lint, test, build]
approvers: ["@acme-corp/payments-platform"]
required_reviewers: 2
package_managers: [go-mod]
containerized: true
docker_compose: false
```

## `type: repo-stub` — `archive/<repo>.md`

```yaml
repo: legacy-billing
domain: payments
tier: 3
archived: true
reason: "archived 2024-03-15, replaced by payments-api"
successor: payments-api
```

## Minimum viable filter surface

A downstream skill can determine relevance from just: `name + type + description + tags + domain + tier`. Body loading is optional and should be deferred until actually needed.
