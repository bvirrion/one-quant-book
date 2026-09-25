# 17. Event-Driven Backtests — brief and source ledger

## Brief

- **Hook.** A strategy resting limit orders at the bid fills every time a bar's low touches its price, in the backtest. Live, it fills a third as often and mostly just before the price falls through.
- **Sections.** Architecture: clock, events, handlers; Orders and fills at bar level; Decision time and latency; Calendars and corporate actions in the loop; Determinism.
- **Defines.** event-driven backtest, simulated clock, fill model, touch fill, penetration fill, volume participation cap, partial fill, order lifecycle.
- **Uses (defined earlier).** order (B1.4), closing price (B1.13), call auction (B1.13), market-on-close order (B1.13), price-time priority (B1.19), trade-through (B1.9), decision time (ch16), execution lag (ch16), fidelity level (ch16), bar (ch2).
- **Tutorial.** Run a limit-order mean-reversion strategy on bars in firm.evbt with touch, penetration and volume-capped fill models, and compare with the level-1 result on the same signal.
- **Build.** `firm.evbt`: level-2 event-driven backtester (priority event queue on a simulated clock, strategy callbacks, order manager with the order lifecycle, pluggable fill models, portfolio and cash, deterministic replay) returning BacktestResult; Python.
- **Weekend problem.** The limit order that always filled — named result: the fill rate and P&L of a passive bar strategy under touch, penetration and capped fills, against the level-3 answer of chapter 18.
- **Facts to verify.** open-source event-driven backtester architectures (LEAN, Zipline documentation); Arnott, Harvey, Markowitz 2019 (JFDS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Zipline, open-source Python backtester (Quantopian): VolumeShareSlippage fills at most volume_limit of each bar's volume, default 0.025 (2.5%), at the bar's close price times (1 +/- price_impact x volume_share^2) | source file zipline/finance/slippage.py (master branch), DEFAULT_EQUITY_VOLUME_SLIPPAGE_BAR_LIMIT and the class docstring | https://github.com/quantopian/zipline/blob/master/zipline/finance/slippage.py | 2026-09-24 | "DEFAULT_EQUITY_VOLUME_SLIPPAGE_BAR_LIMIT = 0.025"; "Maximum percent of historical volume that can fill in each bar ... Default is 0.025 (i.e., 2.5%)"; "where price is the close price for the bar" | section 2; exo 2; pb 16; omsources |

## EXCLUDED

- LEAN (QuantConnect) architecture documentation: not fetched; the chapter describes firm.evbt's own architecture and cites only Zipline's documented default.
- Arnott, Harvey and Markowitz (2019): recorded in chapter 16; not repeated here.
- All fill counts, fill rates, P&L and mark-outs are computed on firm.tape bars and tested; the 2.5% cap is set to Zipline's default.
