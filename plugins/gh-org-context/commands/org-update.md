---
name: org-update
description: Incremental refresh of a previously scanned GitHub org — only re-processes repos with new activity since the last scan
allowed-tools: Bash, Read, Write, Edit
---

# /org-update [<org>]

Incrementally update the context for a previously scanned GitHub org. Only repos with commits, tier changes, or new metadata since the last scan are re-processed.

## Steps

1. **Resolve plugin root and org.** Set `PLUGIN_ROOT` to the absolute path of the plugin directory. If `<org>` is not provided:
   - List directories under `$PLUGIN_ROOT/context/orgs/` and show them to the user.
   - If exactly one exists, use it automatically and confirm with the user.
   - If multiple exist, ask which to update.

2. **Verify a prior scan exists.** Check that `$PLUGIN_ROOT/context/orgs/<org>/ORG.md` exists. If not, tell the user to run `/org-scan <org>` first.

3. **Run preflight** (same as `/org-scan`):
   ```
   bash $PLUGIN_ROOT/skills/org-context/scripts/gh_preflight.sh <org>
   ```
   Handle exit codes identically to `/org-scan`.

4. **Run incremental update:**
   ```
   cd $PLUGIN_ROOT/skills/org-context
   scripts/.venv/bin/python scripts/update.py --org <org> --output $PLUGIN_ROOT/context/orgs/<org>
   ```
   The script reads `.scan-meta.json` to determine what changed, re-processes only dirty repos, and re-synthesizes any affected domain files.

5. **Report what changed.** After the script exits, summarize:
   - How many repos were re-processed (vs. skipped as unchanged)
   - Which domain files were regenerated
   - Whether `ORG.md` was updated
   - Any new failures in `.failures.log`

## Notes

- If `.venv` is missing (e.g., clean checkout on a new machine), recreate it:
  ```
  python3 -m venv $PLUGIN_ROOT/skills/org-context/scripts/.venv
  $PLUGIN_ROOT/skills/org-context/scripts/.venv/bin/pip install -q -r $PLUGIN_ROOT/skills/org-context/scripts/requirements.txt
  ```
- Incremental updates are much faster than full scans — typically only a handful of repos need re-processing.
