# 28. P\&L Analytics and the Strategy Lifecycle — brief and source ledger

## Brief

- **Hook.** A market-making strategy earned less this month than last; the spread was narrower, volume was higher, a competitor arrived on one venue, and someone changed a parameter on the twelfth, and the morning report has to say which of these did it.
- **Sections.** Daily attribution of a market-making book; Parameter changes as experiments; Capture decay and competition; When to retire a strategy.
- **Defines.** strategy lifecycle, parameter change control, capture decay.
- **Uses (defined earlier).** daily P\&L attribution (B8.1), A/B test (B7.21), staged rollout (B7.21), post-publication decay (B7.13), kill criterion (B7.1), CUSUM test (B7.13), crowding (B7.28), mark-out curve (B7.23), spread capture (B7.23), adverse-selection cost (B7.23), inventory P\&L (B7.23), fill rate (B7.23).
- **Tutorial.** Attribute a synthetic market maker's daily P&L over a simulated year with firm.markout's decomposition, detect a planted competitor's arrival and a parameter change, run the parameter change as a randomised experiment, and apply a retirement rule.
- **Build.** `firm.mmattrib`: daily attribution (capture, adverse selection, inventory, fees, rebates) by instrument and venue, change-point detection on capture, parameter experiments by randomised days, a retirement rule; Python, on firm.markout and firm.abtest.
- **Weekend problem.** Which of these did it — named result: the attribution of the month-on-month P&L change to spread, volume, competition and the parameter change, against the planted truth.
- **Facts to verify.** Menkveld 2013 (the one HFT's P&L decomposition) (JFM); Virtu 10-K: capture and volume by segment over time (dated); Budish, Lee, Shim 2019 Will the market fix the market? (working paper) or equivalent on competition and capture.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Menkveld (2013): one large HFT acting as a market maker on Chi-X and Euronext; gross profit per trade EUR 0.88 = EUR 1.55 on the spread net of fees minus a EUR 0.68 positioning loss; positions under five seconds earned EUR 0.45, longer ones lost EUR 1.13; participation 8.1% (incumbent) and 64.4% (Chi-X) | A. J. Menkveld, "High frequency trading and the new market makers", Journal of Financial Markets 16(4), 2013, 712-740 | https://doi.org/10.1016/j.finmar.2013.06.006 | 2026-09-25 | abstract (ScienceDirect/SSRN): "The gross profit per trade is €0.88 which is the result of a €1.55 profit on the spread net of fees and a €0.68 'positioning' loss" | §3 (as verified for chapter 1, F5) |

## EXCLUDED

- Virtu 10-K capture and volume by segment over time; Budish, Lee and Shim (2019): not fetched; the chapter's attribution is on simulated data.
