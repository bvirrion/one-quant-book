# 29. Games, Auctions and Information — brief and source ledger

## Brief

- **Hook.** In 1998 the United States Treasury switched every auction from paying each winner its own bid to paying all winners the same clearing price. A dealer bidding in both formats bids differently in each, and the theory of auctions says whether the Treasury should have expected to raise more.
- **Sections.** Games and equilibrium; Bayesian games; Auction formats and revenue; Entropy and optimal betting.
- **Defines.** normal-form game, Nash equilibrium, mixed strategy, zero-sum game, Bayesian game, Bayes--Nash equilibrium, private-value auction, common-value auction, first-price auction, second-price auction, English auction, Dutch auction, reserve price, pay-as-bid auction, discriminatory auction, bid shading, entropy, mutual information.
- **Uses (defined earlier).** uniform-price auction, winner's curse, call auction, Kelly criterion, growth rate, edge, odds, Bayesian update, Kullback--Leibler divergence, market maker, adverse selection.
- **Results (named theorems, not terms).** existence of mixed Nash equilibria (Nash 1950, stated); von Neumann's minimax theorem; symmetric equilibrium bid in the first-price private-value auction; truthful bidding is dominant in the second-price auction; revenue equivalence theorem; optimal reserve price for uniform values (Myerson); Kelly's result: the gain in growth rate from side information equals the mutual information.
- **Tutorial.** Simulate first- and second-price auctions with private uniform values under equilibrium bidding and check revenue equivalence; add a reserve price; then bet on a horse race with and without a noisy tip and check that the growth gain equals the mutual information.
- **Build.** `firm.bidding`: auction simulator (English, Dutch, first- and second-price, uniform-price and pay-as-bid multi-unit formats; equilibrium bid functions for the symmetric private-value cases; revenue and efficiency statistics; reserve-price optimiser); Python.
- **Weekend problem.** The Treasury's switch — named result: expected revenue of the two formats in the symmetric private-value model (equal, by revenue equivalence), the equilibrium bid shading of five dealers, and the revenue gain from the optimal reserve price.
- **Facts to verify.** US Treasury uniform-price auctions for all marketable securities since November 1998 (reuse Book 2 ch. 4 ledger row F1); Malvey and Archibald 1998 Treasury report on the uniform-price experiment; Nash 1950 (PNAS) / 1951 (Annals of Mathematics); von Neumann 1928 (Math. Annalen); Vickrey 1961 (Journal of Finance); Myerson 1981 (Math. of Operations Research); Riley and Samuelson 1981 (AER); Milgrom and Weber 1982 (Econometrica); Harsanyi 1967-68 Bayesian games (Management Science); Shannon 1948 (Bell System Technical Journal); Kelly 1956 (reuse Book 2 ch. 29 ledger row F2); Cover and Thomas, Elements of Information Theory.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Treasury has used single-price (uniform-price) auctions for all marketable securities since November 1998: all successful bidders are awarded at the highest accepted yield; noncompetitive bids up to USD 10 million awarded in full at that yield; no competitive bidder recognised above 35% of the offering; usual close 12:00 noon ET for noncompetitive and 1:00 pm ET for competitive bids | TreasuryDirect, How Auctions Work / Auctions In Depth (search excerpts) | https://treasurydirect.gov/auctions/how-auctions-work/ | 2026-09-23 | "single-price ... since November 1998"; "limits a bidder's total award to 35 percent" | def auction; dat:m2:the-treasury-market:auctions; build |
| F2 | Malvey and Archibald, "Uniform-Price Auctions: Update of the Treasury Experience", US Treasury Office of Market Finance, October 1998 (foreword by L. H. Summers dated October 26, 1998): experiment with uniform-price auctions of 2- and 5-year notes announced September 3, 1992; participants bid more aggressively; broader distribution of awards; average auction spread over 1:00 pm WI bid for 2-year notes 0.41 bp (multiple-price) cut to 0.22 bp, 5-year 0.33 to 0.20 bp; difference not statistically significant because of greater auction-to-auction volatility under uniform price | the report (US Treasury archive PDF, 33 pp) | https://home.treasury.gov/system/files/136/archive-documents/upas.pdf | 2026-09-24 | foreword; introduction; PDF p. 14: "0.41 of a basis point, was cut by about half, to 0.22", "we cannot say that there is a statistically significant difference", "greater auction-to-auction volatility" | hook; section 3; omsources |
| F3 | J. F. Nash, "Equilibrium points in n-person games", PNAS 36(1) (1950), 48-49 | Crossref record | https://doi.org/10.1073/pnas.36.1.48 | 2026-09-24 | vol 36(1), pp 48-49 | theorem (existence); omsources |
| F4 | J. von Neumann, "Zur Theorie der Gesellschaftsspiele", Math. Annalen 100 (1928), 295-320 | Crossref record | https://doi.org/10.1007/BF01448847 | 2026-09-24 | vol 100(1), pp 295-320 | theorem (minimax); omsources |
| F5 | J. C. Harsanyi, "Games with incomplete information played by Bayesian players, I-III", Management Science 14(3) (1967), 159-182 (parts II and III 1968) | Crossref record (part I) | https://doi.org/10.1287/mnsc.14.3.159 | 2026-09-24 | vol 14(3), pp 159-182, 1967 | def Bayesian game; omsources |
| F6 | W. Vickrey, "Counterspeculation, auctions, and competitive sealed tenders", Journal of Finance 16(1) (1961), 8-37 | Crossref record | https://doi.org/10.1111/j.1540-6261.1961.tb02789.x | 2026-09-24 | vol 16(1), pp 8-37 | def second-price; theorem (revenue equivalence); omsources |
| F7 | R. B. Myerson, "Optimal auction design", Mathematics of Operations Research 6(1) (1981), 58-73 | Crossref record | https://doi.org/10.1287/moor.6.1.58 | 2026-09-24 | vol 6(1), pp 58-73 | theorem; proposition (reserve); omsources |
| F8 | J. G. Riley and W. F. Samuelson, "Optimal auctions", American Economic Review 71(3) (1981), 381-392 | RePEc / IDEAS record | https://ideas.repec.org/a/aea/aecrev/v71y1981i3p381-92.html | 2026-09-24 | "American Economic Review, vol. 71(3), pages 381-392, June"; page opened, authors Riley and Samuelson | theorem (revenue equivalence); omsources |
| F9 | P. R. Milgrom and R. J. Weber, "A theory of auctions and competitive bidding", Econometrica 50(5) (1982), 1089-1122 | Crossref record | https://doi.org/10.2307/1911865 | 2026-09-24 | vol 50(5), p 1089 | section 3 (affiliated values); omsources |
| F10 | C. E. Shannon, "A mathematical theory of communication", Bell System Technical Journal 27(3) (1948), 379-423 | Crossref record | https://doi.org/10.1002/j.1538-7305.1948.tb01338.x | 2026-09-24 | vol 27(3), pp 379-423 | def entropy; omsources |
| F11 | J. L. Kelly, "A new interpretation of information rate", Bell System Technical Journal 35(4) (1956), 917-926 | Crossref record | https://doi.org/10.1002/j.1538-7305.1956.tb03809.x | 2026-09-24 | vol 35(4), pp 917-926 | theorem (Kelly); omsources |
| F12 | T. M. Cover and J. A. Thomas, Elements of Information Theory, 2nd ed., Wiley | Crossref record | https://doi.org/10.1002/047174882X | 2026-09-24 | Wiley (Crossref online date 2005; print edition 2006) | omsources |

## EXCLUDED

- Nothing excluded. F1 is Book 2 chapter 4's ledger row F1, copied as instructed by the brief.
- F8: Riley and Samuelson (1981) has no Crossref DOI; the RePEc/IDEAS record (opened 2026-09-24, authors "Riley, John G & Samuelson, William F") and the SCIRP reference list agree on AER 71(3), 381-392.

## Brief deviations

- The multi-unit model uses unit demand (closed-form pay-as-bid equilibrium); multi-unit demand and demand reduction are left to the stretch goal, and the text says the model cannot settle the Treasury's question.
- The zero-sum example is solved by multiplicative weights (learning dynamics) rather than by linear programming, to keep firm.bidding self-contained.
