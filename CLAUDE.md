# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture: Claude Code IS the agent

`deepCommodity` is an agentic trader where **Claude Code itself is the agent**. There are no agent classes in Python — instead:

- **State** lives in markdown files at the repo root (`AGENT-INSTRUCTIONS.md`, `TRADING-STRATEGY.md`, `RESEARCH-LOG.md`, `TRADE-LOG.md`, `WEEKLY-REVIEW.md`, `PROJECT-TRADING-PLAN.md`). Logs are append-only.
- **Tools** are CLI scripts in `tools/` that the agent invokes via Bash. They import the `deepCommodity/` package for actual logic.
- **Routines** in `.claude/routines/*.md` are prompt files fired by cron (`schedule` skill) via headless `claude -p`.
- **Guardrails** are layered: KILL_SWITCH file, TRADING_MODE env, hard-coded ceilings in `deepCommodity/guardrails/limits.py`, circuit breaker, news sanitization, append-only logs, allowlisted bash in `.claude/settings.local.json`.

The agent has no long-term memory. Every routine starts fresh, reads markdown to recover state, calls tools, writes markdown.

## When extending

1. Read `AGENT-INSTRUCTIONS.md` and `TRADING-STRATEGY.md` first — these define the operating contract.
2. New data sources → new `tools/fetch_*.py` script + (optional) helper in `deepCommodity/sourcing/`.
3. New broker → new `deepCommodity/execution/<name>_adapter.py` implementing `BrokerAdapter`; route from `get_broker()`.
4. New risk rule → add to `HARD_LIMITS` in `deepCommodity/guardrails/limits.py` and to `TRADING-STRATEGY.md`. Hardcoded ceiling beats markdown if markdown is looser.
5. New routine → markdown file in `.claude/routines/`, registered via the `schedule` skill.

## Commands

```bash
make install_requirements   # pip install -r requirements.txt
make install                # pip install . -U
make test                   # coverage + pytest (46 tests, 97% line coverage on safety code)
make black                  # format
make check_code             # flake8

# Backtest (no API keys required):
python tools/backtest.py --bars-json data/history.json
python tools/backtest.py --bars-dir data/bars/   # one CSV per symbol

# Smoke-test individual tools (require .env populated):
python tools/fetch_crypto.py --symbols BTC,ETH,SOL
python tools/fetch_equities.py --symbols AAPL,SOFI
python tools/fetch_news.py --query "BTC macro"
python tools/rank_smallcaps.py --input crypto.json --input equities.json
python tools/forecast.py --input crypto.json
python tools/risk_check.py --symbol BTC --side buy --qty 0.001 --price 60000 --asset-class crypto
TRADING_MODE=paper python tools/place_order.py --symbol BTC --side buy --qty 0.001 \
    --price 60000 --asset-class crypto --reason "smoke test"

# Routines (headless):
claude -p "$(cat .claude/routines/hourly-research.md)"
claude -p "$(cat .claude/routines/daily-decision.md)"
claude -p "$(cat .claude/routines/weekly-review.md)"

# Halt:
touch KILL_SWITCH         # blocks all orders
rm KILL_SWITCH            # resume (manual, deliberate)
```

## Environment

Copy `.env.sample` → `.env` (gitignored). The `.gitignore` is fail-closed for credentials: `.env`, `.env.*`, `*.key`, `*.pem`, `secrets.*`, `service-account*.json`, `id_rsa*`, `.netrc`, `.vault-token`, etc. — only `.env.sample` / `.env.example` / `.env.template` are tracked.

Optional belt-and-suspenders pre-commit hook:
```bash
git config core.hooksPath .githooks
```
The hook scans staged diffs for patterns like `sk-…`, `AKIA…`, `ghp_…`, PEM private keys, and `<BROKER>_API_KEY=<non-empty>` assignments and aborts the commit if any are found.

Required env vars:

- `TRADING_MODE` — `paper` (default) or `live`. Live additionally requires `--confirm-live` on every `place_order.py` invocation.
- `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `BINANCE_TESTNET` (default true)
- `ALPACA_API_KEY`, `ALPACA_API_SECRET`, `ALPACA_PAPER` (default true)
- `PERPLEXITY_API_KEY` — for `tools/fetch_news.py`
- `FRED_API_KEY` — for `tools/fetch_macro.py`
- `COINGECKO_API_KEY`, `ALPHAVANTAGE_API_KEY` — optional

## Hard rules (apply to every routine)

1. Never call `place_order.py` without first calling `risk_check.py` and verifying it returned exit 0.
2. Never call `place_order.py` if `KILL_SWITCH` exists.
3. Use `tools/journal.py` for `RESEARCH-LOG.md` and `TRADE-LOG.md` — never edit prior entries.
4. `TRADING-STRATEGY.md` is the source of truth for universe + limits. Edit only via weekly review proposals + manual merge.
5. No external commands beyond the allowlist in `.claude/settings.local.json`.
6. Live trading requires both `TRADING_MODE=live` AND `--confirm-live` flag.

## Forecaster router (Phase 9)

```bash
# Default (rule-based; works with no models trained):
python tools/forecast.py --input crypto.json

