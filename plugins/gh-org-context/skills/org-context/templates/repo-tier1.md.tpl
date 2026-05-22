---
schema_version: {{ schema_version }}
name: {{ name }}
type: repo
scope: {{ scope }}
scope_name: {{ scope_name }}
org: {{ org }}
description: "{{ description }}"
tags: {{ tags | tojson }}
updated: {{ updated }}
repo: {{ repo }}
domain: {% if domain is string %}"{{ domain }}"{% else %}{{ domain | tojson }}{% endif %}
language: {{ language | default("null") }}
frameworks: {{ frameworks | tojson }}
activity_score: {{ activity_score }}
tier: {{ tier }}
last_release: {{ last_release | default("null") }}
default_branch: {{ default_branch }}
infra: {{ infra | tojson }}
internal_deps: {{ internal_deps | tojson }}
critical: {{ critical | lower }}
visibility: {{ visibility }}
monorepo: {{ monorepo | lower }}
install_cmd: {{ install_cmd | default("null") | tojson }}
dev_cmd: {{ dev_cmd | default("null") | tojson }}
test_cmd: {{ test_cmd | default("null") | tojson }}
runbook_source: {{ runbook_source | default("unknown") }}
release_method: {{ release_method | default("unknown") }}
release_workflow: {{ release_workflow | default("null") | tojson }}
ci_workflows: {{ ci_workflows | tojson }}
approvers: {{ approvers | tojson }}
required_reviewers: {{ required_reviewers | default("null") }}
package_managers: {{ package_managers | tojson }}
containerized: {{ containerized | lower }}
docker_compose: {{ docker_compose | lower }}
---

# {{ repo }}

> {{ description }}

**Domain:** `{{ domain }}` | **Language:** {{ language or "unknown" }} | **Visibility:** {{ visibility }} | **Activity score:** {{ activity_score }}

---

## Runbook

### Install

```
{{ install_cmd or "# Not detected — check README or Makefile" }}
```

### Run locally

```
{{ dev_cmd or "# Not detected — check README or docker-compose.yml" }}
```

### Run tests

```
{{ test_cmd or "# Not detected — check CI workflows or README" }}
```

_Source: `{{ runbook_source }}`_

### Cut a release

{% if release_method == "unknown" %}
_Release method not detected. Check `.github/workflows/` manually._
{% else %}
**Method:** {{ release_method }}
{% if release_workflow %}**Workflow:** `{{ release_workflow }}`{% endif %}
{% endif %}

### CI workflows

{% if ci_workflows %}
| Workflow | Triggers | Jobs |
|----------|----------|------|
{% for wf in ci_workflows %}
| `{{ wf.name }}` | {{ wf.triggers | join(", ") }} | {{ wf.jobs | join(", ") }} |
{% endfor %}
{% else %}
_No `.github/workflows/` found._
{% endif %}

### Approvers

{% if approvers %}
{% for a in approvers %}
- {{ a }}
{% endfor %}
{% if required_reviewers %}
**Required approvals:** {{ required_reviewers }}
{% endif %}
{% else %}
_No CODEOWNERS file found._
{% endif %}

---

## Technical profile

| Field | Value |
|-------|-------|
| Language | {{ language or "—" }} |
| Package managers | {{ package_managers | join(", ") or "—" }} |
| Containerized | {{ containerized }} |
| Docker Compose | {{ docker_compose }} |
| Default branch | `{{ default_branch }}` |
| Infra | {{ infra | join(", ") or "—" }} |

{% if internal_deps %}
## Internal dependencies

These repos within the same org are referenced as dependencies:
{% for dep in internal_deps %}
- `{{ dep }}`
{% endfor %}
{% endif %}

{% if monorepo %}
## Monorepo structure

This repo contains multiple sub-projects. See `packages/`, `apps/`, or `services/` directories for individual components.
{% endif %}
