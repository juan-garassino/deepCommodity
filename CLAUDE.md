# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

`deepCommodity` is an **agentic quant** trader. Claude Code itself is the agent — there are no agent classes in Python. Routines on `claude.ai/code/routines` (cron-fired headless sessions) read state from markdown logs, call tools that fetch data and place orders, and write results back. The LLM is the alpha generator; tools validate.

The system is theme-driven, not list-driven: the agent reads news + 6 parallel signal streams, identifies **active themes** (each must be supported by ≥ 2 distinct source-types), maps themes to second-order beneficiaries via `themes.yaml`, then trades within strict bucket gates.

See `AGENTIC-QUANT.md` for the architecture rationale. See `AGENT-INSTRUCTIONS.md` for the operating contract the routines obey. See `TRADING-STRATEGY.md` for universe + risk limits (source of truth).

## Repo layout

```
.
├── CLAUDE.md                        ← you are here
├── AGENTIC-QUANT.md                 design rationale
├── AGENT-INSTRUCTIONS.md            agent operating procedure
├── TRADING-STRATEGY.md              universe, gates, position caps
├── PROJECT-TRADING-PLAN.md          roadmap + KPIs
├── RESEARCH-LOG.md                  append-only — written by tools/journal.py
├── TRADE-LOG.md                     append-only — every order journaled here
├── WEEKLY-REVIEW.md                 narrative retrospectives
├── .env.sample                      copy → .env (gitignored)
├── deepCommodity/
│   ├── universe/                    themes.yaml + Universe loader
│   ├── execution/                   Binance + Bitfinex + Alpaca adapters
│   ├── guardrails/                  KILL_SWITCH, limits, sanitize, circuit breaker
│   ├── model/                       LSTM + price/orderflow/fused transformers
│   ├── backtest/                    walk-forward engine reusing live risk gates
│   ├── manager/                     BigQuery sink + plotting
│   └── sourcing/                    legacy data fetchers
├── tools/                           CLI scripts the agent invokes
├── tests/                           147 tests, mocked
├── serving/                         FastAPI inference service + Dockerfile
├── deploy/                          VPS deploy: cron, systemd, install_remote.sh
├── notebooks/train_on_colab.ipynb   GPU training entry point
├── .claude/
│   ├── settings.json                bash + edit allowlist (committed)
│   └── routines/managed/            paste-ready prompts for cloud routines
└── .githooks/pre-commit             secret-scanner (opt-in)
```

## Three-bucket decision architecture

| Bucket | Source | Gate | Daily cap |
|---|---|---|---|
| **Anchor** | static list (BTC, ETH, SPY, QQQ, AAPL, MSFT, NVDA, GOOGL, META, AMZN, BRK.B) | forecast confidence ≥ 0.55 | 1 |
| **Theme** | symbols pulled from `themes.yaml` for **active themes** the agent identifies in news | ≥ 2 distinct source-types AND forecast confidence ≥ 0.50 | 2 |
| **Hidden gem** | dynamic CoinGecko top 250 scan via `tools/scan_hidden_gems.py` | rank ≥ 0.65 AND agent thesis ≥ 100 chars citing news | 1 |

**Total cap: 3 new positions / day.** Thesis is required and stored in TRADE-LOG.md `--reason` (free / 50 / 100 chars by bucket).

## The six-stream signal layer

Every research routine reads in parallel before identifying themes. A theme is "active" only when supported by ≥ 2 distinct **source-types**.

| Stream | Tool | Provider | Free? |
|---|---|---|---|
| News | `tools/fetch_news.py` | OpenAI search-preview (Perplexity fallback) | OpenAI = pay-per-call |
| Insider transactions | `tools/fetch_insider.py` | OpenInsider (SEC Form 4 cluster buys) | yes |
| Material events 8-K | `tools/fetch_filings.py` | SEC EDGAR Atom feeds | yes |
| Earnings calendar | `tools/fetch_earnings.py` | Finnhub (free key) → yfinance fallback | yes |
| On-chain crypto | `tools/fetch_onchain.py` | CryptoQuant (free key) → Binance volume z-score | yes |
| Cross-asset regime | `tools/correlation_matrix.py` | yfinance + Binance public; flags 5d-vs-90d corr breaks ≥ 0.30 | yes |
| Fed-funds implied | `tools/fetch_fedwatch.py` | yfinance ZQ=F + FRED current target | yes |

All news-text fetchers pass through `deepCommodity/guardrails/sanitize.sanitize_news` before the agent reads them.

## Tools (CLI; JSON to stdout)

