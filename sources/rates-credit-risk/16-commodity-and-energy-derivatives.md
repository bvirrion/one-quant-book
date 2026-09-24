# 16. Commodity and Energy Derivatives — brief and source ledger

## Brief

- **Hook.** In February 2021 a winter storm froze Texas and day-ahead gas at some hubs traded above 200 dollars per million British thermal units; the owners of gas storage and swing rights earned in a week what they normally earn in years.
- **Sections.** Factor models of the forward curve; The Samuelson effect and forward volatility; Spread options; Storage valuation; Swing contracts.
- **Defines.** Schwartz--Smith model, spread option, Kirk's approximation, intrinsic storage value, extrinsic value, rolling intrinsic.
- **Uses (defined earlier).** forward curve (B3.10), convenience yield (B3.10), theory of storage (B3.10), Samuelson effect (B3.10), swing contract (B3.12), take-or-pay clause (B3.12), calendar-spread option (B3.12), average-price option (B3.12), crack spread (B3.3), spark spread (B3.5), contango (B1.21), backwardation (B1.21), Ornstein--Uhlenbeck process (B4.4), Longstaff--Schwartz method (B5.23), Monte Carlo (B4.26).
- **Tutorial.** Calibrate a two-factor model to a synthetic gas forward curve and its option volatilities, then value a storage facility by rolling intrinsic and by regression Monte Carlo and split intrinsic from extrinsic value.
- **Build.** `firm.energymodel`: two-factor forward-curve model, Kirk spread options, storage and swing valuation by regression.
- **Weekend problem.** The salt cavern in February 2021 — named result: intrinsic and extrinsic value of a storage facility and the value the storm week added to it.
- **Facts to verify.** Winter Storm Uri gas and power prices (EIA); Schwartz 1997; Schwartz and Smith 2000 (papers); Kirk 1995 (paper); Boogert and de Jong 2008 storage by LSM (paper).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | February 2021 cold snap: spot gas at Waha (West Texas) reached $206.19/MMBtu on 16 February; SoCal Citygate $144.00 on 12 February; Oneok Gas Transportation (Oklahoma) averaged $1,192/MMBtu on 17 February according to NGI data, against $2.91 in the first week of February; production fell because of freeze-offs | EIA, Today in Energy, "Cold weather brings near record-high natural gas spot prices" (id 47016) | https://www.eia.gov/todayinenergy/detail.php?id=47016 | 2026-09-24 | "The spot price at the nearby Waha Hub reached $206.19/MMBtu on February 16"; "SoCal Citygate reached $144.00/MMBtu on February 12"; "Oneok Gas Transmission (OGT) reached what might be the highest natural gas price at any natural gas hub in history at an average of $1,192/MMBtu on February 17, according to NGI data"; "The spot price at OGT was $2.91/MMBtu during the first week of February" | hook, dat:rc:commodity-and-energy-derivatives:uri |
| F2 | Henry Hub daily spot prices, December 2020 to April 2021 (2.88 on 1 Feb 2021, 23.86 on 17 Feb 2021, March 2021 average 2.62) | EIA, Henry Hub Natural Gas Spot Price, daily (RNGWHHD); stored as data/rates-credit-risk/henry_hub_daily_2020_2021.csv | https://www.eia.gov/dnav/ng/hist/rngwhhdD.htm | 2026-09-24 | table rows "2021 Feb-15 to Feb-19: 11.32 23.86 8.56 4.96" (15 Feb a holiday) and "2021 Feb- 8 to Feb-12: 3.40 3.35 3.76 6.50 6.12" | figure, weekend problem |
| F3 | Schwartz (1997) studies one-, two- and three-factor models of commodity prices with a mean-reverting convenience yield | E. S. Schwartz, "The stochastic behavior of commodity prices: implications for valuation and hedging", Journal of Finance 52(3), 923-973, 1997 (Crossref metadata) | https://doi.org/10.1111/j.1540-6261.1997.tb02721.x | 2026-09-24 | Crossref record: title, journal, volume 52, issue 3, pages 923-973 | sources |
| F4 | Schwartz and Smith (2000) model log prices as a mean-reverting short-term deviation plus a long-term equilibrium level | E. Schwartz and J. E. Smith, "Short-term variations and long-term dynamics in commodity prices", Management Science 46(7), 893-911, 2000 (Crossref metadata) | https://doi.org/10.1287/mnsc.46.7.893.12034 | 2026-09-24 | Crossref record: title, authors Schwartz and Smith, journal, 46(7) 893-911 | Schwartz-Smith definition, sources |
| F5 | Boogert and de Jong (2008) value gas storage by least-squares Monte Carlo | A. Boogert and C. de Jong, "Gas storage valuation using a Monte Carlo method", Journal of Derivatives 15(3), 81-98, 2008 (Crossref metadata) | https://doi.org/10.3905/jod.2008.702507 | 2026-09-24 | Crossref record: title, authors, JoD 15(3) 81-98 | storage section, sources |
| F6 | Henry Hub natural gas spot price, monthly: January 2021 2.71, February 2021 5.35 dollars per MMBtu | EIA, Henry Hub Natural Gas Spot Price, monthly (RNGWHHDm) | https://www.eia.gov/dnav/ng/hist/rngwhhdm.htm | 2026-09-24 | table row "2021 2.71 5.35 2.62 ..." (the daily file of F2 averages to 5.35 over February's 19 trading days) | dat:rc:commodity-and-energy-derivatives:uri |
| F7 | Kirk (1995): E. Kirk, "Correlation in the energy markets", in R. Jameson (ed.), Managing Energy Price Risk, Risk Publications and Enron Capital & Trade Resources, London, pp. 71-78 (the origin of Kirk's approximation) | Reference list of a peer paper: "A numerical analysis of the modified Kirk's formula and applications to spread option pricing approximations", arXiv:1812.04272 | https://arxiv.org/pdf/1812.04272 | 2026-09-24 | "Kirk, E. (1995). Correlation in the Energy Markets. In, Robert Jameson (Ed.), Managing Energy Price Risk (pp. 71-78). London: Risk Publications and Enron Capital & Trade Resources." | sources |

## EXCLUDED

- Kirk (1995) bibliographic record: restored 2026-09-24 → F7 (no DOI exists for the book chapter; the record is taken from a peer paper's reference list), cited in the sources.
- EIA's February 2021 Henry Hub monthly average: restored 2026-09-24 → F6 (the monthly series gives 5.35, matching the daily file; the earlier 5.49 figure came from another page and is not used). The "$2.84 on 22 February" figure: re-checked, the daily series gives 3.16 on 22 February; not printed.
- Storage and swing contract terms, facility sizes and forward curves: illustrative by design.

