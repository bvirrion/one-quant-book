# 19. The Structured-Products Business — brief and source ledger

## Brief

- **Hook.** A private-bank client buys a two-year capital-protected note on an index with 70% participation; the issuer's funding spread, not the option, decides whether 70 was possible.
- **Sections.** Products and wrappers; Anatomy of a note: a bond plus options; Distribution, margins and regulation; Issuer funding and the product lifecycle; Systematic-strategy indices and options on them.
- **Defines.** structured product, structured note, capital-protected note, reverse convertible, participation rate, structuring margin, systematic strategy index, volatility-target index, decrement index.
- **Uses (defined earlier).** funding spread (Book 1 ch. 17), credit spread (Book 2 ch. 21), zero-coupon rate (Book 2 ch. 3), exchange-traded fund (Book 1 ch. 14), total return swap (Book 1 ch. 6), autocallable (ch. 18), dividend risk (ch. 5), local volatility (ch. 9).
- **Tutorial.** Decompose a capital-protected note into a zero-coupon bond and a call spread, solve for the maximum participation given an issuer spread and a margin, and price a call on a 10% volatility-target index against a call on the raw index.
- **Build.** `firm.termsheet`: term-sheet decomposer (bond and option legs), margin and participation solver, and a volatility-target and decrement index calculator.
- **Weekend problem.** Seventy percent participation — named result: the issuer funding spread at which a two-year 100%-protected note can offer 70% participation after a 1.5% margin.
- **Facts to verify.** EU PRIIPs regulation 1286/2014 (key information document); FINRA regulatory notices on structured products; structured-products volumes (industry associations, e.g. SSPA, EUSIPA); decrement index methodology (index provider); risk-control index methodology (index provider).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Regulation (EU) No 1286/2014 of 26 November 2014 on key information documents for packaged retail and insurance-based investment products (PRIIPs): before a PRIIP is made available to retail investors, the manufacturer draws up a key information document and publishes it on its website (Art. 5); the document is pre-contractual information, accurate, fair, clear and not misleading, stand-alone and separate from marketing materials (Art. 6(1)-(2)), and at most three sides of A4 paper when printed (Art. 6(4)) | Official Journal of the European Union L 352/1, 9.12.2014 (PDF via the EU Publications Office) | https://publications.europa.eu/resource/celex/32014R1286 | 2026-09-24 | PDF text, Articles 5 and 6 | sec. distribution and regulation, dat:dv:the-structured-products-business:rules |
| F2 | FINRA Regulatory Notice 12-03, "Heightened Supervision of Complex Products" (17 January 2012): guidance on supervising products with novel, complicated or intricate derivative-like features such as structured notes, inverse or leveraged ETFs, hedge funds and securitised products; earlier FINRA notices addressed structured products, principal-protected notes and reverse convertibles | FINRA notice page | https://www.finra.org/rules-guidance/notices/12-03 | 2026-09-24 | page text (executive summary, background) | sec. distribution and regulation, dat:dv:the-structured-products-business:rules |

## EXCLUDED

- Structured-products volumes (SSPA, EUSIPA and other industry data): not fetched; the chapter quotes no market size.
- Index providers' methodologies for decrement and risk-control indices (S&P DJI returned 403; STOXX did not respond): the chapter defines both constructions generically and computes them itself.
- The PRIIPs Regulation's later amendments and application date: the chapter cites only the 2014 text's requirements.