| Tool | Purpose |
|---|---|
| `tools/journal.py {research,trade}` | append a dated entry to RESEARCH-LOG / TRADE-LOG |
| `tools/sync_state.py --skip-pull` | bootstrap routine state (env loading, log-branch fetch) |
| `tools/fetch_news.py --query …` | OpenAI search → sanitized digest |
| `tools/fetch_crypto.py --symbols X,Y` or `--top-n 50` | CoinGecko + optional Binance ticker |
| `tools/fetch_equities.py --symbols X,Y` | Alpaca data API (IEX feed for free) |
| `tools/fetch_macro.py --series CPIAUCSL` | FRED |
| `tools/scan_hidden_gems.py` | dynamic CoinGecko top-250 with filters; excludes universe |
| `tools/fetch_insider.py --mode cluster` | OpenInsider scraping |
| `tools/fetch_filings.py --symbols …` | SEC EDGAR 8-K Atom |
| `tools/fetch_earnings.py --days 14` | upcoming earnings |
| `tools/fetch_onchain.py --metric volume-proxy` | crypto exchange / volume |
| `tools/correlation_matrix.py` | cross-asset corr + regime breaks |
| `tools/fetch_fedwatch.py` | implied Fed move |
| `tools/rank_smallcaps.py --input …` | momentum × log-inv-mcap × volume scoring (gem lane only) |
| `tools/forecast.py --model {rule-based\|price\|orderflow\|news\|fused\|ensemble\|api}` | direction + confidence per symbol |
| `tools/risk_check.py …` | pre-trade gate; exit 0 = OK |
| `tools/place_order.py …` | broker dispatch + journals + Telegram |
| `tools/notify_telegram.py` | best-effort Telegram ping (silent if env unset) |
| `tools/persist_logs.sh <routine>` | commit log changes to current claude/<adj-noun> branch |
| `tools/backtest.py --bars-dir …` | replay historical bars through forecaster + risk gates |
| `tools/fetch_history.py` | OHLCV from Binance public / yfinance for training |
| `tools/train_price_transformer.py` | Colab training entry |
| `tools/smoke_paper.sh` | end-to-end smoke against OpenAI + Alpaca paper |

## Routines on claude.ai/code/routines (cloud cadence)

Daily total stays under your 15/day budget.

| Routine | Cron (UTC) | Per day | What |
|---|---|---|---|
| `dc heartbeat` | (paused / disabled) | 0 | canary; not needed when other routines run |
| `dc research (every 3h)` | `7 */3 * * *` | 8 | 6-stream digest → theme detection → journal |
| `dc daily decision (open)` | `0 14 * * 1-5` | 0.71 | weekday morning; bucket gates |
| `dc intraday news` | `0 17 * * *` | 1 | tighter "breaking catalyst" gate; max 2 pos |
| `dc daily decision (close)` | `0 22 * * *` | 1 | crypto-only second pass |
| `dc position-mgmt` (NEW Phase A) | `0 13,21 * * *` | 2 | reconciles open positions; closes decayed thesis; trails stops; **never opens** |
| `dc weekly review` | `0 18 * * 0` | 0.14 | per-bucket + per-theme PnL attribution |
| **Total** | | **12.85/day** | |

The paste-ready prompts are in `.claude/routines/managed/`. The schedule skill (`/schedule`) creates routines; tokens for API triggers are managed in the web UI.

## Hard rules (every routine obeys)

1. **Never** call `place_order.py` without `risk_check.py` exiting 0 first.
2. **Never** call `place_order.py` if `KILL_SWITCH` exists.
3. Use `tools/journal.py` for logs — append-only.
4. `TRADING-STRATEGY.md` and `themes.yaml` are sources of truth. Edit only via weekly-review proposed-edits + manual merge.
5. Live trading requires both `TRADING_MODE=live` AND `DAILY_DECISION_AUTHORIZE_LIVE=true` AND `--confirm-live` flag.
6. Theme is active only with ≥ 2 distinct **source-types** of evidence. Two news bullets = 1 source-type, doesn't qualify.
7. Hidden gem buys require thesis ≥ 100 chars citing news. "high momentum" doesn't count.
8. Auto-heal pip install for ccxt/alpaca-py is allowed; arbitrary pip install is denied.

## Environment

Copy `.env.sample` → `.env`. The `.gitignore` is fail-closed for credentials (`.env`, `.env.*`, `*.key`, `*.pem`, `secrets.*`, `service-account*.json`, `id_rsa*`, `.netrc`). Optional pre-commit hook for secret scanning: `git config core.hooksPath .githooks`.

