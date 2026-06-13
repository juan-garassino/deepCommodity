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
