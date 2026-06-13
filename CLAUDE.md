# CLAUDE.md

Guidance for Claude Code working in this repository.

> **GCP migration note (2026-06-07):** Cloud target if/when deployed: **`garassino-ml`** / `europe-west1` (show-and-destroy under €25/mo workspace cap). No deploy infra yet — runs locally. See workspace root `CLAUDE.md` § "GCP architecture".

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
│   ├── execution/                   adapters + portfolio.py (authoritative broker snapshot)
│   ├── guardrails/                  preflight (the chokepoint), limits, kill_switch/halt, sanitize, circuit breaker
│   ├── model/                       LSTM + price/orderflow/fused transformers
│   ├── backtest/                    walk-forward engine reusing live risk gates
│   ├── manager/                     BigQuery sink + plotting
│   └── sourcing/                    legacy data fetchers
├── tools/                           CLI scripts the agent invokes
├── tests/                           226 tests, mocked (MockBroker/MockPortfolioProvider in _mocks.py)
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
| **Hidden gem** | dynamic CoinGecko top 250 scan via `tools/scan_hidden_gems.py` | rank ≥ 0.65 AND forecast confidence ≥ 0.55 AND agent thesis ≥ 100 chars citing news | 1 |

**Total cap: 3 new positions / day** (also per-bucket: anchor 1 / theme 2 / gem 1) — **the daily + per-bucket caps, position/sector/leverage/cash limits are code-enforced in `check_limits`** against real broker fills. The forecast-confidence floors and thesis-length/source-count requirements remain routine-enforced (the agent obeys them; they are not in `preflight`). Thesis is stored in TRADE-LOG.md `--reason` (free / 50 / 100 chars by bucket).

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
| `tools/risk_check.py …` | pre-trade gate (thin wrapper over `preflight`); exit 0 = OK / 1 = blocked / 2 = halt |
| `tools/place_order.py …` | gated broker dispatch (needs `--allow-buy` to open); journals + Telegram |
| `tools/check_drawdown.py` | drawdown breaker (run by position-mgmt): arms KILL_SWITCH on −4%d/−8%w; fail-closed |
| `tools/notify_telegram.py` | best-effort Telegram ping (silent if env unset) |
| `tools/persist_logs.sh <routine>` | commit log changes to current claude/<adj-noun> branch |
| `tools/backtest.py --bars-dir …` | replay historical bars through forecaster + risk gates |
| `tools/fetch_history.py` | OHLCV from Binance public / yfinance for training |
| `tools/train_price_transformer.py` | Colab training entry |
| `tools/smoke_paper.sh` | end-to-end smoke against OpenAI + Alpaca paper |

## Routines on claude.ai/code/routines (cloud cadence)

**24/7 crypto-first cadence** (Approach A) — crypto has no market hours, so passes are spread evenly
around the clock and optimized for fast reaction to catalysts. Equities are paused (Alpaca live is
EU-unavailable). 3 active routines, ~10/day, under the 15/day budget.

| Routine | Cron (UTC) | Per day | What |
|---|---|---|---|
| `dc decision (24/7)` | `0 */4 * * *` (00/04/08/12/16/20) | 6 | crypto 6-stream read → theme detect → trade within bucket caps |
| `dc position-mgmt` | `0 3,9,15,21 * * *` (offset 3h) | 4 | drawdown breaker (`check_drawdown.py`) + close/trail; **never opens** |
| `dc weekly review` | `0 18 * * 0` | 0.14 | per-bucket + per-theme PnL attribution |
| **Total** | | **~10.1/day** | |

Decision and position-mgmt interleave every ~2h → ≤4h to act on a catalyst, ≤6h to catch a drawdown.
The 3/day cap is code-enforced, so more passes mean faster reaction, not more trades.

Disabled / retired (delete in the web UI): `dc daily decision (open/close)`, `dc intraday news`,
`dc research (every 3h)`, `dc heartbeat` — superseded by the merged `dc decision` prompt.

The paste-ready prompts are in `.claude/routines/managed/` (`decision.md`, `position-mgmt.md`,
`weekly-review.md`). The schedule skill (`/schedule`) creates/updates routines; secrets + network
allowlist live in the cloud `deepCommodity` environment.

## Gates are code-enforced (not prompt-trust)

