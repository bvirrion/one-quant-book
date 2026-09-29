# 21. Machine-Learning and Data Engineer — brief and source ledger

## Brief

- **Hook.** Filings for data scientists at finance employers rose several-fold between fiscal years 2020 and 2025 in the labour-condition data, faster than any other quantitative title; the occupation code itself only entered the US classification in 2018.
- **Sections.** Research-embedded machine-learning roles; Platform machine-learning roles; The data engineer; Growth and pay.
- **Defines.** data scientist, data engineer.
- **Uses (defined earlier).** machine-learning engineer (B12.28), model owner (B12.28), handoff specification (B12.28), machine-learning platform (B12.28), alternative data (B7.12), feature store (B12.24), embedded team (B16.21), research engineer (ch19), labor condition application (ch14), prevailing wage (ch14), wage level (ch14), Standard Occupational Classification (ch14), small-cell suppression (ch14).
- **Tutorial.** The role's pay evidence: LCA base-salary ranges (10th-90th percentile, median) for the role family by employer type and wage level from data/industry/lca_ranges.csv through firm.paydata, cells under ten filings suppressed, beside the OEWS range for the matching occupation in the securities industry. Then the trend with firm.roles: yearly filing counts and median base for SOC 15-2051 and machine-learning titles at finance employers against all employers, FY2021-FY2026, with Poisson intervals on counts. End state: a growth chart and a table of ranges.
- **Build.** `firm.roles` (increment): the machine-learning and data role cards and a filing-trend function (counts by year with intervals, growth rate with its standard error); Python.
- **Weekend problem.** The fastest-growing title -- named result: the annual growth rate of data-scientist filings at finance employers FY2021-FY2025 with its interval, and the median-base premium over software developers at the same wage level.
- **Facts to verify.** SOC 2018 introduction of 15-2051 Data Scientists (BLS); pointer to Book 12 ch. 28 and Book 15.
- **Data.** data/industry/lca_trends.csv (derived).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SOC 2010 to 2018 crosswalk: 15-2099 Mathematical Science Occupations, All Other maps in part to the new 15-2051 Data Scientists; no data-scientist occupation in SOC 2010 | BLS, soc_2010_to_2018_crosswalk.xlsx (Internet Archive copy of 20 December 2025) | https://www.bls.gov/soc/2018/soc_2010_to_2018_crosswalk.xlsx ; https://web.archive.org/web/20251220064948id_/https://www.bls.gov/soc/2018/soc_2010_to_2018_crosswalk.xlsx | 2026-09-29 | rows read | hook; section 4 |
| F2 | O*NET 15-2051 Data Scientists: 'Develop and implement a set of techniques or analytics applications to transform raw data into meaningful information using data-oriented programming languages and visualization software. Apply data mining, data modeling, natural language processing, and machine learning to extract and analyze information from large structured and unstructured datasets'; Job Zone Four; O*NET 15-1243 Database Architects: sample reported job titles include 'Data Architect, Data Engineer'; 'Model, design, and construct large relational databases or data warehouses'; CC BY 4.0 | O*NET OnLine | https://www.onetonline.org/link/summary/15-2051.00 ; https://www.onetonline.org/link/summary/15-1243.00 | 2026-09-29 | sentences quoted | definitions; section 3 |
| F3 | Filing counts by role family at the sourced finance employers (chapter 14's lca_ranges.csv): machine learning and data 136 (fiscal 2021) and 1,051 (fiscal 2025; banks 920); software engineer 2,618 and 5,727; quantitative researcher 1,287 and 1,297; trader 147 and 129; risk 197 and 421; all families 4,422 and 8,808 | chapter 14 derived tables (DOL OFLC disclosure files) | https://www.dol.gov/agencies/eta/foreign-labor/performance | 2026-09-29 | data/industry/lca_ranges.csv | hook; dat:in:machine-learning-and-data-engineer:filings; tutorial; figures |
| F4 | Fiscal 2025 data-scientist filings (15-2051 and 15-2051.01) against software developers (15-1252), all sourced finance employers: medians USD 138,000 and 155,000, difference -17,000 (95% bootstrap -20,000 to -15,000); level I -20,500, II -18,300, III -19,000, IV +2,220 (-5,000 to 4,545) | derived by in_lca_ds_derive.py from chapter 14's cache | https://www.dol.gov/agencies/eta/foreign-labor/performance | 2026-09-29 | data/industry/lca_ds_gap.csv | dat:in:machine-learning-and-data-engineer:filings; section 4; figure 21.3 |
| F5 | OEWS May 2025, 15-2051 Data Scientists: finance and insurance sector 46,730 employed, median 124,770; information sector 32,410, median 141,440; professional, scientific and technical services 69,730, median 126,730; credit intermediation 12,450, median 130,300; insurance carriers 15,090; securities 7,210, median 134,510; software publishers 10,950, median 156,220 | BLS, oesm25in4.zip (natsector and nat4d files; Internet Archive copy) | https://www.bls.gov/oes/special-requests/oesm25in4.zip | 2026-09-29 | data/industry/oews_roles.csv | dat:in:machine-learning-and-data-engineer:survey; figure 21.4 |

## EXCLUDED

- Filing counts for all employers (the brief's comparison 'against all employers') and for fiscal 2020, 2022-2024 and 2026: the one LCA pass read fiscal 2021 and 2025 for the sourced finance employers only (decision 5); growth is measured between the two years read.
- Named firms' machine-learning groups: no primary description fetched; the roles are described from Book 12 and Book 15.
