# 16. Stock Loan and Short Selling in Practice — brief and source ledger

## Brief

- **Hook.** The borrow fee on one stock goes from 1% to 80% a year in a week.
- **Sections.** The lending chain; Fees, rebates and specials; Recalls and buy-ins; Short-sale regulation; Squeezes; Dividends and tax: the cum-ex affair.
- **Defines.** lendable supply, utilisation, general collateral, special, recall, buy-in, short interest, days to cover, short squeeze, naked short sale.
- **Tutorial.** Cost of a short over time with a fee that follows utilisation.
- **Build.** Borrow-cost model feeding the financing calculator.
- **Weekend problem.** The squeeze — named result: the break-even holding period of the short.
- **Facts to verify.** Reg SHO Rule 203/204; EU SSR thresholds; GameStop short interest >100% (SEC report); Volkswagen 2008; cum-ex court rulings.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Reg SHO: locate (Rule 203(b)(1)) "reasonable grounds to believe that the security can be borrowed"; Rule 204 close-out by the beginning of regular trading hours on the settlement day following the settlement date (short sales), third consecutive settlement day (long sales, bona fide market making); threshold securities (10,000 shares and 0.5% of shares outstanding for five consecutive settlement days; 13 days); Rule 201 (10% decline, rest of day and following day); bona fide market making excepted from the locate, not covering speculative selling or one-sided quoting; naked short selling not necessarily a violation | SEC, Key Points About Regulation SHO | https://www.sec.gov/investor/pubs/regsho.htm | 2026-09-18 | "Broker-dealers engaged in bona fide market making activities are excepted from having to borrow or arrange to borrow shares" | dat:m1:stock-loan-and-short-selling:rules; exo 6; iq 5 |
| F2 | EU SSR: net short positions in shares reported to the competent authority from 0.1% of issued share capital and each 0.1% above, public from 0.5%; all short sales of shares and sovereign debt must be covered; exemptions for market making and primary dealers; temporary restrictions by national authorities | ESMA short selling page | https://www.esma.europa.eu/esmas-activities/markets-and-infrastructure/short-selling | 2026-09-18 | "when they reach 0.1% of the issued share capital and every 0.1% above that" | dat rules |
| F3 | GameStop: short interest 122.97% of float in January 2021; intraday high $483.00 on 28 Jan; about 2,700% rise from the 8 Jan intraday low; fall of over 86% to the close at the end of the first week of February; covering a small fraction of buy volume; "it was the positive sentiment, not the buying-to-cover"; explanation of short interest above 100% by re-lending; report dated 14 October 2021 | SEC Staff Report on Equity and Options Market Structure Conditions in Early 2021 (pdftotext) | https://www.sec.gov/files/staff-report-equity-options-market-struction-conditions-early-2021.pdf | 2026-09-18 | pp. 18-26 of the report | ex:m1:stock-loan-and-short-selling:gme; exo 8; pb q16 |
| F4 | Volkswagen 2008: Porsche announced on 26 Oct 2008 that it held 42.6% of VW ordinary shares plus 31.5% in cash-settled options; Lower Saxony 20%; 5.9% free float; about 13% sold short; cash-settled options outside the disclosure rules | The Hedge Fund Journal, "The case of Volkswagen" | https://thehedgefundjournal.com/the-case-of-volkswagen/ | 2026-09-18 | "42.6% of the VW ordinary shares and in addition 31.5% in so called cash-settled options"; "only 5.9% of shares remaining in the free float" | ex:m1:stock-loan-and-short-selling:vw |
| F5 | VW price passed EUR 1,005 on Tuesday 28 Oct 2008 from a Friday close of EUR 211; briefly the most valuable listed company; paper by Allen, Haas, Nowak, Tengulov, JFE | Harvard Law School Forum on Corporate Governance, 15 Sept 2021 | https://corpgov.law.harvard.edu/2021/09/15/market-efficiency-and-limits-to-arbitrage-evidence-from-the-volkswagen-short-squeeze/ | 2026-09-18 | "surged past EUR 1,005 per share on Tuesday, October 28, 2008, from a close the previous Friday of EUR 211" ; journal record https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001975 | ex vw; omsources |
| F6 | German Federal Court of Justice, judgment of 28 July 2021, 1 StR 519/20: claiming refunds of withholding tax not paid, via cum-ex trades, is criminal tax evasion | BGH press release 146/2021 | https://www.bundesgerichtshof.de/SharedDocs/Pressemitteilungen/DE/2021/2021146.html | 2026-09-18 | title: "Bundesgerichtshof bestaetigt Urteil im bundesweit ersten Cum-Ex-Strafverfahren" | section Dividends and tax |
| F7 | Duffie, Garleanu, Pedersen, "Securities lending, shorting, and pricing", JFE 66(2-3), 2002, 307-339 | RePEc | https://ideas.repec.org/a/eee/jfinec/v66y2002i2-3p307-339.html | 2026-09-18 | record | omsources |

## EXCLUDED

- Whether the banks that wrote the VW options held the shares as hedges: the source presents it as speculation; the text says only "whatever shares their writers held as hedges were not for sale".
- Short sellers' aggregate losses in the VW squeeze (EUR 20bn and more in secondary sources): not used.
- Collateral level of 102% (US) / 105% (cross-currency): market convention, no primary source fetched; the figure label says "about 102%".
- Typical general-collateral fee level and any real fee/utilisation curve: vendor data, not public; the curve is declared illustrative.
- "High borrow fees predict low returns": literature claim removed from an interview solution, not verified in this run.
- Cum-ex total tax losses across Europe (press estimates): not used.
