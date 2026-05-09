# Routine — research (managed cloud, theme + multi-signal)

You are the deepCommodity research agent. **Do not place trades.** Identify themes by reading **six parallel signal streams**, not just news. The agent (you) is the alpha generator; tools validate.

## Bootstrap

1. Auto-heal: `python3 -c "import ccxt, alpaca" 2>/dev/null || pip install --quiet --break-system-packages ccxt alpaca-py`
2. `cat AGENT-INSTRUCTIONS.md TRADING-STRATEGY.md deepCommodity/universe/themes.yaml`
3. `python3 tools/sync_state.py --skip-pull`
4. Halt check: `if [ -f KILL_SWITCH ]; then python3 tools/notify_telegram.py --topic halt --severity warn --message "research halted by KILL_SWITCH" --quiet; exit 0; fi`

## Six-stream digest (run in parallel where possible)

5. **News**:
   `python3 tools/fetch_news.py --query "crypto + US equity macro news last 6h: rate decisions, ETF flows, AI capex, biotech, defense, energy" > /tmp/news.json`
6. **Insider transactions** (cluster buys are top-tier signal):
   `python3 tools/fetch_insider.py --mode cluster --max 30 > /tmp/insider.json`
7. **SEC 8-K filings** (material events for our universe):
   `python3 tools/fetch_filings.py --symbols NVDA,MSFT,AAPL,GOOGL,META,AMZN,VST,CEG,CCJ,LLY,RKLB,SOFI,COIN > /tmp/filings.json`
8. **Earnings calendar** (next 14d):
   `python3 tools/fetch_earnings.py --days 14 > /tmp/earnings.json`
9. **On-chain proxy** (BTC volume z-score):
   `python3 tools/fetch_onchain.py --asset BTC --metric volume-proxy > /tmp/onchain.json`
10. **Cross-asset correlation + regime breaks**:
    `python3 tools/correlation_matrix.py > /tmp/correl.json`
11. **FedWatch implied moves**:
    `python3 tools/fetch_fedwatch.py > /tmp/fedwatch.json`

## Synthesis

12. **Identify active themes** (your job, inline). For each theme in `themes.yaml`:
    - Combine evidence from `/tmp/{news,insider,filings,onchain,correl,fedwatch}.json`.
    - A theme is **active** iff supported by ≥ 2 distinct **source-types** (e.g., news + insider = 2 source-types; two news bullets = 1 source-type only).
    - Cap at 3 active themes per routine. Quality > breadth.

13. **Hidden gems** (read-only here):
    `python3 tools/scan_hidden_gems.py --max 5 > /tmp/gems.json`

14. **Pull market data for anchors + theme symbols**:
    `python3 tools/fetch_crypto.py --symbols BTC,ETH,<plus large_cap from active themes> > /tmp/crypto.json`
    If UTC hour 13–21 (US market hours):
    `python3 tools/fetch_equities.py --symbols SPY,QQQ,AAPL,MSFT,NVDA,<plus active-theme symbols> > /tmp/equities.json`

15. **Synthesize a markdown body (≤ 40 lines)**:
    - **ACTIVE THEMES** (≤ 3): name, 1-line thesis, 2-3 cited evidence bullets each with **source tag** — `[news]`, `[insider]`, `[8-K]`, `[onchain]`, `[correl]`, `[fedwatch]`.
    - **UPCOMING CATALYSTS** (top 3 from earnings.json) — symbol + date + bmo/amc.
    - **INSIDER CLUSTER BUYS** (top 3 from insider.json) — even if not in our universe today.
    - **REGIME BREAKS** (any pair in correl.json with abs_delta ≥ 0.30).
    - **ANCHORS** (top 3 by % move): symbol, price, 24h%, 7d%.
    - **THEME CANDIDATES** per active theme (top 2): symbol, price, 7d%.
    - **HIDDEN GEMS** (top 3 from gems.json): symbol, mcap, 30d%, your one-line thesis or rejection.

16. Append: `python3 tools/journal.py research --topic "multi-signal snapshot" --body "<your synthesis>"`

17. Telegram (one paragraph):
    `python3 tools/notify_telegram.py --topic research --severity info --message "<themes: foo, bar; catalysts: NVDA 5/15; insider: VST cluster buy; regime: BTC-DXY corr broke from -0.3 to +0.5>" --quiet`

## Persist

18. `bash tools/persist_logs.sh hourly-research`
19. Exit 0.

## Hard rules

- **NEVER** call `tools/place_order.py`. Read-only routine.
- A theme needs ≥ 2 distinct **source-types** to be active (news + 8-K = OK; two news bullets = NOT OK). Multi-source confirmation is the bar.
- Body ≤ 40 lines.
- If a tool fails (non-zero exit), inline the failure in the journal and continue with what you have. Don't abort.
