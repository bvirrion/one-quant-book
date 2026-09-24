# 16. Asians, Lookbacks, Cliquets and Forward-Starts — brief and source ledger

## Brief

- **Hook.** A corporate treasurer is quoted an option on the monthly average price, 30% cheaper than the vanilla; nobody on the call can say where the 30% went.
- **Sections.** Averaging: Asians; Extremes: lookbacks; Forward-starts and the forward smile; Cliquets; Which model for which payoff.
- **Defines.** Asian option, lookback option, forward-start option, cliquet, reverse cliquet.
- **Uses (defined earlier).** average-price option (Book 3 ch. 12), forward smile, local volatility (ch. 9), stochastic volatility model (ch. 10), Bergomi model (ch. 12), control variate, Monte Carlo (Book 4 ch. 26).
- **Tutorial.** Price an arithmetic Asian by Monte Carlo with the geometric Asian as control variate; then price a forward-start and a cliquet under Black-Scholes, local volatility and Heston calibrated to the same smile, and compare.
- **Build.** `firm.pathdep`: path-dependent payoff library (Asian, lookback, forward-start, cliquet with local and global caps and floors) on a common path interface.
- **Weekend problem.** The cliquet that fits every vanilla — named result: the gap between the local-volatility and the Heston price of a one-year monthly cliquet when both fit the same surface.
- **Facts to verify.** Kemna-Vorst 1990 geometric control variate; Goldman, Sosin, Gatto 1979 lookbacks; Rubinstein 1991 forward-start options; Bergomi on cliquets and forward skew (Risk 2004/2005); reverse-cliquet losses of the early 2000s (only with a source).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Kemna and Vorst, "A pricing method for options based on average asset values", Journal of Banking and Finance 14(1) (1990) 113-129 | Crossref record 10.1016/0378-4266(90)90039-5 | https://api.crossref.org/works/10.1016/0378-4266(90)90039-5 | 2026-09-24 | Crossref metadata | sec. Asians, omsources |
| F2 | Goldman, Sosin and Gatto, "Path dependent options: buy at the low, sell at the high", Journal of Finance 34(5) (1979) 1111-1127 | Crossref record 10.1111/j.1540-6261.1979.tb00059.x | https://api.crossref.org/works/10.1111/j.1540-6261.1979.tb00059.x | 2026-09-24 | Crossref metadata | sec. lookbacks, omsources |
| F3 | Bergomi, "Smile dynamics", Risk, September 2004: the pricing of reverse cliquets and Napoleons depends more on the assumed dynamics of implied volatilities than on today's vanilla prices; example of a six-year Napoleon (6% coupons for two years, then 8% plus the worst of the 12 monthly performances of the Eurostoxx 50 each year, floored at zero) that is in effect a put on long forward volatility; in Heston, forward smiles are more convex than today's smile, and for short-term forward-start options Heston is likely to overemphasise low at-the-money volatility / high skew scenarios; the vol-of-vol calibrated to smiles is about twice its historical value | L. Bergomi, "Smile dynamics", Risk, September 2004 (PDF via pdftotext) | https://www.maths.univ-evry.fr/pages_perso/crepey/Finance/0904_tech_bergomi.pdf | 2026-09-24 | quoted passages on pp. 117-121 | hook of sec. cliquets; sec. which model; omsources |
| F4 | Jeffery, "Reverse cliquets: end of the road?", Risk, February 2004, pp. 20-22 (a review article cited by Bergomi 2004) | reference list of Bergomi (2004) | https://www.maths.univ-evry.fr/pages_perso/crepey/Finance/0904_tech_bergomi.pdf | 2026-09-24 | reference entry "Jeffery C, 2004, Reverse cliquets: end of the road? Risk February, pages 20-22" | sec. cliquets |
| F5 | Bergomi, "Smile dynamics II": a model controlling the short forward skew, spot/vol correlation and term structure of vol-of-vol separately; pricing examples include a reverse cliquet and a Napoleon | Crossref record of SSRN 1493302 (abstract) | https://api.crossref.org/works/10.2139/ssrn.1493302 | 2026-09-24 | abstract in Crossref | sec. which model |

## EXCLUDED

- Rubinstein (1991) on forward-start options: no fetchable record; the forward-start formula is derived in the text from homogeneity and not attributed.
- Losses on reverse cliquets in the early 2000s (sizes, firms): not verified beyond the title of Jeffery (2004); the chapter states only that the product's troubles were the subject of that review.
