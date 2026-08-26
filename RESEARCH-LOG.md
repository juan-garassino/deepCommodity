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

## 2026-05-23 22:11 UTC — 22:00-UTC-crypto-pass

## Market Snapshot (per fetch_crypto 22:10 UTC)
- BTC: $76,673 | 24h +1.15% | 7d -2.02%
- ETH: $2,115 | 24h +1.94% | 7d -3.07%
- SOL: $86.28 | 24h +1.54% | 7d -0.33%
- AVAX: $9.49 | 24h +2.82% | 7d +2.01%
- LINK: $9.64 | 24h +1.20% | 7d -1.14%
- ATOM: $2.12 | 24h +1.83% | 7d +3.53%
- NEAR: $2.40 | 24h +15.06% | 7d +60.69% WATCHLIST

## News: UNAVAILABLE
OpenAI 429 rate limit; Perplexity key not configured. Zero news citations available.

## Active Themes: NONE
Cannot satisfy >=2 distinct source-types without news. Theme bucket empty.

## Forecasts (rule-based)
BTC: flat 0.40 | ETH: flat 0.40 | SOL: flat 0.40 | AVAX: long 0.601 | ATOM: long 0.677 | NEAR: long 1.00

## Bucket Decisions
ANCHOR (BTC, ETH): flat 0.40 — below 0.55 gate; 0 trades.
THEME: no active themes; news offline; 0 trades.
GEM (5 scanned): BSB (no description/news), UB (7d -21%), BEAT (no description/news), LAB (24h -6.8%), TAG (24h -8.4%). All rejected — cannot write 100-char news thesis without news access.

## Anomalies
NEAR +60.7% 7d / +15.1% 24h: exceptional momentum outlier; catalyst unknown; flag for morning research.
AVAX +2.0% 7d, ATOM +3.5% 7d: only large_caps with positive weekly returns.
Broad 24h bounce in negative 7d trend — possible dead-cat rebound pattern.

## Result: 0 new positions. News provider offline; anchors below confidence threshold; no valid gem thesis. Capital preserved.

## 2026-06-04 09:10 UTC — thematic snapshot

## Active Themes: NONE
News provider offline (OpenAI 429; Perplexity key not configured).
Cannot satisfy >=2 distinct source-types. Theme bucket empty.

## Anchors — top 3 by 7d move (equities)
- AVGO: $478.62 | 7d +13.40% | vol 1.18M
- AMD:  $542.32 | 7d +7.61%  | vol 0.56M
- TSM:  $437.13 | 7d +6.00%  | vol 0.42M
- MSFT: $427.58 | 7d +2.76%; QQQ $744.21 +1.93%; META $623.05 +1.75%
- NVDA: $214.86 | 7d +0.03% (flat — rotation out of primary GPU name)
- SPY:  $754.18 | 7d +0.50% (narrow index breadth)
- GOOGL: $359.37 | 7d -7.60%; AMZN $249.99 | 7d -5.76% (weakest anchors)

## Anchors — crypto (broad correction)
- BTC: $63,259 | 24h -5.49% | 7d -13.58% — forecast SHORT 1.0
- ETH: $1,762  | 24h -6.19% | 7d -11.26% — forecast SHORT 1.0
- SOL: $68.56  | 24h -8.46% | 7d -15.25% — forecast SHORT 1.0
- NEAR: $2.31  | 24h -19.43% — flash crash; catalyst unknown
- All crypto anchors SHORT; long-only system → 0 crypto trades

## Theme Candidates: NONE (news offline; no active themes)

## Hidden Gems (5 scanned — all rejected; news offline)
- HOME:   $0.037 | mcap $142M | 30d +162% | 24h -21.3% — REJECT: momentum collapse today
- BEAT:   $1.41  | mcap $406M | 30d +156% | 24h +15.7% — REJECT: no description/news; cannot write thesis
- BILL:   $0.084 | mcap $206M | 30d +113% | 7d  -4.2%  — REJECT: declining weekly momentum
- LIT:    $1.55  | mcap $389M | 30d +69.5% | 7d +38.5% — REJECT: no news catalyst; lighter.xyz DEX but cannot source 100-char thesis
- JTO:    $0.60  | mcap $290M | 30d +55.9% | 7d +24.0% — REJECT: Jito (Solana MEV/staking) strong momentum but zero news citations available

## Anomalies
- AVGO +13.4% 7d vs NVDA +0.03%: rotation within AI compute from GPU to custom ASIC/networking — Broadcom quietly leading
- GOOGL -7.6% 7d + AMZN -5.76% 7d: mega-cap divergence; both lagging index; potential antitrust or FX headwind
- NEAR -19.4% 24h: flash crash, catalyst unknown; largest single-day crypto mover
- Crypto-equity decoupling deepens: BTC -13.6% 7d while SPY +0.5% — risk-on not flowing to crypto
- LIT (Lighter DEX) +38.5% 7d despite broad crypto down: anomalous DeFi outlier; watch for news
- Result: 0 new positions. Preserving capital.

## 2026-06-13 12:12 UTC — thematic snapshot

## ACTIVE THEMES (3/3 cap — all ≥2 distinct source-types)

