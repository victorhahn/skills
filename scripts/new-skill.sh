#!/usr/bin/env bash
# Usage:
#   ./scripts/new-skill.sh <skill-name>                  # flat skill at skills/<skill-name>
#   ./scripts/new-skill.sh --plugin <plugin> <skill>     # nested skill under plugins/<plugin>/skills/<skill>
# Patches the root .claude-plugin/plugin.json (and the per-plugin plugin.json when --plugin is used).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

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
  PLUGIN_JSON="$REPO_ROOT/plugins/$PLUGIN/.claude-plugin/plugin.json"
else
  SKILL_DIR="$REPO_ROOT/skills/$SKILL"
  SKILL_PATH="./skills/$SKILL"
  PLUGIN_JSON=""
fi

ROOT_PLUGIN_JSON="$REPO_ROOT/.claude-plugin/plugin.json"

mkdir -p "$SKILL_DIR"
cat > "$SKILL_DIR/SKILL.md" <<EOF
---
name: $SKILL
description: TODO — describe when this skill should trigger
allowed-tools: Bash, Read, Write, Edit
---

# $SKILL

TODO — describe what this skill does and how to use it.
EOF

echo "Created $SKILL_DIR/SKILL.md"

# Patch root plugin.json
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

# Patch per-plugin plugin.json (only when --plugin is used)
if [[ -n "$PLUGIN_JSON" && -f "$PLUGIN_JSON" ]]; then
  if ! python3 -c "import json,sys; d=json.load(open('$PLUGIN_JSON')); sys.exit(0 if any(s.get('name')=='$SKILL' for s in d.get('skills',[])) else 1)" 2>/dev/null; then
    python3 - <<PYEOF
import json
path = "$PLUGIN_JSON"
with open(path) as f:
    d = json.load(f)
d.setdefault("skills", []).append({"name": "$SKILL", "path": "./skills/$SKILL"})
with open(path, "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
PYEOF
    echo "Patched $PLUGIN_JSON"
  fi
fi

echo "Done. Edit $SKILL_DIR/SKILL.md to fill in the description and body."