Environment variables (free unless noted):
- `TRADING_MODE` — `paper` (default) or `live`
- `DAILY_DECISION_AUTHORIZE_LIVE` — second gate; `true` required for live
- `BINANCE_API_KEY` / `_SECRET` / `_TESTNET` (testnet free)
- `BITFINEX_API_KEY` / `_SECRET` / `_PAPER` (alternative crypto venue)
- `ALPACA_API_KEY` / `_SECRET` / `_PAPER` — must be **paper-trading keys**, not live (different keypair)
- `OPENAI_API_KEY` — primary news provider (search-preview model, ~$0.04/call)
- `PERPLEXITY_API_KEY` — fallback news provider (optional)
- `FINNHUB_API_KEY` — earnings calendar (free, 60/min) — https://finnhub.io/register
- `CRYPTOQUANT_API_KEY` — exchange reserves (free tier) — https://cryptoquant.com/auth
- `FRED_API_KEY` — macro + FedWatch
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — alerts (silent no-op if unset)
- `GIT_BOT_EMAIL` / `GIT_BOT_NAME` — author identity for routine commits

The cloud routines pick up env vars from the `deepCommodity` cloud environment configured at https://claude.ai/code/environments. Setup script there installs deps:
```bash
set -e
python3 -m pip install --quiet --break-system-packages -r requirements.txt
```
Network allowlist must include: `api.openai.com`, `paper-api.alpaca.markets`, `data.alpaca.markets`, `api.binance.com`, `api.coingecko.com`, `api.telegram.org`, `api.finnhub.io`, `api.cryptoquant.com`, `www.sec.gov`, `openinsider.com`, `query2.finance.yahoo.com`.

## Commands

```bash
# tests
make dc-test                      # 147 passing

# end-to-end smoke against real OpenAI + Alpaca paper
make dc-smoke-paper

# Colab training (one command does everything)
make dc-train-all                                                  # auto-detects Drive
make dc-train-all OUTPUT_DIR=/content/drive/MyDrive/dc_outputs

# backtest (no API keys)
python tools/backtest.py --bars-dir data/bars/

# Halt
touch KILL_SWITCH                # blocks all orders, all routines
rm KILL_SWITCH                   # resume

# Forecaster router (Phase 9)
python tools/forecast.py --input crypto.json --model rule-based   # default
python tools/forecast.py --input crypto.json --model ensemble --news-input news.json
python tools/forecast.py --input crypto.json --model api          # calls serving/ FastAPI
```

## Inference deployment

`serving/` is a FastAPI service that loads trained transformer checkpoints from a mounted volume and serves `/forecast`, `/health`, `/reload`. `serving/Dockerfile` + `serving/docker-compose.yml`. The agent calls it via `--model api` once `DC_API_URL` and `DC_API_KEY` are set in the cloud env.

Workflow: train on Colab → save to Drive → rclone-sync into `MODELS_HOST_DIR` → `docker compose up` → routines call the endpoint.

## VPS alternative

`deploy/` has a parallel deployment kit (cron + systemd + Telegram alerts on failure). Use this if you want to migrate off managed routines later. `deploy/install_remote.sh` does one-shot Ubuntu/Debian provisioning.

## Phase status (where each piece sits)

- **Phase 0–4 (foundation, tools, routines, paper-shakedown, go-live)** — all done architecturally; live trading still gated.
- **Phase 5 — price transformer** — architecture done; awaits Colab training. Inference works via `serving/` + `--model api`.
- **Phase 6 — order-flow transformer** — same.
- **Phase 7 — news/sentiment model** — rule-based backend live; sklearn + HuggingFace opt-in.
- **Phase 8 — fused multi-modal** — architecture done; awaits encoders from 5/6.
- **Phase 9 — router** — wired in `tools/forecast.py`. Ensemble degrades gracefully.
- **Phase 10 (this round) — six-stream signal layer + position-mgmt routine** — committed; cloud routine prompts ready to deploy.

## Conventions

- Tools must: read env + args, write JSON to stdout, exit non-zero on hard error.
- All news-text reads through `sanitize_news` before reaching the agent.
- Routines use `persist_logs.sh` for git commits (no manual commits in routines).
- Logs are append-only; corrections go in a new dated entry.
- Per-position cap is 5% NAV; sector cap 30%; cash floor 10%.
- Daily DD breaker 4%, weekly 8% — auto-arm KILL_SWITCH.
- Stop-loss -8%, take-profit +20%, max gross leverage 1.0×.

## Money math

To clear fixed costs (~€700/yr: Anthropic Pro + OpenAI search) at a realistic 20% annual return, **NAV ≥ €3,500**. €5,000+ is where the system contributes meaningfully. €100 = paper-only; €1,000–2,000 = tuition; €10,000+ = the strategy starts paying for itself.

## Routine session ergonomics

Each cloud routine creates a `claude/<adj-noun>` branch per run. `persist_logs.sh` pushes log diffs to that branch (sandbox can't push to other branches). Merge those branches into master periodically — they're append-only, no conflicts.

If a routine ever fails persistently: check (1) GitHub repo cloned via `/web-setup` or Claude GitHub App; (2) cloud env has setup script + env vars; (3) Network allowlist includes all required hosts; (4) `.claude/settings.json` allow-list includes the bash commands used by routine prompts.