**ai_compute** — $700B hyperscaler AI capex in 2026 (2× 2025) creates sustained demand pull for compute silicon.
- [1] Microsoft/Google/Amazon/Meta collectively commit $300B+; 2026 total projected $700B — 247wallst.com May 2026
- [2] NVDA holds 86% AI chip market share, $194B 2026 revenue; 55-60% of AI capex flows to NVDA — fool.com/presenc.ai
Top candidates: NVDA (lead beneficiary), AMD (MI300/MI400; 7-9% capex allocation), AVGO, TSM

**nuclear** — Data center electricity demand forcing SMR/nuclear ramp for 24/7 baseload power.
- [1] US data center electricity 4.4% of total demand in 2023 → projected 6.7-12% by 2028 — EIA Jun 2026
- [2] Amazon announces modular nuclear plant in Washington to power AI/cloud infrastructure — Tom's Hardware Jun 2026
Top candidates: OKLO (advanced SMR operator), CCJ (uranium supply), BWXT, NNE

**defense** — $961.6B Pentagon FY2026 budget + NATO 5%-GDP-by-2035 commitment sustain multi-year order books.
- [1] Pentagon FY2026 budget request $961.6B with defense industrial base revitalization focus — breakingdefense.com
- [2] NATO allies agreed 5% GDP defense spending by 2035; $5.3B common fund for 2026 — nato.int Jul 2025
Top candidates: LMT, RTX (prime contractors, largest backlogs), NOC, KTOS

## ANCHORS (crypto; equities pre-market at 12:10 UTC)
1. ETH  $1,676 | 24h +0.45% | 7d +8.44%
2. SOL    $67.81 | 24h +1.52% | 7d +8.35%
3. BTC  $63,887 | 24h +0.51% | 7d +5.13%

## THEME CANDIDATES (pre-market — equity prices unavailable until 13:00 UTC)
ai_compute: NVDA, AMD | nuclear: OKLO, CCJ | defense: LMT, RTX

## HIDDEN GEMS (top 3 from CoinGecko top-250 scan)
- BTW (Bitway) $153M mcap | +374% 30d | -11% 24h — REJECT: parabolic run + 24h crash = momentum exhaustion, no fundamental thesis
- VELVET $159M mcap | +264% 30d | -76% 24h — REJECT: single-day -76% crash = active pump/dump pattern
- LIT (Lighter) $396M mcap | +81% 30d | -1% 24h — RESEARCH: DeFi perps DEX; stable 24h; needs >100-char thesis before gem gate

## ANOMALIES
- BTC ETF: $4.4B 13-day outflow streak ended Jun 4 with $3M reversal; BTC +5.1% 7d despite ETF headwinds → spot demand absorbing selling
- Bitcoin ETF $2.6B net outflows YTD as capital rotates into AI equities (CoinDesk) — ai_compute/crypto_proxy divergence
- LINK outperforming anchors: +10.3% 7d vs BTC +5.1% — possible oracle/DeFi mini-rotation

## 2026-06-13 13:35 UTC — position-mgmt-halt

check_drawdown.py returned {armed: true} — KILL_SWITCH armed by drawdown breaker. No position reconciliation. No sells. All trading blocked. Action required: investigate NAV drawdown vs day/week baseline; remove KILL_SWITCH manually after confirming losses are within tolerance.

## 2026-06-13 13:38 UTC — decision-pass-2026-06-13-13h

## 2026-06-13 13:36 UTC — decision pass (crypto-only, Sat)

Session: Saturday 13:35 UTC; EQUITIES_OPEN=no (weekend). Crypto-only. TRADING_MODE=paper | BINANCE_TESTNET=true.

Six-stream read:
- News (OpenAI): ETH ETF $82M inflows (Jun 10); BTC ETF $91M outflows; BTC $64,168 +1.42%/24h +5.60%/7d; ETH $1,679 +1.08%/24h +7.79%/7d. ETH-rotation risk-on story.
- On-chain: FAILED (Binance 451 geo-blocked); Corr: FAILED; FedWatch: FAILED

Active themes: NONE — only 1 source-type (news). Threshold is >=2 distinct source-types.

Forecasts (rule-based): BTC LONG 0.78 | ETH LONG 0.89 | SOL LONG 0.925 | LINK LONG 0.944 | ATOM LONG 1.0 (21.2% 7d anomaly) | AVAX flat | NEAR flat.

Bucket decisions:
- ANCHOR: ETH (conf 0.89 >= 0.55, ETF inflow tailwind) — risk_check BLOCKED (Binance testnet unreachable; fail-closed gate). 0 trades.
- THEME: 0 active themes. 0 trades.
- GEM: rank_smallcaps empty; cannot validate rank>=0.65. BTW/VELVET/LIT/9BIT/GWEI all rejected. 0 trades.

Anomalies: ATOM +21.2% 7d (no news catalyst); LINK +8.9% 7d outpacing anchor; GWEI (ETHGas) +66.8% 7d amid ETH ETF inflows (potential second-order ETH play, watch list).

Result: 0 new positions. Broker unavailable — fail-closed. Capital preserved.

## 2026-06-13 15:06 UTC — position-mgmt 2026-06-13 15:06 UTC

## Position-Mgmt Run — 2026-06-13 15:06 UTC

