# CLAUDE.md

This repo is a personal skills marketplace. It must stay compatible with two formats simultaneously: **skills.sh** (public CLI registry) and **Claude Code plugins** (`.claude-plugin/` schema).

## Two registries — keep both in sync

| File | Purpose |
|---|---|
| `.claude-plugin/plugin.json` | skills.sh installability — `npx skills add` reads this |
| `.claude-plugin/marketplace.json` | Claude Code marketplace metadata |

When you add, rename, or remove a skill, update **both** files.

## Adding a skill

1. Create `plugins/<plugin>/skills/<skill-name>/SKILL.md` with frontmatter:
   ```
   ---
   name: <skill-name>
   description: <trigger description>
   allowed-tools: Bash, Read, Write, Edit
   ---
   ```
2. Add the path to root `.claude-plugin/plugin.json` → `skills[]`
3. Add the entry to `plugins/<plugin>/.claude-plugin/plugin.json` → `skills[]`
4. Add the entry to root `.claude-plugin/marketplace.json` if it's a new plugin

## Adding a slash command

Slash command files live in `plugins/<plugin>/commands/<name>.md` and must be registered in the per-plugin `plugin.json` → `commands[]`.

## Runtime data

`plugins/<plugin>/context/` is gitignored — it's written at runtime by the skill, never committed.

## Validation checklist before committing

- Root `plugin.json` lists every skill folder
- Root `marketplace.json` lists every plugin
- Every `SKILL.md` has `name` and `description` frontmatter
- No `context/` files staged
