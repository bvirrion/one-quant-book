# 10. Retail Flow and Wholesaling — brief and source ledger

## Brief

- **Hook.** Your market order for ten shares never reaches an exchange.
- **Sections.** The path of a retail order; Payment for order flow; Price improvement and how it is measured; Why uninformed flow is valuable; January 2021.
- **Defines.** wholesaler, payment for order flow, price improvement, internalisation, effective spread, realised spread, Rule 605 report, Rule 606 report.
- **Tutorial.** Compute effective spread, realised spread and price improvement from simulated fills.
- **Build.** Execution-quality report generator.
- **Weekend problem.** Pricing retail flow — named result: the maximum payment per share the wholesaler can afford.
- **Facts to verify.** Rule 605/606 text and 2024 amendments; SEC staff report on Jan 2021; PFOF totals (606 aggregations); Robinhood SEC settlement 2020.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SEC v. Robinhood Financial, 17 Dec 2020: $65m; misleading statements 2015 to late 2018 omitting PFOF as largest revenue source; best-execution failures Sept 2016 to June 2019; inferior prices cost customers $34.1m even after commission savings; settled without admitting or denying | SEC press release 2020-321; order 33-10906 | https://www.sec.gov/newsroom/press-releases/2020-321 | 2026-09-18 | "provided inferior trade prices that in aggregate deprived customers of $34.1 million even after taking into account the savings from not paying a commission" | ex case |
| F2 | Rule 605 amendments adopted 6 March 2024: broader scope (large broker-dealers), summary report | SEC, Disclosure of Order Execution Information | https://www.sec.gov/rules-regulations/2025/09/disclosure-order-execution-information | 2026-09-18 | search extract of the adopting release summary | dat:m1:retail-flow-and-wholesaling:scale; def reports |
| F3 | Compliance date extended from 14 Dec 2025 to 1 Aug 2026; price-improvement statistics relative to best displayed price due in November 2026 | Federal Register, Extension of Compliance Date, 2 Oct 2025 | https://www.federalregister.gov/documents/2025/10/02/2025-19316/extension-of-compliance-date-for-disclosure-of-order-execution-information | 2026-09-18 | "is extended from December 14, 2025, to August 1, 2026" | dat:m1:retail-flow-and-wholesaling:scale |
| F4 | US retail brokers received about $953m of PFOF in Q2 2025 (equities and options), from Rule 606 reports | Global Trading; Finance Magnates | https://www.globaltrading.net/robinhood-schwab-led-us461m-retail-order-flow-payment-bonanza-in-may/ | 2026-09-18 | "Payments for order flow reached about US$953 million in the second quarter of 2025"; https://www.financemagnates.com/forex/analysis/remember-robinhoods-65-million-pfof-fine-the-market-just-paid-1-billion-in-a-quarter/ | dat:m1:retail-flow-and-wholesaling:scale |
| F5 | SEC staff report on early 2021: "it was the positive sentiment, not the buying-to-cover, that sustained the weeks-long price appreciation of GameStop stock" | SEC Staff Report, Oct 2021 | https://www.sec.gov/files/staff-report-equity-options-market-struction-conditions-early-2021.pdf | 2026-09-18 | quoted sentence | section 4 |

## EXCLUDED

- Names and market shares of individual wholesalers: no primary source fetched; the chapter names none.
- An annual industry PFOF total ($4.8bn for 2025) appeared only on a blog; not printed. The quarterly figure is attributed in the text to 'a trade publication's compilation'.
- The share of off-exchange principal volume that is retail wholesaling (as opposed to bank single-dealer platforms): not available; the hook says 'a large part'.
- The informed-order probabilities (5%, 35%) and the 3-cent move are model parameters, labelled as such.
- The fate of the SEC's 2022 order-competition proposals: not researched; not mentioned.
