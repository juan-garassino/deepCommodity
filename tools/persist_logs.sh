#!/usr/bin/env bash
# Commit append-only log changes back to the repo so the next managed-routine
# run starts with the latest state.
#
# Usage:  ./tools/persist_logs.sh "<routine-name>"
#
# Cloud-routine deployment: by default, Claude Code routines can only push to
# `claude/`-prefixed branches. We push log updates to claude/logs so no special
# repo permission is needed; merge that branch into main on your own cadence
# (a periodic PR is fine — these are append-only files with no conflicts).
#
# VPS deployment: this script is unnecessary because state is local; harmless if
# called.

set -u
ROUTINE="${1:-routine}"
STAMP="$(date -u +%FT%TZ)"
LOG_BRANCH="${LOG_BRANCH:-claude/logs}"

git config user.email "${GIT_BOT_EMAIL:-bot@deepcommodity.local}"
git config user.name  "${GIT_BOT_NAME:-deepCommodity-bot}"

# Stage only the log files — never auto-commit anything else.
git add RESEARCH-LOG.md TRADE-LOG.md WEEKLY-REVIEW.md KILL_SWITCH 2>/dev/null || true

if git diff --cached --quiet; then
  echo "persist_logs: no log changes"
  exit 0
fi

# Switch to (or create) the log branch off origin/<log-branch> if it exists,
# else off the current HEAD. Avoids polluting the routine's working branch.
if git ls-remote --exit-code --heads origin "$LOG_BRANCH" >/dev/null 2>&1; then
  git fetch origin "$LOG_BRANCH" --depth=1 2>/dev/null || true
  git checkout -B "$LOG_BRANCH" "origin/$LOG_BRANCH"
  # re-apply staged changes against the log branch
  git add RESEARCH-LOG.md TRADE-LOG.md WEEKLY-REVIEW.md KILL_SWITCH 2>/dev/null || true
else
  git checkout -B "$LOG_BRANCH"
fi

git commit -m "${ROUTINE}: ${STAMP}" --no-verify
echo "persist_logs: committed log changes for ${ROUTINE} @ ${STAMP}"

if git remote get-url origin >/dev/null 2>&1; then
  if git push -u origin "$LOG_BRANCH" 2>/dev/null; then
    echo "persist_logs: pushed $LOG_BRANCH"
  else
    echo "persist_logs: push failed — commit kept locally" >&2
  fi
fi
