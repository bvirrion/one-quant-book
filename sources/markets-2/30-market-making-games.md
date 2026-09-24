# 30. Market-Making Games — brief and source ledger

## Brief

- **Hook.** An interviewer says: make me a market on the number of windows in this building. You answer 200 at 400. She says: I buy.
- **Sections.** Make me a market; Updating on trades; Adverse selection around a table; The training games firms describe.
- **Defines.** make-me-a-market, width, inventory, Bayesian update, winner's curse.
- **Uses (defined earlier).** market maker, bid--ask spread, adverse selection, edge.
- **Tutorial.** Play a simulated card-sum market against informed and uninformed bots and plot P&L by width.
- **Build.** `firm.mmgame`: market-making game engine.
- **Weekend problem.** The card-sum market — named result: the width that maximises expected P&L against the table's mix of traders.
- **Facts to verify.** public descriptions of trading games (firm blogs/careers pages); Glosten-Milgrom 1985.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Jane Street's public "Probability and Markets" guide: market jargon ("I'm 2 bid for 10", "I have 10 at 4", "2 at 4, 10 up"; "sold" hits the bid, "take 'em" lifts the offer; fill, partial fill, "I'm out"); strategy: buy below expected value, weigh losses against capital, balance likelihood of trading with expected profit, example market "3 at 4, 10 up" on a d6 contract; practice markets (d20, max of 3 d6, reroll option, temperature, 1,000,000 x d6); adverse selection: "the trades you get to do are worse than they would appear, because someone else is selecting into the trade against you"; update beliefs when filled; Groucho Marx quote | Jane Street, "Probability and Markets Guide" (trading-interview.pdf) | https://www.janestreet.com/static/pdfs/trading-interview.pdf | 2026-09-24 | "Adverse selection is the idea that the trades you get to do are worse than they would appear, because someone else is selecting into the trade against you." | §1; §3; §4 |
| F2 | Jane Street trading internship: mock trading ("Team up with fellow interns to analyze, and trade on, a trading scenario constructed by full-time traders"); classes including poker | Jane Street, Trading Internship page | https://www.janestreet.com/join-jane-street/internships/trading/ | 2026-09-24 | "Team up with fellow interns to analyze, and trade on, a trading scenario constructed by full-time traders." | §4 |
| F3 | Glosten and Milgrom (1985), "Bid, ask and transaction prices in a specialist market with heterogeneously informed traders", Journal of Financial Economics 14(1), 71-100 | EconPapers bibliographic record (and Crossref); abstract read in a copy of the article hosted at edegan.com/pdfs | https://econpapers.repec.org/RePEc:eee:jfinec:v:14:y:1985:i:1:p:71-100 | 2026-09-24 | "The presence of traders with superior information leads to a positive bid-ask spread even when the specialist is risk-neutral and makes zero expected profits." | §2; §3; omsources |

## EXCLUDED

- Other firms' games (SIG, Optiver, Citadel Securities training): not fetched; only Jane Street's own public pages are cited.
- The card-sum game, the price-sensitive uninformed traders and the widths are this chapter's construction; no external source.

