# deepCommodity — Live-Readiness Remediation Design

**Date:** 2026-06-13
**Status:** Approved (design); pending implementation plan
**Author:** Juan Garassino + Claude Code
**Source:** 6-agent parallel safety audit (2026-06-13)

## 1. Context

`deepCommodity` is an agentic quant trader where Claude Code (in cloud routines) is the
decision-maker and Python tools fetch data, gate, and place orders. A full safety audit
ahead of go-live found **9 BLOCKER-class defects plus a set of HIGH-severity issues**. The
unifying root cause: **risk limits are enforced by trusting the LLM to follow the prompt, not
by code.** Several documented "hard" limits are decorative (stubbed inputs, dead code, or
fail-open fallbacks). The test suite is green (147/0) but verifies the guardrail *math* in
isolation while the *wiring* to real orders is broken or untested.

This design fixes all of it. It is scoped to a single weekend of TDD work, ending in a
paper-validated system whose live keypair flip is one env change away, on the operator's go.

## 2. Goals / non-goals

**Goals**
- Make every risk limit **code-enforced** against **real broker state**, fail-closed.
- One auditable code path from decision to `broker.submit()`; impossible to reach submit
  without passing every gate.
- Full TDD coverage of the execution + gate paths (currently 0%).
- A reliable halt mechanism that reaches headless cloud routines.
- Harden the prompt-injection surface and the agent's capability blast radius.
- Keep CLAUDE.md / TRADING-STRATEGY.md / AGENT-INSTRUCTIONS.md / .env.sample current.

**Non-goals (this weekend)**
- Real money at full intended NAV. Posture is **code-complete + paper-validated**; live flip
  is a deliberate, separate, operator-gated step.
- A standalone risk daemon / RPC service (over-engineered for one operator).
- Real Bitfinex sandbox routing (Bitfinex is disabled in the live path instead).
- New alpha/model work. This is purely a safety remediation.

## 3. Decisions (resolved design forks)

| Fork | Decision |
|---|---|
| Risk posture | Code-complete + paper-validated this weekend; live keypair flip on operator go after a clean paper run. |
| Source of truth | **Broker is the only authoritative source** for NAV, positions (USD notional), today's fills, sector map, read at order time. Fail **closed** if unavailable. |
| Halt mechanism | **Env-var halt** (`DC_HALT=true` or `TRADING_MODE=halt`) in the cloud environment, fail-closed; local `KILL_SWITCH` file anchored to repo root for local runs. |
| Bitfinex (B7) | **Disable in live path** (hard-fail any real-order route); keep the module. |
| Scope | All 9 BLOCKERs + every HIGH + ops fixes + a final adversarial re-sweep of changed code. |
| Structure | **Approach A** — single chokepoint `preflight()` + broker-backed `PortfolioProvider`. |

## 4. Architecture

### 4.1 `deepCommodity/execution/portfolio.py` (new)

`PortfolioProvider` ABC returning a real `Snapshot`:

```
Snapshot(
    nav_usd: float,
    cash_usd: float,
    positions: dict[str, float],        # symbol -> USD notional
    sector_notional: dict[str, float],  # sector -> USD notional
    new_positions_today: dict[str, int],  # bucket -> count of new positions opened today (total = sum)
    as_of: datetime,
    source: str,
)
```

- `AlpacaPortfolioProvider` — `nav=account.equity`, `cash=account.cash` (read, not derived),
  `positions={sym: market_value}`; `new_positions_today` from the orders API filtered to
  buys filled today (UTC) on symbols not already held at start of day.
- `BinancePortfolioProvider` — **fixes B5**: values *all* balances via tickers
  (`free+locked` × mark price); `nav = Σ balances_usd`; `positions = {asset: usd_notional}`
  for non-stable assets; `cash = free USDT`; `new_positions_today` from trade/order history
  for the UTC day.
- `sector_notional` — map each held symbol → sector via `themes.yaml` / `Universe`, summed.
- `MockPortfolioProvider` — explicit values for tests.
- **Any API failure raises `PortfolioUnavailable`. Never fabricates a snapshot.** (kills B3)
- Bucket attribution: the broker is authoritative for *which orders actually filled today*;
  the per-bucket label for each filled symbol is joined from TRADE-LOG.md (by symbol + UTC
  date). A filled symbol with no matching journal entry counts toward the **total** cap and is
  conservatively attributed to the tightest applicable bucket. The safety-critical fact (a real
  fill happened) is never taken from the journal alone.
- Invariant assertion: `sum(positions.values()) <= nav_usd + epsilon`.

### 4.2 `deepCommodity/guardrails/preflight.py` (new) — the chokepoint

