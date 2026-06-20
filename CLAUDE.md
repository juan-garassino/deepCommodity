# CLAUDE.md

Guidance for Claude Code working in this repository.

> **Deployment (2026-06-19):** Crypto runs on an always-on GCE VM **`dc-trader`** (e2-micro, Ubuntu 22.04) in **`garassino-ai`** / `europe-west1-b` — *not* `garassino-ml` (which stays show-and-destroy). Verified: Binance egress from europe-west1 returns HTTP 200, not the 451 the Anthropic cloud egress hits. Static IP `dc-trader-ip`, SSH via IAP only (tag `dc-trader`), no service account. `garassino-ai` is the always-on project (career-navigator lives there too), so the trading box fits its posture. Headless Claude via `ANTHROPIC_API_KEY` in `.env`; routines run through `deploy/` (systemd/cron). **CI/CD (paper):** `.github/workflows/ci.yml` gates merges (tests + smoke-import); the VM runs `deepcommodity-selfupdate.timer` (`deploy/selfupdate.sh`) which pulls the deploy branch (`develop`) every 10 min — so **merge to `develop` → on the paper VM within ~10 min**. Live (mainnet) deploy is a future gated `develop→master` Action, not auto. See `deploy/README.md` and workspace root `CLAUDE.md` § "GCP architecture".

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
| `tools/fetch_macro_features.py` | global-macro panel (M2/net-liquidity/DXY/total-cap) → `data/macro/features.csv`, **publication-lag-shifted** (leakage-safe) |
| `tools/build_contextual_dataset.py` | align daily bars + macro (point-in-time) → `data/contextual/dataset.npz` |
| `tools/train_contextual.py` | train the shared-macro contextual transformer → `data/models/contextual.pt` |
| `tools/eval_contextual.py` | walk-forward SHIP/NO-SHIP gate vs rule-based baseline (exit 0 = SHIP) |
| `tools/contextual_alert.py` | Telegram shadow alert from `contextual_signal.json` (regime + biases) |
| `tools/forecast.py --model contextual` | run the contextual model → per-asset weekly+daily dir + regime |
| `tools/fetch_funding.py` | Binance perp funding-rate history → `data/funding/<SYM>.csv` (carry sleeve) |
| `tools/analyze_feature_combos.py` | regime-neutral greedy feature-combo search (which signals combine best, OOS) |
| `tools/backtest_portfolios.py` | backtest the named risk portfolios (L/S + carry) → comparison report |

## Routines on claude.ai/code/routines (cloud cadence)

**24/7 cadence** (Approach A) — passes spread evenly around the clock, optimized for fast reaction
to catalysts. One decision routine handles **both asset classes**: crypto (Binance) always, US
equities (Alpaca, **paper-only** — live is EU-unavailable) when US markets are open (UTC 13–21
weekdays). 3 active routines, ~10/day, under the 15/day budget.

| Routine | Cron (UTC) | Per day | What |
|---|---|---|---|
| `dc decision (24/7)` | `0 */4 * * *` (00/04/08/12/16/20) | 6 | six-stream read (crypto + equities-when-open) → theme detect → trade within bucket caps |
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

**Deployment reality (2026-06-13):** Binance geo-blocks the Anthropic cloud egress (HTTP 451), so
**crypto cannot execute from cloud routines**. Crypto runs on the **VPS** (`deploy/`) in a
Binance-allowed region — Binance reachable, `KILL_SWITCH` is a persistent local file, local `.env`.
If the VPS runs the trading routines, **disable the cloud trading routines** to avoid double-execution.
Cloud routines remain usable for research / equities-paper (non-Binance signal hosts are reachable).
The reliable cloud halt is the `DC_HALT` env var (the gitignored `KILL_SWITCH` file does not propagate
across stateless cloud runs).

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

`deploy/` has a parallel deployment kit (cron + systemd + Telegram alerts on failure) — this is the **required** host for crypto, since Binance geo-blocks the cloud egress (HTTP 451). `deploy/install_remote.sh` does one-shot Ubuntu/Debian provisioning; `deploy/preflight.sh` is the pre-enable gate (claude+auth, Binance 200-not-451, `.env` keys, ccxt/alpaca import — must PASS before any trading timer). The systemd timers (`deepcommodity-{decision,position-mgmt,weekly-review,heartbeat}.timer`) and `crontab.template` both match the live schedule. Headless Claude auth via `CLAUDE_CODE_OAUTH_TOKEN` (subscription, from `claude setup-token`) or `ANTHROPIC_API_KEY` in `.env`.

**Reactive watcher (`deploy/watch_loop.py` + `deepcommodity-watch.service`):** an always-on alternative to the fixed `decision` timer — a continuous daemon that polls prices for free (CoinGecko) and fires a full `decision` pass only on a catalyst (`DC_WATCH_MOVE_PCT` move) or a max-interval floor (`DC_WATCH_MAX_INTERVAL_SEC`), with a `DC_WATCH_MIN_COOLDOWN_SEC` floor. Cheap "always-on agent": Claude/OpenAI spent only on catalysts. Run the watcher service **instead of** `decision.timer` (not both); `position-mgmt`/`weekly-review` stay timers. Cadence knobs are env vars (see `deploy/README.md`).

## Phase status (where each piece sits)

- **Phase 0–4 (foundation, tools, routines, paper-shakedown, go-live)** — all done architecturally; live trading still gated.
- **Phase 5 — price transformer** — architecture done; awaits Colab training. Inference works via `serving/` + `--model api`.
- **Phase 6 — order-flow transformer** — same.
- **Phase 7 — news/sentiment model** — rule-based backend live; sklearn + HuggingFace opt-in.
- **Phase 8 — fused multi-modal** — architecture done; awaits encoders from 5/6.
- **Phase 9 — router** — wired in `tools/forecast.py`. Ensemble degrades gracefully.
- **Phase 10 — six-stream signal layer + position-mgmt routine** — committed; cloud routine prompts ready to deploy.
- **Phase 12 — portfolio research (market-neutral L/S + funding carry)** — `deepCommodity/portfolio/` (sleeves: XS cross-sectional L/S, CARRY funding harvest, DIR regime-directional) + four named **risk portfolios** (`portfolios.yaml`: carry/neutral/directional/beta_lite) with vol targeting + a graduated drawdown ladder + a portfolio backtester (`tools/backtest_portfolios.py`). **Offline research only** — live shorting/leverage needs a signed-guardrails redesign + a Binance perps adapter (Phase B, gated on the backtest). `beta_lite` is long-only and runs on the current guardrails. `make dc-s07-backtest-portfolios`.
- **Phase 11 — macro-contextual forecaster (crypto-first)** — a shared global-macro encoder (M2, net liquidity, DXY, total-crypto-cap) conditions per-asset price encoders → multi-horizon (weekly+daily) direction, trained jointly over BTC/ETH/SOL. `deepCommodity/model/contextual_transformer.py` + `tools/{fetch_macro_features,build_contextual_dataset,train_contextual,eval_contextual}.py`; `forecast.py --model contextual`. **Leakage-safe** (per-series publication lags + train-only norm). Runs in **shadow** (Telegram regime alert via `dc-contextual-signal`) — does **not** size live orders until `dc-train-contextual`'s walk-forward eval beats the rule-based baseline (≥5% acc lift + non-negative PnL edge). Train/infer **off-box** (e2-micro has no torch); equities + serving integration = v2. `make dc-train-contextual`.

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
