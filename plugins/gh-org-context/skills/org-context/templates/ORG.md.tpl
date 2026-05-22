---
schema_version: {{ schema_version }}
name: {{ name }}
type: org-summary
scope: org
scope_name: {{ scope_name }}
org: {{ org }}
description: "{{ description }}"
tags: {{ tags | tojson }}
updated: {{ updated }}
domains: {{ domains | tojson }}
repo_count: {{ repo_count }}
tier1_count: {{ tier1_count }}
critical_domains: {{ critical_domains | tojson }}
---

# {{ scope_name }} org — at a glance

| Metric | Value |
|--------|-------|
| Total repos | {{ repo_count }} |
| Tier-1 (full context) | {{ tier1_count }} |
| Domains | {{ domains | length }} |
| Last scanned | {{ updated }} |

## Domains

{% for domain in domains | sort %}
- **{{ domain }}**
{% endfor %}

## Critical domains

{% if critical_domains %}
{% for d in critical_domains %}
- {{ d }}
{% endfor %}
{% else %}
_None marked critical — edit `domains.yml` to flag critical domains._
{% endif %}

## How to use this context

Downstream skills can:
- Load `ORG.md` frontmatter for a quick org overview.
- Scan `domains/<domain>.md` for cross-repo capability maps and conventions.
- Load `repos/<repo>.md` for full runbooks, CI details, and dependency graphs (Tier-1 repos only).
- Check `archive/<repo>.md` for historical stubs of retired repos.

Filter by frontmatter fields without loading full bodies:
```python
# Find all Tier-1 repos in a domain
for md in (context_root / "repos").glob("*.md"):
    fm = parse_frontmatter(md)
    if fm.get("domain") == "payments" and fm.get("tier") == 1:
        ...
```