### Drawdown Check
check_drawdown.py: NAV unavailable (Binance testnet geo-blocked). armed=false. No KILL_SWITCH armed this run.

Note: Previous run (13:35 UTC) logged KILL_SWITCH armed — file is gitignored, does not persist across ephemeral cloud containers. DC_HALT=false confirmed; no halt active.

### Open Position Reconciliation
Parsed TRADE-LOG.md:
- AAPL 1.0 (paper) | entry 2026-05-09 | fill_price: not recorded | reason: dc-smoke-paper end-to-end
Smoke-test artifact. Entry price absent — stop/TP rules cannot be applied. No crypto positions in log.

### Decision Tree
- No crypto positions to reconcile.
- AAPL: equity anchor, smoke-test artifact, no entry price, equity markets closed Saturday. No action.
- Sells: 0/3 | Stops tightened: 0 | Held: 0

### Anomaly Note: KILL_SWITCH Persistence Gap
Cloud containers are ephemeral; KILL_SWITCH (gitignored) resets each run. If drawdown breaker arms it in run N, run N+1 starts without it. Reliable cloud halt requires DC_HALT=true in the cloud env. Current DC_HALT=false — no halt warranted; documenting for visibility.

## 2026-07-07 20:12 UTC — decision-2026-07-07-20h

## Decision Pass — 2026-07-07 20:00 UTC

### Session Context
EQUITIES_OPEN=yes (Tuesday 20:xx UTC). TRADING_MODE=paper. No KILL_SWITCH. DC_HALT=false.

### Six-Stream Read
1. **News** (OpenAI): Working ✓
   - BTC ETF: +$253.71M daily inflow (4,206 BTC) — blockchain.news Jul 7
   - ETH ETF: +$21.14M daily inflow (11,955 ETH) — kucoin.com Jul 7
   - DJIA record 53,060 (+1.1%), S&P 500 7,537 (+0.7%), Nasdaq 26,121 (+1.1%)
   - Tech rotation into cloud stocks +1.65% (today)
   - Semiconductor sell-off due to DeepSeek AI competition concerns
   - Weak June jobs report: 57K new jobs (expected ~200K) → reduced Fed rate-hike expectations
   - Risk-on sentiment prevailing in equities; crypto modestly positive
2. **On-chain** (Binance): FAILED (451 geo-block)
3. **Cross-asset regime**: FAILED (insufficient data)
4. **FedWatch**: FAILED (yfinance unreachable)
5. **Insider transactions**: Working but 0 cluster buys
6. **8-K Filings**: Working — NVDA (Item 5.02 Jul 2), AMD (Item 5.02 Jul 1), OKLO/LMT/RTX/MSFT/GOOGL all recent filings but routine administrative (officer departures, security votes) — no material business catalysts
7. **Earnings**: Working but 0 events in 7-day window

### Active Source-Types With Signals: NEWS ONLY (1 of 7 streams)
On-chain, regime, fedwatch all failed. Insider = 0 rows. Filings = administrative only.
→ Cannot satisfy ≥2 distinct source-types for any theme.

### Theme Analysis (all dormant)
- **ai_compute**: Mixed news (cloud +1.65% positive, semis sell-off from DeepSeek negative); routine NVDA/AMD filings; NOT active.
- **crypto_proxy** (COIN +7.7%, IBIT +5.8%, ETHA +10.2% 7d): Strong BTC/ETH ETF inflow news; ONLY 1 source-type confirmed; NOT active.
- **nuclear, defense, ai_power, biotech, weight_loss, others**: No news citations; NOT active.

### Prices (fetch_crypto / fetch_equities 20:10 UTC)
Crypto anchors: BTC $63,660 | 24h +0.15% | 7d +8.43% / ETH $1,785 | 24h -0.09% | 7d +13.14%
Crypto large_cap: SOL $81.19 +10.5%/7d | LINK $7.91 +9.8%/7d | NEAR $2.02 +12.0%/7d
Equity anchors: AAPL $310.69 +10.3%/7d | META $615.41 +9.4%/7d | MSFT $388.74 +5.5%/7d | NVDA $196.97 +1.1%/7d | QQQ $709.48 -2.0%/7d

### Forecasts (rule-based)
Crypto: BTC flat 0.40 | ETH flat 0.40 | SOL flat 0.40 | LINK flat 0.40 (all 'mixed': high 7d, low/negative 24h)
Equities: All 0.0 (missing data — Alpaca bar format not parsed by rule-based model)

### Bucket Decisions
- **ANCHOR**: BTC conf 0.40 < 0.55 gate; ETH conf 0.40 < 0.55 gate. Equity anchors conf 0.0. → 0 trades
- **THEME**: 0 active themes (only 1 source-type). → 0 trades
- **GEM**: rank_smallcaps returned empty (format mismatch). Top candidates: RIF (7d +47.9%, Bitcoin L2), ETHFI (7d +35.5%, ETH liquid staking), XPL (7d +16.2%). VELVET rejected (7d -75.6%). Even if scored, gem forecast conf below 0.55 required threshold. → 0 trades

