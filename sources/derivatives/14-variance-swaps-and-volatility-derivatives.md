# 14. Variance Swaps and Volatility Derivatives — brief and source ledger

## Brief

- **Hook.** A contract with no strike in price, only one in volatility squared; its hedge is a strip of every out-of-the-money option on the index, each weighted by one over its strike squared.
- **Sections.** Variance swaps and their replication; The log contract and the volatility-index formula; Volatility swaps and convexity; Futures and options on the volatility index; Skew, jumps and the limits of replication.
- **Defines.** variance swap, variance notional, vega notional, log contract, volatility swap, corridor variance swap, gamma swap, variance risk premium, VIX option.
- **Uses (defined earlier).** volatility index, VIX future, realised volatility, variance (Book 1 ch. 25), convexity adjustment (Book 2 ch. 8), Itô's formula (Book 4 ch. 3), Black model (ch. 3), forward variance (ch. 12), Heston model (ch. 10).
- **Tutorial.** Replicate a variance swap from a strip of options on a synthetic surface, compute the fair strike and the index-style number, and simulate the hedge's P&L on paths with and without jumps.
- **Build.** `firm.varswap`: variance- and volatility-swap pricer (strip replication, discrete-monitoring and jump corrections) and a variance-swap mark-to-market.
- **Weekend problem.** Vol or variance — named result: the convexity adjustment between the one-year variance-swap and volatility-swap strikes on the chapter's surface under Heston dynamics.
- **Facts to verify.** Cboe VIX methodology white paper (current version); VIX futures launch 2004, VIX options 2006 (Cboe); Demeterfi, Derman, Kamal, Zou 1999 'More than you ever wanted to know about volatility swaps'; Carr-Wu 2009 RFS variance risk premia; 2008 single-stock variance market (Risk / papers); Carr-Lee 2009 volatility derivatives survey.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Index formula sigma^2 = (2/T) sum (dK_i / K_i^2) e^{RT} Q(K_i) - (1/T)(F/K0 - 1)^2; Q = bid-ask midpoint; out-of-the-money puts below K0, calls above, both at K0; K0 = first strike at or immediately below the forward; only options with a non-zero bid; near and next terms interpolated to a constant 30 days; VIX = 100 sigma; methodology version 6.0, last revised 26 February 2026 | Cboe, "Cboe Volatility Index Methodology" (PDF, pdftotext) | https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf | 2026-09-24 | formula on p. 4, filtering section 3.2, version table | sec. index formula, dat:dv:variance-swaps-and-volatility-derivatives:vix |
| F2 | Cboe introduced the VIX in 1993 (30-day volatility implied by at-the-money S&P 100 options); updated in 2003 with Goldman Sachs to an S&P 500 strip; first VIX futures on CFE on 24 March 2004; VIX options launched February 2006 | same document, section 1 | https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf | 2026-09-24 | "On March 24, 2004, Cboe introduced the first exchange-traded VIX futures contract ... in February 2006, VIX options were launched" | sec. futures and options on the index |
| F3 | Demeterfi, Derman, Kamal, Zou, "More than you ever wanted to know about volatility swaps", Goldman Sachs Quantitative Strategies Research Notes, March 1999 (cited by the index methodology as its basis) | same document, footnote to the formula | https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf | 2026-09-24 | footnote on p. 4 | sec. replication, omsources |
| F4 | Carr and Wu, "Variance risk premiums", Review of Financial Studies 22(3) (2009) 1311-1341 | Crossref record 10.1093/rfs/hhn038 | https://api.crossref.org/works/10.1093/rfs/hhn038 | 2026-09-24 | Crossref metadata | sec. variance risk premium, omsources |
| F5 | Carr and Lee, "Volatility derivatives", Annual Review of Financial Economics 1 (2009) 319-339: survey of variance swaps, VIX futures and options, and proofs of results on variance and volatility swaps | Crossref record with abstract, 10.1146/annurev.financial.050808.114304 | https://api.crossref.org/works/10.1146/annurev.financial.050808.114304 | 2026-09-24 | abstract in Crossref | omsources |
| F6 | Rough Bergomi with a deterministic change of measure produces flat VIX smiles, in contrast to the upward-sloping VIX smiles observed in the market | Guerreiro and Guerra, "VIX pricing in the rBergomi model under a regime switching change of measure", arXiv 2201.10391; Quantitative Finance 23(5) (2023) 721-738 | https://arxiv.org/abs/2201.10391 | 2026-09-24 | abstract and journal ref (arXiv API) | sec. futures and options on the index; also chapter 12 |
| F7 | VIX options show an upward-sloping implied-volatility skew; a pure-diffusion 3/2 model captures it | Baldeaux and Badran, "Consistent modeling of VIX and equity derivatives using a 3/2 plus jumps model", arXiv 1203.5903 (2012) | https://arxiv.org/abs/1203.5903 | 2026-09-24 | abstract (arXiv API) | sec. futures and options on the index |
| F8 | The large asset price jumps of 2008 and 2009 disrupted volatility derivatives markets and caused the single-name variance swap market to dry up completely | Martin, "Simple variance swaps", NBER Working Paper 16884 (March 2011), abstract | https://www.nber.org/system/files/working_papers/w16884/w16884.pdf | 2026-09-24 | abstract (pdftotext, quoted) | sec. skew, jumps and the limits of replication; omsources |

## EXCLUDED

- Dealers' 2008 losses on single-stock variance (amounts, firms; Risk.net reports): not attributed; the chapter states only Martin's (F8) description of the market drying up, restored in Phase C.
- Market conventions for variance-swap caps (the usual multiple of the strike): not verified; the chapter describes caps without a number.
- Carr and Wu's (2009) measured premium levels: the abstract was not available; the chapter cites the paper for the concept only.