# Specialists (require their own checkpoint at data/models/):
python tools/forecast.py --input crypto.json --model price       # data/models/<SYM>.pt
python tools/forecast.py --input crypto.json --model orderflow   # data/models/<SYM>.orderflow.pt
python tools/forecast.py --input crypto.json --model news --news-input news.json

# Ensemble: combines rule-based + whichever specialists have checkpoints + news (if --news-input):
python tools/forecast.py --input crypto.json --model ensemble --news-input news.json
```

The ensemble degrades gracefully — missing checkpoints / digest reduce contributors but never crash.

## Training (Phase 5+)

**One command does everything:**
```bash
make dc-train-all                                      # auto-detects Drive on Colab
make dc-train-all OUTPUT_DIR=/path/to/outputs          # explicit override
make dc-train-all-fast                                 # smoke test, ~10 min on T4
```

`OUTPUT_DIR` auto-resolves: if `/content/drive/MyDrive` exists (Colab with Drive mounted), defaults to `/content/drive/MyDrive/deepCommodity_outputs`; on a laptop falls back to `./data`.

**On Colab — 4 cells (`notebooks/train_on_colab.ipynb`):**
```python
!git clone -b master --single-branch https://github.com/<you>/deepCommodity.git
%cd deepCommodity
from google.colab import drive; drive.mount('/content/drive')
!make dc-train-all OUTPUT_DIR=/content/drive/MyDrive/deepCommodity_outputs
```

What `dc-train-all` does (7 stages):
1. fetch crypto OHLCV (Binance public)
2. fetch equity OHLCV (yfinance)
3. fetch crypto order flow
4. train price transformer per crypto symbol
5. train price transformer per equity symbol
6. train order-flow transformer per crypto symbol
7. backtest crypto + equity baselines

For finer control: `dc-pipeline*` and `dc-s01` … `dc-s06` stages remain runnable individually. Tunables (`SYMBOLS`, `EQUITY_SYMBOLS`, `DAYS`, `SEQ_LEN`, `HORIZON`, `EPOCHS`, `BATCH_SIZE`, `LR`) override on the make command line.

`TrainConfig.device` auto-selects cuda → mps → cpu, so the same code runs on Colab GPU, Apple Silicon, or a vanilla laptop. Inference (`predict_proba`) runs fine on CPU — only training needs the GPU.

## Backtest harness

`deepCommodity/backtest/` is a broker-agnostic walk-forward engine. Inputs are per-symbol bar history; the forecaster is any `(window) -> [Forecast]` callable. The engine reuses `guardrails/limits.check_limits` so the backtest's risk gating is **identical** to live's — what blocks in backtest will block in production.

When Phase 5+ models arrive, they plug in as a forecaster callable. Compare them against `rule_based` (in `deepCommodity/backtest/forecasters.py`) on the same bar set; the gate to ship is ≥5% directional-accuracy lift in backtest.

## Reuse map

- Sourcing helpers: `deepCommodity/sourcing/api_sourcing_boilerplate.py` (FRED, Alpha Vantage, CoinGecko range, technical indicators).
- LSTM model (Phase 5 forecaster swap-in): `deepCommodity/model/LSTM.py`.
- Time-series windowing: `deepCommodity/sourcing/preprocessing.py` (`get_folds`, `get_X_y_strides`).
- BigQuery sink: `deepCommodity/manager/manager.py:upload_dataframe_to_bigquery`.

## Phase status

- Phase 0 — foundation fixes — **done**.
- Phase 1 — markdown state + tools — **done** (this commit).
- Phase 2 — routines + cron registration — routines authored; cron registration via `/schedule` is a manual step.
- Phase 3 — paper-trading shakedown — pending.
- Phase 4 — go-live — gated, manual.
- Phase 5 — price transformer specialist (`deepCommodity/model/price_transformer.py`, `tools/train_price_transformer.py`) — **architecture done; awaits Colab training**.
- Phase 6 — order-flow transformer specialist (`deepCommodity/model/orderflow_transformer.py`, `tools/fetch_orderflow.py`) — **architecture done; awaits trade-tape pull + Colab training**.
- Phase 7 — news/sentiment model (`deepCommodity/model/news_model.py`) — **rule-based backend ready**; sklearn + HuggingFace backends opt-in.
- Phase 8 — fused multi-modal transformer (`deepCommodity/model/fused_transformer.py`) — **architecture done; awaits encoders from 5/6**.
- Phase 9 — router (`tools/forecast.py --model {rule-based|price|orderflow|news|fused|ensemble}`) — **wired**; ensemble auto-includes whichever backends have checkpoints + news digest.

## Project conventions worth knowing

- 3-hour bar fold convention from the legacy LSTM pipeline: `FOLD_LENGTH = 8*365*3` (3y), `FOLD_STRIDE = 8*91` (1q), `INPUT_LENGTH = 8*14` (2w), `TRAIN_TEST_RATIO = 0.66`. Reuse if you swap the rule-based forecaster for the LSTM/transformer.
- CSV-cache + last-date-collected pattern in `api_sourcing_boilerplate.py` — preserve for incremental backfills.
- Tools must: read env + args, write JSON to stdout, exit non-zero on hard error.
