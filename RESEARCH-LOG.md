# RESEARCH-LOG.md

Append-only research notes. Written by `tools/journal.py research`. Do not edit prior entries.

---

## 2026-05-09 10:50 UTC — smoke test

- system online\n- tools layer initialized\n- this entry verifies journal.py append

## 2026-05-09 10:54 UTC — heartbeat

alive at 2026-05-09T10:54:26Z; guardrails OK; rank+forecast OK

## 2026-05-09 15:24 UTC — heartbeat

make dc-s06-heartbeat: guardrails OK, rank+forecast OK

## 2026-05-09 21:49 UTC — 22:00 UTC daily-decision — crypto pass

- Universe: BTC,ETH,SOL,AVAX,LINK,ATOM,NEAR,INJ,FET,RNDR,TIA,JUP
- Ranker top 6: JUP(0.768), TIA(0.634), NEAR(0.536), INJ(0.507), FET(0.506), RNDR(0.493)
- Forecast model: rule-based
- Gate results (rank>=0.55 AND conf>=0.60):
  - JUP: rank=0.768 conf=1.00 direction=long → PASS both gates
  - TIA: rank=0.634 conf=0.40 direction=flat → FAIL confidence
  - NEAR: rank=0.536 conf=0.40 direction=flat → FAIL confidence
  - INJ/FET/RNDR: conf=0.40 → FAIL confidence
- JUP signal rationale: momentum 24h=+1.31% 7d=+38.41%
- risk_check JUP buy 100 @ 0.248796: OK
- place_order failed: ccxt not installed (RuntimeError) — order not submitted
- Candidates placed: 0 / cap 2 for this slot
