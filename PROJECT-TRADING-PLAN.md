# PROJECT-TRADING-PLAN.md

## Mission

Operate an agentic trader where Claude Code itself is the agent — driven by scheduled routines, with markdown logs as durable memory and python tools for I/O.

## KPIs

| Metric | v1 target (paper) | v2 target (live) |
|--------|-------------------|------------------|
| Hit rate | ≥55% | ≥55% |
| Sharpe (90d) | ≥1.0 | ≥1.2 |
| Max drawdown | ≤8% | ≤8% |
| Tool-call success rate | ≥98% | ≥98% |
| Routine completion (no halts) | ≥95% | ≥99% |
| Avg routine wall-clock | ≤120s | ≤120s |

## Phases (gating)

- **Phase 0 — foundation fix.** ✅ done.
- **Phase 1 — markdown state + tools.** In progress.
- **Phase 2 — routines + scheduling.** Gate: every tool has a passing standalone smoke test.
- **Phase 3 — paper-trading shakedown.** Gate: 7 consecutive days of clean routine runs in paper mode.
- **Phase 4 — go-live.** Gate: code review of `place_order.py` + full guardrails stack; $100 sanity trade verified on each broker.
- **Phase 5 — price transformer (specialist).** Train a transformer on OHLCV bars across the full universe (multi-asset attention). Ships as `deepCommodity/model/price_transformer.py` with `tools/forecast.py --model price-transformer`. Gate: ≥5% directional accuracy lift over LSTM in backtest.
- **Phase 6 — order-flow transformer (specialist).** Train a separate transformer on order-book snapshots + trade-tape from Binance/Bitfinex (millisecond/second resolution). Ships as `deepCommodity/model/orderflow_transformer.py`. Gate: ≥5% lift on short-horizon (≤1h) directional calls vs price-only.
- **Phase 7 — news / sentiment model (specialist).** Embedding-based classifier or small LM scoring sanitized Perplexity output → bull / bear / neutral with confidence. Ships as `deepCommodity/model/news_model.py`. Gate: meaningful Sharpe contribution when added to the ensemble.
- **Phase 8 — fused multi-modal transformer.** Modular shared trunk: each Phase 5–7 specialist's encoder head feeds into a common prediction layer. Training runs end-to-end, but each encoder retains its standalone weights so it can fall back to specialist mode if a modality's data stream is degraded. Ships as `deepCommodity/model/fused_transformer.py`. Gate: ≥5% directional accuracy lift over the **best specialist** (not just LSTM); robust to one modality missing (eval with each input stream zeroed in turn).
- **Phase 9 — ensemble & routing.** `tools/forecast.py` becomes a router that can call any specialist, the fused model, or an explicit ensemble (mean / weighted / stacking). Strategy file picks per-symbol which forecaster to trust. Specialists remain first-class — agent may consult `--model price-transformer` directly when the order book is stale or news is sparse.

## Modeling architecture (Phases 5–9 at a glance)

```
                     ┌────────────────────────────────────────┐
                     │  tools/forecast.py  (router)           │
                     │  --model {price | orderflow | news |   │
                     │            fused | ensemble}           │
                     └──────────┬─────────────────────────────┘
                                │
        ┌───────────────────────┼─────────────────────────┐
        ▼                       ▼                         ▼
┌──────────────────┐   ┌────────────────────┐   ┌────────────────┐
│ price_transformer│   │ orderflow_transfor.│   │  news_model    │
│ (OHLCV bars,     │   │ (book + trades,    │   │ (sanitized     │
│  multi-asset)    │   │  ms/s resolution)  │   │  Perplexity)   │
└────────┬─────────┘   └─────────┬──────────┘   └───────┬────────┘
         │ encoder head          │ encoder head         │ encoder head
         └───────────────────────┼──────────────────────┘
                                 ▼
                      ┌──────────────────────┐
                      │ fused_transformer    │
                      │ (shared prediction   │
                      │  trunk; modalities   │
                      │  degrade gracefully) │
                      └──────────────────────┘
```

Each specialist is independently trained and independently invocable. The fused model adds a shared trunk on top of their encoder heads — it does not replace them. The agent (via `tools/forecast.py`) picks which to call per routine; the strategy file declares per-symbol defaults.

## Out of scope (explicitly)

- Options, futures, leverage > 1×.
- Margin trading.
- Pairs / arb / market-making.
- Non-US equities.
- Stablecoin yield strategies.
