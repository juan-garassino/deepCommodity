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

## Risk limits (code-enforced through `preflight` → `check_limits`; ceilings in `deepCommodity/guardrails/limits.py`)

Every order — from `risk_check.py` or `place_order.py` — passes the SAME `preflight()` chokepoint, fed by an authoritative broker snapshot (`execution/portfolio.py`). The gate **fails closed**: a broker that can't report state blocks the trade. The per-position cap counts the existing holding (no pyramiding); the daily cap is counted from real fills (per-bucket + total).

| Limit | Value | Enforced by |
|-------|-------|-------------|
| Max single position % NAV (incl. existing holding) | 5% | check_limits |
| Max sector concentration % NAV | 30% | check_limits |
| Max new positions per day (total) | 3 | check_limits (from real fills) |
| Per-bucket daily cap | anchor 1 / theme 2 / gem 1 | check_limits |
| Max gross leverage | 1.0× (no leverage) | check_limits |
| Cash floor | ≥10% NAV | check_limits |
| Max daily drawdown before halt | 4% | circuit_breaker via `tools/check_drawdown.py` (arms KILL_SWITCH) |
| Max weekly drawdown before halt | 8% | circuit_breaker via `tools/check_drawdown.py` |
| Live NAV ceiling | `DC_MAX_NAV_USD` | place_order (live only) |
| Stop-loss per position | -8% from entry | place_order |
| Take-profit per position | +20% from entry | place_order |

## Cadence

- Heartbeat: hourly at :03 UTC (canary; no trades).
- Hourly research: hourly at :07 UTC (theme detection + journal entry).
- Daily decision: 14:00 UTC weekdays (US open + 30 min) and 22:00 UTC daily (crypto-only second pass).
- Weekly review: Sunday 18:00 UTC.

## Mode

- `TRADING_MODE` env: `paper` | `live` | `halt`. Default `paper`.
- Live orders additionally require `DAILY_DECISION_AUTHORIZE_LIVE=true` AND `--confirm-live` flag AND NAV ≤ `DC_MAX_NAV_USD` — all code-enforced.
- Emergency stop: `DC_HALT=true` or `TRADING_MODE=halt` (reaches cloud routines), or a repo-root `KILL_SWITCH` file (local). The halt check fails closed.
