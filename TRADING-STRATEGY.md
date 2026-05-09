# TRADING-STRATEGY.md

Source of truth for the agent's universe, position sizing, and risk limits. Edited only by the weekly review (proposed) + manual merge.

## Universe

### Crypto (Binance)
- **Tier 1 (large cap, anchor):** BTC, ETH
- **Tier 2 (mid cap, $1B–$30B):** SOL, AVAX, LINK, ATOM, NEAR
- **Tier 3 (small cap, $100M–$1B):** INJ, FET, RNDR, TIA, JUP

### US Equities (Alpaca)
- **Tier 1 (mega cap, anchor):** AAPL, MSFT, NVDA
- **Tier 2 (mid cap, $2B–$30B):** SOFI, PLTR, RKLB
- **Tier 3 (small cap, $300M–$2B):** IONQ, RXRX, ASTS

Tier 3 is where the small-cap upside thesis is expressed. The ranker (`rank_smallcaps.py`) is biased toward tier 3 by design.

## Ranking weights (consumed by `rank_smallcaps.py`)

```yaml
momentum_weight: 0.4         # 7d return z-score
mcap_weight: 0.4             # log_inverse market cap
volume_weight: 0.2           # 24h volume / 30d avg volume
news_sentiment_weight: 0.0   # disabled in v1, enable after sentiment validation
```

## Position sizing

- **Per-position cap:** 5% of total portfolio NAV.
- **Tier sleeves:** ≤40% NAV in tier 1, ≤40% NAV in tier 2, ≤20% NAV in tier 3.
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

## Forecast threshold

- Minimum forecast confidence to trade: **0.60**.
- Minimum rank score (composite from `rank_smallcaps.py`): **0.55**.
- Both must hold simultaneously.

## Cadence

- Hourly research: every hour 00–23 UTC (lower-priority slots may be skipped if last research is <30 min old).
- Daily decision: 14:00 UTC (≈30 min after US open) for equities + crypto; 22:00 UTC for crypto-only second pass.
- Weekly review: Sunday 18:00 local.

## Mode

- `TRADING_MODE` env: `paper` | `live`. Default `paper`.
- Live orders additionally require `--confirm-live` flag at the CLI.
