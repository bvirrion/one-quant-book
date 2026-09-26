# 19. Transaction-Cost Analysis — brief and source ledger

## Brief

- **Hook.** A portfolio manager's order cost 25 basis points against the arrival price; the broker's report says it beat VWAP by three. Both numbers are right, and only one of them says what the order cost the fund.
- **Sections.** Benchmarks and what each hides; Pre-trade estimates; Post-trade attribution; Comparing across orders, brokers and peers; Closing the loop.
- **Defines.** pre-trade cost estimate, execution benchmark, slippage attribution, post-trade reversion, peer-universe comparison.
- **Uses (defined earlier).** implementation shortfall (B7.19), arrival price (B7.19), transaction cost analysis (B7.23), delay cost (B7.23), opportunity cost (B7.23), VWAP slippage (B7.23), mark-out curve (B7.23), square-root impact law (B7.27), VWAP algorithm (ch16), execution algorithm (ch16), impact prefactor (ch11), clustered standard errors (B4.16), A/B test (B7.21), CUPED (B7.21), information leakage (ch9).
- **Tutorial.** Generate a parent-order log in firm.exchsim with the algorithms of chapter 16 under varied parameters and market conditions; run TCA against every benchmark, attribute slippage to spread, impact, timing and opportunity, regress costs on size, volatility and participation with clustered errors, and read post-trade reversion as a leakage signal; compare with the pre-trade model. Data: simulated.
- **Build.** `firm.tca`: pre-trade model (on Book 7's firm.tcost), post-trade reports by benchmark, slippage attribution, reversion, difficulty-adjusted peer comparison with robust errors, and the feedback step that refits an algorithm's parameters; Python, on Book 7's firm.markout.
- **Weekend problem.** Bad broker or hard day? -- named result: the difficulty-adjusted cost difference between two algorithms with its confidence interval, against the raw difference.
- **Facts to verify.** Perold 1988 the implementation shortfall: paper versus reality (JPM); Kissell 2013; Frazzini, Israel, Moskowitz 2018; Anand, Irvine, Puckett, Venkataraman 2012 performance of institutional trading desks (RFS); MiFID II RTS 27/28 and their suspension or deletion in the 2024 review (dated); FCA best execution thematic reviews (2014, 2017).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. F. Perold, "The implementation shortfall: paper versus reality", Journal of Portfolio Management 14(3) (1988) 4-9 | Crossref record | https://doi.org/10.3905/jpm.1988.409150 | 2026-09-26 | bibliographic record (the full title "The Implementation Shortfall: Paper versus Reality" in the Streetwise reprint record, 10.1515/9781400829408-014) | §1, omsources |
| F2 | A. Anand, P. Irvine, A. Puckett, K. Venkataraman, "Performance of institutional trading desks: an analysis of persistence in trading costs", Review of Financial Studies 25(2) (2012) 557-598: institutional trading desks sustain relative performance over adjacent periods | Crossref record; SSRN abstract (1272040) | https://doi.org/10.1093/rfs/hhr110 | 2026-09-26 | "we document that institutional trading desks can sustain relative performance over adjacent periods" | §4, omsources |
| F3 | A. Frazzini, R. Israel, T. J. Moskowitz, "Trading costs", SSRN working paper 3229719 (2018): 1.7 trillion dollars of live executions of a large institutional manager, 21 markets, 19 years; actual trading costs an order of magnitude smaller than previous studies suggest | Crossref record with abstract | https://doi.org/10.2139/ssrn.3229719 | 2026-09-26 | "Using 1.7 trillion dollars of live trade execution data from a large institutional money manager ... We find actual trading costs to be an order of magnitude smaller than previous studies suggest" | §4, omsources |
| F4 | R. Kissell, The Science of Algorithmic Trading and Portfolio Management, Academic Press (2014) | Crossref record (book chapter) | https://doi.org/10.1016/B978-0-12-401689-7.00001-5 | 2026-09-25 | bibliographic record (see chapter 16, F5) | omsources |
| F5 | Directive (EU) 2021/338, Article 1(6): the periodic public reporting requirement of Article 27(3) of MiFID II does not apply until 28 February 2023 | EUR-Lex, official text | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32021L0338 | 2026-09-26 | "in Article 27(3), the following subparagraph is added: 'The periodic reporting requirement to the public laid down in this paragraph shall not apply until 28 February 2023.'" | dat:mx:transaction-cost-analysis:rts, omsources |
| F6 | Directive (EU) 2024/790 of 28 February 2024: recital (8) (the reports under Article 27(3) and (6) are rarely read and do not enable meaningful comparisons); Article 1(4): Article 27(3) replaced by a duty to inform the client of the execution venue, Article 27(6) deleted; Article 2: transposition by 29 September 2025 | EUR-Lex, official text (OJ L 2024/790, 8.3.2024) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024L0790 | 2026-09-26 | "Evidence and feedback from stakeholders have shown that those reports are rarely read and do not enable investors or other users of those reports to make meaningful comparisons"; "(b) paragraph 3 is replaced by the following: '3. ... inform the client of the venue where the order was executed.'; (c) paragraph 6 is deleted"; "Member States shall bring into force the laws ... by 29 September 2025" | dat:mx:transaction-cost-analysis:rts, omsources |
| F7 | FCA PS21/20 (2021): from 1 December 2021 UK firms are no longer required to prepare RTS 27 and RTS 28 reports | FCA policy statement PDF | https://www.fca.org.uk/publication/policy/ps21-20.pdf | 2026-09-26 | "From 1 December 2021, your firm will no longer be required to prepare RTS 27 and RTS 28 reports." | dat:mx:transaction-cost-analysis:rts, omsources |

## EXCLUDED

- FCA best-execution thematic reviews (2014, 2017): not needed once the dated box states the RTS 27/28 history from primary texts; not cited.
- Frazzini-Israel-Moskowitz's manager is not named (the abstract does not name it).
- Attribution into impact and timing uses the simulator's counterfactual day (same exogenous flow without the order); real TCA cannot, and the
  chapter says so.
- All numbers are computed by mx_tca and firm.tca and tested.

