# 25. Volatility as a Traded Quantity: First Contact — brief and source ledger

## Brief

- **Hook.** The option's price is 4.20; the trader says it is ``18 vol''.
- **Sections.** Put-call parity with dividends and borrow; Implied volatility; Skew and term structure; The volatility index; Futures on volatility.
- **Defines.** put--call parity, implied volatility, volatility skew, term structure of volatility, at-the-money, volatility index, variance, realised volatility, VIX future.
- **Tutorial.** Implied volatility by root finding; implied forward and borrow from parity.
- **Build.** Parity checker and implied-volatility solver.
- **Weekend problem.** Reading a chain — named result: the implied dividend and the skew.
- **Facts to verify.** Cboe VIX methodology white paper; VIX futures spec; Feb 2018 VIX spike numbers.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | VIX formula sigma^2 = (2/T) sum dK_i/K_i^2 e^{RT} Q(K_i) - (1/T)(F/K0 - 1)^2; Q = mid-quote; only options with non-zero bid; strip stops after two consecutive zero bids; K0 = first strike at or immediately below the forward index level; near- and next-term variances interpolated to a constant 30 days; SPX options | Cboe, Volatility Index Methodology: Cboe Volatility Index (pdftotext) | https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf | 2026-09-18 | "only options that have a non-zero bid price are included"; formula on p. 4 | def vix; dat:m1:volatility-first-contact:vix; build |
| F2 | VX futures: multiplier $1000; tick 0.05 = $50; final settlement on the Wednesday 30 days prior to the third Friday of the following month; final settlement value = special opening quotation of the VIX from opening prices of SPX options | Cboe VIX futures contract specifications (search excerpt) | https://www.cboe.com/tradable-products/vix/vix-futures/specifications | 2026-09-18 | quoted excerpt | dat vix; exo 3 |
| F3 | 5 Feb 2018: S&P 500 fell 4%, VIX jumped 20 points; leveraged and inverse volatility ETPs both had to buy VIX futures at the end of the day; assets of select such ETPs about $4bn at end-2017 | BIS Quarterly Review, March 2018, box "The equity market turbulence of 5 February" | https://www.bis.org/publ/qtrpdf/r_qt1803t.htm | 2026-09-18 | "the S&P 500 index fell 4% while the VIX ... jumped 20 points" | ex:m1:volatility-first-contact:feb2018; iq 6 |
| F4 | The largest inverse VIX ETN lost 96.3% of its value on 5 Feb 2018 and was redeemed early by its issuer (acceleration event) | ETF.com, "Inverse VIX ETN shuts down" (search excerpt) | https://www.etf.com/sections/news/inverse-vix-etn-shuts-down | 2026-09-18 | "lost 96.3% of its value on Monday, prompting its issuer to redeem the notes early" | ex feb2018 (unnamed: "the largest inverse product") |
| F5 | Since the 1987 crash, implied volatilities of index options decrease with strike (out-of-the-money puts above calls) | E. Derman, "The Volatility Smile and Its Implied Tree" (Goldman Sachs QS research notes, 1994); M. Rubinstein, "Implied Binomial Trees", J. Finance 49(3), 1994 (search extracts) | https://emanuelderman.com/the-volatility-smile-and-its-implied-tree/ | 2026-09-19 | "Ever since the '87 crash, the market's implied Black-Scholes volatilities for index options have shown a negative relationship" | section skew |

## EXCLUDED

- "Largest one-day rise of the index" (115.6%): from a regulator's note seen only as a search excerpt; removed.
- The statement that implied volatility has exceeded realised on average (variance risk premium): standard, stated qualitatively without a number or a citation; the literature (Carr and Wu 2009) is left to Book 6.
- "Since 1987" for the index skew: conventional dating (Rubinstein 1994), not fetched; kept as the single word "since 1987". RESOLVED 2026-09-19 in the front-to-back read: see F5.
- Black-Scholes 1973 and Black 1976 references: bibliographic details from memory, standard.
- The two futures curves in the term-structure figure are declared illustrative.