`preflight(proposal, provider, *, mode, now) -> Decision(allow: bool, reason: str, code: str)`
is the **only** path to `broker.submit()`. Fail-closed at every step, in order:

1. **Halt.** Halted if `DC_HALT` truthy OR `TRADING_MODE==halt` OR repo-root `KILL_SWITCH`
   exists. If halt-state cannot be *positively confirmed* (e.g. cannot read the env / file),
   treat as halted → block. (B6)
2. **Input validation.** `qty`, `price`, `notional` must be finite and `> 0`; `confidence`
   (if present) clamped to `[0,1]`; reject non-finite. (notional=0 / NaN / negative)
3. **Snapshot.** Fetch via provider; on `PortfolioUnavailable` → block. (B3)
4. **Limits** (enhanced `check_limits`, all against the real snapshot):
   - `nav_usd > 0` else block.
   - position cap: `(existing_holding_notional + proposal_notional) / nav <= 0.05`
     (existing-holding-aware → no pyramiding).
   - sector cap: `(sector_notional[sector] + proposal_notional) / nav <= 0.30`.
   - cash floor: `cash_after = cash - proposal_notional; cash_after >= 0.10 * nav`.
   - gross leverage: `(Σ positions + proposal_notional) / nav <= 1.0`.
   - daily count: the proposal carries its `bucket` (anchor/theme/gem). If
     `proposal.symbol not in positions`, block when either the **total** daily new-position
     cap (3) OR the **per-bucket** cap (anchor 1 / theme 2 / gem 1) is already met by
     `new_positions_today` (counted per-bucket from real fills). (B2)
   - tighten-not-loosen invariant preserved (min(hard, strategy)).

`place_order.py` and `risk_check.py` both call `preflight` — single source of gate truth, no
divergence.

### 4.3 Changed modules

- **`guardrails/limits.py`** — `check_limits` enhanced per §4.2 (existing-holding-aware
  position cap, gross leverage, finiteness guards). Fed real data, never stubs.
- **`guardrails/kill_switch.py`** — anchor root to `Path(__file__).resolve().parents[2]`;
  add `halt_state() -> (halted, confirmed, reason)` covering env + file.
- **`guardrails/circuit_breaker.py`** + new **`tools/check_drawdown.py`** (run by
  `position-mgmt`): fetch NAV, compare to committed `state/nav_baseline.json`
  (daily + weekly baselines), evaluate `daily_pnl_breach` / `weekly_pnl_breach`, and on breach
  **arm the halt** (write KILL_SWITCH + Telegram). Fail-closed: if PnL can't be computed, arm.
  (B4)
- **`tools/place_order.py`** — rewrite:
  - build proposal; **fetch reference price from the broker** (don't trust `--price`; validate
    it if supplied).
  - call `preflight`; only on `allow` generate a deterministic `client_order_id`
    (hash of symbol+side+qty+date-bucket+reason) and call `broker.submit`.
  - map result honestly: `accepted` vs `filled` (don't journal an unfilled market order as
    filled); correct exit codes (0 ok / 2 halt / 3 blocked / 4 broker-reject).
  - **B1 live gate in code**: live requires `TRADING_MODE==live` AND
    `DAILY_DECISION_AUTHORIZE_LIVE==true` AND `--confirm-live` AND `nav <= DC_MAX_NAV_USD`.
  - `_envbool(name, default)` helper (`.strip().lower()` ∈ {true,1,yes}) used everywhere.
- **`tools/risk_check.py`** — thin CLI wrapper over `preflight`; exit 0 allow / 1 block /
  2 halt; fail-closed on provider error.
- **`tools/forecast.py`** — api path clamps confidence to `[0,1]`, rejects non-finite,
  validates `direction`.
- **Execution adapters**:
  - `bitfinex_adapter.py` — **B7**: hard-fail in `__init__`/`submit` unless an explicit
    `BITFINEX_SANDBOX_CONFIRMED` flag is set (we never set it) → disabled in live path.
  - `alpaca_adapter.py` — assert paper/live consistency: `mode != live` forces `paper=True`;
    `mode == live` requires explicit `ALPACA_PAPER=false` + the live-enable gate; reject
    mismatched combos at construction.
  - `binance_adapter.py` — `_envbool` hardening; `amount_to_precision` (round **down**) +
    re-assert `qty > 0` after rounding (M1); pass `clientOrderId`.
  - new **`MockBroker`** recording submitted `OrderRequest`s for tests. (enables B9)

### 4.4 Security

- **`.claude/settings.json`** — **B8**: remove `Bash(python:*)` / `Bash(python3:*)`; allowlist
  only the specific tool entrypoints the routines call (`Bash(python tools/fetch_news.py:*)`,
  …, `Bash(python tools/place_order.py:*)`, `Bash(python -m pytest:*)`). Keep existing denies.
