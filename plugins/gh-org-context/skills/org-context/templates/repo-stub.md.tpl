---
schema_version: {{ schema_version }}
name: {{ name }}
type: repo-stub
scope: {{ scope }}
scope_name: {{ scope_name }}
org: {{ org }}
description: "{{ description }}"
tags: {{ tags | tojson }}
updated: {{ updated }}
repo: {{ repo }}
domain: "{{ domain }}"
tier: {{ tier }}
archived: {{ archived | lower }}
reason: "{{ reason }}"
successor: {{ successor | default("null") | tojson }}
---

# {{ repo }} _(archived/stale)_

{{ description }}

**Reason:** {{ reason }}
{% if successor %}**Successor:** `{{ successor }}`{% endif %}

_This repo is in the archive tier. For active context, see its successor or the `{{ domain }}` domain file._
