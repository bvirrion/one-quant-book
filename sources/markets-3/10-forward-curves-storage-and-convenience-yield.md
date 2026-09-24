# 10. Forward Curves, Storage and Convenience Yield — brief and source ledger

## Brief

- **Hook.** In early 2009, and again in spring 2020, tankers anchored full of crude: the contango paid more than the charter.
- **Sections.** The forward curve of a commodity; The theory of storage and the convenience yield; Roll yield and the decomposition of futures returns; Commodity indices and their roll; The footprint of the index roll.
- **Defines.** forward curve, theory of storage, convenience yield, full carry, cash-and-carry trade, floating storage, Samuelson effect, roll yield, spot return, collateral return, commodity index, roll window.
- **Uses (defined earlier).** contango, backwardation, cost of carry, roll, front month, futures strip, total return index, carry, fair value, implied financing rate, storage valuation (Book 6), mean-reverting diffusion (Book 4).
- **Tutorial.** From EIA NYMEX WTI contracts 1-4 compute the implied convenience yield and the roll yield of a front-month rolling position since the 1980s, and decompose its return into spot, roll and collateral.
- **Build.** `firm.commcurve`: commodity forward-curve object (contracts to curve, implied convenience yield, roll-yield decomposition, index roll schedule and roll-cost measurement); used by `firm.crude` and `firm.hedgeprog`.
- **Weekend problem.** Front-running the roll — named result: the cost to a long-only index investor of rolling inside the published window rather than before it, per dollar of index money, for a stated price-impact coefficient.
- **Facts to verify.** Kaldor (1939), Working (1949), Brennan (1958) theory of storage; Samuelson (1965) proposition on futures volatility; S&P GSCI roll period (fifth to ninth business day) and BCOM roll (sixth to tenth); commodity index investment size (CFTC 2008 staff report or later official figure); Mou (2010) on front-running the Goldman roll; floating storage 2009 and 2020 (IEA or EIA); Gorton and Rouwenhorst (2006) facts on commodity futures returns; EIA WTI futures series licence (public domain).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | S&P GSCI roll period: 5th to 9th S&P GSCI business day of each month, 20% a day | S&P Dow Jones Indices, S&P GSCI Methodology (July 2026) | https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-gsci.pdf | 2026-09-24 | "the period of five S&P GSCI business days beginning on the fifth (5th) and ending on the ninth (9th) S&P GSCI business day" (search excerpt) | dat:m3:forward-curves-storage-and-convenience-yield:windows; build |
| F2 | Bloomberg Commodity Index rolls on the 6th to 10th business days of each month, 20% a day | Bloomberg, BCOM methodology / primer | https://assets.bbhub.io/professional/sites/27/BCOM.pdf | 2026-09-24 | "Roll Period means the sixth to tenth business day of each month, at 20% (1/5) each business day" (search excerpt) | dat:m3:forward-curves-storage-and-convenience-yield:windows |
| F3 | Mou (2010): index roll price impact statistically and economically significant; front-running strategies with Sharpe ratios as high as 4.39 from 2000 to March 2010; investors forwent 3.6% annual return | Y. Mou, Limits to Arbitrage and Commodity Index Investment: Front-Running the Goldman Roll (SSRN 1716841; CFTC-hosted copy) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1716841 | 2026-09-24 | "Sharpe ratios as high as 4.39 from 2000 to March 2010"; "investors forwent 3.6% annual return" (abstract, search excerpt) | §5; problem 14 |
| F4 | Index variants that roll dynamically or select contracts by curve: S&P GSCI Dynamic Roll, Bloomberg Roll Select Commodity Index | S&P GSCI Dynamic Roll methodology; BCOM Roll Select factsheet | https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-gsci-dynamic-roll.pdf | 2026-09-24 | document titles (search results) | §5 |
| F5 | WTI contracts 1-4 daily 1985-2024 (ch. 2 F13) and 3-month T-bill (DTB3): nearby 25.92 (2 Jan 1985) to 86.91 (5 Apr 2024); spot 3.08%, roll -0.71%, collateral 3.18%, total 5.55% a year; backwardation on 45% of days; vols 40.9/38.3/35.3/33.6% | EIA RCLC1-4; FRED DTB3; data/markets-3/tbill3m_daily.csv | https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3 | 2026-09-24 | computed in m3_curves | hook; §3-5; figs |
| F6 | Global crude floating storage (ClipperData definition) rose from 65.9 million barrels on 1 Mar 2020 to 221.5 million on 9 Jul 2020 | EIA, This Week in Petroleum, 21 Oct 2020 | https://www.eia.gov/petroleum/weekly/archive/2020/201021/includes/analysis_print.php | 2026-09-24 | "global crude oil floating storage ... increased from 65.9 million barrels on March 1, 2020, to 221.5 million barrels on July 9, 2020" | section on storage |

## EXCLUDED

- Floating storage volumes in 2009 and 2020 (IEA): not fetched; the text defines the mechanism without figures. **2020 restored → F6 (EIA citing ClipperData); 2009 re-searched 2026-09-24, only secondary figures; not stated.**
- Commodity index assets under management: not fetched; the problem's 50 million barrels is illustrative. **re-searched 2026-09-24: only broker and blog estimates (e.g. about USD 102bn for one index) without a primary source; the problem's volume stays illustrative.**
- Contract identities: the weekend-only expiry calendar may place a few rolls a day off; stated in the caption. **note on the build, not a sourcing gap.**