As of the live-readiness pass, the risk gates live in **`deepCommodity/guardrails/preflight.py`** — the single chokepoint every order passes through, fed by an authoritative broker snapshot (`deepCommodity/execution/portfolio.py`). `place_order.py` and `risk_check.py` are thin wrappers over it, so they cannot diverge. The position/sector/gross-leverage/cash-floor/daily-cap limits, the finiteness checks, the halt check, and the live-authorization gate are all enforced in code and **fail closed** (a broker that can't report state blocks the trade — no fabricated portfolio). The rules below are still the operating contract, but they are now backstopped by code rather than relying on the agent to remember them.

## Hard rules (every routine obeys)

1. **Never** call `place_order.py` without `risk_check.py` exiting 0 first. (`place_order` re-runs the same `preflight` in-process regardless.)
2. **Never** call `place_order.py` if halted. Halt = `KILL_SWITCH` file OR `DC_HALT=true` OR `TRADING_MODE=halt`; the gate fails closed if it can't confirm.
3. Use `tools/journal.py` for logs — append-only.
4. `TRADING-STRATEGY.md` and `themes.yaml` are sources of truth. Edit only via weekly-review proposed-edits + manual merge.
5. Live trading requires **all** of `TRADING_MODE=live` AND `DAILY_DECISION_AUTHORIZE_LIVE=true` AND the `--confirm-live` flag AND account NAV ≤ `DC_MAX_NAV_USD` — all code-enforced in `place_order.py`.
6. Theme is active only with ≥ 2 distinct **source-types** of evidence. Two news bullets = 1 source-type, doesn't qualify.
7. Hidden gem buys require thesis ≥ 100 chars citing news. "high momentum" doesn't count.
8. Opening/adding a position requires the `--allow-buy` flag (code-enforced). The position-mgmt routine never passes it, so it structurally **cannot open**.
9. Auto-heal pip install for ccxt/alpaca-py is allowed; arbitrary pip install is denied.

## Environment

Copy `.env.sample` → `.env`. The `.gitignore` is fail-closed for credentials (`.env`, `.env.*`, `*.key`, `*.pem`, `secrets.*`, `service-account*.json`, `id_rsa*`, `.netrc`). Optional pre-commit hook for secret scanning: `git config core.hooksPath .githooks`.

Environment variables (free unless noted):
- `TRADING_MODE` — `paper` (default), `live`, or `halt` (emergency stop)
- `DAILY_DECISION_AUTHORIZE_LIVE` — second live gate; `true` required for live
- `DC_HALT` — out-of-band kill switch that reaches cloud routines; `true` halts all orders next run
- `DC_MAX_NAV_USD` — code-enforced ceiling on NAV traded live (keep small for the first live window)
- `BINANCE_API_KEY` / `_SECRET` / `_TESTNET` (testnet free; live requires `_TESTNET=false`)
- `BITFINEX_API_KEY` / `_SECRET` / `BITFINEX_SANDBOX_CONFIRMED` — Bitfinex is **disabled in the live path** (audit B7); use Binance for crypto
- `ALPACA_API_KEY` / `_SECRET` / `_PAPER` — must be **paper-trading keys**, not live (different keypair); live requires `_PAPER=false`
- `DC_API_KEY` / `DC_ALLOW_OPEN` — serving auth is fail-closed; unset key ⇒ 503 unless `DC_ALLOW_OPEN=true` (local dev)
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
make dc-test

# go-live gate: full suite + paper smoke (must be clean before flipping live)
make dc-preflight-live

# end-to-end smoke against real OpenAI + Alpaca paper
make dc-smoke-paper

# Colab training (one command does everything)
make dc-train-all                                                  # auto-detects Drive
make dc-train-all OUTPUT_DIR=/content/drive/MyDrive/dc_outputs

# backtest (no API keys)
python tools/backtest.py --bars-dir data/bars/

# Halt (local)
touch KILL_SWITCH                # blocks all orders, all routines (repo-root anchored)
rm KILL_SWITCH                   # resume
# Halt (cloud routines): set DC_HALT=true or TRADING_MODE=halt in the cloud env —
# reaches the next headless run regardless of git/branch state. Gate fails closed.

# Forecaster router (Phase 9)
python tools/forecast.py --input crypto.json --model rule-based   # default
python tools/forecast.py --input crypto.json --model ensemble --news-input news.json
python tools/forecast.py --input crypto.json --model api          # calls serving/ FastAPI
```

## Going live (paper → live)

The posture is **code-complete + paper-validated, then flip on a deliberate decision** — never
flip fresh code straight to real money. The risk gates are code-enforced and fail closed, but
validate behavior in paper first.

**1. Gate — must be clean:**
```bash
make dc-preflight-live          # full suite + paper smoke (real OpenAI + Alpaca paper)
```
Then let the routines run in **paper** for a stretch (at least a few cron cadences) and confirm
`TRADE-LOG.md` looks sane (sizing, buckets, no surprise blocks).

**2. Flip — set these in the cloud environment** (https://claude.ai/code/environments):
```
TRADING_MODE=live
DAILY_DECISION_AUTHORIZE_LIVE=true
DC_MAX_NAV_USD=500          # hard ceiling — START SMALL; place_order blocks any live order above it
ALPACA_PAPER=false          # live equities keypair (DIFFERENT from the paper keypair)
BINANCE_TESTNET=false       # live crypto
```
Per-order, the agent still needs `--allow-buy` (decision/intraday routines pass it; position-mgmt
never does) and `--confirm-live`. All four live conditions are enforced in `place_order.py`.

**3. Emergency stop (any time):** set `DC_HALT=true` (or `TRADING_MODE=halt`) in the cloud env —
it reaches the next headless run regardless of git/branch state, and the gate fails closed if it
can't confirm. Locally, `touch KILL_SWITCH` (repo-root anchored).

**Two things that bound the risk:**
- `DC_MAX_NAV_USD` caps blast radius — a bug can lose at most a bounded amount. Raise it only
  after you've watched live behavior, deliberately.
- Live broker keypairs are **separate** from paper keys; real money is only reachable once you
  paste the live keys AND set all of the above. Until then the system physically can't touch it.

See the per-bucket NAV guidance under **Money math** — paper/€100 = shakedown, €3,500+ = the
system can clear its own costs.

### API keys you need

Full template + signup links are in `.env.sample`. Minimum to actually trade + research:

| Key | For | Required? | Cost |
|---|---|---|---|
| `ALPACA_API_KEY` / `_SECRET` | US equities (Alpaca). **Paper** keypair for paper; a **separate LIVE** keypair for live (`ALPACA_PAPER=false`). | Required for equities | Free |
| `BINANCE_API_KEY` / `_SECRET` | Crypto (Binance). **Testnet** keys for paper; live keys for live (`BINANCE_TESTNET=false`). | Required for crypto | Free |
| `OPENAI_API_KEY` | News / signal engine (`fetch_news.py`, search-preview model). The research + decision routines lean on it. | Effectively required | ~$0.04 / call |
| `FINNHUB_API_KEY` | Earnings calendar | Recommended | Free (60/min) — finnhub.io/register |
| `FRED_API_KEY` | Macro + FedWatch | Recommended | Free |
| `CRYPTOQUANT_API_KEY` | On-chain crypto | Optional (falls back to Binance volume) | Free tier |
| `COINGECKO_API_KEY` | Higher CoinGecko rate limits | Optional (works without) | Free |
| `PERPLEXITY_API_KEY` | Fallback news provider | Optional | Paid tier |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Trade / halt alerts | Optional (silent no-op if unset) | Free |
| `DC_API_KEY` | Auth for the `serving/` inference service | Only if you run `--model api` | n/a |
| `GLASSNODE` / `SANTIMENT` / `ALPHAVANTAGE` `_API_KEY` | Extra signal streams | Optional | Free tiers |

Bare minimum to go live on one venue: that venue's broker keypair + `OPENAI_API_KEY`. Bitfinex
keys are not used — it's disabled in the live path (audit B7).

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
- Per-position cap is 5% NAV (existing holding counts); sector cap 30%; cash floor 10%; gross leverage ≤ 1.0× — all enforced in `check_limits`.
- Daily DD breaker 4%, weekly 8% — `tools/check_drawdown.py` arms KILL_SWITCH (wired; fail-closed if NAV unreadable).
- Stop-loss -8%, take-profit +20%.

## Money math

To clear fixed costs (~€700/yr: Anthropic Pro + OpenAI search) at a realistic 20% annual return, **NAV ≥ €3,500**. €5,000+ is where the system contributes meaningfully. €100 = paper-only; €1,000–2,000 = tuition; €10,000+ = the strategy starts paying for itself.

## Routine session ergonomics

Each cloud routine creates a `claude/<adj-noun>` branch per run. `persist_logs.sh` pushes log diffs to that branch (sandbox can't push to other branches). Merge those branches into master periodically — they're append-only, no conflicts.

If a routine ever fails persistently: check (1) GitHub repo cloned via `/web-setup` or Claude GitHub App; (2) cloud env has setup script + env vars; (3) Network allowlist includes all required hosts; (4) `.claude/settings.json` allow-list includes the bash commands used by routine prompts.
