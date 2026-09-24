# 3. The Buy Side — brief and source ledger

## Brief

- **Hook.** Twelve thousand index funds must all buy the same stock at the same closing auction.
- **Sections.** Asset owners and asset managers; Mandates, benchmarks and tracking error; Hedge funds and their structures; Why each of them trades; Retail.
- **Defines.** buy side, mandate, benchmark, tracking error, passive management, active management, commodity trading advisor, management fee, performance fee, high-water mark.
- **Tutorial.** Compute tracking error and fee drag for three funds on simulated returns.
- **Build.** Fund fee engine with high-water mark.
- **Weekend problem.** Two and twenty — named result: the manager's share of gross alpha over ten years.
- **Facts to verify.** share of passive in US equity funds (ICI); hedge fund industry AUM (HFR/SEC); UCITS / 40 Act citations.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | At year-end 2025 index mutual funds and index ETFs together held 52% of assets in US long-term funds | ICI, 2026 Investment Company Fact Book, chapter 2 | https://icifactbook.org/pdf/2026-factbook-ch2.pdf | 2026-09-18 | "index mutual funds and index ETFs together accounted for the majority (52%) of assets in long-term funds" | dat:m1:the-buy-side:passive |
| F2 | Global hedge fund industry capital $5.6tn at end of Q2 2026; passed $5tn for the first time in Q4 2025 ($5.15tn) | HFR market commentary / Global Hedge Fund Industry Report | https://www.hfr.com/media/market-commentary/global-hedge-fund-industry-capital-surges-past-historic-5-trillion-milestone/ | 2026-09-18 | "surged to $5.6 trillion in Q2"; "record $5.15 trillion, surpassing the historic $5 trillion milestone" (also https://www.hfr.com/hfr-media/hfr_world/hfr-world-global-hedge-fund-industry-report-2026q1/) | dat:m1:the-buy-side:hf |
| F3 | 1940 Act diversified company: 75% of assets such that no issuer exceeds 5% of the fund's assets or 10% of the issuer's outstanding voting securities | SEC staff report to Congress on threshold limits for diversified companies, Feb 2022 | https://www.sec.gov/files/staff-report-threshold-limits-diversified-funds.pdf | 2026-09-18 | section 5(b)(1) test described in the report | rem:m1:the-buy-side:law |
| F4 | UCITS 5/10/40 rule: max 10% of assets in one issuer; holdings above 5% may not together exceed 40% | Directive 2009/65/EC art. 52; summary in financialregulations.eu glossary and ESMA UCITS Q&A | https://www.esma.europa.eu/sites/default/files/library/esma34_43_392_qa_on_application_of_the_ucits_directive.pdf | 2026-09-18 | "no more than 10% ... investments of more than 5% with a single issuer may not make up more than 40%" | rem:m1:the-buy-side:law; exo 4 |

## EXCLUDED

- The original hook ('twelve thousand index funds') and a typical pension asset split: no source; the hook is now an explicitly illustrative scene.
- 'Typical' tracking-error limits of institutional mandates: no primary source; replaced by a conditional statement.
- CTA definition follows the Commodity Exchange Act usage; statutory text not fetched — stated generically ('registered to advise on futures trading').
