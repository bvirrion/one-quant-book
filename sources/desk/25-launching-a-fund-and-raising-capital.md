# 25. Launching a Fund and Raising Capital — brief and source ledger

## Brief

- **Hook.** A new manager with a two-year track record at a Sharpe ratio of 1.5 wants a hundred million dollars. The record is barely two standard errors from zero, the fund loses money on every dollar below its break-even size, and the seeder's term sheet asks for a fifth of the firm's revenue for as long as the fund exists.
- **Sections.** The first hundred million; Seed capital and its price; What a track record proves; Due diligence; Raising: investors, consultants and the pitch.
- **Defines.** emerging manager, seed investor, revenue-share agreement, capacity right, founders' share class, track record portability, operational due diligence, due diligence questionnaire.
- **Uses (defined earlier).** hedge fund (B1.1), assets under management (B1.1), management fee (B1.3), performance fee (B1.3), high-water mark (B1.3), Sharpe ratio (B4.11), deflated Sharpe ratio (B4.12), standard error (B4.11), fund administrator (ch4), side letter (ch4), most-favoured-nation clause (ch4), master--feeder structure (ch4), fee hurdle (ch4), lock-up period (ch4).
- **Tutorial.** A fund's first five years: inflows depend on the track record's age and Sharpe ratio; fees are net of a seeder's revenue share; costs cover people and service providers. Simulate the paths, find the break-even AUM, the probability of reaching a hundred million dollars within three years, and the value of the seed deal to manager and seeder. End state: a fan chart of AUM with the break-even line, and the probability curve.
- **Build.** `firm.fundlaunch`: a launch cost model (people, administrator, audit, legal, prime broker, data), fee revenue net of revenue share and founders' discounts, an inflow model conditioned on the track record, break-even AUM, survival probability, and the seed deal's value to both sides; Python; uses firm.fees and firm.fundterms.
- **Weekend problem.** The first hundred million -- named result: the break-even AUM and the months to a hundred million dollars under a 20 per cent revenue share, and the track-record length at which a Sharpe ratio of 1 is two standard errors from zero.
- **Facts to verify.** SEC Marketing Rule, Advisers Act Rule 206(4)-1 (2020), and the performance-portability no-action letters (Horizon Asset Management 1996; Great Lakes Advisors 1992) (dated); SEC Private Funds Statistics: size distribution of hedge funds (dated); AIMA illustrative due diligence questionnaire (latest) (dated); Seward & Kissel New Hedge Fund Study (launch terms) (dated); Aggarwal and Jorion 2010 (JFE), The performance of emerging hedge funds and managers; a public description of a seeding platform (press or manager publication) (dated).
- **Data.** Synthetic; SEC statistics derived.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SEC Marketing Rule, 17 CFR 275.206(4)-1 (86 FR 13024, 5 March 2021): an adviser may not advertise gross performance without net performance of at least equal prominence (d)(1); performance of portfolios other than private funds must show one-, five- and ten-year periods (d)(2); predecessor performance only if the persons primarily responsible manage accounts at the advertising adviser, the accounts are sufficiently similar, all substantially similar accounts are included unless excluding them would not materially raise performance, and the advertisement discloses that the results came from another entity (d)(7) | eCFR | https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1 | 2026-09-28 | "Any presentation of gross performance, unless the advertisement also presents net performance"; "The person or persons who were primarily responsible for achieving the prior performance results manage accounts at the advertising adviser"; "the performance results were from accounts managed at another entity"; "[86 FR 13024, Mar. 5, 2021" | dat:fm:launching-a-fund-and-raising-capital:marketing |
| F2 | V. Aggarwal and P. Jorion, "The performance of emerging hedge funds and managers", Journal of Financial Economics, 2010 | OpenAlex / Crossref | https://doi.org/10.1016/j.jfineco.2009.12.010 | 2026-09-28 | bibliographic (title) | section 3 |

## EXCLUDED

- The Horizon (1996) and Great Lakes (1992) no-action letters: not fetched; the rule's own conditions are stated instead.
- SEC Private Funds Statistics size distribution, the AIMA due diligence questionnaire, Seward & Kissel's launch study and a seeding platform's terms: not fetched; the chapter's launch terms are illustrative inputs.
- Aggarwal and Jorion's findings: no abstract retrieved; only the title is cited.