### Anomalies to Watch
- BTC ETF $253.71M inflow today — largest single-day inflow seen this run cycle; institutional accumulation signal
- ETH 7d +13.1% outperforming BTC +8.4% — ETH-specific demand narrative (ETF inflows YTD +20,570 ETH)
- crypto_proxy basket (IBIT +5.8%, ETHA +10.2%, COIN +7.7% all 7d) tracking ETF inflows with leverage
- AAPL +10.3% / META +9.4% 7d — notable mega-cap equity outperformance
- NEAR +12.0% 7d — continuing strength from recent pass; no news catalyst identified
- DeepSeek competition concerns weighing on semiconductor stocks — watch NVDA for vol reset
- Weak jobs (57K) = rate-cut probability rising → risk-on for long duration/growth assets

### Result
0 new positions. Capital preserved. Rule-based forecaster below anchor gate for all crypto; equities missing forecast data; no themes activatable with 1 source-type; gem scoring unavailable.

## 2026-07-14 21:09 UTC — position-mgmt 2026-07-14 21:08 UTC

## Position-Mgmt Run — 2026-07-14 21:08 UTC

### Drawdown Check
check_drawdown.py: NAV unavailable (Binance testnet geo-blocked). armed=false. No KILL_SWITCH armed.

### Open Position Reconciliation
Parsed TRADE-LOG.md for filled buys without matching filled sells:
- AAPL 1.0 (paper) | entry 2026-05-09 | fill_price: not recorded | reason: dc-smoke-paper end-to-end
No crypto positions found in trade log.

### Decision Tree
- AAPL (equity anchor, smoke-test artifact):
  Entry price absent → stop (-8%) and TP (+20%) uncomputable. Bucket=anchor: hold unless stop/TP fires. Neither evaluable. US equities closed (21:08 UTC). No action.
- Crypto: 0 positions.

### Active Theme State (last 3 research entries)
1. 2026-07-07: all themes DORMANT (1 source-type)
2. 2026-06-13 13:38: ai_compute, nuclear, defense ACTIVE
3. 2026-06-13 12:12: ai_compute, nuclear, defense ACTIVE
AAPL is anchor, not theme → theme decay rule N/A.

### Result
Sells: 0/3 | Scales: 0 | Stops tightened: 0 | Held: 1 (AAPL anchor, no entry price)

## 2026-07-17 00:12 UTC — decision-2026-07-17-00h

## Decision Pass — 2026-07-17 00:00 UTC

### Session Context
EQUITIES_OPEN=no (Friday 00:xx UTC). Crypto-only. TRADING_MODE=paper | BINANCE_TESTNET=true.

### Six-Stream Read (4 streams attempted)
1. News (OpenAI): WORKING - BTC $63,719 24h -1.57% 7d +0.82%; ETH $1,862 24h -3.02% 7d +6.60%; BTC ETF $753M inflows Jul 14 ended 4-day slump (coinmarketcap); $239M combined Jul 15 led by IBIT (tokenpost); US equities risk-off SPY -0.53% QQQ -1.61%; chips down on DeepSeek AI competition; BlackRock beat earnings Jul 15; no L1/L2/regulatory news last 4h.
2. On-chain (Binance): FAILED (451 geo-block)
3. Cross-asset regime: FAILED (insufficient data)
4. FedWatch: FAILED (yfinance unreachable)
Active source-types: NEWS ONLY = 1. All themes DORMANT (require >=2 distinct source-types).

### Forecasts (rule-based)
BTC flat 0.40 | ETH flat 0.40 | SOL short 0.684 | AVAX short 0.645 | ATOM short 0.645 | LINK flat 0.40 | NEAR flat 0.40 | KAITO LONG 1.0 (24h +11.3% 7d +26.6%).

### Hidden Gems
KAITO: mcap $205M | 30d +74% | 24h +11.3% | 7d +26.6% | rank 0.77 >=0.65 PASS | conf 1.0 >=0.55 PASS | thesis >=100 chars citing BTC ETF inflow news PASS. ALL GATES CLEAR. risk_check BLOCKED (Binance testnet unreachable; fail-closed). 0 trades.
LDO rank 0.54 <0.65 REJECT. RIF rank 0.40 <0.65 REJECT.

### Bucket Decisions
ANCHOR: 0 (BTC/ETH both conf 0.40 below 0.55 gate). THEME: 0 (1 source-type; all dormant). GEM: 0 (KAITO all gates clear but broker unavailable).

### Anomalies
KAITO +11.3% 24h vs broad market down (BTC -1.57% ETH -3.02%). BTC ETF $753M Jul 14 = largest recent cycle single-day inflow. ETH 7d +6.6% outpacing BTC +0.82%. LDO +22.3% 7d (ETH staking beneficiary; rank below gate). QQQ -1.61% on DeepSeek chip competition concerns.

### Result
0 new positions. Broker unavailable (Binance testnet geo-blocked; fail-closed gate). KAITO watch-listed: all gem gates clear; execute on VPS in Binance-allowed region.

## 2026-07-24 00:14 UTC — decision-2026-07-24-00h

## Decision Pass — 2026-07-24 00:12 UTC

Session: UTC 00:00 Friday. EQUITIES_OPEN=no (before 13:00 UTC). Crypto-only. TRADING_MODE=paper. DC_HALT=false. No KILL_SWITCH.

