# 26. Prediction and Sports Market Making — brief and source ledger

## Brief

- **Hook.** A goal is scored and the television picture arrives several seconds after the stadium's; the betting exchange holds every in-play order for a few seconds before it matches, so that the fans in the stands do not win every race.
- **Sections.** Pricing models for events and matches; Making markets on exchanges and prediction venues; In-play latency and the bet delay; Limits and counterparty selection.
- **Defines.** bet delay, courtsiding, stake limiting.
- **Uses (defined earlier).** betting exchange (B3.27), bookmaker (B3.27), overround (B3.27), in-play betting (B3.27), implied probability (B3.27), favourite--longshot bias (B3.27), event contract (B3.27), back bet (B3.27), lay bet (B3.27), Poisson process (B4.6), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** prediction-market making on a central limit order book; in-play exchange trading with the bet delay; cross-venue event arbitrage.
- **Tutorial.** Price a football match with a Poisson goals model, make a market on a simulated betting exchange, and trade in play with a bet delay against faster and slower counterparties; measure the market maker's loss to the fastest and its gain from the slowest.
- **Build.** `firm.sportsmm`: Poisson match model with in-play updating, exchange market making with a bet delay, counterparty limits by mark-out; Python, on firm.odds.
- **Weekend problem.** Faster than the television — named result: the market maker's loss per goal to courtsiders as a function of the bet delay, and the delay that makes it negligible.
- **Facts to verify.** Croxson and Reade 2014 Information and efficiency: goal arrival in soccer betting (EJ); Betfair exchange in-play delay rules (dated); Kalshi CFTC designation and the 2024 D.C. court ruling on event contracts (dated); Polymarket CFTC settlement 2022 and later status (dated); A court or regulator record on courtsiding (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Croxson and Reade (2014): goal arrival in soccer betting as a clean test of efficiency with high-frequency data; prices update swiftly and fully | Economic Journal 124(575), 2014, 62-91 | https://ideas.repec.org/a/wly/econjl/v124y2014i575p62-91.html | 2026-09-25 | abstract: "news can break remarkably cleanly, as when a goal is scored in soccer"; "On our evidence, prices update swiftly and fully" | §1; strategy file |
| F2 | Betfair developer support: in-play markets carry a delay on placing bets varying from 1 to 12 seconds, to allow customers to cancel unmatched orders when market conditions change | Betfair Developer Program support article | https://support.developer.betfair.com/hc/en-us/articles/360002825652-Why-do-you-have-a-delay-on-placing-bets-on-a-market-that-is-in-play | 2026-09-25 | "This delay is in place to allow customers to cancel unmatched orders on the system when there is a change in market conditions"; "varying from 1-12 seconds" | dat:hf:prediction-and-sports-market-making:venues |
| F3 | Courtsiding case, Australian Open 2014: prosecution withdrew the charge against Daniel Dobson (accused of sending live scores to a betting agency from the ground) because there was no reasonable prospect of conviction; 6 March 2014 | ABC News | https://www.abc.net.au/news/2014-03-06/tennis-illegal-betting-charges-dropped/5302508 | 2026-09-25 | "there was no reasonable prospect of a conviction in the case"; "using a hidden electronic device to send live score updates to a betting agency" | §4 |
| F4 | KalshiEX LLC v. CFTC (D.D.C. No. 23-3257): memorandum opinion of 12 Sep 2024 finds congressional control contracts involve neither unlawful activity nor gaming, the CFTC's order exceeded its statutory authority, grants Kalshi summary judgment; event contracts must be listed on a DCM; complaint filed 1 Nov 2023 | CourtListener, Doc 51 (memorandum opinion) | https://storage.courtlistener.com/recap/gov.uscourts.dcd.261465/gov.uscourts.dcd.261465.51.0_2.pdf | 2026-09-24 | "The CFTC's order exceeded its statutory authority. Kalshi's contracts do not involve unlawful activity or gaming." | dat:hf:prediction-and-sports-market-making:venues (row as verified for Book 3 ch. 27, F1) |
| F5 | D.C. Circuit No. 24-5205: per curiam order of 7 May 2025 granting the CFTC's unopposed motion for voluntary dismissal | CourtListener docket search | https://www.courtlistener.com/api/rest/v4/search/?q=KalshiEX%20CFTC%20dismiss%20appeal&type=rd | 2026-09-24 | "PER CURIAM ORDER filed granting motion for voluntarily dismissal"; "UNOPPOSED MOTION to dismiss case voluntarily filed by CFTC" | dat:hf:prediction-and-sports-market-making:venues (row as verified for Book 3 ch. 27, F2) |
| F6 | CFTC settled charges against Blockratize, Inc. d/b/a Polymarket (January 2022) for off-exchange event-based binary options without DCM designation or SEF registration; $1.4m penalty; wind down non-compliant markets; markets included "Will Trump win the 2020 presidential election?" | CFTC press release 8478-22 | https://www.cftc.gov/PressRoom/PressReleases/8478-22 | 2026-09-24 | "The order requires that Polymarket pay a $1.4 million civil monetary penalty, facilitate the resolution (i.e. wind down) of all markets" | dat:hf:prediction-and-sports-market-making:venues (row as verified for Book 3 ch. 27, F3) |

## EXCLUDED

- Betfair's passive bet delay (2025 newsletter): page returned 403; not used.
- The chapter's dated box names no venue for the delay and the rulings; the ledger rows carry the names.
