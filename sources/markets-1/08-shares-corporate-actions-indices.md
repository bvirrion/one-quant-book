# 8. Shares, Corporate Actions and Indices — brief and source ledger

## Brief

- **Hook.** A stock closes at 480 and opens at 120; nobody lost a cent.
- **Sections.** What a share is; Dividends and the ex-date; Splits, rights, spin-offs and mergers; Adjustment factors; Indices: weighting and the divisor.
- **Defines.** share, free float, dividend, ex-dividend date, record date, stock split, rights issue, spin-off, adjustment factor, index divisor, total return index, market capitalisation.
- **Tutorial.** Build back-adjusted price series and a divisor-maintained index.
- **Build.** Corporate-action adjuster.
- **Weekend problem.** Maintaining an index through a bad week — named result: the new divisor.
- **Facts to verify.** ex-date rule under T+1; S&P/MSCI/FTSE methodology documents; Dow price-weighting.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Nvidia 10-for-1 split: closed $1,208.88 on Fri 7 June 2024; nine additional shares per share distributed after the close; split-adjusted trading from 10 June 2024 at about $120.88; announced 22 May 2024 | CNBC 22 May 2024; Yahoo Finance 10 June 2024 | https://www.cnbc.com/2024/05/22/nvidia-announces-10-for-1-stock-split.html | 2026-09-18 | "Friday closing price was $1,208.88"; "began trading on a split-adjusted basis at market open on June 10" (https://finance.yahoo.com/news/nvidia-stock-rises-after-10-for-1-stock-split-204412528.html) | hook; build test |
| F2 | Under T+1 (from 28 May 2024) the ex-dividend date of a normal distribution is the record date; previously one business day before | SEC Release 34-99881 (NYSE Arca Rule 7.4-E amendment) | https://www.sec.gov/files/rules/sro/nysearca/2024/34-99881.pdf | 2026-09-18 | "transactions in stocks traded 'regular way' generally will be 'ex-dividend' ... on the record date" | dat:m1:shares-corporate-actions-indices:exdate |
| F3 | S&P DJI indices use the divisor methodology; float adjustment | S&P Dow Jones Indices, Index Mathematics Methodology (April 2026) | https://www.spglobal.com/spdji/en/documents/methodologies/methodology-index-math.pdf | 2026-09-18 | document title and scope | def divisor; prop divisoradj |
| F4 | The Dow Jones Industrial Average is price-weighted, 30 stocks, divisor below one | S&P DJI, Dow Jones Averages Methodology (May 2026); "How the Dow Works" | https://www.spglobal.com/spdji/en/documents/methodologies/methodology-dj-averages.pdf | 2026-09-18 | "The Dow indices are price weighted"; divisor "less than one" corroborated https://www.spglobal.com/spdji/en/documents/education/spdji-how-the-dow-works.pdf | section Indices |

## EXCLUDED

- The current numerical value of the Dow divisor: a search returned 0.1321 without date or primary source; not printed.
- The due-bill rule for large special distributions (ex-date after payment date): not verified; sentence removed.
- The Dow's 1896 start date: not in a fetched source; removed.
- Which data vendors use which dividend-adjustment convention: not verified per vendor; stated generically.
