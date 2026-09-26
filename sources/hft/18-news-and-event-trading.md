# 18. News and Event Trading — brief and source ledger

## Brief

- **Hook.** At half past eight on the first Friday of the month a number is released; within the next millisecond futures trade in Chicago and the arbitrage to New York is under way, and the market makers who did not want to be part of it pulled their quotes a second before.
- **Sections.** Scheduled numbers and the release race; Machine-readable headlines; Social media and unscheduled events; The market maker's event protocol; Risk controls for event trading.
- **Defines.** release lock-up, release race, event protocol.
- **Uses (defined earlier).** machine-readable news (B8.17), news reaction window (B8.17), economic release (B2.31), data surprise (B2.31), consensus forecast (B2.31), trading halt (B8.17), latency race (ch9), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** macro-release race in futures; machine-readable earnings headline race; social-media headline reaction; market-maker event protocol: pull, widen, re-enter.
- **Tutorial.** Simulate a scheduled release with a surprise distribution, traders reacting at several latencies and a market maker who pulls, widens and re-enters on a schedule; measure who captures the move and what the market maker saves.
- **Build.** `firm.newsrace`: scheduled releases with surprises, reaction by latency, headline misparsing risk, a market maker's event protocol as a Quoter wrapper; Python, on firm.newsevent.
- **Weekend problem.** Half past eight — named result: the share of the release's move captured by each latency tier, and the market maker's loss with and without its event protocol.
- **Facts to verify.** Hu, Pan, Wang 2017 Early peek advantage? (JFE); New York Attorney General settlements on early data access (Thomson Reuters 2014; Business Wire 2014) (dated); BLS or DOL media lock-up rules and changes (dated); AP Twitter account hack of 23 April 2013 and the market's move (dated); SEC v. Musk 2018 settlement (the funding-secured tweet) (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Hu, Pan and Wang (2017): 2007-June 2013, select high-speed traders received the Michigan consumer sentiment index two seconds early; highly concentrated trading and price discovery under 200 ms; diff-in-diff vs other releases and after July 2013; tiered release may reduce rather than enhance the faster traders' informational advantage | Journal of Financial Economics 126(2), 2017, 399-421 | https://ideas.repec.org/a/eee/jfinec/v126y2017i2p399-421.html | 2026-09-25 | abstract: "highly concentrated trading and a fast price discovery of less than 200 milliseconds"; "tiered information release may help to reduce, rather than enhance, the informational advantage of faster traders" | §1; strategy file |
| F2 | NY Attorney General, 8 July 2013: Thomson Reuters agreed to immediately discontinue providing high-frequency traders certain consumer survey results before other subscribers; HFTs got them two seconds earlier | NY AG press release | https://ag.ny.gov/press-release/2013/ag-schneiderman-secures-agreement-thomson-reuters-stop-offering-early-access | 2026-09-25 | "High-frequency traders were able to access and act on this information two seconds earlier than other Thomson Reuters subscribers"; "agreed to immediately discontinue the practice" | dat:hf:news-and-event-trading:events |
| F3 | AP Twitter account hijack, 23 April 2013: false tweet just after 1 p.m. EDT; Dow, Nasdaq and S&P 500 spiked downward for a few minutes until traders realised it was a prank | NBC News | https://www.nbcnews.com/news/amp/wbna51635713 | 2026-09-25 | "the Dow Jones Industrial Average, NASDAQ and the S&P 500 all spiking downward for a few minutes until traders realized it was a prank"; "just after 1 p.m. EDT" | dat:hf:news-and-event-trading:events |
| F4 | SEC, 29 September 2018: Musk and Tesla each pay a $20 million penalty; Musk steps down as chairman; tweets that he could take Tesla private at $420 a share with funding secured | SEC press release 2018-226 | https://www.sec.gov/newsroom/press-releases/2018-226 | 2026-09-25 | "step down as Tesla's Chairman"; "pay a separate $20 million penalty"; "take Tesla private at $420 per share ... funding for the transaction had been secured" | dat:hf:news-and-event-trading:events |

## EXCLUDED

- Point size of the April 2013 fall (reported as about 140-145 Dow points in secondary coverage): CNBC 403, NPR timeout; only NBC's "a few minutes" is used.
- BLS/DOL lock-up rules and their changes: not fetched; the lock-up is defined generically.
- Business Wire 2014 settlement: not fetched.
