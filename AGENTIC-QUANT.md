# AGENTIC-QUANT.md

Why this system isn't a list ranker, and what it is instead.

## Data layer (six-stream digest)

Every research routine reads **six parallel signal streams** before identifying themes. A theme is "active" only when supported by ≥ 2 distinct source-types — multi-source confirmation is the bar.

| Stream | Tool | Source | Tier |
|---|---|---|---|
| News | `tools/fetch_news.py` | OpenAI search | S |
| Insider transactions | `tools/fetch_insider.py` | OpenInsider (SEC Form 4) | S |
| Material events (8-K) | `tools/fetch_filings.py` | SEC EDGAR | S |
| Earnings calendar | `tools/fetch_earnings.py` | Finnhub (or yfinance fallback) | S |
| On-chain crypto | `tools/fetch_onchain.py` | CryptoQuant (or Binance volume z-score) | S |
| Cross-asset regime | `tools/correlation_matrix.py` | yfinance + Binance public | S |
| Fed-funds implied moves | `tools/fetch_fedwatch.py` | yfinance ZQ=F + FRED target rate | S |
| Hidden gems scanner | `tools/scan_hidden_gems.py` | CoinGecko top 250 | A |

All news-text fetchers (insider, 8-K summaries, news) pass through `deepCommodity/guardrails/sanitize.sanitize_news` before the agent reads them — prompt-injection patterns redacted.

## The shift

**Old** (mechanical-momentum): a fixed 12-symbol crypto list + 9-symbol equity list, ranked by `momentum × log_inverse_mcap × volume`. Every run surfaces the same kind of small-cap momentum candidate (JUP, TIA, INJ). The "agent" is a thin wrapper around a ranker.

**New** (theme-driven): the LLM is the alpha generator. It reads news, identifies *active themes*, maps each theme to **second-order beneficiaries** through cross-sector reasoning (e.g. AI capex → power utilities → uranium miners), and uses technicals only to validate.

The mechanical ranker stays — but only for the **hidden gem** lane, where it scans CoinGecko top 250 dynamically and hands candidates to the agent for thesis writing. It never decides anchor or theme positions.

## The three buckets

| Bucket | Source | Gate | Daily cap |
|---|---|---|---|
| **Anchor** | static list (BTC, ETH, SPY, QQQ, AAPL, MSFT, NVDA, GOOGL, META, AMZN, BRK.B) | forecast confidence ≥ 0.55 | 1 |
| **Theme** | symbols pulled from `themes.yaml` for **agent-identified active themes** | ≥ 2 evidence citations from news AND forecast confidence ≥ 0.50 | 2 |
| **Hidden gem** | dynamic CoinGecko scan (mcap $30M–$500M, +30d ≥ 30%, vol ≥ $5M, not in static universe) | rank score ≥ 0.65 AND agent thesis ≥ 100 chars citing news | 1 |

Total: **3 new positions/day**, mixed across buckets. Same total cap as before — just much more diverse composition.

## Theme detection happens inline in the agent

No separate OpenAI call. The agent (Claude, running the routine) reads:
1. The news digest (`/tmp/news.json` from `tools/fetch_news.py`)
2. `deepCommodity/universe/themes.yaml`

…and judges per theme: *does the news provide ≥ 2 distinct evidence points for this theme right now?* If yes, the theme is **active** and its symbols become candidates. If no, the theme is dropped.

The agent must cite the evidence (specific news bullets) in the journal entry. This is the integrity contract: themes don't fire on vibes.

## Per-bucket thesis requirements

When `place_order.py` is called, `--reason` must contain:

| Bucket | Minimum | Format |
|---|---|---|
| Anchor | free text | "anchor: <signal>" — momentum direction is enough |
| Theme | ≥ 50 chars | "theme=<name>: <thesis>; cited <evidence>" |
| Hidden gem | ≥ 100 chars | "gem=<symbol>: <thesis>; description=<…>; cited <news>" |

The thesis goes into TRADE-LOG.md and stays there forever. Weekly review attributes PnL by bucket and theme.

## How to add a new theme

1. Edit `deepCommodity/universe/themes.yaml`.
2. Add the theme key (lowercase + underscore) and ≥ 3 symbols.
3. Run `make dc-test` — `test_universe.py` validates schema.
4. Commit. The agent picks it up on next routine fire.

The weekly-review routine **proposes** new themes (in the proposed-edits block) but does NOT auto-merge — operator merges manually.

## How a routine actually decides

The new `daily-decision` flow:

1. Bootstrap (sync_state, halt check, recover state).
2. Fetch news → `/tmp/news.json`.
3. Read `themes.yaml`.
4. **Reason**: which themes are active right now? Cite evidence.
5. **Build candidate set per bucket**:
   - anchors: always — fetch all 11
   - theme: for each active theme, pull 3-5 symbols from the YAML
   - gem: `tools/scan_hidden_gems.py --max 5`
6. Fetch market data + forecasts for the union of candidates.
7. **Apply per-bucket gate** to each candidate:
   - anchor: forecast confidence ≥ 0.55
   - theme: theme_active AND forecast confidence ≥ 0.50
   - gem: rank_score ≥ 0.65 AND agent thesis ≥ 100 chars
8. Cap: 1 anchor + 2 themes + 1 gem; total ≤ 3.
9. For each surviving candidate: risk_check → place_order with thesis in `--reason`.

## Why this is "agentic"

In the new architecture, when `JUP` shows up as a candidate, the agent has to answer: *which active theme does Jupiter participate in, or what news justifies a hidden-gem buy?* If the answer is "high momentum" → gem lane requires a real thesis citing news. If there's no news driving it, the position doesn't get opened.

Compare to before: high momentum + small cap = auto-buy. The "agent" had nothing to reason about.

## What stays unchanged

- All risk limits (5% per position, 30% sector, 4%/8% drawdown breakers, KILL_SWITCH).
- Order routing, broker adapters, paper-vs-live gates.
- Trained transformer (Phase 5+) plugs into `tools/forecast.py` regardless of bucket.
- All four routine cadences (heartbeat, hourly research, daily decision, weekly review).
