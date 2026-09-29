# 5. Multi-Manager Platforms — brief and source ledger

## Brief

- **Hook.** The Form ADV of the largest multi-manager platforms shows their employee counts rising several-fold in a decade, while the press reports each year dozens of teams hired and dozens let go. For a portfolio manager the platform is a job with a known exit condition: a drawdown limit.
- **Sections.** The platform from the employee's side; Size: assets, employees and teams; Team turnover: what the public record shows; Drawdown limits and how long a team lasts; How platforms hire.
- **Defines.** team turnover rate, team tenure.
- **Uses (defined earlier).** multi-manager platform (B1.1), pod (B8.28), drawdown limit (B8.28), pass-through fee (B16.3), payout rate (B16.3), centre book (B16.3), netting risk (B16.3), de-risking ladder (B16.8), track record portability (B16.25), Sharpe ratio (B4.11), regulatory assets under management (ch4).
- **Tutorial.** Two readings: (i) platform growth from Form ADV snapshots 2016-2026 with firm.formadv (employees, RAUM, private funds); (ii) team tenure implied by drawdown rules: on firm.multistrat's pods with Sharpe ratios drawn from a stated range, apply a two-step drawdown ladder (wrapping firm.podshop and firm.ddrules) and measure the survival curve of teams and the share of cut teams that were skilled. End state: ADV growth table and survival curves under two ladders.
- **Build.** `firm.teamtenure`: team survival under drawdown rules (Kaplan--Meier estimate from simulated teams, median tenure, false-cut rate), the relation between a platform's annual team turnover rate and the ladder, and a comparison hook for press-reported turnover ranges; Python; wraps firm.podshop and firm.ddrules.
- **Weekend problem.** How long does a team last? -- named result: median team tenure under the ladder for teams of Sharpe ratio 0.5 and 1.0, and the share of cut teams whose true Sharpe ratio was above 0.5.
- **Facts to verify.** Form ADV rows of Millennium Management, Citadel Advisors, Point72 Asset Management, Balyasny, ExodusPoint, Schonfeld, Verition: employees and RAUM 2016-2026 (dated); press reports of team counts and team departures at platforms (Bloomberg, FT, WSJ; dated ranges; else EXCLUDED); any platform-published description of risk limits (only with a citable source); Grossman and Zhou (1993) pointer to Book 8 ch. 28.
- **Data.** data/industry/adv_platforms.csv (derived); synthetic teams.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SEC adviser files, rows of four platform advisers matched by CRD number (employees item 5.A, advisory employees 5.B(1), RAUM 5.F(2)(c)) in the files of January 2016 (ia010416), January 2017 (ia010317), December 2022 (ia120122), December 2024 (ia120224) and January 2026 (ia010226): e.g. Millennium Management 1,625 / 1,830 / 3,985 / 5,550 / 6,140 employees and $181.5 / 207.9 / 341.0 / 505.9 / 571.1 bn RAUM; Balyasny 287 / 395 / 1,048 / 1,857 / 2,063 employees | SEC, Information about registered investment advisers (Internet Archive copies of the monthly files); derived by in_platform_derive.py | https://www.sec.gov/foia/iareports/ia010416.zip ; https://www.sec.gov/foia/iareports/ia010317.zip ; https://www.sec.gov/files/investment/data/information-about-registered-investment-advisers-exempt-reporting-advisers/ia120122.zip ; https://www.sec.gov/files/investment/data/information-about-registered-investment-advisers-exempt-reporting-advisers/ia120224.zip ; https://www.sec.gov/files/investment/data/information-about-registered-investment-advisers-exempt-reporting-advisers/ia010226.zip | 2026-09-29 | rows extracted to data/industry/adv_platforms.csv | dat:in:multi-manager-platforms:size; figure growth; tutorial |
| F2 | Millennium: 'a global, diversified alternative investment firm'; home page facts '35+ Years of Evolution', '$97BN+ AUM', '7,000+ Employees Globally', '140+ Employee Locations', '360+ Investment Teams' | Millennium home page | https://www.mlp.com/ | 2026-09-29 | page text quoted | dat:in:multi-manager-platforms:size |
| F3 | Balyasny (BAM): 'a global investment firm founded in 2001 focused on delivering consistent, alpha-driven returns through a multi-strategy, multi-PM approach'; 'The firm's 165 investment teams span six strategies, including Equities Long/Short, Equities Arbitrage, Macro, Commodities, Systematic, and Growth Equity'; home page: '$37B Assets Under Management', '2000+ Investment Team & Support Professionals' | Balyasny, About page (Internet Archive copy) and home page | https://www.bamfunds.com/about/ ; https://www.bamfunds.com/ | 2026-09-29 | sentences quoted | dat:in:multi-manager-platforms:size; section 1 |
| F4 | Schonfeld: 'Founded in 1988 ... the firm has grown from a proprietary trading firm with deep systematic roots into a multi-strategy, multi-manager hedge fund with an investing footprint that spans five continents' | Schonfeld home page | https://www.schonfeld.com/ | 2026-09-29 | sentence quoted | dat:in:multi-manager-platforms:size; section 1 |
| F5 | 'ExodusPoint Group' is 'a global, multi-strategy, multi-manager investment firm headquartered in New York City with operations in the UK and globally' | ExodusPoint, UK tax strategy statement on its website | https://www.exoduspoint.com/ | 2026-09-29 | sentence quoted | dat:in:multi-manager-platforms:size |

## EXCLUDED

- Numbers of teams hired and let go each year, and platforms' drawdown limits: press accounts only (no primary source); the chapter models turnover from illustrative ladders and says so.
- Citadel and Point72 as multi-manager platforms: their own pages fetched on 2026-09-29 do not describe themselves in those terms; they are not named as platforms.
- Platform payout percentages: press only; chapter 22 treats the deal with illustrative parameters.

