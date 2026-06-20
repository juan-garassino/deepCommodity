# deepCommodity routine runner — headless Claude Code on a schedule.
#
# The image bakes the runtime (python deps + Node + claude-code CLI) and the repo
# code, so a locally-tested image runs identically on the VM. Secrets are NEVER
# baked (.env is dockerignored) — pass them at runtime via --env-file / -e.
#
# Build:  docker build -f deploy/Dockerfile -t dc-trader:local .
# Test:   docker run --rm -e CLAUDE_CODE_OAUTH_TOKEN=... -e OPENAI_API_KEY=... \
#                 -e BINANCE_API_KEY=... -e BINANCE_API_SECRET=... -e BINANCE_TESTNET=true \
#                 -e TRADING_MODE=paper dc-trader:local decision
# Prod:   docker run --rm --env-file /srv/deepCommodity/.env \
#                 -v /srv/deepCommodity:/app dc-trader:local decision
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 REPO=/app HOME=/home/trader

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 10001 trader && chown -R trader:trader /app /home/trader
USER trader

# run_routine.sh reads REPO/.env if present (prod bind-mount) or the docker env (test).
ENTRYPOINT ["bash", "deploy/run_routine.sh"]
CMD ["heartbeat"]
