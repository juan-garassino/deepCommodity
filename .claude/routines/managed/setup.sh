#!/usr/bin/env bash
# Setup script for the deepCommodity Claude Code cloud environment.
#
# Paste this into the environment's "Setup script" field at
# claude.ai/code/routines (or claude.ai/code/environments). The result is
# cached, so it runs once per environment-version, not per routine run.

set -e

python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r requirements.txt

# Inference-only — no torch unless the routine explicitly opts into trained
# transformers (in which case add torch + yfinance to the env's setup script).
# Most routines run with the rule-based forecaster which needs no extra deps.

echo "deepCommodity environment ready"
