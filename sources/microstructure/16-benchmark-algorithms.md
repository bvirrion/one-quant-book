# 16. Benchmark Algorithms — brief and source ledger

## Brief

- **Hook.** Most institutional equity orders are handed to algorithms that promise a benchmark: the day's volume-weighted price, the arrival price, the close. Each promise is a schedule, and each schedule is only as good as its forecast of the day's volume.
- **Sections.** The algorithms and their benchmarks; Forecasting intraday volume; VWAP: static and dynamic; Participation and its feedback; Implementation-shortfall and close algorithms.
- **Defines.** execution algorithm, VWAP algorithm, TWAP algorithm, participation algorithm, implementation-shortfall algorithm, target-close algorithm, intraday volume forecast, dynamic VWAP.
- **Uses (defined earlier).** volume-weighted average price (B7.2), intraday volume profile (B7.5), percentage of volume (B7.27), VWAP slippage (B7.23), implementation shortfall (B7.19), arrival price (B7.19), closing price (B1.13), market-on-close order (B1.13), parent order (ch14), child order (ch14), Almgren--Chriss model (ch14), ARMA process (B4.17), principal component analysis (B4.22).
- **Tutorial.** Forecast intraday volume on simulated days (static curve, rolling average, a PCA-plus-ARMA decomposition); run VWAP, TWAP, participation, shortfall and close algorithms in firm.exchsim; measure VWAP slippage from forecast error, and the feedback of a participation algorithm on a thin day. Data: simulated.
- **Build.** `firm.algos`: the benchmark algorithms as schedulers on firm.acexec's interface (static and dynamic VWAP, TWAP, participation with caps, shortfall via Almgren-Chriss, close with a market-on-close split) and the intraday volume forecaster; Python.
- **Weekend problem.** VWAP on a day that was not average -- named result: the VWAP slippage explained by volume-forecast error, for static and dynamic VWAP, on the simulator's high-volume days.
- **Facts to verify.** Konishi 2002 optimal slice of a VWAP trade (JFM); Bialkowski, Darolles, Le Fol 2008 improving VWAP strategies: a dynamic volume approach (JBF); Humphery-Jenner 2011 optimal VWAP trading under noisy conditions (JBF); Madhavan 2002 VWAP strategies (Transaction Performance / Trading); Kissell 2013 The Science of Algorithmic Trading and Portfolio Management; a broker's public algorithm guide (dated; only with a citable document).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | H. Konishi, "Optimal slice of a VWAP trade", Journal of Financial Markets 5(2) (2002) 197-221: the static slicing of a VWAP order | Crossref record | https://doi.org/10.1016/S1386-4181(01)00023-4 | 2026-09-25 | bibliographic record (title, journal, volume, pages); no abstract in open sources, so the text claims only that the paper treats the static slicing | §2, omsources |
| F2 | J. Białkowski, S. Darolles, G. Le Fol, "Improving VWAP strategies: a dynamic volume approach", Journal of Banking and Finance 32(9) (2008) 1709-1722: volume decomposed into a market part and a stock-specific part, the specific part modelled by ARMA and SETAR, with dynamic adjustments during the day | Crossref record; RePEc/IDEAS abstract | https://doi.org/10.1016/j.jbankfin.2007.09.023 ; https://ideas.repec.org/a/eee/jbfina/v32y2008i9p1709-1722.html | 2026-09-25 | "The idea of considered models is based on the decomposition of traded volume into two parts: one reflects volume changes due to market evolution; the second describes the stock specific volume pattern. The dynamic of the specific volume part is depicted by ARMA and SETAR models." | §2, omsources |
| F3 | M. Humphery-Jenner, "Optimal VWAP trading under noisy conditions", Journal of Banking and Finance 35(9) (2011) 2319-2329: a dynamic VWAP framework that incorporates intraday news | Crossref record; RePEc/IDEAS abstract | https://doi.org/10.1016/j.jbankfin.2011.01.028 ; https://ideas.repec.org/a/eee/jbfina/v35y2011i9p2319-2329.html | 2026-09-25 | "this paper presents a Dynamic VWAP (DVWAP) framework that allows informed traders to utilize random news; and thus, improve trade-execution" | §3, omsources |
| F4 | A. Madhavan, "Volume-weighted average price (VWAP)", Encyclopedia of Quantitative Finance, Wiley (2010): the VWAP as a common benchmark for trading and execution | Crossref record with abstract | https://doi.org/10.1002/9780470061602.eqf07036 | 2026-09-25 | "The volume- (or time-) weighted average price is a common benchmark used to evaluate performance in trading and execution." | §1, omsources |
| F5 | R. Kissell, The Science of Algorithmic Trading and Portfolio Management, Academic Press (2014), chapter 1 "Algorithmic Trading" | Crossref record (book chapter) | https://doi.org/10.1016/B978-0-12-401689-7.00001-5 | 2026-09-25 | bibliographic record; Crossref dates the book 2014 (the brief said 2013, the print year of first release); the chapter cites 2014 | §1, omsources |

## EXCLUDED

- A broker's public algorithm guide (brief, "dated; only with a citable document"): not used; the chapter names no broker and its algorithm
  descriptions are the generic ones of the literature, so no dated box.
- Madhavan (2002), "VWAP strategies" (Transaction Performance): not found in Crossref or an open archive; replaced by his 2010 encyclopaedia entry.
- Market shares of algorithmic execution: no primary source verified; not stated.
- All numbers are computed by mx_algos and firm.algos and tested. The simulated day is 26 one-minute bins (firm.agentmkt with an activity curve);
  the panel's forecast study is bin-level (the volume the simulator prints, drawn in advance), the VWAP, participation and benchmark studies run in
  firm.exchsim.

