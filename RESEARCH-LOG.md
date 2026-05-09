# RESEARCH-LOG.md

Append-only research notes. Written by `tools/journal.py research`. Do not edit prior entries.

---

## 2026-05-09 10:50 UTC — smoke test

- system online\n- tools layer initialized\n- this entry verifies journal.py append

## 2026-05-09 10:54 UTC — heartbeat

alive at 2026-05-09T10:54:26Z; guardrails OK; rank+forecast OK

## 2026-05-09 15:24 UTC — heartbeat

make dc-s06-heartbeat: guardrails OK, rank+forecast OK

## 2026-05-09 22:11 UTC — 22:00 UTC crypto decision

Routine: 22:00 UTC second daily pass (crypto-only).

**Market context (news digest)**
- BTC: $80,730 +0.55%; ETH: $2,330 +0.59%; SOL: $93.39 +0.94%
- No significant regulatory news or ETF flow events in last 12h
- Mild positive drift across large caps; small caps mixed/slightly negative 24h

**Ranking (top 6 crypto)**
| Symbol | Score | 24h | 7d |
|--------|-------|-----|----|
| JUP    | 0.77  | +0.43% | +37.7% |
| TIA    | 0.64  | -2.17% | +22.6% |
| NEAR   | 0.54  | -0.59% | +20.1% |
| INJ    | 0.52  | -1.15% | +11.2% |
| FET    | 0.51  | -1.19% | +11.9% |
| RNDR   | 0.50  | -1.79% | +13.4% |

**Forecast (rule-based)**
- SOL: long, confidence 1.0 (strong 7d momentum +10.1%) — but rank below 0.55 threshold
- All ranked candidates: flat, confidence 0.40 — 24h short-term momentum mixed/negative despite strong 7d

**Gate check**
- Candidates with rank ≥ 0.55: JUP (0.77), TIA (0.64)
- Both fail forecast confidence gate (0.40 < 0.60 required)
- NEAR fails rank gate (0.54 < 0.55) and confidence gate

**Decision: 0 orders placed, 2 skipped (JUP, TIA failed confidence), rest below rank threshold**
