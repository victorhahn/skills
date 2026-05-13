---
name: repos-update
description: Incremental refresh of a previously scanned bundle — re-processes only repos with new activity
allowed-tools: Bash, Read, Write, Edit
---

# /repos-update [<bundle>]

Incrementally update the context for a previously scanned bundle. Reads membership from `bundle.yml` — no need to re-supply the repo list.

## Steps

1. **Resolve plugin root and bundle.** If `<bundle>` is not given:
   - List directories under `$PLUGIN_ROOT/context/bundles/` and show them.
   - If exactly one exists, use it automatically and confirm.
   - If multiple exist, ask which to update.

2. **Verify prior scan exists.** Check that `$PLUGIN_ROOT/context/bundles/<bundle>/BUNDLE.md` exists. If not, tell the user to run `/repos-scan <bundle> <repo>...` first.

3. **Run preflight for each distinct owner** in `bundle.yml`. Same error handling as `/repos-scan`.

4. **Run incremental update:**
   ```
   $PLUGIN_ROOT/skills/org-context/scripts/.venv/bin/python \
     $PLUGIN_ROOT/skills/org-context/scripts/update.py \
     --bundle <bundle> \
     --bundle-file $PLUGIN_ROOT/context/bundles/<bundle>/bundle.yml \
     --output $PLUGIN_ROOT/context/bundles/<bundle>
   ```

5. **Report what changed** — repos re-processed, domains regenerated, summary file updated, any failures.

## Notes

- To add or remove repos from a bundle, edit `bundle.yml` directly and re-run `/repos-update <bundle>`. Removed repos will have their context files deleted; added repos will be processed as if new.
- Venv bootstrap: if `.venv` is missing, recreate it before running the update script.