- **`guardrails/sanitize.py`** — rebuild: NFKC-normalize, strip zero-width/control chars, strip
  HTML, wrap fetched text in explicit `<UNTRUSTED_DATA>…</UNTRUSTED_DATA>` delimiters; demote
  the regex blocklist to telemetry only. Route `scan_hidden_gems` (name + description) and the
  8-K `title` through it. Stop echoing raw `r.text` / `str(e)` into agent-facing stdout.
- **`serving/auth.py`** — fail-closed: refuse to start if `DC_API_KEY` unset; bind localhost by
  default.

### 4.5 Ops

- `requirements.txt` — pin every dependency (`==`); add `requests`; drop unused heavy deps
  (twine, mlflow, gcsfs, s3fs, pmdarima, statsmodels) from the runtime set.
- `deploy/run_routine.sh` — prompt path → `.claude/routines/managed/${ROUTINE}.md`.
- `tools/persist_logs.sh` — on push failure: Telegram alert + non-zero exit.
- `position-mgmt` routine — code-enforced `--allow-buy` flag (default off); routine never sets
  it, making "never opens" structural rather than prose.
- H2 doc/code mismatch — reconcile the hidden-gem confidence threshold across
  TRADING-STRATEGY.md and CLAUDE.md and encode it in the gem gate.

## 5. Test strategy (TDD — tests precede each fix)

Built on `MockBroker` + `MockPortfolioProvider`:

- **preflight**: each limit blocks independently; pyramiding (existing + new) blocked; sector
  aggregate blocked; gross leverage blocked; 4th new position blocked via real fills; halt
  blocks; `PortfolioUnavailable` blocks; NaN/inf/0/negative qty blocked; confidence clamp.
- **place_order**: happy path → `submit` called exactly once → exit 0 → journal `filled`;
  broker reject → exit 4 → journal `rejected`; **live requires all three gates** — assert each
  one missing blocks; idempotency → duplicate deduped/rejected.
- **adapters**: Alpaca + Binance paper/live routing; Bitfinex hard-fails any real route.
- **drawdown**: simulated −5% day → `KILL_SWITCH` armed.
- **sanitize**: injection payloads neutralized/delimited; `scan_hidden_gems` + 8-K title
  sanitized.
- **risk_check CLI**: exit 0 / 1 / 2 contract.

## 6. Go-live gate

New `make dc-preflight-live` runs: full suite + `smoke_paper` + each routine's decision logic
in paper mode. Live keypair flip permitted **only** after a clean run **and** explicit operator
go. `DC_MAX_NAV_USD` provides a code-enforced float ceiling for the first live window. A final
**adversarial re-sweep** re-audits all changed code before sign-off.

## 7. Sequencing

1. Test scaffolding: `MockBroker`, `MockPortfolioProvider`.
2. `portfolio.py` providers (Alpaca, Binance, Mock) — TDD.
3. `preflight.py` + enhanced `limits.py` — TDD.
4. `place_order.py` rewrite over preflight + idempotency + live gate — TDD.
5. `risk_check.py` rewrite over preflight — TDD.
6. Adapter hardening (Bitfinex disable, Alpaca/Binance routing, rounding) — TDD.
7. Halt: `kill_switch.py` anchoring + env halt; `check_drawdown.py` + wiring — TDD.
8. Security: settings.json allowlist, sanitize rebuild + fetcher routing, serving auth.
9. Ops: requirements pin/+requests, run_routine path, persist_logs alert, position-mgmt flag.
10. Docs update (same commits).
11. `make dc-preflight-live` + adversarial re-sweep.

## 8. Docs to update (in the same commits as the code)

- **CLAUDE.md** — new modules (`execution/portfolio.py`, `guardrails/preflight.py`,
  `tools/check_drawdown.py`); new env vars (`DC_HALT`, `DC_MAX_NAV_USD`); new make target
  (`dc-preflight-live`); `.claude/settings.json` allowlist change; new halt mechanism; explicit
  "risk gates are code-enforced against live broker state, fail-closed" note; Bitfinex disabled
  in live path.
- **.env.sample** — `DC_HALT`, `DC_MAX_NAV_USD`, `DC_API_KEY` (mandatory note), any new vars.
- **TRADING-STRATEGY.md** — reconcile the hidden-gem confidence threshold (single source of
  truth); note gates are code-enforced.
- **AGENT-INSTRUCTIONS.md** — halt via env var; gates enforced in code not prompt;
  position-mgmt cannot open (code-enforced).
- **README.md** — only if run/setup instructions change (new make target, mandatory DC_API_KEY
  for serving).
