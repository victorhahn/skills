# AGENTS.md

This repo is a personal skills marketplace. It must stay compatible with two formats simultaneously: **skills.sh** (public CLI registry) and **Claude Code plugins** (`.claude-plugin/` schema).

## Layout

Most things in this repo are **standalone skills** living flat at `skills/<skill-name>/`. Only command-bearing bundles live under `plugins/` — currently:

- `plugins/gh-org-context/` — ships slash commands + a skill

If you're adding something new and it's just `SKILL.md` + references, make it a flat skill. Reach for a plugin only when you need slash commands or want to ship multiple skills as a single installable unit.

## Two registries — keep both in sync

| File | Purpose |
|---|---|
| `.claude-plugin/plugin.json` | skills.sh installability — `npx skills add` reads this. Lists every skill path (flat and plugin-nested). |
| `.claude-plugin/marketplace.json` | Claude Code marketplace metadata. Lists only the **plugins** (not flat skills). |

When you add, rename, or remove a skill or plugin, update **both** files as applicable.

## Adding a skill

**In agentic sessions, always use the scaffold script instead of creating files by hand — it patches the registries atomically:**

```bash
# Flat skill (default)
./scripts/new-skill.sh <skill-name>

# Skill inside an existing plugin
./scripts/new-skill.sh --plugin <plugin-name> <skill-name>
```

Then fill in the `description` and body in the generated `SKILL.md`.

If you're creating a skill manually:

**Flat skill:**
1. Create `skills/<skill-name>/SKILL.md` with frontmatter (`name`, `description`, `allowed-tools`).
2. Add `./skills/<skill-name>` to root `.claude-plugin/plugin.json` → `skills[]`.

**Plugin-nested skill:**
1. Create `plugins/<plugin>/skills/<skill-name>/SKILL.md` with frontmatter.
2. Add the path to root `.claude-plugin/plugin.json` → `skills[]`.
3. Add `{name, path}` to `plugins/<plugin>/.claude-plugin/plugin.json` → `skills[]`.
4. If it's a new plugin, also add it to root `.claude-plugin/marketplace.json` → `plugins[]`.

## Adding a slash command

Slash commands belong to plugins. Files live in `plugins/<plugin>/commands/<name>.md` and must be registered in the per-plugin `plugin.json` → `commands[]`.

## Runtime data

`plugins/<plugin>/context/` is gitignored — written at runtime by the skill, never committed.

## Validation checklist before committing

- Root `plugin.json` lists every flat skill folder and every plugin-nested skill path
- Root `marketplace.json` lists every plugin (not flat skills)
- Every `SKILL.md` has `name` and `description` frontmatter
- No `context/` files staged
