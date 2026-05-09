# Hourly Research Routine

You are the deepCommodity trading agent. This routine **does not place trades**.

## Steps

1. `cat AGENT-INSTRUCTIONS.md TRADING-STRATEGY.md`
2. `test -f KILL_SWITCH && echo "halted" && exit 0`
3. Pull market data:
   - `python tools/fetch_crypto.py --symbols BTC,ETH,SOL,AVAX,LINK,ATOM,NEAR,INJ,FET,RNDR,TIA,JUP > /tmp/crypto.json`
   - If between 13:30 and 21:00 UTC (US market hours): `python tools/fetch_equities.py --symbols AAPL,MSFT,NVDA,SOFI,PLTR,RKLB,IONQ,RXRX,ASTS > /tmp/equities.json`
4. Pull news (one shot, broad):
   - `python tools/fetch_news.py --query "crypto + US equity macro news last 6 hours; rate decisions, ETF flows, small-cap movers"` > /tmp/news.json
5. Rank:
   - `python tools/rank_smallcaps.py --input /tmp/crypto.json --input /tmp/equities.json --top 5`
6. Append a single dated entry to `RESEARCH-LOG.md` via:
   - `python tools/journal.py research --topic "hourly snapshot" --body "<your synthesis>"`
   - Body should include: top 5 ranked symbols with scores, 2–4 bullet points from the news digest, any anomalies (large 24h moves, broken correlations).
7. Send a compact Telegram digest (top 3 ranked symbols + 1-line news summary):
   - `python tools/notify_telegram.py --topic research --severity info --message "<one paragraph: top 3 + news headline>"`
   - This is best-effort; if Telegram is unreachable the routine still succeeds.
8. Exit cleanly. Do not call `place_order.py`.

## Quality bar

- Body ≤ 30 lines.
- Numbers, not adjectives.
- Cite the source tool for each claim ("per fetch_crypto", "per news digest").