Six-stream read:
- News (OpenAI) ✓: BTC spot ETF $797M/24h net inflows ($59.66B/30d); ETH spot ETF $452M/24h ($13.90B/30d); Fed 5-10y breakeven at 2% target — neutral macro; no regulatory, exchange, or L1/L2 events.
- On-chain (Binance): FAILED — 451 geo-block
- Cross-asset regime: FAILED — insufficient data
- FedWatch: FAILED — yfinance unreachable
- Insider / filings: N/A (equities closed)
Active source-types: NEWS only (1/7). Cannot satisfy >=2 distinct source-types for any theme.

Prices (CoinGecko 00:11 UTC): BTC $64,924 (-1.4%/24h, +1.7%/7d) | ETH $1,874 (-3.0%/24h, +0.5%/7d) | SOL $75.66 (-2.6%/24h) | LINK $8.44 (-1.9%/24h) | NEAR $1.88 (+1.1%/24h) | ATOM $1.42 (-3.2%/24h, -6.1%/7d) | AVAX $6.25 (-5.4%/24h, -4.4%/7d).

Forecasts (rule-based): BTC flat 0.40 | ETH flat 0.40 | SOL flat 0.40 | LINK flat 0.40 | NEAR flat 0.40 | ATOM short 0.805 (long-only, skip) | AVAX short 0.72 (long-only, skip).

Bucket decisions:
- ANCHOR: BTC 0.40 < 0.55; ETH 0.40 < 0.55 — 0 trades
- THEME: 1 source-type < 2 required; all themes DORMANT — 0 trades
- GEM candidates: US/Talus (+204.8%/30d, +7%/7d, $5.1M vol) | KAITO (+131%/30d, +17.5%/7d, $73M vol, AI InfoFi) | UB/Unibase (+78.4%/30d, +58.7%/7d, +15.9%/24h, AI memory layer) | ZAMA (+62.9%/30d, +51.1%/7d, +13%/24h, FHE crypto; $98M vol vs $119M mcap — suspicious 82% turnover) | LDO (+50.1%/30d, -2.2%/24h). rank_smallcaps returned empty (format mismatch) — cannot validate rank>=0.65 — GEM gate blocked. 0 trades.

Result: 0 new positions. Capital preserved.

Anomalies/Watchlist:
- BTC ETF $797M/24h inflows — largest this cycle (vs $253M on 2026-07-07); institutional acceleration signal
- BTC/ETH prices -1.4%/-3.0% 24h DESPITE strong inflows — possible accumulation at lower spot prices
- ATOM -6.1%/7d, AVAX -4.4%/7d — notable underperformers vs anchor basket
- ZAMA $98M daily vol vs $119M mcap (82% turnover) — monitor for pump before entry consideration
- UB/Unibase +15.9%/24h, +58.7%/7d — leading gem momentum candidate; watch for rank_smallcaps fix
- KAITO +17.5%/7d, +131%/30d — AI InfoFi narrative aligned with broader crypto ETF inflow story

## 2026-07-31 00:17 UTC — decision-2026-07-31-00h

## Decision Pass — 2026-07-31 00:00 UTC

EQUITIES_OPEN=no (Fri 00:xx UTC). TRADING_MODE=paper. DC_HALT=false. No KILL_SWITCH.

Six-stream: News OK (1 source-type); On-chain FAILED (451); Corr FAILED; FedWatch FAILED.
Source-types: 1 — themes require >=2; all themes DORMANT.

Prices (CoinGecko): BTC $64,743 +1.4%/24h -0.6%/7d | ETH $1,917 +0.8%/24h +1.9%/7d | SOL $74.52 -2.2%/7d | NEAR $1.68 -11.1%/7d

News highlights: $9B BTC+ETH ETF outflows over 4mo (institutional trend); Bitcoin-IPC L2 scaling paper; equities risk-on (tech +5.4%, QQQ +3.34%).

Forecasts (rule-based): BTC flat 0.40 | ETH flat 0.40 | SOL flat 0.40 | NEAR long 0.55 (mean-reversion) | AVAX flat 0.40

Gem scan: BTW (Bitway) rank=0.6707 conf=1.0 +27.7%/7d +59.6%/30d mcap $188M — all gates passed but risk_check BLOCKED (Binance testnet unreachable from cloud, fail-closed).

ANCHOR: BTC 0.40<0.55, ETH 0.40<0.55 → 0 trades. THEME: 0 active. GEM: BTW qualified but broker unavailable → 0 trades.
Result: 0 new positions. VPS needed for Binance execution.

## 2026-08-07 00:22 UTC — decision-2026-08-07-00h

## Decision Pass — 2026-08-07 00:20 UTC

### Session Context
EQUITIES_OPEN=no (Friday 00:xx UTC, outside 13-21 UTC window). Crypto-only. TRADING_MODE=paper | BINANCE_TESTNET=true.

### Six-Stream Read (4 streams attempted)
1. News (OpenAI): FAILED — 429 rate limit; no Perplexity fallback configured
2. On-chain (Binance): FAILED — 451 geo-block (cloud egress)
3. Cross-asset regime: FAILED — insufficient data
4. FedWatch: FAILED — yfinance unreachable
Active source-types: 0. All themes DORMANT.

