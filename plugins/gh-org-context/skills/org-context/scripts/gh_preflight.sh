#!/usr/bin/env bash
# gh_preflight.sh <org>
# Checks gh CLI readiness for scanning <org>.
# Exit codes:
#   0  — all good; prints JSON {login, org_role, rate_remaining, rate_reset}
#   10 — gh not installed
#   20 — not authenticated
#   30 — missing read:org or repo scope
#   40 — org not found or SSO not authorized
#   50 — rate limit too low (<500 remaining)

set -euo pipefail

ORG="${1:-}"
if [[ -z "$ORG" ]]; then
  echo "Usage: gh_preflight.sh <org>" >&2
  exit 1
fi

# ── 1. gh installed? ─────────────────────────────────────────────────────────
if ! command -v gh &>/dev/null; then
  echo "ERROR:10:gh CLI not found. Install with: brew install gh  (or visit https://cli.github.com)" >&2
  exit 10
fi

# ── 2. Authenticated? ─────────────────────────────────────────────────────────
if ! gh auth status &>/dev/null; then
  echo "ERROR:20:Not authenticated. Run: gh auth login  (choose GitHub.com → HTTPS → browser)" >&2
  exit 20
fi

# ── 3. Scopes ─────────────────────────────────────────────────────────────────
# gh auth token --hostname github.com outputs the raw token; scopes come from the API
TOKEN=$(gh auth token 2>/dev/null || true)
if [[ -z "$TOKEN" ]]; then
  echo "ERROR:20:Could not retrieve auth token." >&2
  exit 20
fi

SCOPES_HEADER=$(curl -sf -H "Authorization: token $TOKEN" \
  -I "https://api.github.com/user" 2>/dev/null | \
  grep -i '^x-oauth-scopes:' | tr -d '\r' | sed 's/^[^:]*: //' || true)

MISSING_SCOPES=()
if [[ "$SCOPES_HEADER" != *"read:org"* ]] && [[ "$SCOPES_HEADER" != *"admin:org"* ]]; then
  MISSING_SCOPES+=("read:org")
fi
if [[ "$SCOPES_HEADER" != *"repo"* ]]; then
  MISSING_SCOPES+=("repo")
fi

if [[ ${#MISSING_SCOPES[@]} -gt 0 ]]; then
  MISSING=$(IFS=,; echo "${MISSING_SCOPES[*]}")
  echo "ERROR:30:Token missing scopes: ${MISSING}. Run: gh auth refresh -s ${MISSING}" >&2
  exit 30
fi

# ── 4. Org accessible? ────────────────────────────────────────────────────────
ORG_JSON=$(gh api "orgs/${ORG}" 2>&1 || true)
if echo "$ORG_JSON" | grep -q '"message".*"Not Found"'; then
  echo "ERROR:40:Org '${ORG}' not found — you may not be a member, or SSO is not authorized for your token." >&2
  echo "         Visit https://github.com/settings/tokens to configure SSO, or contact the org admin." >&2
  exit 40
fi
if echo "$ORG_JSON" | grep -q '"message"'; then
  MSG=$(echo "$ORG_JSON" | grep -o '"message":"[^"]*"' | head -1)
  echo "ERROR:40:Org API returned an error: ${MSG}" >&2
  exit 40
fi

# ── 5. Rate limit ─────────────────────────────────────────────────────────────
RATE_JSON=$(gh api rate_limit 2>/dev/null)
REMAINING=$(echo "$RATE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['resources']['core']['remaining'])" 2>/dev/null || echo 0)
RESET_TS=$(echo "$RATE_JSON"  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['resources']['core']['reset'])"     2>/dev/null || echo 0)
RESET_TIME=$(python3 -c "import datetime; print(datetime.datetime.fromtimestamp(${RESET_TS}).strftime('%H:%M:%S'))" 2>/dev/null || echo "unknown")

if [[ "$REMAINING" -lt 500 ]]; then
  echo "ERROR:50:Rate limit low: ${REMAINING} requests remaining (resets at ${RESET_TIME})." >&2
  exit 50
fi

# ── 6. Collect user info ──────────────────────────────────────────────────────
LOGIN=$(gh api user --jq '.login' 2>/dev/null || echo "unknown")
MEMBERSHIP=$(gh api "orgs/${ORG}/memberships/${LOGIN}" --jq '.role' 2>/dev/null || echo "member")

python3 - <<EOF
import json
print(json.dumps({
  "login": "${LOGIN}",
  "org": "${ORG}",
  "org_role": "${MEMBERSHIP}",
  "rate_remaining": ${REMAINING},
  "rate_reset": "${RESET_TIME}"
}))
EOF
