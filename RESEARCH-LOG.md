# RESEARCH-LOG.md

Append-only research notes. Written by `tools/journal.py research`. Do not edit prior entries.

---

## 2026-05-09 10:50 UTC — smoke test

- system online\n- tools layer initialized\n- this entry verifies journal.py append

## 2026-05-09 10:54 UTC — heartbeat

alive at 2026-05-09T10:54:26Z; guardrails OK; rank+forecast OK

## 2026-05-09 15:24 UTC — heartbeat

make dc-s06-heartbeat: guardrails OK, rank+forecast OK

## 2026-05-14 03:10 UTC — thematic snapshot

## Active Themes (2/3 cap)

**1. ai_compute** — ACTIVE
Thesis: AI chip demand at record highs; US-China trade diplomacy centers on semiconductor access.
- Evidence A: Nvidia/chip stocks drove S&P 500 + Nasdaq to record closing highs (Straits Times, AP 2026-05-13)
- Evidence B: Trump Beijing summit featured Nvidia CEO negotiating trade + market access; Cerebras IPO price range raised on surging demand (Kiplinger 2026-05-13)
Candidates: NVDA (direct beneficiary, Beijing-access catalyst), TSM (foundry demand), AVGO (AI networking)

**2. defense** — ACTIVE
Thesis: Dual geopolitical flashpoints — Middle East oil spike + US-China tech-trade friction — signal elevated defense procurement environment.
- Evidence A: Oil spiked above $100/bbl amid Middle East tensions; energy stocks led S&P to new high (Kiplinger 2026-05-13)
- Evidence B: Trump-Beijing summit framed around trade disputes with military/tech overtones (Straits Times 2026-05-13)
Candidates: RTX (missile systems, MidEast exposure), LMT (F-35 + strategic contracts)

## Anchors (top 3 by move)
- QQQ: $714.71 | 24h +1.02% (per news digest — chip-led rally)
- SPY: $742.31 | 24h +0.56% (per news digest)
- ETH: $2,246.68 | 24h -2.03% | 7d -3.46% (per fetch_crypto)
- BTC: $79,226 | 24h -2.19% | 7d -2.39% (per fetch_crypto)

## Theme Candidates
ai_compute top 2: NVDA (record + Beijing trade catalyst), TSM (foundry supply chain)
defense top 2: RTX (Raytheon, direct MidEast systems supplier), LMT (F-35 backlog + strategic)

## Hidden Gems (top 3 of 5 scanned — all rejected)
- LAB: $6.03 | mcap $463M | 30d +890% — REJECT: no news catalyst; pure momentum, fails 100-char thesis gate
- SKYAI: $0.457 | mcap $457M | 30d +314% — REJECT: -21% today, momentum collapsing, no catalyst
- SAHARA: $0.044 | mcap $145M | 30d +99% | 7d +74% — REJECT: AI-named token, no news-linked thesis available

## Anomalies
- Kevin Warsh confirmed as Fed Chair (hawkish); PPI +1.4% in April (4yr high) → rate cuts off table
- Crypto -2% 24h while US equities at record highs: BTC/ETH decoupling bearishly from risk-on
- Oil >$100 + hot PPI = dual inflation shock; macro headwind for rate-sensitive positions
- Cerebras Systems IPO demand surge = private AI infra buildout accelerating beyond public markets

## 2026-05-14 18:10 UTC — thematic snapshot

## Active Themes (2/3 cap)

**1. ai_compute** — ACTIVE
Thesis: H200 China export approval + chip-led record equity rally signals sustained AI semiconductor demand across the supply chain.
- Evidence A: US approved H200 chip sales to ~10 Chinese firms; NVDA +3% intraday (MarketScreener/Newsquawk, 2026-05-14)
- Evidence B: S&P 500 and Nasdaq hit new record highs driven by tech/chip gains; Dow +0.8%, Nasdaq leads (BusinessTimes/FXLeaders, 2026-05-14)
Candidates: NVDA (direct H200 beneficiary, +19.2% 7d, $234.25), AMD (AI chip competitor, +25.4% 7d — strongest mover)

**2. defense** — ACTIVE
Thesis: Dual geopolitical pressure — US-China summit Hormuz/Iran framing + Middle East oil spike — sustains defense procurement outlook.
- Evidence A: US-China summit; both sides agreed to keep Strait of Hormuz open and prevent Iran nuclear weapons (Newsquawk, 2026-05-14)
- Evidence B: Energy sector led S&P to new high on Middle East oil spike above $100/bbl (Kiplinger, 2026-05-11)
Candidates: RTX ($175.94, +1.8% 7d — Raytheon missile systems, MidEast exposure), LMT ($519.01, +1.9% 7d — F-35 backlog)

