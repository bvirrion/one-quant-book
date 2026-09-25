# 14. Cross-Currency Basis and FX Carry — brief and source ledger

## Brief

- **Hook.** Since 2008 borrowing dollars through the FX swap market has cost more than covered interest parity says it should; the gap is small, persistent and largest at quarter-ends, and it is where balance sheets are priced.
- **Sections.** FX carry: construction and crash risk; The cross-currency basis; Quarter-ends; Funding-driven trades.
- **Defines.** FX carry basket, basis funding trade, crash-hedged carry.
- **Uses (defined earlier).** cross-currency basis (B2.16), covered interest parity (B2.16), forward points (B2.16), carry crash (B8.20), carry strategy (B8.20), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** G10 carry basket; crash-hedged carry with options; quarter-end basis trade; basis funding arbitrage; carry with momentum filter.
- **Tutorial.** Build G10 carry baskets on firm.synthfut currencies with planted crash risk, hedge the crashes with synthetic options, and simulate a cross-currency basis with quarter-end spikes to trade.
- **Build.** `firm.fxcarry`: carry baskets, option-hedged carry, basis funding trades and quarter-end effects; Python.
- **Weekend problem.** Priced at the quarter-end — named result: the carry basket's Sharpe ratio with and without crash hedges, and the basis trade's quarter-end return.
- **Facts to verify.** Du, Tepper, Verdelhan 2018 (JF); Jurek 2014 crash-neutral currency carry trades (JFE); BIS on the cross-currency basis (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. W. Jurek, "Crash-neutral currency carry trades", Journal of Financial Economics 113(3) (2014) 325-347: G10 carry trades exploiting violations of uncovered interest parity delivered significant excess returns with annualised Sharpe ratios equal to or greater than equity market factors (1990-2012); using out-of-the-money FX options, crash-hedged portfolios show the high returns are not due to peso problems; crash risk premia account for at most one-third of the excess return | Crossref metadata; RePEc abstract | https://doi.org/10.1016/j.jfineco.2014.05.004 | 2026-09-25 | "crash risk premia account for at most one-third of the excess return to currency carry trades" | hook; section 1; strat:s2:cross-currency-basis-and-fx-carry:hedged; omsources |
| F2 | W. Du, A. Tepper, A. Verdelhan (2018), as in chapter 12: large, persistent CIP deviations for major currencies, not explained by credit risk or transaction costs, strongest for forwards that appear on banks' balance sheets at quarter-end | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/jofi.12620 | 2026-09-25 | as chapter 12 ledger F2 | hook; section 2; section 3; strat:s2:cross-currency-basis-and-fx-carry:qe; omsources |
| F3 | FRED: H.10 daily dollar exchange rates for EUR, JPY, GBP, CHF, AUD, NZD, CAD, SEK, NOK (DEXUSEU ... DEXNOUS) and OECD three-month interbank rates (IR3TIB01xxM156N) for those countries and the US, used only through derived statistics | FRED series pages (CSV) | https://fred.stlouisfed.org/series/DEXUSAL ; https://fred.stlouisfed.org/series/IR3TIB01AUM156N (and the others) | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_g10.py | section 1 |

## EXCLUDED

- BIS measurements of the cross-currency basis (Borio et al. 2016 Quarterly Review): page not fetchable as text; the chapter's basis is synthetic, sourced only for its quarter-end pattern (Du, Tepper, Verdelhan).
- FX option prices for real crash hedges: not free; the chapter's hedge is synthetic and Jurek's result quoted from his abstract.
- OECD three-month interbank rates are monthly averages or month-end values depending on the country: the chapter's real basket is approximate and says so.

