# deepCommodity — model serving

FastAPI inference endpoint for the trained transformers + news/rule-based fallbacks. Trained checkpoints are produced on Colab and bind-mounted into the container; the agent's forecast router calls this service when invoked with `--model api`.

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | none | liveness + which models are loaded |
| POST | `/forecast` | `X-API-Key` | run a forecast (price / orderflow / news / rule-based / ensemble) |
| POST | `/reload` | `X-API-Key` | re-scan `MODELS_DIR` to pick up new checkpoints |

## Run locally (without Docker)

```bash
pip install -r serving/requirements.txt
pip install torch    # CPU is fine for inference
export DC_API_KEY=$(openssl rand -hex 32)
export MODELS_DIR=$(pwd)/data/models
uvicorn serving.app:app --host 0.0.0.0 --port 8080
```

Smoke:
```bash
curl -s http://127.0.0.1:8080/health | jq
curl -s -X POST http://127.0.0.1:8080/forecast \
  -H "X-API-Key: $DC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC","model":"rule-based","pct_change_24h":1.2,"pct_change_7d":5.0}'
```

## Run via Docker Compose

```bash
# .env in this dir or exported in the shell:
#   DC_API_KEY=...                             (required)
#   DC_SERVE_PORT=8080                         (default)
#   MODELS_HOST_DIR=/path/to/your/models       (default ./models)
docker compose -f serving/docker-compose.yml up -d --build
docker compose -f serving/docker-compose.yml logs -f
```

The container is sandboxed (`read_only: true`, `no-new-privileges`, `/tmp` as tmpfs). Only the models directory is mounted, read-only.

## Wiring the agent's forecast router to the API

Once the service is up, the `tools/forecast.py` router can call it with `--model api`:

```bash
python tools/forecast.py \
  --model api \
  --api-url https://your-endpoint.example.com \
  --api-key "$DC_API_KEY" \
  --input /tmp/crypto.json --news-input /tmp/news.json
```

In the managed routines, set two extra env vars on the cloud environment:
```
DC_API_URL=https://your-endpoint.example.com
DC_API_KEY=...
```
and update the daily-decision routine to use `--model api` (the prompt change is one line).

## Updating models

Train on Colab → save to Drive → rclone-sync the `models/` folder onto the host → call:
```bash
curl -s -X POST http://127.0.0.1:8080/reload -H "X-API-Key: $DC_API_KEY" | jq
```
No restart needed; `reload` swaps the registry atomically.

## Security checklist before exposing publicly

- Set `DC_API_KEY` to a real secret (32+ bytes random). The startup logs warn if unset.
- Put a TLS-terminating reverse proxy (Caddy, Cloudflare Tunnel, nginx) in front. The container speaks plain HTTP on port 8080 — never expose it directly.
- Restrict ingress to known IPs (your routine cloud + your dev box) where possible.
- Rotate `DC_API_KEY` periodically; clients re-read it from env on next call.