## Anchors (top 3 by 7d move)
- AMD: $445.38 | 7d +25.4% (ai_compute spillover — cheaper AI chip exposure)
- NVDA: $234.25 | 7d +19.2% (H200 China access direct catalyst)
- QQQ: $718.87 | 7d +5.5% (chip-led index momentum)
- BTC: $81,597 | 24h +2.57% | 7d +1.9% (per fetch_crypto)
- ETH: $2,307 | 24h +2.04% | 7d +0.3% (per fetch_crypto)

## Theme Candidates
ai_compute top 2: NVDA ($234.25, +19.2% 7d), AMD ($445.38, +25.4% 7d — outpacing primary)
defense top 2: RTX ($175.94, +1.8% 7d), LMT ($519.01, +1.9% 7d)

## Hidden Gems (top 5 scanned — all rejected)
- LAB: $6.25 | mcap $473M | 30d +975% — REJECT: parabolic meme coin, no news catalyst, fails thesis gate
- TROLL: $0.134 | mcap $133M | 30d +722% | 7d +184% — REJECT: meme token, zero fundamental basis
- B (BUILDon): $0.484 | mcap $485M | 24h -27.6% — REJECT: momentum collapse intraday, no thesis
- SKYAI: $0.376 | mcap $376M | 7d -38.1% — REJECT: 7d deeply negative, momentum broken
- H (Humanity): $0.250 | mcap $455M | 30d +156% — REJECT: biometric identity chain, no news-linked thesis available

## Anomalies
- AMD +25.4% 7d > NVDA +19.2% 7d: second-order AI chip beneficiary outpacing the primary — sector rotation into cheaper exposure
- Defense underperforming vs geopolitical catalysts: RTX/LMT +1-2% 7d vs SPY +3.2% — market pricing risk-on over defensive allocation
- Crypto lagging US equity risk-on: BTC +1.9% 7d, ETH +0.3% 7d while QQQ +5.5%
- Cisco (CSCO) +14.7% on restructuring + revenue raise — enterprise tech restructuring wave accelerating
- Kevin Warsh (hawkish) confirmed as Fed Chair (54-45 Senate, 2026-05-13) — rate cuts increasingly off table
- Mortgage rate eased to 6.36% despite hawkish Fed signal — mixed rate trajectory signals

## 2026-05-16 22:04 UTC — 22:00-UTC-crypto-pass

## 22:00 UTC crypto pass — 2026-05-16

### Market Snapshot (per fetch_crypto 22:03 UTC)
- BTC: $78,197 | 24h -1.01% | 7d -3.21%
- ETH: $2,180.90 | 24h -1.66% | 7d -6.36%
- SOL: $86.56 | 24h -2.86% | 7d -7.34%
- AVAX: $9.31 | 24h -2.10% | 7d -6.52%
- LINK: $9.75 | 24h -2.81% | 7d -6.33%
- ATOM: $2.05 | 24h +6.15% | 7d +5.88% (sole green signal, no theme/news backing)
- NEAR: $1.49 | 24h -2.74% | 7d -4.20%

### News Digest (per fetch_news 22:03 UTC)
Empty tape — no ETF flows, no regulatory updates, no L1/L2 upgrades, no exchange news in last 12h.

### Active Themes: NONE
No active crypto themes. News citations = 0; ≥2 distinct source-types required per theme. No themes activated.

### Forecasts (rule-based)
BTC: SHORT 0.66 | ETH: SHORT 0.818 | SOL: SHORT 0.867 | AVAX: SHORT 0.826 | LINK: SHORT 0.816 | ATOM: LONG 0.794 | NEAR: SHORT 0.710

### Bucket Decisions
- ANCHOR (BTC, ETH): Both forecast SHORT; long-only system; 0 trades.
- THEME: No active themes; ATOM lone long but no mapped theme + zero news citations; 0 trades.
- GEM (5 scanned): LAB (meme +838% 30d, no catalyst), UB (-30.7% intraday collapse), B (-11.9% intraday), H (no description/news), GWEI (-5.6% 24h, no news). All rejected.

### Result: 0 new positions. Broad crypto correction, empty news tape. Capital preserved.
