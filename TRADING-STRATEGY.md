# TRADING-STRATEGY.md

Source of truth for the agent's universe, position sizing, and risk limits. Edited only by the weekly review (proposed) + manual merge.

## Universe

The full tradable universe is defined in **`deepCommodity/universe/themes.yaml`** — the YAML is loaded by the agent every routine and by `tools/scan_hidden_gems.py` (to exclude already-known names from the gem scanner).

Three buckets:

- **Anchors** (always evaluated on momentum) — BTC, ETH, SPY, QQQ, AAPL, MSFT, NVDA, GOOGL, META, AMZN, BRK.B
- **Crypto large cap / mid cap** — top-30-ish crypto majors; large_cap is tradable, mid_cap is research-only and must clear the gem-style thesis gate to qualify
- **Equity themes** — buckets keyed by narrative (`ai_compute`, `ai_power`, `nuclear`, `grid_infra`, `biotech`, `weight_loss`, `space`, `quantum`, `defense`, `crypto_proxy`, `fintech`, `reshoring`, `copper`, `climate`)
- **Hidden gems** (dynamic) — top 250 by mcap from CoinGecko, filtered for $30M ≤ mcap ≤ $500M, +30d ≥ 30%, vol ≥ $5M, not already in the static universe

See **AGENTIC-QUANT.md** for the full rationale.

## Per-bucket gates

| Bucket | Gate | Min thesis (chars in `--reason`) | Daily cap |
|---|---|---|---|
| Anchor | forecast confidence ≥ 0.55 | free text | 1 |
| Theme | ≥ 2 evidence citations from news AND forecast confidence ≥ 0.50 | 50 | 2 |
| Hidden gem | rank score ≥ 0.65 AND forecast confidence ≥ 0.55 | 100 | 1 |

Total cap: **3 new positions per day** (unchanged).

## Ranking weights (used by `tools/rank_smallcaps.py` for the gem lane only)

```yaml
momentum_weight: 0.4         # 7d return z-score
mcap_weight: 0.4             # log_inverse market cap
volume_weight: 0.2           # 24h volume / 30d avg volume
```

## Position sizing

- **Per-position cap:** 5% of total portfolio NAV.
- **Tier sleeves:** ≤40% NAV in anchors, ≤40% NAV in theme positions, ≤20% NAV in gems.
- **Cash floor:** ≥10% NAV always uninvested.
- **Sizing formula:** `position_value = min(per_position_cap, conviction × tier_sleeve_remaining)` where `conviction ∈ [0.3, 1.0]` from forecast confidence.

## Risk limits (enforced by `risk_check.py`; hardcoded ceilings in `deepCommodity/guardrails/limits.py`)

| Limit | Value | Enforced by |
|-------|-------|-------------|
| Max single position % NAV | 5% | risk_check |
| Max sector concentration % NAV | 30% | risk_check |
| Max new positions per day | 3 | risk_check |
| Max daily drawdown before halt | 4% | circuit_breaker |
| Max weekly drawdown before halt | 8% | circuit_breaker |
| Stop-loss per position | -8% from entry | place_order (OCO) |
| Take-profit per position | +20% from entry | place_order (OCO) |
| Max gross leverage | 1.0× (no leverage) | risk_check + adapter |

## Cadence

- Heartbeat: hourly at :03 UTC (canary; no trades).
- Hourly research: hourly at :07 UTC (theme detection + journal entry).
- Daily decision: 14:00 UTC weekdays (US open + 30 min) and 22:00 UTC daily (crypto-only second pass).
- Weekly review: Sunday 18:00 UTC.

## Mode

- `TRADING_MODE` env: `paper` | `live`. Default `paper`.
- Live orders additionally require `DAILY_DECISION_AUTHORIZE_LIVE=true` AND `--confirm-live` flag.
