# 3. Government Bonds — brief and source ledger

## Brief

- **Hook.** Two traders agree on a bond's yield to the fourth decimal and disagree on the price by 1{,}800 dollars per million: one quoted clean, the other dirty.
- **Sections.** Cash flows, day counts and accrued interest; Price and yield; Duration, DV01 and convexity; Zero-coupon rates, par yields and strips.
- **Defines.** coupon, par, clean price, dirty price, accrued interest, day-count convention, yield to maturity, Macaulay duration, modified duration, DV01, convexity, zero-coupon rate, par yield, STRIPS.
- **Uses (defined earlier).** settlement, notional.
- **Tutorial.** Price a bond from its yield on a real calendar, get accrued interest right across a coupon date, and check DV01 against a bumped reprice.
- **Build.** `firm.bond`: day counts, schedules, accrued interest, price/yield, DV01 (Python, C++20, Rust).
- **Weekend problem.** The 32nds desk — named result: the hedge ratio that neutralises a two-bond position and the P&L it leaves after a 25 bp parallel move.
- **Facts to verify.** US Treasury note/bond conventions (semiannual, ACT/ACT, 32nds); Bund/gilt/JGB coupon frequencies and day counts; STRIPS programme start (1985); US Treasury marketable debt outstanding.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | US Treasury notes and bonds pay interest semiannually; each regular payment is half the annual coupon regardless of the number of days in the half-year; accrued interest uses a daily interest decimal based on the actual number of days in the half-year; half-years run on the coupon frequency dates defined by the maturity (e.g. May 31 to Nov 30, Feb 29 to Aug 31 in a leap year) | 31 CFR Part 356, Appendix B, section I (Cornell LII) | https://www.law.cornell.edu/cfr/text/31/appendix-B_to_part_356 | 2026-09-23 | "a semiannual interest payment represents one half of one year's interest, and is computed on this basis regardless of the actual number of days in the half-year" | def accrued; def daycount; build rules |
| F2 | Treasury yield-to-price formulas: P[1 + (r/s)(i/2)] = (C/2)(r/s) + (C/2)a_n + 100 v^n (regular first period), and (P + A)[1 + (r/s)(i/2)] = C/2 + (C/2)a_n + 100 v^n with A = [(s - r)/s](C/2) between coupons; worked examples 8 3/4% of 2020 at 8.84% -> 99.057893; 9 1/2% of Nov 1995 settling 29 Nov 1985 at 9.54% -> A = 0.367403, P = 99.730918 | 31 CFR Part 356, Appendix B, section II | https://www.law.cornell.edu/cfr/text/31/appendix-B_to_part_356 | 2026-09-23 | formulas and examples as quoted | rem conventions; tutorial; build acceptance tests |
| F3 | Treasury note and bond quotations: 86-12 means 86 12/32 percent of face; a plus sign adds a 64th; the buyer pays the price plus accrued interest | P. Ritchken, Fixed Income textbook, chapter 2 "Treasury Securities" (Case Western Reserve University) | https://faculty.weatherhead.case.edu/ritchken/textbook/Fixed_Income/Chap_revised_2.pdf | 2026-09-23 | "A plus sign following the number of 32nds means that a 64th is added to the price" | def price quote; exo 2; problem |
| F4 | In 1985 the US Treasury designated securities eligible to be stripped through the Federal Reserve book-entry system (STRIPS) | same textbook chapter | https://faculty.weatherhead.case.edu/ritchken/textbook/Fixed_Income/Chap_revised_2.pdf | 2026-09-23 | "in 1985, the US Treasury designated some Treasury securities eligible to be stripped through the Federal Reserve book entry system" | def strips |
| F5 | STRIPS: fixed-principal notes, bonds and TIPS may be stripped; bills and FRNs cannot; stripped securities may be reconstituted; held and traded only through financial institutions, brokers and dealers | TreasuryDirect, STRIPS | https://www.treasurydirect.gov/marketable-securities/strips/ | 2026-09-23 | "Bills and FRNs can't be stripped"; "may be reassembled into a single security" | def strips |
| F6 | Marketable Treasury debt, 31 Aug 2026 (USD million): bills 7,248,070; notes 16,218,421; bonds 5,525,284; TIPS 2,152,660; FRNs 679,976; total marketable 31,828,001 | US Treasury, Monthly Statement of the Public Debt, table 1 (Fiscal Data API) | https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/debt/mspd/mspd_table_1?sort=-record_date | 2026-09-23 | API rows for record_date 2026-08-31 | dat:m2:government-bonds:debt |
| F7 | Gilts pay coupons semi-annually on quasi-coupon dates defined by the maturity date; accrued interest actual/actual since 1 November 1998; ex-dividend date seven business days before the payment date | UK Debt Management Office, formulae for calculating gilt prices from yields (pdftotext) | https://www.dmo.gov.uk/media/1sljygul/yldeqns.pdf | 2026-09-23 | "Coupon payments on all current gilts outstanding are made semi-annually"; "The ex-dividend date for all gilts except 3 1/2% War Loan is currently the date seven [business days before]" | dat:m2:government-bonds:conventions |
| F8 | German Federal bonds (Bunds): maturities of 7, 10, 15 or 30 years at issue; fixed annual coupon; repayment at 100 at maturity | Deutsche Finanzagentur, Federal Bonds | https://www.deutsche-finanzagentur.de/en/federal-securities/types-of-federal-securities/federal-bonds | 2026-09-23 | search excerpt: "Holders receive fixed annual interest payments (coupons)" | dat:m2:government-bonds:conventions |

## EXCLUDED

- JGB conventions (semiannual coupons, day count): not fetched; Japan is not named in the conventions box.
- Bund day count (actual/actual ICMA): not confirmed on the agency's page; the box states only the annual coupon.
- US settlement cycle for Treasuries (T+1): not fetched; the chapter's examples take a settlement date without naming the cycle.
- The notes of the chapter (4.25% of August 2036, 4.00% of September 2031) are illustrative, not claimed to be outstanding issues.

