---
name: repos-scan
description: Full scan of a curated, cross-org list of repos — builds a named bundle under context/bundles/<bundle>/
allowed-tools: Bash, Read, Write, Edit
---

# /repos-scan <bundle> [<owner/repo> ...]

Scan a curated set of repos (potentially spanning multiple GitHub orgs) and generate structured context under `${CLAUDE_PLUGIN_ROOT}/context/bundles/<bundle>/`.

## Invocation forms

- **Inline slugs:** `/repos-scan my-stack acme-corp/api acme-tools/cli other-org/worker`
- **From file:** `/repos-scan my-stack --from /path/to/repos.txt`  (newline-separated `owner/repo` slugs)
- **Edit then scan:** `/repos-scan my-stack --edit`  (opens `bundle.yml` for hand-editing before running)
- **Re-scan existing bundle:** `/repos-scan my-stack` with no slugs — reads membership from `bundle.yml`

## Steps

1. **Resolve plugin root.** Set `PLUGIN_ROOT` to the plugin directory's absolute path. Output goes to `$PLUGIN_ROOT/context/bundles/<bundle>/`.

2. **Determine the repo list.**
   - If `--from <file>` was given: read slugs from the file (one `owner/repo` per line, `#` lines ignored).
   - If `--edit` was given: open `$PLUGIN_ROOT/context/bundles/<bundle>/bundle.yml` in the default editor (or show it for the user to edit), then proceed.
   - If slugs were given inline: use those, and save them to `bundle.yml`.
   - If no slugs and no flags: check whether `$PLUGIN_ROOT/context/bundles/<bundle>/bundle.yml` exists and load it. If it doesn't exist, ask the user for the repo list.

   Always validate that each slug is `owner/repo` format. Ask the user to fix any that aren't.

3. **Prompt for a bundle purpose** if `bundle.yml` doesn't already have one (or if it's being created fresh). One sentence: why are these repos grouped? (e.g., "Platform team's owned services", "All repos touched by the payments domain"). This gets written to `bundle.yml` and appears in `BUNDLE.md`.

4. **Run preflight for each distinct owner.** For each unique GitHub org/owner in the bundle, run:
   ```
   bash $PLUGIN_ROOT/skills/org-context/scripts/gh_preflight.sh <owner>
   ```
   A bundle can span multiple orgs; the user may need to authenticate to each. Handle exit codes the same as `/org-scan`.

5. **Set up venv if needed:**
   ```
   python3 -m venv $PLUGIN_ROOT/skills/org-context/scripts/.venv 2>/dev/null || true
   $PLUGIN_ROOT/skills/org-context/scripts/.venv/bin/pip install -q -r $PLUGIN_ROOT/skills/org-context/scripts/requirements.txt
   ```

6. **Run the scan:**
   ```
   $PLUGIN_ROOT/skills/org-context/scripts/.venv/bin/python \
     $PLUGIN_ROOT/skills/org-context/scripts/scan.py \
     --bundle <bundle> \
     --bundle-file $PLUGIN_ROOT/context/bundles/<bundle>/bundle.yml \
     --output $PLUGIN_ROOT/context/bundles/<bundle>
   ```

7. **Report summary.** After completion:
   - Total repos, Tier-1/2/3 breakdown
   - Distinct orgs represented
   - Domains discovered
   - Failures if any
   - Suggest reviewing `domains.yml` auto-generated entries

## Notes

- Repo filenames inside `repos/` and `archive/` use `<owner>__<repo>.md` (double-underscore) to avoid collisions when different orgs share a repo name.
- If `<bundle>` is missing from the command, ask for it before doing anything.
- The same extraction engine as `/org-scan` runs under the hood — tiering, runbook inference, domain clustering, and cross-repo connection mapping all apply.
