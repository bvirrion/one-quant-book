# 12. Swap-Spread and Asset-Swap Trades — brief and source ledger

## Brief

- **Hook.** For years the swap rate sat below the Treasury yield of the same maturity, which a textbook says cannot last; it lasted because the trade that would close it uses balance sheet that banks no longer had.
- **Sections.** Swap spreads and asset swaps; Negative swap spreads; Balance sheet as a cost; Trades and their carry.
- **Defines.** swap-spread trade, balance-sheet cost.
- **Uses (defined earlier).** swap spread (B2.9), asset-swap spread (B2.21), repo rate (B2.5), DV01 (B2.3), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** long swap spread; asset-swap carry; swap-spread curve trade; year-end balance-sheet trade.
- **Tutorial.** Simulate Treasury, repo and swap curves with a planted balance-sheet cost that moves swap spreads, run swap-spread trades with their carry and funding, and measure the balance sheet they consume.
- **Build.** `firm.swapspread`: swap-spread and asset-swap trade accounting, carry, balance-sheet usage and a leverage-ratio cost; Python.
- **Weekend problem.** Below the Treasury — named result: the swap-spread trade's return with and without a balance-sheet charge.
- **Facts to verify.** Du, Tepper, Verdelhan 2018 deviations from covered interest rate parity (JF) (balance-sheet argument); Jermann 2020 negative swap spreads and limited arbitrage (RFS); FRED swap and Treasury rates (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | U. J. Jermann, "Negative swap spreads and limited arbitrage", Review of Financial Studies 33(1) (2020) 212-238: since October 2008 30-year swap fixed rates have mostly been below Treasury rates of the same maturity, which under standard assumptions implies arbitrage; a model where frictions for holding bonds limit arbitrage shows negative swap spreads should not be surprising, and matches empirical spreads without large demand imbalances in swaps | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhz030 | 2026-09-25 | abstract: "Since October 2008, fixed rates for interest rate swaps with a 30-year maturity have been mostly below Treasury rates with the same maturity"; "frictions for holding bonds limit arbitrage" | hook; section 2; section 3; strat:s2:swap-spread-and-asset-swap-trades:long; omsources |
| F2 | W. Du, A. Tepper, A. Verdelhan, "Deviations from covered interest rate parity", Journal of Finance 73(3) (2018) 915-957: CIP deviations imply large, persistent, systematic arbitrage opportunities not explained by credit risk or transaction costs; strongest for forward contracts that appear on banks' balance sheets at quarter-end, pointing to a causal effect of banking regulation; correlated with other fixed-income spreads | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/jofi.12620 | 2026-09-25 | abstract: "They are particularly strong for forward contracts that appear on banks' balance sheets at the end of the quarter, pointing to a causal effect of banking regulation on asset prices" | section 3; strat:s2:swap-spread-and-asset-swap-trades:yearend; omsources |
| F3 | ICE (formerly ISDA) US dollar swap rates at 2, 5, 10 and 30 years (FRED DSWP2 ... DSWP30, July 2000 to October 2016) and H.15 constant-maturity Treasury yields (DGS2 ... DGS30), used only through derived statistics | FRED series pages (CSV) | https://fred.stlouisfed.org/series/DSWP10 (and DSWP2, DSWP5, DSWP30, DGS2 ... DGS30) | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_swaps.py | hook; section 2 |

## EXCLUDED

- Swap spreads after October 2016 (SOFR swaps): not on FRED; the chapter's real statistics stop in 2016 and say so.
- The supplementary leverage ratio's calibration (e.g. 5% for large US banks): not fetched; the chapter's 5% capital and 10% hurdle are its own assumptions for the charge.
- Named banks' balance-sheet charges: none quoted.