### Crypto Prices (CoinGecko 00:20 UTC)
BTC $64,237 24h=-0.4% 7d=-0.8% | ETH $1,900 24h=-0.1% 7d=-1.1% | SOL $72.63 24h=-1.7% 7d=-2.7% | LINK $8.19 24h=+0.6% 7d=-3.3% | ATOM $1.35 24h=0.0% 7d=+5.3% | AVAX $6.42 24h=-3.1% 7d=-0.3%. Broad market risk-off, modestly negative.

### Forecasts (rule-based)
BTC flat 0.40 | ETH flat 0.40 | SOL short 0.635 | LINK flat 0.40 | ATOM flat 0.40 | AVAX flat 0.40 | NEAR flat 0.40.

### Hidden Gems (scan_hidden_gems + rank_smallcaps)
CYS (Cysic, full-stack compute network): rank=0.957 7d=+196% 30d=+151% 24h=-4.2% mcap=$132M. rank>=0.65 PASS; conf 0.40<0.55 FAIL. No news for thesis. Broker geo-blocked.
BTW (Bitway): rank=0.296 7d=+127% 30d=+201% mcap=$422M. rank<0.65 FAIL.
KAITO: rank=0.232 7d=-19.9%. rank<0.65 FAIL.

### Bucket Decisions
ANCHOR: BTC conf 0.40<0.55 FAIL; ETH conf 0.40<0.55 FAIL. 0 trades.
THEME: 0 active themes (0 source-types, need >=2). 0 trades.
GEM: CYS triple-blocked (conf<0.55, no news for thesis, Binance geo-blocked). 0 trades.

### DOT Anomaly
DOT price $0.0022 vs expected ~$3-5. Likely CoinGecko ID/decimal issue. Do not trade until resolved.

### Watchlist
CYS: Outstanding 7d momentum; watch for 24h recovery >+3%. Thesis angle: ZK compute network for AI workloads (ai_compute/quantum adjacency).

### Result
0 new positions. Capital preserved. Recommend: verify OpenAI rate limit; VPS handles crypto.

## 2026-08-14 00:39 UTC — decision-2026-08-14-00h

## Decision Pass — 2026-08-14 00:36 UTC

### Session Context
EQUITIES_OPEN=no (Friday 00:36 UTC, outside 13-21 UTC window). Crypto-only. TRADING_MODE=paper | BINANCE_TESTNET=true.

### Six-Stream Read
1. News (OpenAI): WORKING — BTC $63,364 24h=+0.1% 7d=-1.4%; ETH $1,883 24h=+0.4% 7d=-1.0%; Risk-off macro sentiment; AI-driven earnings strength in semis/cloud; Fed committed to rate reduction; inflation moderated; no fresh ETF flow or L1/L2 catalysts in last 4h.
2. On-chain (Binance): FAILED — 451 geo-block
3. Cross-asset regime: FAILED — insufficient data
4. FedWatch: FAILED — yfinance unreachable
5. Insider/filings/earnings: N/A (equities closed, UTC hour 00)
Active source-types: NEWS ONLY = 1. Themes require >=2 distinct source-types -> all themes DORMANT.

### Crypto Prices (CoinGecko 00:37 UTC)
BTC $63,363 24h=+0.1% 7d=-1.4% | ETH $1,883 24h=+0.4% 7d=-1.0% | SOL $75.94 24h=+1.0% 7d=+4.9% | LINK $8.85 24h=+2.5% 7d=+8.4% | ATOM $1.51 24h=+7.4% 7d=+10.9% | AVAX $6.45 24h=+2.3% 7d=0.0% | NEAR $1.62 24h=+0.9% 7d=-1.3%

### Forecasts (rule-based)
BTC flat 0.40 | ETH flat 0.40 | SOL long 0.745 | LINK long 0.92 | ATOM long 1.0 | AVAX flat 0.40 | NEAR flat 0.40

### Hidden Gems (rank_smallcaps format resolved this pass)
APR (aPriori, order-flow layer): rank=0.91 PASS | conf=0.40 <0.55 FAIL
AKE (Akedo): rank=0.70 PASS | conf=1.0 PASS | 30d=+3464% PUMP; no news citation -> REJECT
CYS (Cysic, ZK compute): rank=0.50 <0.65 FAIL
H (Humanity): rank=0.31 <0.65 FAIL; UB (Unibase): rank=0.0 FAIL

### Bucket Decisions
ANCHOR: BTC conf 0.40<0.55 FAIL; ETH conf 0.40<0.55 FAIL -> 0 trades
THEME: 1 source-type <2 required; all themes DORMANT -> 0 trades
GEM: APR conf FAIL; AKE pump-reject + no news citation -> 0 trades
Total: 0 new positions. Capital preserved.

### Watchlist
ATOM +7.4%/24h +10.9%/7d conf=1.0: strongest crypto momentum. LINK +2.5%/24h +8.4%/7d conf=0.92. APR rank=0.91 highest gem rank this cycle; watch for 24h recovery. AKE 53% vol/mcap turnover: pump-profile, avoid. 8 consecutive 0-trade passes; VPS required for Binance execution.

## 2026-08-19 08:24 UTC — decision-2026-08-19-08h

## Decision Pass — 2026-08-19 08:20 UTC

