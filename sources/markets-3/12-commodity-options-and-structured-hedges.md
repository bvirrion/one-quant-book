# 12. Commodity Options and Structured Hedges — brief and source ledger

## Brief

- **Hook.** Every year Mexico's finance ministry buys put options on its oil exports; in a year of collapsing prices the programme paid it billions of dollars.
- **Sections.** Options on commodity futures; Average-price and calendar-spread options; Swing contracts; Collars and three-way collars; Producer, consumer and sovereign hedging programmes.
- **Defines.** futures option, average-price option, calendar-spread option, swing contract, take-or-pay clause, collar, three-way collar, hedging programme.
- **Uses (defined earlier).** calendar month average, commodity swap, calendar spread, implied volatility, volatility skew, American exercise, expiry, call option, put option, delta hedging, Samuelson effect, Asian option (Book 5), spread option (Book 6), Monte Carlo simulation (Book 4).
- **Tutorial.** Price an average-price option against a vanilla option on the same future by Monte Carlo under a lognormal future, and tabulate a three-way collar's payoff against a swap and a put across price scenarios.
- **Build.** `firm.hedgeprog`: hedging-programme evaluator (swaps, puts, collars, three-ways, average-price options on simulated price paths; hedged budget and cash flow at risk); uses `firm.commcurve`.
- **Weekend problem.** The finance ministry's put — named result: the cost of the put programme as a share of hedged export revenue and its payout in a year like 2009 or 2015, against a three-way collar of the same premium.
- **Facts to verify.** Mexico oil hedge costs and payouts by year (SHCP reports or official statements); NYMEX WTI option expiry relative to the futures (CME rule); CME average-price options on WTI (contract spec); airline fuel hedging disclosures (a 10-K); swing contract clauses (DCQ, ACQ) from a regulator or academic source; Ecuador or other sovereign hedge (only with a source).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Mexico's oil hedge payouts: almost $5.1bn in December 2009, $6.4bn in 2015, $2.7bn in 2016; executed with Wall Street banks | MoneyWeek, "Mexico's lucrative Hacienda hedge", 21 April 2017 | https://moneyweek.com/465651/mexicos-lucrative-hacienda-hedge | 2026-09-24 | "In December 2009, the proceeds from the wager totalled almost $5.1bn"; "In 2015, Mexico earned $6.4bn and $2.7bn the next year" | hook; dat:m3:commodity-options-and-structured-hedges:mexico |
| F2 | Mexico hedges the year ahead with Asian put options at various strike prices | Jain Family Institute (JFI Research), "Mexico's Petroleum Hedging Program", 6 Sep 2023 (pdftotext) | https://jfiresearch.org/wp-content/uploads/2023/09/JFI-Hacienda-Hedge-2023.09.06.pdf | 2026-09-24 | "for the year ahead in the form of Asian put options at various strike prices" | dat:m3:commodity-options-and-structured-hedges:mexico |
| F3 | NYMEX Light Sweet Crude Oil Option (ch. 310): expires at the close of trading on the third business day immediately preceding the expiration of the underlying futures; American-style | CME Group, NYMEX Rulebook ch. 310 (Internet Archive copy) | https://web.archive.org/web/2025/https://www.cmegroup.com/content/dam/cmegroup/rulebook/NYMEX/3/310.pdf | 2026-09-24 | "shall expire at the close of trading on the third business day immediately preceding the expiration of the underlying Light Sweet Crude Oil futures contract"; "The option is an American-style option" | section on futures options |
| F4 | NYMEX WTI Average Price Option (ch. 341): value at expiration is the difference between the average daily settlement price during the calendar month of the first nearby Light Sweet Crude Oil futures and the strike, times 1,000 barrels; expires on the last business day of the calendar month; cash-settled European-style | CME Group, NYMEX Rulebook ch. 341 (Internet Archive copy) | https://web.archive.org/web/2025/https://www.cmegroup.com/rulebook/NYMEX/3/341.pdf | 2026-09-24 | "A WTI Average Price Option Contract shall expire on the last business day of the Calendar Month"; "a cash-settled European-Style Average Price option" | section on futures options |
| F5 | January 2020: Mexico's finance minister said the annual cost of the oil hedge is around USD 1bn; deputy minister Gabriel Yorio said the average cost over the programme's life has been USD 1.2bn | Alto Nivel (with Reuters), 10 Jan 2020 | https://www.altonivel.com.mx/que-son-las-coberturas-petroleras-y-cuanto-le-cuestan-a-mexico/ | 2026-09-24 | "el costo anual de la cobertura petrolera ronda los 1,000 millones de dólares"; "en promedio durante toda la vida del programa el costo de la cobertura ha sido de 1,200 millones de dólares" | dat:m3:commodity-options-and-structured-hedges:mexico |

## EXCLUDED

- Annual cost of Mexico's hedge (reported by secondary sources as about $1-1.5bn a year): not confirmed from an official document; not stated. **restored → F5 (officials' statements as reported by the press; no official document found, re-searched 2026-09-24).**
- Executing institution (central bank vs ministries): sources differ; not stated. **re-searched 2026-09-24: not found in an official source; not stated.**
- WTI option expiry rule relative to the futures: not verified; the text says "shortly before". **restored → F3.**
- CME average price option contract details: not fetched; the text describes the product generically. **restored → F4.**
