# 2. Money Markets — brief and source ledger

## Brief

- **Hook.** On the last business day of a quarter, the rate at which a bank will lend cash overnight jumps, and on the next morning it falls back.
- **Sections.** Bills and their quoting conventions; Commercial paper and certificates of deposit; Money-market funds; Turns: quarter-end and year-end.
- **Defines.** Treasury bill, discount yield, money-market yield, bond-equivalent yield, commercial paper, certificate of deposit, money-market fund, turn, reverse repo facility.
- **Uses (defined earlier).** repurchase agreement, general collateral, overnight benchmark rate, policy rate.
- **Tutorial.** Convert a strip of bill quotes between discount, money-market and bond-equivalent yields and plot the resulting bill curve.
- **Build.** `firm.mmyield`: money-market quote converter.
- **Weekend problem.** Parking cash over year-end — named result: the implied year-end turn from three quoted rates.
- **Facts to verify.** US bill conventions (discount basis, ACT/360, 4/8/13/17/26/52-week); ACT/365 vs ACT/360 by currency; MMF size (ICI weekly data); ON RRP usage peak and recent level; SEC 2023 MMF reforms; 2008 Reserve Primary Fund broke the buck.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Treasury bills are offered at terms of 4, 6, 8, 13, 17, 26 and 52 weeks; cash management bills at various times and variable terms; bills are sold at a discount or at par and pay face value at maturity | TreasuryDirect, Treasury Bills | https://www.treasurydirect.gov/marketable-securities/treasury-bills/ | 2026-09-23 | "4, 6, 8, 13, 17, 26, and 52 weeks" | def bill; fig bills |
| F2 | Bill price P = 100 (1 - d r / 360), prices rounded to six decimals; discount rate d = (100 - P)/100 x 360/r; investment rate for bills of not more than one half-year i = (100 - P)/P x y/r; beyond, P [1 + (r - y/2)(i/y)] (1 + i/2) = 100 solved as a quadratic; y = 366 if the year after issue contains 29 February, else 365; bills sold on a discount-rate basis since 18 April 1983; worked examples (7.610% 90 days -> 98.097500; 95.934567 182 days -> 8.042%; 99.559444 20 days -> 8.076%; 92.265000 364 days -> 8.237%) | 31 CFR Part 356, Appendix B, section VI (Cornell LII text) | https://www.law.cornell.edu/cfr/text/31/appendix-B_to_part_356 | 2026-09-23 | formulas and examples as quoted | defs discount / mmy / bey; prop conversions; build tests; exo 5 |
| F3 | Money market fund assets USD 7.92 trillion for the week ended Wednesday 16 Sept 2026 (down 51.97bn): government 6.53tn, prime 1.24tn, tax-exempt 150.42bn; retail 3.11tn, institutional 4.81tn | ICI, Money Market Fund Assets release, 17 Sept 2026 | https://www.ici.org/research/stats/mmf | 2026-09-23 | "Total money market fund assets decreased by $51.97 billion to $7.92 trillion" | dat:m2:money-markets:mmf |
| F4 | ON RRP take-up (USD bn): 2,425.910 on 30 Sept 2022; 2,252.523 on 3 Oct 2022; 2,308.319 on 29 Dec 2022; 2,553.716 on 30 Dec 2022; 2,188.272 on 3 Jan 2023 | FRED series RRPONTSYD (NY Fed operation results); file data/markets-2/rrp_ontsyd_2022h2.csv | https://fred.stlouisfed.org/series/RRPONTSYD | 2026-09-23 | values in the downloaded CSV | hook; fig rrp; §4 |
| F5 | ON RRP record USD 2.554 trillion on 30 Dec 2022, USD 245 billion more than the day before, the biggest one-day increase; year-end balance-sheet reduction by banks cited | Bloomberg Law / Bloomberg News, 30 Dec 2022 | https://news.bloomberglaw.com/banking-law/fed-reverse-repo-facility-use-jumps-to-record-2-55-trillion-1 | 2026-09-23 | "biggest one-day increase ever" | hook |
| F6 | SEC money market fund reforms adopted 12 July 2023: removed redemption gates and the link between liquidity levels and fees; minimum daily and weekly liquid assets raised from 10% and 30% to 25% and 50%; mandatory liquidity fee for institutional prime and institutional tax-exempt funds when daily net redemptions exceed 5% of net assets; discretionary fees up to 2% for non-government funds; compliance dates 2 Oct 2023, 2 April 2024, 2 Oct 2024 | SEC press release 2023-129 (search excerpts of the release and law-firm summaries) | https://www.sec.gov/newsroom/press-releases/2023-129 | 2026-09-23 | "from 10% and 30%, to 25% and 50%, respectively" | §3; dat:m2:money-markets:mmf; exo 6 |
| F7 | Reserve Primary Fund, a USD 62 billion money market fund, held USD 785 million of Lehman Brothers debt on the day of Lehman's bankruptcy; investors withdrew about USD 300 billion (14%) from prime money market funds in the week of 15 Sept 2008; Treasury temporarily guaranteed the USD 1.00 share price of more than USD 3 trillion of money market fund shares | SEC Chairman Schapiro, testimony to the Senate Banking Committee, 21 June 2012 | https://www.sec.gov/news/testimony/2012-ts062112mlshtm | 2026-09-23 | "held $785 million in Lehman Brothers debt"; "approximately $300 billion (14%)" | §3; iq 3 |
| F8 | On 16 Sept 2008 the Reserve valued its Lehman exposure at zero and the fund's NAV per share fell to USD 0.97 | Yale Journal of Financial Crises, "United States: Reserve Primary Fund Suspension, 2008" | https://elischolar.library.yale.edu/cgi/viewcontent.cgi?article=1655&context=journal-of-financial-crises | 2026-09-23 | search excerpt: "resulting in a reduction in the net asset value of a share to USD 0.97" | §3 |
| F9 | Commercial paper exempt from registration under Securities Act section 3(a)(3): maturity not exceeding nine months (270 days), proceeds for current transactions | Federal Reserve Bank of Richmond, T. Hahn, "Commercial Paper", Economic Quarterly 1993 | https://www.richmondfed.org/~/media/richmondfedorg/publications/research/economic_quarterly/1993/spring/pdf/hahn.pdf | 2026-09-23 | search excerpt: "Section 3(a)(3) limits maturities to 270 days" | def cp |
| F10 | Fed ON RRP offering rate 3.75% from 17 Sept 2026 | see Chapter 1 ledger F2 | https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a1.htm | 2026-09-23 | see Chapter 1 | problem |

## EXCLUDED

- Commercial paper outstanding and typical maturities: not fetched; the text says only that most paper is much shorter than the legal maximum, without a number.
- Certificate-of-deposit market size and conventions beyond simple interest: not stated.
- Why banks shrink at quarter-ends (foreign banks' quarter-end reporting, the annual G-SIB score): mechanism stated generically ("balance sheets that are measured on the last day"), no rule cited.
- Bill curve levels: illustrative, not market quotes (caption says so).

