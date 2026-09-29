# 27. Crisis Management — brief and source ledger

## Brief

- **Hook.** On 31 October 2011 a large futures broker filed for bankruptcy, and its customers learned that money which should have been held apart for them was missing. Firms that cleared through it spent the next days finding out which of their positions still existed, where their margin was, and who could move it.
- **Sections.** The first hour of a technology incident; Liquidity squeezes: margin calls you cannot meet; When a counterparty fails; Drills and playbooks.
- **Defines.** crisis management plan, crisis committee, liquidity drill, trapped assets.
- **Uses (defined earlier).** kill switch (B11.27), mass cancel (B13.22), failover (B13.24), margin call (B1.6), margin spiral (B3.28), fire sale (B3.28), rehypothecation (B1.6), customer asset segregation (B3.15), default waterfall (B1.5), futures commission merchant (B1.30), incident commander (B15.28), runbook (B15.28), disaster-recovery site (B14.28), business continuity plan (B14.28), operational resilience (B14.28), house margin (ch14), unencumbered cash (ch14), liquidity buffer (ch14), survival horizon (ch14).
- **Tutorial.** A crisis drill on the synthetic firm: a volatility shock raises margin at every counterparty, one prime broker fails and a fraction of the assets it holds is trapped; hour by hour over 72 hours, compute cash sources and calls, the survival horizon, and the cheapest set of actions (cut positions with impact, draw lines, move collateral) that extends it past 72 hours. End state: an hourly cash chart under the drill, with and without the action set.
- **Build.** `firm.crisisdrill`: scenario definitions (shocks, counterparty failures, trapped fractions, withdrawn lines), an hourly liquidity engine (margin calls through firm.treasury and firm.initmargin, cash sources, actions with costs and delays), the survival horizon, and an action optimiser (greedy by cost per hour gained); Python.
- **Weekend problem.** Seventy-two hours -- named result: the survival horizon under the drill, and the cost of the cheapest action set that extends it to 72 hours.
- **Facts to verify.** MF Global: bankruptcy filing date, customer shortfall (SIPA trustee's report, 2013) and CFTC order (dated); Lehman Brothers International (Europe) client assets: administrators' reports (pointer to Book 1 ch. 6); FSB, Liquidity preparedness for margin and collateral calls (December 2024) (dated); Bank of England Financial Policy Committee record on the LDI episode, September-October 2022; Book 13 ch. 22 and 24, Book 14 ch. 28, Book 15 ch. 28 (pointers).
- **Data.** Synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CFTC press release 7508-17 (2017) on the orders against MF Global's former chief executive and its assistant treasurer: the orders find that he was CEO of MF Global from 1 September 2010 through the commencement of its liquidation proceedings on 31 October 2011 | CFTC | https://www.cftc.gov/PressRoom/PressReleases/7508-17 | 2026-09-28 | "the commencement of its liquidation proceedings on October 31, 2011" | hook; dat:fm:crisis-management:record |
| F2 | CFTC press release 6776-13 (18 November 2013): consent order of 8 November 2013 (S.D.N.Y.) requiring MF Global Inc., a registered futures commission merchant, to pay $1.212 billion in restitution to its customers to recover losses sustained when it failed in 2011, and a $100 million penalty; the complaint charged that during the last week of October 2011 it unlawfully used customer segregated funds to support its own proprietary operations and those of its affiliates; the trustee obtained permission to pay restitution in full from the general estate | CFTC | https://www.cftc.gov/PressRoom/PressReleases/6776-13 | 2026-09-28 | "requiring it to pay $1.212 billion in restitution to customers of MF Global to ensure customers recover their losses sustained when MF Global failed in 2011"; "during the last week of October 2011, MF Global unlawfully used customer segregated funds to support its own proprietary operations" | hook; dat:fm:crisis-management:record |
| F3 | CFTC press release 6904-14 (2014): the trustee announced final distributions to customers to satisfy full restitution of $1.212 billion of customer losses | CFTC | https://www.cftc.gov/PressRoom/PressReleases/6904-14 | 2026-09-28 | "the company will now begin making final distributions to its customers to satisfy its obligation of full restitution for $1.212 billion in losses sustained by customers" | dat:fm:crisis-management:record |
| F4 | Bank of England news release, 28 September 2022: after a significant repricing affecting long-dated UK government debt, the Bank would carry out temporary purchases of long-dated gilts from 28 September to restore orderly market conditions, on whatever scale necessary, fully indemnified by HM Treasury; the Financial Policy Committee noted the risks to financial stability from gilt market dysfunction; auctions until 14 October | Bank of England | https://www.bankofengland.co.uk/news/2022/september/bank-of-england-announces-gilt-market-operation | 2026-09-28 | "the Bank will carry out temporary purchases of long-dated UK government bonds from 28 September"; "Auctions will take place from today until 14 October" | dat:fm:crisis-management:record |

## EXCLUDED

- The SIPA trustee's 2013 report on MF Global: not fetched; the customer figures are the CFTC's.
- The link between the September 2022 gilt episode and liability-driven investment funds' collateral calls: not in the fetched release; not stated.
- LBIE administrators' reports: pointer to Book 1 chapter 6 only.

