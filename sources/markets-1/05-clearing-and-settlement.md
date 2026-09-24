# 5. Clearing and Settlement — brief and source ledger

## Brief

- **Hook.** On 28 January 2021 a retail broker received a multi-billion-dollar collateral call before dawn.
- **Sections.** From trade to settlement; The central counterparty and novation; Margin and the default waterfall; Settlement cycles, DVP and fails; When a member defaults.
- **Defines.** clearing, settlement, central counterparty, novation, initial margin, variation margin, default fund, default waterfall, delivery versus payment, central securities depository, settlement fail.
- **Tutorial.** Net a day of trades multilaterally and compute settlement obligations.
- **Build.** `firm.clearing`: multilateral netting engine.
- **Weekend problem.** The default of member C — named result: the loss reaching the mutualised default fund.
- **Facts to verify.** US T+1 date (SEC rule); NSCC January 2021 call (congressional testimony / report); CPMI-IOSCO PFMI waterfall; Lehman default at LCH (public account).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | 28 Jan 2021, approx. 5:11 a.m. EST: NSCC daily collateral deposit requirement for Robinhood Securities of approx. $3.7bn; approx. $700m already on deposit; additional $3bn due by 10 a.m.; components: VaR charge approx. $1.3bn and Excess Capital Premium charge of $2.2bn; $3.5bn fundraising target | US House Committee on Financial Services, majority staff report "Game Stopped", June 2022 | https://democrats-financialservices.house.gov/uploadedfiles/6.22_hfsc_gs.report_hmsmeetbp.irm.nlrf.pdf | 2026-09-18 | pp. 50-52 of the PDF text: "daily collateral deposit requirement of approximately $3.7 billion ... approximately $700 million on deposit ... deposit an additional $3 billion ... by 10 a.m. ... Value-at-Risk charge of approximately $1.3 billion ... Excess Capital Premium charge of $2.2 billion" | hook; ex why |
| F2 | DTCC waived $9.7bn of Excess Capital Premium charges across members during the event | same report, Key Finding #4 | https://democrats-financialservices.house.gov/uploadedfiles/6.22_hfsc_gs.report_hmsmeetbp.irm.nlrf.pdf | 2026-09-18 | "The Depository Trust & Clearing Corporation (DTCC) waived $9.7 billion of ..." | ex why |
| F3 | SEC staff report confirms deposit deficit of over $3bn and the ECP waiver for all members | SEC Staff Report on Equity and Options Market Structure Conditions in Early 2021 | https://www.sec.gov/files/staff-report-equity-options-market-struction-conditions-early-2021.pdf | 2026-09-18 | search extract: "deposit deficit of over $3 billion"; "NSCC waived Excess Capital Premium charges for all members" | ex why |
| F4 | US moved to T+1 on 28 May 2024 | SEC press release 2024-62 | https://www.sec.gov/newsroom/press-releases/2024-62 | 2026-09-18 | title and text | dat:m1:clearing-and-settlement:tplus1 |
| F5 | EU: CSDR art. 5 amendment published in the Official Journal 14 Oct 2025, T+1 applies from 11 Oct 2027; UK and Switzerland aligned on 11 Oct 2027 | Euronext T+1 programme page; FCA "About T+1 settlement" | https://www.euronext.com/en/regulation/t1-programme | 2026-09-18 | "published in the EU Official Journal on 14 October 2025 for application on 11 October 2027"; FCA: https://www.fca.org.uk/markets/about-t1-settlement | dat:m1:clearing-and-settlement:tplus1 |
| F6 | Lehman default at LCH SwapClear, 15 Sep 2008: 66,390 trades, $9tn notional, 5 currencies; approx. $2bn initial margin; auctions 24 Sep to 3 Oct; managed within margin, default fund not used | LCH.Clearnet press release 8 Oct 2008; CCP Global "The Lehman Case" | https://secure-area.lchclearnet.com/media_centre/press_releases/2008-10-08.asp | 2026-09-18 | "total notional value of the portfolio was $9 trillion, encompassing a total of 66,390 trades across 5 major currencies ... well within Lehman margin held" ; https://ccp-global.org/the-lehman-case | ex lehman |
| F7 | Default waterfall order (defaulter's margin, defaulter's fund contribution, CCP capital, survivors' contributions, assessments) | CPMI-IOSCO, Principles for financial market infrastructures, April 2012 (Principles 4 and 13) | https://www.bis.org/cpmi/publ/d101a.pdf | 2026-09-18 | standard structure described under Principle 4; URL from memory of the BIS publication number, title verified via search results listing bis.org/cpmi | def waterfall |

## EXCLUDED

- 'NSCC netting removes 98% of the value of obligations': searched, no primary source found (DTCC pages describe CNS qualitatively). The chapter reports only its own simulation's 98% and does not attribute a figure to the real clearing house.
- The exact amount Robinhood finally deposited and raised: only the $3.5bn fundraising *target* is in the fetched source; the amount raised is omitted.
- Status of litigation over Lehman's uncleared derivatives: unsourced, sentence removed.
