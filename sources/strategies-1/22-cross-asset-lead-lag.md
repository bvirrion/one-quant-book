# 22. Cross-Asset Lead-Lag — brief and source ledger

## Brief

- **Hook.** Bond futures react to a surprise in the payrolls report within a second; small-cap stocks take days. The information is the same.
- **Sections.** Intermarket signals at daily horizons; Intraday lead-lag between futures; Slow diffusion and who is slow; Trading it.
- **Defines.** intermarket signal, slow diffusion.
- **Uses (defined earlier).** lead--lag relationship (B7.10), lead--lag estimator (B7.10), futures-to-cash lead (B7.10), Hayashi--Yoshida estimator (B4.21), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** bond-to-equity signal; commodity-to-producer signal; futures-to-cash intraday lead; currency-to-exporter signal.
- **Tutorial.** Plant diffusion lags between firm.synthfut markets and firm.synthmkt industries, detect them with Book 7's lead-lag tools, and trade intermarket signals at daily and intraday horizons.
- **Build.** `firm.xasset`: intermarket signal construction on firm.leadlag, with lag estimation, stability tests and portfolio construction; Python.
- **Weekend problem.** Same information, different speeds — named result: the lead detected at each horizon and the strategy's Sharpe ratio after costs.
- **Facts to verify.** Hong, Torous, Valkanov 2007, Do industries lead stock markets? (JFE); Menzly and Ozbas 2010 market segmentation and cross-predictability (JF); Hou 2007 industry information diffusion (RFS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | H. Hong, W. Torous, R. Valkanov, "Do industries lead stock markets?", Journal of Financial Economics 83(2) (2007) 367-396: a significant number of US industry returns, including retail, services, commercial real estate, metal and petroleum, forecast the stock market by up to two months; an industry's propensity to predict the market correlates with its propensity to forecast economic activity such as industrial production; similar patterns in the eight largest non-US markets; information diffuses gradually across markets | Crossref metadata; authors' working-paper version (Columbia, pdftotext) | https://doi.org/10.1016/j.jfineco.2005.09.010 ; http://www.columbia.edu/~hh2679/industry-12-05-05.pdf | 2026-09-25 | abstract: "a significant number of industry returns, including retail, services, commercial real estate, metal and petroleum, can forecast the stock market by up to two months" | hook; section 1; strat:s1:cross-asset-lead-lag:commodity; omsources |
| F2 | H. Hong, W. Torous, R. Valkanov, "Note on Do Industries Lead Stock Markets" (7 October 2014): replication data and code posted; the sample extended from 1946-2002 to 1946-2013; a subset of the same industries continues to predict the market; the subset is smaller, with time variation in the predictive relations; a robust core of industries leads throughout | authors' note (UCSD, pdftotext) | https://rady.ucsd.edu/_files/faculty-research/valkanov/Note_10282014.pdf | 2026-09-25 | "A subset of the same industries that predicted the market in HTV (2007) continue to predict in the extended sample. The subset of industries is smaller, due to some time-variation in the predictive relations" | section 3 |
| F3 | L. Menzly, O. Ozbas, "Market segmentation and cross-predictability of returns", Journal of Finance 65(4) (2010) 1555-1580: with investor specialization and segmentation, information diffuses gradually; stocks in economically related supplier and customer industries cross-predict each other's returns; cross-predictability declines with the number of informed investors (analyst coverage, institutional ownership) | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1540-6261.2010.01578.x | 2026-09-25 | abstract: "stocks that are in economically related supplier and customer industries cross-predict each other's returns"; "the magnitude of return cross-predictability declines with the number of informed investors" | section 3; strat:s1:cross-asset-lead-lag:commodity; omsources |
| F4 | K. Hou, "Industry information diffusion and the lead-lag effect in stock returns", Review of Financial Studies 20(4) (2007) 1113-1138: slow diffusion of industry information is a leading cause of the lead-lag effect; the big-to-small lead-lag is mainly intra-industry, driven by sluggish adjustment to negative information, stronger in small, less competitive and neglected industries | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/revfin/hhm003 | 2026-09-25 | abstract: "the lead-lag effect between big firms and small firms is predominantly an intra-industry phenomenon. Moreover, this effect is driven by sluggish adjustment to negative information" | hook; section 3; omsources |

## EXCLUDED

- Y. Tse (2015) SSRN re-examination of Hong, Torous and Valkanov: not fetched (SSRN blocks scripts); the authors' own 2014 note on time variation is cited instead.
- Intraday lead-lag between index futures and cash stocks or ETFs at specific latencies: no primary source fetched; the chapter's intraday numbers are synthetic.
- The planted diffusion (0.08 over five days on three links), the tick process and the cost assumptions are the chapter's own choices.
