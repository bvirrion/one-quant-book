# 11. The Bond-Futures Basis Trade — brief and source ledger

## Brief

- **Hook.** Buy a Treasury, sell the future on it, finance the bond in repo at fifty times leverage, and earn a few basis points; in March 2020 the few basis points became losses large enough for the central bank to step in.
- **Sections.** Mechanics: cash, future, repo; Leverage and who does it; March 2020; Measuring the crowding.
- **Defines.** basis-trade leverage, repo rollover risk.
- **Uses (defined earlier).** basis trade (B2.6), cheapest-to-deliver (B2.6), implied repo rate (B2.6), gross basis (B2.6), net basis (B2.6), haircut (B1.6), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** cash-futures basis long; delivery option trade; basis-trade crowding signal.
- **Tutorial.** Price a bond future's delivery basket on firm.ctd, simulate the basis and repo, run a leveraged basis book, and stress it with a repo-haircut increase and a futures margin call.
- **Build.** `firm.basistrade`: basis trade accounting (implied repo, carry, margin and haircut funding) and a deleveraging stress; Python.
- **Weekend problem.** Fifty times — named result: the trade's return on capital by leverage and the loss in the planted funding stress.
- **Facts to verify.** Barth and Kahn 2021 hedge funds and the Treasury cash-futures disconnect (OFR); Federal Reserve March 2020 Treasury market actions (dated); CFTC traders in financial futures (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | D. Barth, R. J. Kahn, "Hedge funds and the Treasury cash-futures disconnect", OFR Working Paper 21-01 (1 April 2021): hedge funds go long the basis (short futures, long cash notes) to meet asset managers' demand for off-balance-sheet duration; at the peak the basis-trade positions were an estimated $400-500 billion, more than 60% of hedge fund Treasury exposure, more than 70% of hedge fund repo borrowing and more than 25% of dealers' repo lending; from end-2017 to September 2019 hedge fund Treasury exposure grew from $1.06 trillion to $2.02 trillion and their short futures by $352 billion; the trade exposes the market to margin risk and repo rollover risk; hedge funds cut short 2-, 5- and 10-year futures from $659 billion to $554 billion between 18 February and 17 March 2020 and large basis traders sold $91-105 billion of Treasuries; the authors argue basis trades were unlikely to be the primary cause of the stress before 17 March | OFR working paper PDF (pdftotext) | https://www.financialresearch.gov/working-papers/files/OFRwp-21-01-hedge-funds-and-the-treasury-cash-futures-disconnect.pdf | 2026-09-25 | "we estimate the size of hedge fund positions associated with the basis trade was between $400 - $500 billion"; "reducing short futures held in the 2-year, 5-year, and 10-year contracts from $659 billion to $554 billion between February 18 and March 17, 2020"; "basis trades were unlikely to be the primary cause of stress in Treasury markets leading up to March 17" | hook; section 2; section 3; strat:s2:the-bond-futures-basis-trade:long; omsources |
| F2 | Federal Reserve press releases: 15 March 2020, the FOMC will increase its holdings of Treasury securities by at least $500 billion and agency MBS by at least $200 billion to support smooth functioning; 23 March 2020, it will purchase Treasury securities and agency MBS in the amounts needed | Federal Reserve press releases | https://www.federalreserve.gov/newsevents/pressreleases/monetary20200315a.htm ; https://www.federalreserve.gov/newsevents/pressreleases/monetary20200323b.htm | 2026-09-25 | "increase its holdings of Treasury securities by at least $500 billion"; "purchase Treasury securities and agency mortgage-backed securities in the amounts needed to support smooth market functioning" | section 3 |
| F3 | CFTC Traders in Financial Futures (futures only), yearly files 2010-2026: leveraged funds' long and short positions in CBOT Treasury futures by contract code, used through derived statistics (net notional by week) | CFTC historical compressed files | https://www.cftc.gov/files/dea/history/fut_fin_txt_2024.zip (and 2010-2026) | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_tff.py | dat:s2:the-bond-futures-basis-trade:tff; section 4 |

## EXCLUDED

- The size of the basis move, haircut and margin changes in March 2020: not in the fetched sources as numbers; the chapter's stress is planted and labelled as such.
- Hedge fund leverage multiples in the basis trade (the "fifty times" of the outline hook): no citable figure fetched; the hook was rewritten to use the OFR sizes and the synthetic leverages.
- Leveraged-funds positions are not all basis trades: the TFF category includes other strategies; stated in the chapter.

