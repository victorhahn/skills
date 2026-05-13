---
schema_version: {{ schema_version }}
name: {{ name }}
type: domain
scope: {{ scope }}
scope_name: {{ scope_name }}
org: {{ org }}
description: "{{ description }}"
tags: {{ tags | tojson }}
updated: {{ updated }}
domain: {{ domain }}
teams: {{ teams | tojson }}
repos: {{ repos | tojson }}
tier1_repos: {{ tier1_repos | tojson }}
capabilities: {{ capabilities | tojson }}
critical: {{ critical | lower }}
upstream_deps: {{ upstream_deps | tojson }}
downstream_consumers: {{ downstream_consumers | tojson }}
---

# Domain: {{ domain }}

{{ description }}

## Repos

| Repo | Tier | Notes |
|------|------|-------|
{% for r in repos %}
| {{ r }} | {% if r in tier1_repos %}1 — full context{% elif r in tier2_repos | default([]) %}2 — metadata only{% else %}2{% endif %} | |
{% endfor %}

## Capabilities

{% if capabilities %}
{% for cap in capabilities %}
- {{ cap }}
{% endfor %}
{% else %}
_No capabilities inferred — add them manually or enrich Tier-1 repo descriptions._
{% endif %}

## Teams

{% if teams %}
{% for team in teams %}
- `{{ team }}`
{% endfor %}
{% else %}
_No team ownership mapped — check CODEOWNERS or add team mappings to `domains.yml`._
{% endif %}

## Cross-domain dependencies

{% if upstream_deps %}
**Upstream (this domain consumes):** {{ upstream_deps | join(", ") }}
{% endif %}
{% if downstream_consumers %}
**Downstream (consumers of this domain):** {{ downstream_consumers | join(", ") }}
{% endif %}
{% if not upstream_deps and not downstream_consumers %}
_No cross-domain dependencies mapped yet. Update after reviewing repo internal_deps._
{% endif %}

## Domain conventions

{% if domain_conventions %}
{% if domain_conventions.common_test_cmd %}
**Test command (all Tier-1 repos):** `{{ domain_conventions.common_test_cmd }}`
{% endif %}
{% if domain_conventions.release_methods %}
**Release methods used:** {{ domain_conventions.release_methods | join(", ") }}
{% endif %}
{% else %}
_No common conventions detected._
{% endif %}
