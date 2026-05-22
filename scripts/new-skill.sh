#!/usr/bin/env bash
# Usage:
#   ./scripts/new-skill.sh <skill-name>                  # flat skill at skills/<skill-name>
#   ./scripts/new-skill.sh --plugin <plugin> <skill>     # nested skill under plugins/<plugin>/skills/<skill>
#
# Flat skill: creates SKILL.md + per-skill .claude-plugin/plugin.json + per-skill .cursor-plugin/plugin.json,
# then patches the two repo-root registries (.claude-plugin/plugin.json and .claude-plugin/marketplace.json).
#
# Plugin-nested skill: creates SKILL.md, patches root plugin.json, and patches the parent plugin's
# plugin.json. Per-skill manifests are NOT created — the parent plugin manifest covers nested skills.
#
# The README Skills/Plugins table is not patched automatically — add the row manually.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AUTHOR_NAME="Victor Hahn"
AUTHOR_EMAIL="vhahnwebdev@gmail.com"

PLUGIN=""
if [[ "${1:-}" == "--plugin" ]]; then
  PLUGIN=${2:?Usage: new-skill.sh --plugin <plugin> <skill>}
  SKILL=${3:?Usage: new-skill.sh --plugin <plugin> <skill>}
else
  SKILL=${1:?Usage: new-skill.sh <skill-name>  OR  new-skill.sh --plugin <plugin> <skill>}
fi

if [[ -n "$PLUGIN" ]]; then
  SKILL_DIR="$REPO_ROOT/plugins/$PLUGIN/skills/$SKILL"
  SKILL_PATH="./plugins/$PLUGIN/skills/$SKILL"
  PARENT_PLUGIN_JSON="$REPO_ROOT/plugins/$PLUGIN/.claude-plugin/plugin.json"
else
  SKILL_DIR="$REPO_ROOT/skills/$SKILL"
  SKILL_PATH="./skills/$SKILL"
  PARENT_PLUGIN_JSON=""
fi

ROOT_PLUGIN_JSON="$REPO_ROOT/.claude-plugin/plugin.json"
ROOT_MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"
PLACEHOLDER_DESC="TODO — describe when this skill should trigger"

mkdir -p "$SKILL_DIR"
cat > "$SKILL_DIR/SKILL.md" <<EOF
---
name: $SKILL
description: $PLACEHOLDER_DESC
allowed-tools: Bash, Read, Write, Edit
---

# $SKILL

TODO — describe what this skill does and how to use it.
EOF

echo "Created $SKILL_DIR/SKILL.md"

# Per-skill manifests — only for flat skills. Plugin-nested skills are covered by the parent plugin manifest.
if [[ -z "$PLUGIN" ]]; then
  mkdir -p "$SKILL_DIR/.claude-plugin" "$SKILL_DIR/.cursor-plugin"

  PER_SKILL_MANIFEST=$(cat <<EOF
{
  "name": "$SKILL",
  "description": "$PLACEHOLDER_DESC",
  "version": "1.0.0",
  "author": {
    "name": "$AUTHOR_NAME",
    "email": "$AUTHOR_EMAIL"
  },
  "category": "TODO",
  "keywords": []
}
EOF
)
  printf '%s\n' "$PER_SKILL_MANIFEST" > "$SKILL_DIR/.claude-plugin/plugin.json"
  printf '%s\n' "$PER_SKILL_MANIFEST" > "$SKILL_DIR/.cursor-plugin/plugin.json"
  echo "Created $SKILL_DIR/.claude-plugin/plugin.json"
  echo "Created $SKILL_DIR/.cursor-plugin/plugin.json"
fi

# Patch root .claude-plugin/plugin.json (skills.sh registry)
if ! python3 -c "import json,sys; d=json.load(open('$ROOT_PLUGIN_JSON')); sys.exit(0 if '$SKILL_PATH' in d.get('skills',[]) else 1)" 2>/dev/null; then
  python3 - <<PYEOF
import json
path = "$ROOT_PLUGIN_JSON"
with open(path) as f:
    d = json.load(f)
d.setdefault("skills", []).append("$SKILL_PATH")
with open(path, "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
PYEOF
  echo "Patched $ROOT_PLUGIN_JSON"
fi

# Patch root .claude-plugin/marketplace.json (Claude Code marketplace)
if ! python3 -c "import json,sys; d=json.load(open('$ROOT_MARKETPLACE_JSON')); sys.exit(0 if any(p.get('name')=='$SKILL' for p in d.get('plugins',[])) else 1)" 2>/dev/null; then
  python3 - <<PYEOF
import json
path = "$ROOT_MARKETPLACE_JSON"
with open(path) as f:
    d = json.load(f)
d.setdefault("plugins", []).append({
    "name": "$SKILL",
    "path": "$SKILL_PATH",
    "description": "$PLACEHOLDER_DESC"
})
with open(path, "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
PYEOF
  echo "Patched $ROOT_MARKETPLACE_JSON"
fi

# Patch the parent plugin's plugin.json (only when --plugin is used)
if [[ -n "$PARENT_PLUGIN_JSON" && -f "$PARENT_PLUGIN_JSON" ]]; then
  if ! python3 -c "import json,sys; d=json.load(open('$PARENT_PLUGIN_JSON')); sys.exit(0 if any(s.get('name')=='$SKILL' for s in d.get('skills',[])) else 1)" 2>/dev/null; then
    python3 - <<PYEOF
import json
path = "$PARENT_PLUGIN_JSON"
with open(path) as f:
    d = json.load(f)
d.setdefault("skills", []).append({"name": "$SKILL", "path": "./skills/$SKILL"})
with open(path, "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
PYEOF
    echo "Patched $PARENT_PLUGIN_JSON"
  fi
fi

echo ""
echo "Done. Next steps:"
echo "  1. Fill in the description and body in $SKILL_DIR/SKILL.md"
if [[ -z "$PLUGIN" ]]; then
  echo "  2. Update description + category + keywords in $SKILL_DIR/.claude-plugin/plugin.json and .cursor-plugin/plugin.json"
  echo "  3. Update the description in $ROOT_MARKETPLACE_JSON to match"
  echo "  4. Add a row to the README Skills table"
else
  echo "  2. Add a row to the README Skills table (or Plugins table if this is a new plugin)"
fi
