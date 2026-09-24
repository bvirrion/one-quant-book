# 21. Corporate Bonds — brief and source ledger

## Brief

- **Hook.** A company rated one notch above junk is downgraded; by Monday its bonds are owned by different people.
- **Sections.** Issuance and the new-issue concession; Ratings and the investment-grade line; The family of spread measures; Covenants, seniority and recovery.
- **Defines.** investment grade, high yield, credit rating, fallen angel, new-issue concession, credit spread, G-spread, I-spread, Z-spread, asset-swap spread, option-adjusted spread, covenant, seniority, recovery rate.
- **Uses (defined earlier).** yield to maturity, par swap rate, underwriting, benchmark, callable bond.
- **Tutorial.** Compute G-, I-, Z- and asset-swap spreads of one bond and show why they differ.
- **Build.** `firm.spreads`: spread-measure library.
- **Weekend problem.** The fallen angel — named result: the forced-selling discount given index exit and the recovery of the spread afterwards.
- **Facts to verify.** rating scales (S&P/Moody's) and IG cut-off; US corporate bond market size (SIFMA); Moody's recovery statistics by seniority; fallen-angel price effect literature.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Investment grade = rated BBB- or above, high yield = BB+ or below; a fallen angel is an issuer downgraded from IG to HY by at least one of the three major agencies; mandates can force sales; repricing precedes the downgrade (CDS widens before the first downgrade, small reaction at the event, partial recovery after the last IG rating is lost, suggesting undervaluation); no broad post-downgrade illiquidity; index providers' rules differ; 93% of passive bond funds use optimised sampling and may retain a security for a while; per Moody's over 20 years nearly a quarter of fallen angels returned to IG, almost half stayed HY, 12% defaulted; downgrades bring lower issuance | Belloni, Helmersson, Jarmuzek, Mosk and Nikolic, "Understanding what happens when angels fall", ECB Financial Stability Review, November 2020, box | https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2020/html/ecb.fsrbox202011_03~578f4f74dc.en.html | 2026-09-23 | "relatively safe "investment grade" (rated BBB- or above) or more risky "high yield" (rated BB+ or below)" | §2; problem; hook |
| F2 | Fed PMCCF term sheet (9 Apr 2020): issuers rated at least BBB-/Baa3 on 22 Mar 2020 by a major NRSRO; those later downgraded must be at least BB-/Ba3 when the Facility buys | Federal Reserve, Primary Market Corporate Credit Facility term sheet | https://www.federalreserve.gov/newsevents/pressreleases/files/monetary20200409a5.pdf | 2026-09-23 | "Issuers that were rated at least BBB-/Baa3 as of March 22, 2020, but are subsequently downgraded, must be rated at least BB-/Ba3" | §2 |
| F3 | HQM corporate bond spot rates: Treasury zero-coupon rates consistent with yields of high-quality corporate bonds rated AAA, AA or A; monthly; 10-year HQM minus 10-year Treasury (GS10) monthly: 0.92 in Jan 2007, 5.04 in Oct 2008 (series maximum since 1984), 4.78 in Dec 2008, 2.05 and 2.11 in Mar and Apr 2020, 0.90 in Aug 2026 | FRED HQMCB10YR (US Treasury) and GS10 (data/markets-2/hqm_gs10_monthly.csv) | https://fred.stlouisfed.org/series/HQMCB10YR | 2026-09-23 | "consistency with yields from "high quality corporate bonds rated AAA, AA, or A"" | fig; §3; dat:m2:corporate-bonds:spreads |

## EXCLUDED

- US corporate bond market size (SIFMA/Z.1): the Z.1 FRED series refused automated download; not used.
- Recovery rates by seniority (Moody's, S&P annual studies): not fetched from a public source; the text explains seniority and uses illustrative recoveries; standard CDS recovery assumptions come in ch. 23.
- ICE BofA and Moody's spread indices: licensed data, not redistributed; the Treasury HQM curve is used instead.

