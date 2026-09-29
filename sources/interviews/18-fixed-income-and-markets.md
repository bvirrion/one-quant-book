# 18. Fixed Income and Markets — brief and source ledger

## Brief

- **Hook.** 'Tell me what happened in markets yesterday.' One candidate lists five closing levels. Another says two-year yields rose twelve basis points after a strong payroll number, the curve flattened, the dollar rallied, and equities recovered in the afternoon, and then says what she would have expected to see in the front-end futures. The interviewer asked for the second answer; only one candidate knew that.
- **Sections.** Price, yield, duration and convexity at interview speed; Curves: forwards, carry and roll-down; Repo, swaps and the basis in one paragraph each; The market recap: level, change, cause and the cross-asset link.
- **Defines.** market recap.
- **Uses (defined earlier).** yield to maturity (B2.3), par yield (B2.3), zero-coupon rate (B2.3), DV01 (B2.3), Macaulay duration (B2.3), modified duration (B2.3), convexity (B2.3), carry (B1.7), repurchase agreement (B1.6), repo rate (B2.5), interest-rate swap (B2.9), overnight index swap (B2.9), par swap rate (B2.9), swap spread (B2.9), covered interest parity (B2.16), economic release (B2.31), consensus forecast (B2.31), data surprise (B2.31), steepener (B2.31), curve fly (B2.31), sanity check (ch5).
- **Question bank.** 13 questions, 4/5/4. Families: price change from duration and convexity (numeric); DV01 of a position and the hedge ratio between two bonds (numeric); forwards implied by a curve and the carry and roll-down of a bond over three months (numeric); a repo-financed position's P&L; swap rate against a bond yield (what the swap spread says); a market recap from a supplied table of moves (the structure scored, not recall of real days); a cross-asset question (what a surprise rate hike does to the currency, the curve and equities, and why each can go the other way); covered interest parity with numbers. Roles: trader 5, bank 3, researcher 2, risk 2. Firms: bank 5, multi-manager fund 2, asset manager 2, market maker 1, any 2.
- **Facts to verify.** none external: the recap question uses a supplied synthetic table, never a real day's levels; method pointers to Book 2 ch. 3, 5, 9, 16, 31.
- **Data.** Figures: one chart (a synthetic curve today and in three months under an unchanged curve, showing roll-down; fig_iv_rolldown.py). Code: iv_rates.py (bond pricing, duration, convexity, DV01 hedges, forwards, carry and roll-down; exact to the printed precision).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Nelson and Siegel, Parsimonious modeling of yield curves, Journal of Business 60(4), 1987 (first page 473) | Crossref | https://api.crossref.org/works/10.1086/296409 | 2026-09-29 | title, journal, volume, issue, first page | figure; omsources |

## EXCLUDED

The recap uses a synthetic session only; no real day's levels are stated.

