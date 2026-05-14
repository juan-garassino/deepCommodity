#!/usr/bin/env bash
# Commit append-only log changes back to the repo.
#
# Cloud Routines reality: the sandbox owns ONE auto-generated `claude/<adj-noun>`
# branch per run and can only push to that one. We cannot reuse a fixed
# `claude/logs` branch across runs (the sandbox's git credentials are scoped
# to the run-specific branch).
#
# So:
#   1. Stage log changes.
#   2. Commit on the current branch (whatever the sandbox named it — typically
#      `claude/<adj-noun>` in cloud routines, or `master` on a VPS deploy).
#   3. `git push` to that same branch. The sandbox is allowed to push there.
#
# Net effect on the cloud:
#   - Each routine fire creates a separate branch with one or two log diffs.
#   - You merge them as a batch (or open a PR) on your own cadence.
#   - For "what happened" between merges: read the session transcript or
#     Telegram pings; the per-branch diffs are the audit trail.

set -u
ROUTINE="${1:-routine}"
STAMP="$(date -u +%FT%TZ)"

git config user.email "${GIT_BOT_EMAIL:-bot@deepcommodity.local}"
git config user.name  "${GIT_BOT_NAME:-deepCommodity-bot}"

# Stage only the log files — never auto-commit anything else.
# Add each file individually so a missing KILL_SWITCH doesn't block the others.
for _f in RESEARCH-LOG.md TRADE-LOG.md WEEKLY-REVIEW.md; do
  [ -f "$_f" ] && git add "$_f" 2>/dev/null || true
done
[ -f KILL_SWITCH ] && git add KILL_SWITCH 2>/dev/null || true

if git diff --cached --quiet; then
  echo "persist_logs: no log changes for ${ROUTINE}"
  exit 0
fi

git commit -m "${ROUTINE}: ${STAMP}" --no-verify
echo "persist_logs: committed log changes for ${ROUTINE} @ ${STAMP}"

# Push to whatever the current HEAD branch is (sandbox-owned).
current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
if [ -z "$current_branch" ] || [ "$current_branch" = "HEAD" ]; then
  echo "persist_logs: detached HEAD; nothing to push"
  exit 0
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "persist_logs: no remote configured; commit kept locally"
  exit 0
fi

if git push -u origin "$current_branch" 2>&1 | tail -3; then
  echo "persist_logs: pushed ${current_branch}"
else
  echo "persist_logs: push to ${current_branch} failed (commit kept locally)" >&2
fi

# Always succeed — log persistence is best-effort, the routine itself succeeded.
exit 0
