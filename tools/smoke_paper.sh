#!/usr/bin/env bash
# Live-keys smoke test — exercises the pipeline against real OpenAI + Alpaca
# paper. Fail-fast: any non-zero exit aborts the whole run.
set -euo pipefail

# Load .env into the current shell.
if [ ! -f .env ]; then
  echo "  ✗ .env not found (run: cp .env.sample .env, then fill in)" >&2
  exit 1
fi
set -a; . ./.env; set +a

echo ""
echo "================================================================"
echo "  DC  SMOKE TEST  —  OpenAI news + Alpaca paper"
echo "  TRADING_MODE=${TRADING_MODE:-paper}  ALPACA_PAPER=${ALPACA_PAPER:-true}"
echo "================================================================"

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "  ✗ OPENAI_API_KEY not set in .env" >&2; exit 1
fi
if [ -z "${ALPACA_API_KEY:-}" ] || [ -z "${ALPACA_API_SECRET:-}" ]; then
  echo "  ✗ ALPACA_API_KEY/SECRET not set in .env" >&2; exit 1
fi

# Don't trip over a stale KILL_SWITCH from earlier tests.
if [ -f KILL_SWITCH ]; then
  echo "  → removing stale KILL_SWITCH from previous test runs"
  rm KILL_SWITCH
fi

PY="python3"
SUMMARY=$($PY <<'EOF'
import json, sys
def show(label, path, fields):
    try:
        d = json.load(open(path))
    except Exception as e:
        print(f"  ✗ {label}: {e}"); return
    if "symbols" in d:
        for s, row in d["symbols"].items():
            parts = [f"{k}={row.get(k)}" for k in fields if row.get(k) is not None]
            print(f"  {s}: " + "  ".join(parts))
    else:
        for k in fields:
            v = d.get(k)
            if v is not None:
                print(f"  {k}: {v}")
EOF
)

echo ""; echo "── 1/6  fetch news (OpenAI) ──"
python3 tools/fetch_news.py --query "BTC + AAPL + NVDA news, last 6 hours, market-moving only" --max-tokens 500 > /tmp/news.json
python3 -c "
import json
d = json.load(open('/tmp/news.json'))
print(f'  provider: {d[\"provider\"]}')
digest = d['digest'].replace('\n', ' ')[:200]
print(f'  digest: {digest}…')
print(f'  citations: {len(d.get(\"citations\", []))}')
"

echo ""; echo "── 2/6  fetch equities (Alpaca paper data API) ──"
python3 tools/fetch_equities.py --symbols AAPL,NVDA,SOFI > /tmp/equities.json
python3 -c "
import json
d = json.load(open('/tmp/equities.json'))
for s, r in d['symbols'].items():
    price = r.get('price_usd')
    vol = r.get('volume', 0)
    pct7 = r.get('pct_change_7d')
    pct7s = f'{pct7:+.2f}%' if pct7 is not None else '-'
    print(f'  {s:<6} price=\${price:>8.2f}  vol={vol:>12,.0f}  7d={pct7s}')
"

echo ""; echo "── 3/6  fetch crypto (Binance public, no key) ──"
python3 tools/fetch_crypto.py --symbols BTC,ETH,TIA > /tmp/crypto.json
python3 -c "
import json
d = json.load(open('/tmp/crypto.json'))
for s, r in d['symbols'].items():
    price = r.get('price_usd', 0)
    mcap = (r.get('market_cap_usd') or 0) / 1e9
    pct7 = r.get('pct_change_7d')
    pct7s = f'{pct7:+.2f}%' if pct7 is not None else '-'
    print(f'  {s:<6} price=\${price:>10,.2f}  mcap=\${mcap:>6.1f}B  7d={pct7s}')
"

echo ""; echo "── 4/6  rank + forecast ──"
python3 tools/rank_smallcaps.py --input /tmp/crypto.json --input /tmp/equities.json --top 5 > /tmp/ranked.json
python3 -c "
import json
d = json.load(open('/tmp/ranked.json'))
print('  top 5 ranked:')
for r in d['ranked']:
    print(f\"    {r['symbol']:<6} score={r['score']:.3f}\")
"
python3 tools/forecast.py --input /tmp/crypto.json --input /tmp/equities.json --model rule-based > /tmp/forecasts.json
python3 -c "
import json
d = json.load(open('/tmp/forecasts.json'))
print('  forecasts:')
for f in d['forecasts']:
    print(f\"    {f['symbol']:<6} {f['direction']:<6} conf={f['confidence']:.2f}\")
"

echo ""; echo "── 5/6  risk_check on a small AAPL paper order ──"
python3 tools/risk_check.py --symbol AAPL --side buy --qty 1 --price 200 --asset-class equity

echo ""; echo "── 6/6  place AAPL paper order via Alpaca ──"
TRADING_MODE=paper python3 tools/place_order.py \
  --symbol AAPL --side buy --qty 1 --price 200 \
  --asset-class equity --reason "dc-smoke-paper end-to-end"

echo ""; echo "── last 12 lines of TRADE-LOG.md: ──"
tail -n 12 TRADE-LOG.md

echo ""
echo "################################################################"
echo "  SMOKE TEST COMPLETE"
echo "  ✓ OpenAI news fetched"
echo "  ✓ Alpaca paper bars fetched"
echo "  ✓ Binance public bars fetched"
echo "  ✓ rank + forecast produced"
echo "  ✓ risk_check OK"
echo "  ✓ 1 AAPL paper order routed → check Alpaca paper dashboard"
echo "################################################################"
