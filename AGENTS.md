# AGENTS.md

This repo is a personal skills marketplace. It must stay compatible with two formats simultaneously: **skills.sh** (public CLI registry) and **Claude Code plugins** (`.claude-plugin/` schema).

## Layout

Most things in this repo are **standalone skills** living flat at `skills/<skill-name>/`. Only command-bearing bundles live under `plugins/` — currently:

- `plugins/gh-org-context/` — ships slash commands + a skill

If you're adding something new and it's just `SKILL.md` + references, make it a flat skill. Reach for a plugin only when you need slash commands or want to ship multiple skills as a single installable unit.

## The four manifest types — what each one does

There are **two registries at the repo root** and **two manifests per skill**. Every skill needs all four touchpoints, or it won't install cleanly across all three distribution channels.

### Repo-root registries (one of each, total)

| File | Consumer | Purpose | What it lists |
|---|---|---|---|
| `.claude-plugin/plugin.json` | **skills.sh** (`npx skills add`) | Tells the `skills` CLI which folders contain installable skills. | Every skill path in the repo (flat **and** plugin-nested). |
| `.claude-plugin/marketplace.json` | **Claude Code marketplace** (`/plugin marketplace add` → `/plugin install`) | Tells Claude Code which plugins this marketplace publishes. Each entry becomes installable as `<name>@victorhahn-skills`. | Every installable unit — both standalone skills (treated as single-skill plugins) and command-bearing plugin bundles. |

### Per-skill manifests (one of each, per skill)

| File | Consumer | Purpose |
|---|---|---|
| `skills/<name>/.claude-plugin/plugin.json` | **Claude Code** | Standalone-plugin manifest. Required for Claude Code to install this skill as its own plugin via `/plugin install <name>@victorhahn-skills`. |
| `skills/<name>/.cursor-plugin/plugin.json` | **Cursor team marketplace** | Same manifest, Cursor-side. Required for the skill to appear as an installable plugin in Cursor's marketplace panel. |

Per-skill manifests follow this shape (keep `name` and `description` in sync with `SKILL.md` frontmatter and with the root `marketplace.json` entry):

```json
{
  "name": "<skill-name>",
  "description": "<one-line — match SKILL.md and marketplace.json>",
  "version": "1.0.0",
  "author": { "name": "Victor Hahn", "email": "vhahnwebdev@gmail.com" },
  "category": "<workflow|refactoring|meta|...>",
  "keywords": ["..."]
}
```

### The 4-point checklist when adding a skill

Every new skill needs:

1. `skills/<name>/SKILL.md` (or `plugins/<plugin>/skills/<name>/SKILL.md` for plugin-nested) — with `name` + `description` frontmatter.
2. `skills/<name>/.claude-plugin/plugin.json` — Claude Code per-skill manifest.
3. `skills/<name>/.cursor-plugin/plugin.json` — Cursor per-skill manifest.
4. Entry added to **both** repo-root registries:
   - `./skills/<name>` (or nested path) appended to root `.claude-plugin/plugin.json` → `skills[]`
   - `{ name, path, description }` appended to root `.claude-plugin/marketplace.json` → `plugins[]`

And a 5th: add a row to the README's Skills table.

The `scripts/new-skill.sh` scaffold handles 1, 2, 3, and 4. The README row is manual.

### Plugin-bundled skills (rare — only `gh-org-context` today)

When a plugin ships **multiple** skills or **slash commands**, it gets its own `plugins/<plugin>/.claude-plugin/plugin.json` listing the bundled skills and commands. The two repo-root registries still need entries (the plugin path is `./plugins/<plugin>` in marketplace.json, and each nested skill path is added to root plugin.json's `skills[]`). Per-skill `.claude-plugin/` and `.cursor-plugin/` folders are **not** needed for plugin-nested skills — the parent plugin manifest covers them.

When you add, rename, or remove a skill or plugin, walk the 4-point checklist.

## Adding a skill

**In agentic sessions, always use the scaffold script instead of creating files by hand — it patches the registries atomically:**

```bash
# Flat skill (default)
./scripts/new-skill.sh <skill-name>

# Skill inside an existing plugin
./scripts/new-skill.sh --plugin <plugin-name> <skill-name>
```

Then fill in the `description` and body in the generated `SKILL.md`.

If you're creating a skill manually, walk the 4-point checklist above. Concretely:

**Flat skill:**
1. Create `skills/<skill-name>/SKILL.md` with frontmatter (`name`, `description`, optionally `allowed-tools`).
2. Create `skills/<skill-name>/.claude-plugin/plugin.json` (per-skill Claude Code manifest).
3. Create `skills/<skill-name>/.cursor-plugin/plugin.json` (per-skill Cursor manifest — usually identical to the Claude one).
4. Append `./skills/<skill-name>` to root `.claude-plugin/plugin.json` → `skills[]`.
5. Append `{ name, path, description }` to root `.claude-plugin/marketplace.json` → `plugins[]`.
6. Add a row to the README Skills table.

**Plugin-nested skill (rare):**
1. Create `plugins/<plugin>/skills/<skill-name>/SKILL.md` with frontmatter.
2. Append the path to root `.claude-plugin/plugin.json` → `skills[]`.
3. Add `{ name, path }` to `plugins/<plugin>/.claude-plugin/plugin.json` → `skills[]`.
4. If it's a new plugin, also add it to root `.claude-plugin/marketplace.json` → `plugins[]` and add a row to the README Plugins table.
5. Per-skill `.claude-plugin/` and `.cursor-plugin/` folders are **not** needed — the parent plugin manifest covers them.

## Adding a slash command

Slash commands belong to plugins. Files live in `plugins/<plugin>/commands/<name>.md` and must be registered in the per-plugin `plugin.json` → `commands[]`.

## Runtime data

`plugins/<plugin>/context/` is gitignored — written at runtime by the skill, never committed.

## Validation checklist before committing

- Every flat skill has all four touchpoints:
  - `SKILL.md` with `name` + `description` frontmatter
  - `.claude-plugin/plugin.json`
  - `.cursor-plugin/plugin.json`
  - Listed in **both** root `.claude-plugin/plugin.json` `skills[]` and root `.claude-plugin/marketplace.json` `plugins[]`
- Every plugin-nested skill is listed in root `plugin.json` `skills[]` and in its parent `plugins/<plugin>/.claude-plugin/plugin.json` `skills[]`
- README Skills/Plugins tables reflect the current set
- No `context/` files staged
- `name` and `description` are consistent across SKILL.md frontmatter, per-skill manifests, and the root `marketplace.json` entry
