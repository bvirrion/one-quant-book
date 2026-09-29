# 20. Build against Buy — brief and source ledger

## Brief

- **Hook.** In 2019 an electronic market maker paid about a billion dollars for an agency broker, in large part for its execution technology and its clients: the most expensive way to buy software is to buy the company that wrote it.
- **Sections.** What firms build and what they buy; Total cost of ownership; Lock-in and the option to switch; Choosing a vendor.
- **Defines.** build against buy, total cost of ownership, vendor lock-in, switching cost, source-code escrow, request for proposal.
- **Uses (defined earlier).** order management system (B10.20), execution management system (B10.20), machine-learning platform (B12.28), security master (B7.4), handoff specification (B12.28), service-level agreement (B14.15), platform team (ch19).
- **Tutorial.** Compare building an order-management system with buying one over seven years: engineering cost with a maintenance tail, a licence with annual escalators, integration and customisation, the opportunity cost of engineers, and the option to switch later valued on a small binomial tree; run a tornado of the inputs. End state: the net present cost of each path against the horizon, and a tornado chart.
- **Build.** `firm.buildbuy`: build and buy cost models (engineer-years, maintenance share, licence and escalators, integration, exit costs), net present cost and the break-even horizon, a binomial real option to switch vendors or to insource, and a sensitivity report; Python.
- **Weekend problem.** Seven years of an order-management system -- named result: the fully loaded engineer-year cost at which building beats buying over seven years, and the value of the option to switch.
- **Facts to verify.** Virtu Financial's acquisition of Investment Technology Group (2019): price and stated rationale (press release, Form 8-K); Dixit and Pindyck 1994, Investment under uncertainty (real options); Boehm 1981, Software engineering economics (maintenance share); industry estimates of vendor OMS/EMS market (only as cited) (dated).
- **Data.** Synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Virtu Financial press release, 7 November 2018 (Form 8-K, Exhibit 99.1): definitive agreement to acquire Investment Technology Group in a cash transaction valued at $30.30 per ITG share; rationale: a complete suite of agency services including transparent trading and workflow technology, analytics and liquidity solutions leveraging Virtu's technology infrastructure; approximately $123 million of net pre-tax expense savings within two years of completion plus $125 million of capital synergies; the deal further diversifies Virtu after the acquisition of KCG | SEC EDGAR, Form 8-K | https://www.sec.gov/Archives/edgar/data/1592386/000095014218002166/es1801200_ex9901.htm | 2026-09-28 | "a cash transaction valued at $30.30 per ITG share"; "a complete suite of agency services, including transparent trading and workflow technology, analytics, and liquidity solutions"; "approximately $123 million of net pre-tax expense savings, in addition to $125 million of capital synergies" | hook |
| F2 | Virtu Financial press release, 1 March 2019 (Form 8-K, Exhibit 99.1): completion of the acquisition of ITG in a cash transaction valued at $30.30 per share, or a total of approximately $1.0 billion | SEC EDGAR, Form 8-K | https://www.sec.gov/Archives/edgar/data/1592386/000110465919012016/a19-5723_1ex99d1.htm | 2026-09-28 | "in a cash transaction valued at $30.30 per ITG share, or a total of approximately $1.0 billion" | hook |
| F3 | A. K. Dixit and R. S. Pindyck, Investment under Uncertainty, Princeton University Press, 1994 | Crossref | https://doi.org/10.1515/9781400830176 | 2026-09-28 | bibliographic | section 3 |
| F4 | B. W. Boehm, Software Engineering Economics, Prentice-Hall, 1981 | Open Library | https://openlibrary.org/works/OL6034830W | 2026-09-28 | bibliographic | section 2 |

## EXCLUDED

- Industry estimates of the vendor OMS/EMS market: not fetched; not stated.
- Boehm's maintenance-share estimates: not restated; the chapter's maintenance tail is an input.

