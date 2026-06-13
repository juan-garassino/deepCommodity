# deepCommodity — 24/7 Crypto Routine Schedule

**Date:** 2026-06-13
**Status:** Approved (design)

## Context
Alpaca live equities are unavailable in the EU, so the near-term focus is **crypto-only on Binance**.
Crypto trades 24/7, which makes the old US-market-hours anchoring (14:00 open / 17:00 intraday /
22:00 close) the wrong frame. We also want to optimize for **signal freshness** — fast to *act* on a
catalyst — within the ~15 cloud-sessions/day cap and the code-enforced 3-trades/day limit.

## Decision (Approach A — "Merged 24/7")
Collapse the 6 differently-shaped routines into **3 active** ones:

| Routine | Cron (UTC) | /day | Role |
|---|---|---|---|
| `dc decision (24/7)` | `0 */4 * * *` | 6 | crypto 6-stream read → theme detect → trade within caps |
| `dc position-mgmt` | `0 3,9,15,21 * * *` | 4 | drawdown breaker + close/trail; never opens |
| `dc weekly review` | `0 18 * * 0` | 0.14 | per-bucket/theme PnL retro |

~10.1 sessions/day. Decision and risk passes interleave every ~2h. Max latency to **act** on a
catalyst ≈ 4h; max ≈ 6h to catch a drawdown. The 3/day cap is code-enforced, so more passes ⇒
faster reaction, not more trades.

Rationale for A over a research+decision split: a separate research routine logs catalysts but
only the *decision* pass acts — so frequent decisions (every 4h) give the best action latency, at
lower OpenAI cost than an 8×/day research cadence, and far simpler (one prompt, no open/close/intraday
variants).

## Components
- **New prompt** `.claude/routines/managed/decision.md` — single crypto-only merged prompt: halt-check
  → six-stream read (news/on-chain/correlation/fedwatch; insider/filings/earnings skipped as
  equity-oriented) → active-theme detection (≥2 source-types) → forecast → bucket gates
  (anchor 0.55 / theme 0.50 / gem 0.65+thesis) → `risk_check` → `place_order … --allow-buy`
  (`--confirm-live` only live) → journal → persist. Anchors = BTC/ETH.
- `position-mgmt.md`, `weekly-review.md`, `heartbeat.md` unchanged (already current).

## Deployment (via /schedule → RemoteTrigger; cannot delete via API)
- **Repurpose** `dc daily decision (open)` → `dc decision (24/7)`, cron `0 */4 * * *`, prompt = decision.md.
- **Create** `dc position-mgmt`, cron `0 3,9,15,21 * * *`, prompt = position-mgmt.md.
- **Refresh** `dc weekly review` prompt from weekly-review.md (cron unchanged).
- **Disable** `dc daily decision (close)`, `dc intraday news`, `dc research (every 3h)` (user deletes in web UI later).
- **heartbeat** stays disabled.
- Model `claude-sonnet-4-6`; paper mode; env from the cloud `deepCommodity` environment.

## Non-goals
Equity routines (revisit when an IBKR adapter exists). Sub-hour cadence (cloud min is 1h).
Going live (separate, deliberate flip).

## Docs to update (same change)
- `CLAUDE.md` routines table → the 3-routine 24/7 cadence.
- `.claude/routines/managed/REGISTER.md` → registration tables + crons to match.
