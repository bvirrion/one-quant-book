# 17. Quant Researcher — brief and source ledger

## Brief

- **Hook.** A high-frequency researcher sees the result of a change after a day of thousands of independent trades; a researcher whose signal rebalances monthly sees twelve observations a year, and needs decades to tell a Sharpe ratio of one-half from zero. The same title covers jobs whose feedback differs by a factor of a thousand.
- **Sections.** Three research jobs: high frequency, medium frequency, asset manager; Horizon, data and feedback speed; Ownership of P&L and of credit; What a researcher ships; Where researchers come from.
- **Defines.** quantitative researcher, feedback speed.
- **Uses (defined earlier).** Sharpe ratio (B4.11), breadth (B7.15), research log (B7.1), research review (B7.1), credit attribution (B16.9), research portfolio (B16.9), medium-frequency trading (ch6), labor condition application (ch14), prevailing wage (ch14), wage level (ch14).
- **Tutorial.** The role's pay evidence: LCA base-salary ranges (10th-90th percentile, median) for the role family by employer type and wage level from data/industry/lca_ranges.csv through firm.paydata, cells under ten filings suppressed, beside the OEWS range for the matching occupation in the securities industry. Then feedback speed with firm.roles: the time needed to reject a zero Sharpe ratio at 95 per cent as a function of the signal's horizon and true Sharpe ratio (standard error of the estimated Sharpe ratio, Lo 2002), by role. End state: the pay-range chart and a log-log chart of years-to-significance against horizon.
- **Build.** `firm.roles` (increment): the quant-researcher role card and the feedback-speed function (years to significance, independent bets per year from horizon and breadth); Python.
- **Weekend problem.** How long until you know? -- named result: the time to reject a zero Sharpe ratio for a true Sharpe ratio of 2 at a one-day horizon, of 1 at a one-week horizon and of 0.5 at a one-month horizon.
- **Facts to verify.** Lo (2002), The statistics of Sharpe ratios, Financial Analysts Journal; firms' own descriptions of quantitative-research roles (careers pages; dated); pointer to Book 7 ch. 15 (breadth) and Book 16 ch. 9 (credit attribution).
- **Data.** data/industry/lca_ranges.csv.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Lo (2002), 'The Statistics of Sharpe Ratios', Financial Analysts Journal 58(4), 36-52: under IID returns the estimated Sharpe ratio has asymptotic variance (1 + SR^2/2)/T (per-period units) | Crossref record; the formula as used in Book 4 | https://api.crossref.org/works/10.2469/faj.v58.n4.2453 | 2026-09-29 | title, journal, volume, issue, pages (Crossref); formula per Book 4 | method; tutorial |
| F2 | Grinold (1989), 'The fundamental law of active management', Journal of Portfolio Management 15(3), 30-37 (the information ratio grows as skill times the square root of breadth; Book 7, chapter 15) | Crossref record | https://api.crossref.org/works/10.3905/jpm.1989.409211 | 2026-09-29 | title, journal, volume, issue, pages | method; section 2 |
| F3 | Optiver, 'Breaking down the trading industry': 'Quantitative researchers focus on solving complex problems through deep, independent research. Their work shapes trading strategies, enhances execution, and improves position management. Some projects start with a quick idea, while others involve longer investigations and iteration. Using tools like statistics, machine learning, and programming, they design and optimize trading algorithms' | Optiver career hub article | https://optiver.com/working-at-optiver/career-hub/breaking-down-the-trading-industry/ | 2026-09-29 | sentences quoted | section 1; section 4 |
| F4 | O*NET 13-2099.01 Financial Quantitative Analysts: 'Develop quantitative techniques to inform securities investing, equities investing, pricing, or valuation of financial instruments'; 'Job Zone Five: Extensive Preparation Needed ... Most of these occupations require graduate school. For example, they may require a master's degree, and some require a Ph.D.' | O*NET OnLine, 13-2099.01 | https://www.onetonline.org/link/summary/13-2099.01 | 2026-09-29 | sentences quoted | definition; section 5 |
| F5 | Quantitative researcher pay evidence, LCA fiscal 2025 ('quant researcher' family, which includes SOC 13-2099.01 filings with generic titles): medians USD 220,000 (systematic funds, 120 applications, 5 employers), 190,000 (platforms, 45, 3), 175,000 (market makers, 131, 9), 158,100 (banks, 825, 9), 107,100 (exchanges, 35, 4); by wage level at market makers I 150,000, II 200,000, III 150,000, IV 225,000; at banks I 88,300, II 145,300, III 179,335, IV 200,000; OEWS May 2025, financial specialists all other (13-2099) in securities: median 100,190, 10th-90th 55,370-222,100 | chapter 14 derived tables | https://www.dol.gov/agencies/eta/foreign-labor/performance ; https://www.bls.gov/oes/special-requests/oesm25in4.zip | 2026-09-29 | cross-reference | dat:in:quant-researcher:pay; tutorial |

## EXCLUDED

- Named firms' research organisation beyond Optiver's published description: not used (careers pages rendered by script only).
- The skill (information coefficient) and breadth of the feedback model: illustrative parameters, not facts.

