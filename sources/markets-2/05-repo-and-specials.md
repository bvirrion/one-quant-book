# 5. Repo and Specials — brief and source ledger

## Brief

- **Hook.** On 17 September 2019 the overnight general-collateral repo rate printed near ten percent while the policy range stood near two.
- **Sections.** The repo trade from both sides; Tri-party, bilateral and sponsored; Specials and specialness; Fails and the fails charge; September 2019.
- **Defines.** repo rate, reverse repo, tri-party repo, bilateral repo, term repo, special repo rate, specialness, sponsored repo, fails charge.
- **Uses (defined earlier).** repurchase agreement, haircut, general collateral, special, rehypothecation, on-the-run.
- **Tutorial.** Value the specialness of an on-the-run note: the financing advantage over its expected special life.
- **Build.** `firm.repo`: repo book (trades, accrual, margin calls, specialness).
- **Weekend problem.** The special — named result: the break-even price premium an on-the-run can carry given its expected specialness.
- **Facts to verify.** Sept 2019 repo spike (SOFR 5.25%, GC highs; Fed/BIS reports); TMPG fails charge formula (3% minus fed funds, floor 0); FICC sponsored service description; tri-party repo mechanics (BNY); US repo market size (OFR data).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SOFR 5.25% for 17 Sep 2019 (2.43 on 16 Sep, 2.55 on 18 Sep); EFFR 2.25 (16 Sep), 2.30 (17 Sep), 2.25 (18 Sep); FOMC target range 2.00-2.25% until 18 Sep, 1.75-2.00% from 19 Sep; SOFR 2.35 on 30 Sep 2019 | FRED series SOFR, EFFR, DFEDTARU, DFEDTARL; file data/markets-2/repo_sept2019.csv | https://fred.stlouisfed.org/series/SOFR | 2026-09-23 | values in the joined CSV | hook; fig sept2019; §5 |
| F2 | 16 Sep 2019: quarterly corporate tax payments withdrawn from bank and MMF accounts and USD 54 billion of Treasury coupon securities settled; reserves declined about USD 120 billion over two business days to 1.34 trillion, the lowest since 2012; 17 Sep: EFFR 2.30%, above the range, SOFR above 5%; the Desk's overnight repo operation at 9:30 offered up to USD 75 billion and provided 53 billion | Federal Reserve, FEDS Notes, "What Happened in Money Markets in September 2019?", 27 Feb 2020 | https://www.federalreserve.gov/econres/notes/feds-notes/what-happened-in-money-markets-in-september-2019-20200227.html | 2026-09-23 | "$54 billion of long-term Treasury debt settled on September 16"; "provided $53 billion in additional reserves" | hook; §5; exo 8 |
| F3 | TMPG fails charge (Treasury and agency debt): C = (1/360) x 0.01 x max(3 - R, 0) x P per day, R the TMPG reference rate at 5 pm on the preceding business day = FOMC target rate or lower limit of the target range; applies to Treasury trades from 1 May 2009; example R = 1%: USD 5,555.56 a day on USD 100 million | TMPG, Frequently Asked Questions: TMPG Fails Charges (2013, pdftotext) | https://www.newyorkfed.org/medialibrary/microsites/tmpg/files/04_01_2013_Fails_charges_FAQ.pdf | 2026-09-23 | "the greater of (a) 3 percent per annum minus the TMPG reference rate ... and (b) zero"; "C = $5,555.56" | def fails charge; prop floor; build test; exo 5; dat:m2:repo-and-specials:fails |
| F4 | FICC sponsored repo and sponsored reverse repo volumes (USD): sum peaked at 2.960 trillion on 31 Dec 2025 (repo 1.384, reverse 1.576); 2.329 trillion on 21 Aug 2026 (repo 1.053, reverse 1.276); series from 23 Mar 2020 | Office of Financial Research, Hedge Fund Monitor, dataset ficc (API); file data/markets-2/ficc_sponsored.csv | https://data.financialresearch.gov/hf/v1/series/timeseries?mnemonic=FICC-SPONSORED_REPO_VOL | 2026-09-23 | API values | fig sponsored; dat:m2:repo-and-specials:sponsored |
| F5 | Sponsored repo: a FICC member dealer sponsors a non-dealer counterparty, typically a hedge fund or money market fund, onto FICC's cleared repo platform; sponsored reverse repo predominantly money market funds; data combine GC and DVP | OFR, FICC Sponsored Repo Service Volumes (dataset page) | https://www.financialresearch.gov/hedge-fund-monitor/datasets/ficc/ | 2026-09-23 | "a dealer that is a member of the Fixed Income Clearing Corporation (FICC) sponsors a non-dealer counterparty" | def sponsored |
| F6 | Oct 2019: the Federal Reserve would purchase Treasury bills at least into Q2 2020 to maintain ample reserves at or above the early-September 2019 level, at an initial pace of about USD 60 billion per month from mid-October; balance sheet normalization concluded in August 2019, after which reserves kept declining; Treasury issuance added to already elevated primary-dealer inventories | Federal Reserve statement, 11 Oct 2019; FEDS Notes, 27 Feb 2020 | https://www.federalreserve.gov/newsevents/pressreleases/monetary20191011a.htm | 2026-09-23 | "purchase Treasury bills at a pace of about $60 billion per month" | §5 |
| F7 | 28 Jul 2021: FOMC established a domestic standing repo facility (daily overnight repo against Treasuries, agency debt and agency MBS, maximum operation size USD 500 billion, minimum bid rate initially 25 bp) and a FIMA repo facility | Federal Reserve press release, 28 July 2021 | https://www.federalreserve.gov/newsevents/pressreleases/monetary20210728b.htm | 2026-09-23 | search excerpt of the release | §5 |
| F8 | Before May 2009 the convention was to postpone a failed delivery without explicit penalty and at an unchanged invoice price; after Lehman's insolvency (Sept 2008) a decline in short-term rates set the stage for an extraordinary volume of settlement fails; the fails charge was introduced in May 2009 | K. Garbade et al., "The Introduction of the TMPG Fails Charge for U.S. Treasury Securities", FRBNY Economic Policy Review, Oct 2010 (abstract) | https://www.newyorkfed.org/medialibrary/media/research/epr/10v16n2/1010garb.pdf | 2026-09-23 | "a decline in short-term interest rates set the stage for an extraordinary volume of settlement fails" | §4 |
| F9 | Target range 0 to 1/4 percent from 15 Mar 2020 (lower limit 0 through 2021) | Federal Reserve press release 15 Mar 2020 (Chapter 4 ledger F6); FRED DFEDTARL | https://www.federalreserve.gov/newsevents/pressreleases/monetary20200315a.htm | 2026-09-23 | "0 to 1/4 percent" | exo 6 |

## EXCLUDED

- Intraday high of GC repo on 17 Sep 2019 (press reported about 10%): the Fed note does not give it; the hook uses SOFR's 5.25% instead (the brief said "near ten percent").
- Identity of the tri-party agent(s) in the US: not sourced; the text says "a clearing bank acting as agent".
- US repo market size (OFR data on all segments): not fetched; the sponsored series only.
- Typical haircuts on Treasuries: not sourced; the 2% of the examples is labelled illustrative.
- The specialness path of the problem is illustrative.

