# 17. Options and Derivatives — brief and source ledger

## Brief

- **Hook.** A screen shows a call at 7.10 and a put at 2.40 on the same stock, same strike 100, same three-month expiry, with the stock at 104 and rates at 4 per cent. The candidate is given ten seconds to say whether there is money on the table and, if so, what to trade.
- **Sections.** No-arbitrage: parity, bounds and convexity in the strike; Greeks by intuition: signs, shapes and where they peak; The smile and what it implies; Hedging scenarios: gamma, theta, vega and the P&L of a hedged book.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** call option (B1.23), put option (B1.23), American exercise (B1.23), European exercise (B1.23), put--call parity (B1.25), implied volatility (B1.25), volatility skew (B1.25), box spread (B5.1), Black--Scholes formula (B5.3), Greeks (B5.4), delta (B1.26), gamma (B1.26), vega (B5.4), theta (B5.4), hedging P\&L (B5.4), break-even volatility (B5.4), cash gamma (B5.4), straddle (B5.4), early-exercise premium (B5.6), digital option (B5.15), variance swap (B5.14), local volatility (B5.9), risk-neutral measure (B4.5).
- **Question bank.** 14 questions, 5/5/4. Families: parity checks with numbers (the hook's quotes, with dividends); bounds on calls and puts, and convexity in the strike (a butterfly with a negative price); early exercise of American calls and puts (when it can be optimal); Greeks' signs and peaks (gamma of an at-the-money option near expiry, the vega of a digital); the at-the-money approximation of a call's price (numeric, against Black-Scholes); a delta-hedged book's P&L over a day (gamma times the squared move against theta, numeric); a smile question (what a steep put skew implies for the density, the digital priced off the skew); a variance-swap replication question. Roles: trader 7, researcher 2, bank 4, risk 2. Firms: market maker 6, bank 5, proprietary firm 1, multi-manager fund 1, any 2.
- **Facts to verify.** none external: all answers derived (pointers to Book 1 ch. 25-26 and Book 5 ch. 1-6, 9, 14-15).
- **Data.** Figures: one chart (gamma and theta of a call against the spot at three expiries; fig_iv_greeks.py). Code: iv_options.py (Black-Scholes and Greeks from scipy.stats.norm; parity and bound checks; the at-the-money approximation's error; a hedged-P&L simulation over seeds).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Breeden and Litzenberger, Prices of state-contingent claims implicit in option prices, Journal of Business 51(4), 1978 (first page 621) | Crossref | https://api.crossref.org/works/10.1086/296025 | 2026-09-29 | title, journal, volume, issue, first page | section 3; omsources |

## EXCLUDED

