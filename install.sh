#!/usr/bin/env zsh
# install.sh — Install skills into ~/.agents/skills.
#
# Layout in this repo:
#   skills/<skill-name>/SKILL.md           — flat top-level skills
#   plugins/<plugin>/skills/<skill>/...    — skills bundled inside a plugin
#
# Both forms are copied flat into ~/.agents/skills/<skill-name>/ since Claude
# Code and Cursor both expect a flat skills directory.

set -euo pipefail

REPO_DIR="${0:A:h}"
SKILLS_SRC="${REPO_DIR}/skills"
PLUGINS_SRC="${REPO_DIR}/plugins"
DEST="${HOME}/.agents/skills"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

autoload -U colors && colors
info()    { print -P "%F{cyan}  →%f $*" }
success() { print -P "%F{green}  ✓%f $*" }
warn()    { print -P "%F{yellow}  ⚠%f $*" }
error()   { print -P "%F{red}  ✗%f $*" >&2 }
header()  { print -P "\n%B%F{white}$*%f%b" }
prompt()  { print -Pn "%F{magenta}  ?%f $* " }

ask_yn() {
  local question="$1" default="${2:-n}"
  local yn_hint
  [[ "$default" == "y" ]] && yn_hint="[Y/n]" || yn_hint="[y/N]"
  prompt "$question $yn_hint:"
  read -r answer
  answer="${answer:-$default}"
  [[ "$answer" =~ ^[Yy] ]]
}

backup_dir() {
  local target="$1"
  local backup="${target}.bak.${TIMESTAMP}"
  info "Backing up $(basename $target) → $(basename $backup)"
  cp -r "$target" "$backup"
  success "Backup created at $backup"
}

copy_skill() {
  local src="$1"
  local skill_name="${src:t}"
  local skill_dest="${DEST}/${skill_name}"

  if [[ ! -f "${src}/SKILL.md" ]]; then
    warn "Skipping ${skill_name}: no SKILL.md found"
    return
  fi

  if [[ -d "$skill_dest" ]]; then
    warn "Overwriting existing skill: $skill_name"
    rm -rf "$skill_dest"
  fi

  cp -r "$src" "$skill_dest"
  success "Installed $skill_name"
}

print -P "\n%B%F{cyan}skills installer%f%b"
print    "  Repo:         $REPO_DIR"
print    "  Destination:  $DEST"

header "Step 1 — Backup"
if [[ -d "$DEST" ]]; then
  print "  Existing skills directory detected: $DEST"
  if ask_yn "Create a backup before installing?" y; then
    backup_dir "$DEST"
  fi
else
  info "No existing skills directory found — no backup needed."
fi

mkdir -p "$DEST"

header "Step 2 — Installing flat skills"
for skill_src in "${SKILLS_SRC}"/*(N/); do
  copy_skill "$skill_src"
done

header "Step 3 — Installing plugin-bundled skills"
if [[ -d "$PLUGINS_SRC" ]]; then
  for plugin_src in "${PLUGINS_SRC}"/*(N/); do
    local inner="${plugin_src}/skills"
    [[ -d "$inner" ]] || continue
    for skill_src in "${inner}"/*(N/); do
      copy_skill "$skill_src"
    done
  done
else
  info "No plugins/ directory — skipping."
fi

print -P "\n%F{green}%BDone!%b%f Skills installed to $DEST\n"
