# 16. Alternative-Data Strategies — brief and source ledger

## Brief

- **Hook.** Satellite counts of cars in retailers' car parks predicted their revenue surprises; by the time the data were sold widely, the prices already knew.
- **Sections.** From dataset to position; What has been documented to work; Decay as the data spread; Operating an alternative-data strategy.
- **Defines.** nowcast, data decay, alternative-data strategy.
- **Uses (defined earlier).** alternative data (B7.12), backfill bias (B7.3), earnings surprise (B7.11), post-publication decay (B7.13), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** revenue nowcast trade; web-traffic signal; sentiment signal; supply-chain linkage signal.
- **Tutorial.** Take Book 7 chapter 12's synthetic card-panel through to a strategy: a revenue nowcast, trades ahead of announcements, and the decay of its IC as a growing share of the market buys the same data.
- **Build.** `firm.altstrat`: nowcast models for fundamentals from alternative panels, pre-announcement positions, and a data-diffusion model of decay; Python.
- **Weekend problem.** By the time it is sold — named result: the nowcast strategy's Sharpe ratio as the share of informed capital using the data grows.
- **Facts to verify.** Zhu 2019, Big data as a governance mechanism (RFS); Katona, Painter, Patatoukas, Zeng 2025 satellite car counts (JFQA); Cohen and Frazzini 2008 economic links (JF); Green, Huang, Wen, Zhou 2019 crowdsourced employer reviews (JFE).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | C. Zhu, "Big data as a governance mechanism", Review of Financial Studies 32(5) (2019) 2021-2061: technology companies sell real-time indicators of fundamentals (consumer transactions, satellite images); their introduction increases stock price informativeness through lower information-acquisition costs, especially where sophisticated investors have stronger incentives; managers reduce opportunistic trading and invest more efficiently | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhy081 | 2026-09-25 | abstract: "These data include consumer transactions and satellite images. The introduction of these data increases price informativeness through decreased information acquisition costs" | section 3; strat:s1:alternative-data-strategies:nowcast; omsources |
| F2 | Z. Katona, M. O. Painter, P. N. Patatoukas, J. Zeng, "On the capital market consequences of big data: evidence from outer space", Journal of Financial and Quantitative Analysis 60(2) (online 2024) 551-579: satellite coverage of major retailers let sophisticated investors with access form profitable strategies, especially targeting upcoming reports of retailers with bad news; it led to more informed short selling, less informed individual buying and lower liquidity around the reports; unequal access can increase information asymmetry without immediately improving price discovery | Crossref metadata; OpenAlex abstract | https://doi.org/10.1017/s0022109023001448 | 2026-09-25 | abstract: "Satellite data enabled sophisticated investors with access to such data to formulate profitable trading strategies, especially by targeting the upcoming reports of retailers with bad news for the quarter"; "unequal access to big data can increase information asymmetry among market participants without immediately enhancing price discovery" | hook; section 2; section 3; strat:s1:alternative-data-strategies:nowcast; omsources |
| F3 | L. Cohen, A. Frazzini, "Economic links and predictable returns", Journal of Finance 63(4) (2008) 1977-2011: with attention-constrained investors, prices do not promptly incorporate news about economically related firms (principal customers); a long-short strategy on the effect earns monthly alphas of over 150 basis points | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1540-6261.2008.01379.x | 2026-09-25 | abstract: "stock prices do not incorporate news involving related firms, generating predictable subsequent price moves. A long-short equity strategy based on this effect yields monthly alphas of over 150 basis points" | section 2; strat:s1:alternative-data-strategies:supply; omsources |
| F4 | T. C. Green, R. Huang, Q. Wen, D. Zhou, "Crowdsourced employer reviews and stock returns", Journal of Financial Economics 134(1) (2019) 236-251: firms with improving crowdsourced employer ratings significantly outperform firms with declines; the effect is concentrated in current employees' reviews and related to career opportunities and senior management; rating changes help forecast next-quarter earnings surprises | Crossref metadata; abstract on the RePEc/IDEAS record | https://doi.org/10.1016/j.jfineco.2019.03.012 ; https://ideas.repec.org/a/eee/jfinec/v134y2019i1p236-251.html | 2026-09-25 | abstract: "firms experiencing improvements in crowdsourced employer ratings significantly outperform firms with declines"; "help forecast one-quarter-ahead earnings announcement surprises" | section 2; strat:s1:alternative-data-strategies:web; strat:s1:alternative-data-strategies:sentiment; omsources |

## EXCLUDED

- Named data vendors, their prices and client counts: none named, no primary source fetched.
- The claim that satellite car counts predicted revenue surprises specifically: the Katona et al. abstract describes profitable strategies targeting reports with bad news, which the chapter quotes instead.
- The panel's coverage (10%), noise and delivery lag are the chapter's own choices.

