---
schema_version: {{ schema_version }}
name: {{ name }}
type: bundle-summary
scope: bundle
scope_name: {{ scope_name }}
org: "{{ orgs | join(', ') }}"
description: "{{ description }}"
tags: {{ tags | tojson }}
updated: {{ updated }}
orgs: {{ orgs | tojson }}
bundle_purpose: "{{ bundle_purpose }}"
domains: {{ domains | tojson }}
repo_count: {{ repo_count }}
tier1_count: {{ tier1_count }}
critical_domains: {{ critical_domains | tojson }}
---

# Bundle: {{ scope_name }}

> {{ bundle_purpose }}

| Metric | Value |
|--------|-------|
| Repos in bundle | {{ repo_count }} |
| Tier-1 (full context) | {{ tier1_count }} |
| GitHub orgs | {{ orgs | join(", ") }} |
| Domains | {{ domains | length }} |
| Last scanned | {{ updated }} |

## Domains

{% for domain in domains | sort %}
- **{{ domain }}**
{% endfor %}

## Orgs represented

{% for o in orgs | sort %}
- `{{ o }}`
{% endfor %}

## Notes

- Edit `bundle.yml` to add or remove repos from this bundle.
- Run `/repos-update {{ scope_name }}` to refresh with the latest activity.
- Repo files are named `<owner>___<repo>.md` inside `repos/` to avoid cross-org collisions.
