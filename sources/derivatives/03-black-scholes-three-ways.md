# 3. Black--Scholes Three Ways — brief and source ledger

## Brief

- **Hook.** On 26 April 1973 the Chicago Board Options Exchange listed its first calls; the paper that priced them appeared in the Journal of Political Economy that same spring.
- **Sections.** The model and the replication argument; The pricing equation; The martingale route; The binomial limit; Black's formula on forwards, and what each derivation teaches.
- **Defines.** Black--Scholes model, Black--Scholes equation, Black--Scholes formula, Black model.
- **Uses (defined earlier).** geometric Brownian motion, Feynman--Kac formula (Book 4 ch. 4), Itô's formula (Book 4 ch. 3), Girsanov's theorem, numeraire (Book 4 ch. 5), implied volatility, put--call parity (Book 1 ch. 25), delta, delta hedging (Book 1 ch. 26), replicating portfolio, self-financing strategy, risk-neutral measure (Book 4 ch. 5), Cox--Ross--Rubinstein tree (ch. 2), futures option (Book 3 ch. 12).
- **Tutorial.** Implement the Black-Scholes and Black formulas and a robust implied-volatility solver (rational initial guess, Newton safeguarded by bisection); check them against the tree of chapter 2 and against put-call parity to machine precision.
- **Build.** `firm.bs`: Black-Scholes / Black kernels: price, analytic Greeks, implied volatility (Python, C++20, Rust) — the inner loop every later engine and Book 6's risk engine call.
- **Weekend problem.** One price, three derivations — named result: the price of a one-year at-the-money call by the formula, by a 1,000-step tree and by 10^6 Monte Carlo paths, with the error of each.
- **Facts to verify.** CBOE first trading day 26 April 1973, calls on 16 stocks; Black & Scholes 1973 JPE 81(3) 637-654; Merton 1973 Bell Journal; 1997 Nobel prize (Scholes, Merton; Black died 1995); Black 1976 JFE 'The pricing of commodity contracts'; Jäckel 2015 'Let's be rational' (implied-volatility solver).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Cboe opened on 26 April 1973, standardised call options on 16 stocks; opening-day volume 911 contracts | H. A. Baker, "Cboe at 50", Financial History (Museum of American Finance), Spring 2023 (PDF, pdftotext) | https://static.moaf.org/docs/Cboe%2050th%20Anniversary.pdf | 2026-09-24 | "Fifty years ago, on April 26, 1973, the Chicago Board Options Exchange (Cboe) opened its doors"; "covering call options on 16 stocks"; "its opening day trading volume of 911 contracts" | hook |
| F2 | Black and Scholes, JPE 81(3), May-June 1973, 637-654 | IDEAS/RePEc record; U. Chicago Press | https://ideas.repec.org/a/ucp/jpolec/v81y1973i3p637-54.html | 2026-09-24 | "Vol. 81, No. 3 (May - Jun., 1973), pp. 637-654" (search summary of the record) | hook; omsources |
| F3 | 1997 prize to Merton and Scholes; Black died in 1995 | NBER news item on the 1997 prize (nobelprize.org press release returned 403) | https://www.nber.org/news/robert-c-merton-and-myron-s-scholes-won-1997-nobel-prize-finding-ways-value-stock-options-and-other | 2026-09-24 | "developed this method in close collaboration with Fischer Black, who died in his mid-fifties in 1995" (press release as quoted in search) | not printed (background) |
| F4 | Merton, "Theory of rational option pricing", Bell Journal of Economics and Management Science 4(1) (1973) 141-183 | RePEc record | https://www.hbs.edu/faculty/Pages/item.aspx?num=8804 | 2026-09-24 | "Bell Journal of Economics and Management Science" 4(1), spring 1973, 141-183 (search summary of the record) | hook; omsources |
| F5 | Black, "The pricing of commodity contracts", JFE 3(1-2) (1976) 167-179 | RePEc record | https://ideas.repec.org/a/eee/jfinec/v3y1976i1-2p167-179.html | 2026-09-24 | bibliographic record | def Black model; omsources |
| F6 | Jäckel, "Let's be rational", Wilmott 2015 (75) 40-53: implied volatility to machine precision in two iterations | author's site | https://onlinelibrary.wiley.com/doi/abs/10.1002/wilm.10395 | 2026-09-24 | "with as little as two iterations to maximum attainable precision on standard (64-bit floating point) hardware for all possible inputs" (abstract, via search) | method box; omsources |

## EXCLUDED

- The legend of traders' calculators programmed with the formula in the 1970s: not used.