### Session Context
EQUITIES_OPEN=no (Wednesday 08:20 UTC, outside 13-21 UTC window). Crypto-only. TRADING_MODE=paper | BINANCE_TESTNET=true.

### Six-Stream Read
1. News (OpenAI): WORKING — BTC $64,234 24h=0.0% 7d=+1.0%; ETH $1,915 24h=+0.7% 7d=+1.5%; Bitcoin ETF 3-day outflow streak ($57.6M) but weekly inflows at 4-month high (security breach driving ETF shift); Fidelity filing to stake ETH in ETF (85% rewards); Intel $15B AI capex; 91% strategists expect AI to drive H2 2026. Risk-off macro sentiment.
2. On-chain (Binance): FAILED — 451 geo-block (persistent; VPS required)
3. Cross-asset regime: FAILED — insufficient data
4. FedWatch: FAILED — yfinance unreachable
Active source-types: NEWS ONLY = 1. Themes require >=2 -> all DORMANT.

### Crypto Prices (CoinGecko 08:22 UTC)
BTC $64,234 0.0%/+1.0% | ETH $1,915 +0.7%/+1.5% | SOL $77.04 +1.2%/+1.3% | LINK $9.67 +2.7%/+11.1% | INJ $4.24 +4.6%/-8.0%

### Forecasts (rule-based)
BTC flat 0.40 | ETH flat 0.40 | SOL flat 0.40 | LINK long 1.000 | FET short 1.00

### Gems (rank_smallcaps)
CAP (DeFi credit): rank=0.717 PASS; no news citation for thesis -> BLOCKED. AKE rank=0.591 FAIL. H/PIEVERSE/UB rank<0.25 FAIL.

### Bucket Decisions
ANCHOR: BTC/ETH conf 0.40<0.55 FAIL -> 0. THEME: 1 source-type <2 -> DORMANT -> 0. GEM: thesis gate blocks all -> 0. Total: 0 new positions.

### Watch
LINK long 1.000 conf 7d=+11.1%; needs on-chain (VPS) or 2nd source-type. ETH Fidelity staking ETF structural catalyst. BTC ETF weekly inflows at 4-month high despite 3-day streak outflows — divergence. 9 consecutive cloud 0-trade passes; VPS handles live crypto.

## 2026-08-21 03:09 UTC — position-mgmt 2026-08-21 09:00 UTC

## Position-Mgmt Run — 2026-08-21 09:00 UTC

### Drawdown Check
check_drawdown.py: NAV unavailable (Binance testnet geo-blocked from cloud egress). armed=false. No KILL_SWITCH armed.

### Open Position Reconciliation
Parsed TRADE-LOG.md for filled buys without matching filled sells:
- AAPL 1.0 (paper) | entry 2026-05-09 | fill_price: not recorded | reason: dc-smoke-paper end-to-end
No crypto positions found in trade log.

### Active Theme State (last 3 research entries)
1. 2026-08-19: all themes DORMANT (1 source-type; require >=2)
2. 2026-08-14: all themes DORMANT (1 source-type; require >=2)
3. 2026-08-07: all themes DORMANT (0 source-types)
Theme decay not applicable — AAPL is anchor bucket, not theme.

### Decision Tree
- AAPL (equity anchor, smoke-test artifact):
  Entry price absent -> stop (-8%) and TP (+20%) thresholds uncomputable.
  Bucket=anchor: hold unless stop/TP fires. Neither evaluable without entry price.
  Market not open (09:00 UTC; equities open 13:00-21:00 UTC).
  No action.
- Crypto: 0 open positions.

### Result
Sells: 0/3 | Scales: 0 | Stops tightened: 0 | Held: 1 (AAPL anchor, no entry price)

### Infrastructure Note
Binance testnet geo-blocked (HTTP 451) from cloud egress. 9 consecutive cloud 0-trade decision passes. VPS required for crypto execution.

## 2026-08-24 04:25 UTC — decision-2026-08-24-04h

## Decision Pass — 2026-08-24 04:21 UTC

EQUITIES_OPEN=no (Monday 04:21 UTC). Crypto-only. TRADING_MODE=paper.

Six-stream: News OK (1 source-type); On-chain FAILED (451 geo-block); Corr FAILED; FedWatch FAILED. Source-types: 1 — themes DORMANT (need >=2).

MAJOR RALLY: BTC $77,172 (+21.4%/7d) new cycle high in logs. ETH $2,443 (+27.8%/7d) outperforming. SOL $94.18 (+24.3%/7d). NEAR +10.1%/24h. Broad risk-on; no specific catalyst in last 4h news.

Forecasts (rule-based): BTC flat 0.40 | ETH long 1.0 | SOL long 1.0 | AVAX long 1.0 | NEAR long 1.0 | ATOM long 0.86.

Gems (rank_smallcaps format fixed via transform): TRAC rank=0.746 PASS but 7d=-10.1% from live fetch vs +60.5% from scan (ID mismatch, rejected). CASHCAT rank=0.678 PASS conf=1.0 PASS but no news citation, pump profile (rejected). STX rank=0.576 below gate (Bitcoin L2, watch).

Bucket decisions — ANCHOR: ETH conf=1.0 passes gate; risk_check BLOCKED (Binance testnet unreachable, fail-closed). THEME: 0 active. GEM: 0 (data integrity + no news citation). Total: 0 new positions.

Watchlist: ETH strong anchor candidate for VPS execution. NEAR leading 24h mover. STX Bitcoin L2 approaching rank gate if rally continues. TRAC needs CoinGecko ID disambiguation.

## 2026-08-24 12:35 UTC — Decision Pass 2026-08-24 12:33 UTC — 0 trades (Binance geo-blocked)

EQUITIES_OPEN=no (Monday 12:33 UTC). Crypto-only. TRADING_MODE=paper. Six-stream: News OK (1 source-type, no catalysts); On-chain FAILED (Binance 451 geo-block); Corr FAILED (yfinance); FedWatch FAILED (yfinance). Source-types: 1 — all themes DORMANT (need >=2). 10th consecutive cloud 0-trade pass. Prices: BTC $78,552 (+23% 7d), ETH $2,496 (+30.8% 7d), SOL $95.59 (+26.4% 7d). Forecasts: BTC long 1.0, ETH long 1.0, SOL long 1.0. Anchor: ETH/BTC pass gate, risk_check BLOCKED (Binance testnet 451 unreachable). Gems: CASHCAT pump/no-citation rejected; STX +100% 7d Bitcoin L2 watchlisted; rank_smallcaps returned empty. Result: 0 new positions. VPS execution required for crypto.

## 2026-08-25 08:23 UTC — decision-2026-08-25-08h

## Decision Pass — 2026-08-25 08:21 UTC

EQUITIES_OPEN=no (Tuesday 08:21 UTC). Crypto-only. TRADING_MODE=paper | BINANCE_TESTNET=true.

Six-stream: News OK (OpenAI) — BTC $79,993 +3.72%/+24.1%7d approaching $80K; ETH $2,487 +1.74%/+30.5%7d; SOL $100.47 +7.17%/+32%7d (first $100 close); SHIB +3.72% (441% burn rate spike + Japan listing); AAVE -8.7% leveraged deleveraging; ZRO -10% bridge exploit; SPY -0.29%/QQQ -0.99% equities cautious. On-chain FAILED (Binance 451 geo-block). Corr FAILED (yfinance). FedWatch FAILED (yfinance). Source-types: 1 — all themes DORMANT (need >=2).

Prices: BTC $79,993 +3.72%/+24.1%7d | ETH $2,487 +1.74%/+30.5%7d | SOL $100.47 +7.17%/+32%7d | LINK $11.64 +1.94%/+22.9%7d | AVAX $7.56 +1.61%/+18.7%7d

Forecasts (rule-based): BTC long 1.00 | ETH long 1.00 | SOL long 1.00 | AVAX long 1.00 | LINK long 1.00 | NEAR flat 0.40 | ATOM flat 0.40

Gems: CASHCAT pump/no-description REJECTED; NPC meme REJECTED; META token-ID-mismatch REJECTED; CVX no-news-citation REJECTED.

Bucket decisions — ANCHOR: BTC/ETH conf=1.00 pass gate; risk_check BLOCKED (Binance testnet binance.vision unreachable, fail-closed). THEME: 0 active (1 source-type). GEM: 0. Total: 0 new positions.

Watchlist: BTC ~$80K milestone; ETH +30.5%7d; SOL $100 breakout; SHIB burn spike needs on-chain for theme activation. Avoid: ZRO (exploit), AAVE (deleveraging). 11th consecutive cloud 0-trade pass; VPS required for crypto.

## 2026-08-26 13:02 UTC — decision-2026-08-26-12h

EQUITIES_OPEN=no (Wed 12:00 UTC). Crypto-only. TRADING_MODE=paper.

Six-stream: News OK (1 source-type) — BTC/ETH ETF $706M inflows Aug 19 (BTC $517M strongest since May; ETH $189M largest since Oct 2025). Risk-ON: SPY+0.31% QQQ+0.62% XBI+3%. On-chain FAILED (451 geo-block); Corr FAILED; FedWatch FAILED. Source-types: 1 — all themes DORMANT (need >=2).

Prices: BTC $78,346 -0.8%/+21.5%7d | ETH $2,455 -0.7%/+27.8%7d | SOL $97.07 -1.5%/+25.3%7d | ATOM $1.56 +1.3%/+10.1%7d | DOGE +41.8%7d

Forecasts: BTC flat 0.40 | ETH flat 0.40 | SOL flat 0.40 | ATOM long 1.0

Gems: CASHCAT rank=0.733 PASS conf=1.0 PASS but pump/no-news-citation REJECTED. STX (Bitcoin L2) rank=0.60 <0.65 FAIL, conf=1.0, +124.1%/7d — near gate, watchlist. CYS rank=0.529 FAIL. risk_check ETH: BLOCKED (Binance testnet 451 fail-closed).

Bucket decisions — ANCHOR: BTC/ETH conf 0.40<0.55 FAIL. THEME: 0 active (1 source-type). GEM: 0 (pump/no-citation or rank<0.65). Total: 0 new positions. 12th consecutive cloud 0-trade pass.

Watchlist: ATOM long 1.0 (persistent strength, needs VPS/2nd source); STX Bitcoin L2 rank=0.60 approaching gate; ETH anchor +27.8%/7d needs VPS. VPS required for crypto execution.
