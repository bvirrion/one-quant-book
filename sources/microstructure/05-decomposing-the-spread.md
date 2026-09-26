# 5. Decomposing the Spread — brief and source ledger

## Brief

- **Hook.** A buy of 1,000 shares pays two cents over the mid. A minute later the mid has moved one and a half cents the way the trade went: the liquidity provider kept half a cent, and the rest was what the trade told the market.
- **Sections.** Quoted, effective and realised spreads; The price impact of a trade; Structural decompositions; The vector-autoregression view; Spreads from daily data.
- **Defines.** quoted spread, trade price impact, adverse-selection component, spread decomposition, Huang--Stoll model, Madhavan--Richardson--Roomans model, low-frequency spread estimator.
- **Uses (defined earlier).** effective spread (B1.10), realised spread (B1.10), price improvement (B1.10), Rule 605 report (B1.10), trade sign (B7.9), Lee--Ready algorithm (B7.9), vector autoregression (B4.20), impulse response function (B4.20), generalised method of moments (B4.11), Roll's estimator (B4.21), order-processing cost (ch4), inventory-holding cost (ch4), Glosten--Milgrom model (ch4), informed trader (ch4).
- **Tutorial.** On firm.tape, where every trade's informed flag is known, compute quoted, effective and realised spreads and the trade price impact by horizon; estimate the adverse-selection component with Huang-Stoll, MRR (GMM) and a Hasbrouck VAR, and score each against the planted truth; then estimate spreads from daily bars with the low-frequency estimators. Data: firm.tape (simulated).
- **Build.** `firm.spreaddecomp`: quoted / effective / realised spreads and trade price impact by horizon, Glosten-Harris, Huang-Stoll, MRR by GMM, Hasbrouck VAR impulse responses, Roll, Corwin-Schultz and Abdi-Ranaldo estimators; Python (statsmodels).
- **Weekend problem.** Who paid the two cents? -- named result: the adverse-selection share estimated by each method against the simulator's truth, and the horizon at which the realised spread settles.
- **Facts to verify.** Glosten and Harris 1988 estimating the components of the bid/ask spread (JFE); Huang and Stoll 1997 the components of the bid-ask spread: a general approach (RFS); Madhavan, Richardson, Roomans 1997 why do security prices change? (RFS); Hasbrouck 1991 measuring the information content of stock trades (JF); Corwin and Schultz 2012 (JF); Abdi and Ranaldo 2017 (RFS); SEC 2024 amendments to Rule 605: realized-spread horizons (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | L. R. Glosten and L. E. Harris, "Estimating the components of the bid/ask spread", Journal of Financial Economics 21(1) (1988) 123-142 | Crossref record | https://doi.org/10.1016/0304-405X(88)90034-7 | 2026-09-25 | bibliographic record | §3, omsources |
| F2 | R. D. Huang and H. R. Stoll, "The components of the bid-ask spread: a general approach", Review of Financial Studies 10(4) (1997) 995-1034 | Crossref record | https://doi.org/10.1093/rfs/10.4.995 | 2026-09-25 | bibliographic record | §3, omsources |
| F3 | A. Madhavan, M. Richardson and M. Roomans, "Why do security prices change? A transaction-level analysis of NYSE stocks", Review of Financial Studies 10(4) (1997) 1035-1064 | Crossref record | https://doi.org/10.1093/rfs/10.4.1035 | 2026-09-25 | bibliographic record | §3, omsources |
| F4 | J. Hasbrouck, "Measuring the information content of stock trades", Journal of Finance 46(1) (1991) 179-207 | Crossref record | https://doi.org/10.1111/j.1540-6261.1991.tb03749.x | 2026-09-25 | bibliographic record | §4, omsources |
| F5 | S. A. Corwin and P. Schultz, "A simple way to estimate bid-ask spreads from daily high and low prices", Journal of Finance 67(2) (2012) 719-760 | Crossref record | https://doi.org/10.1111/j.1540-6261.2012.01729.x | 2026-09-25 | bibliographic record | §5, omsources |
| F6 | F. Abdi and A. Ranaldo, "A simple estimation of bid-ask spreads from daily close, high, and low prices", Review of Financial Studies 30(12) (2017) 4437-4480 | Crossref record | https://doi.org/10.1093/rfs/hhx084 | 2026-09-25 | bibliographic record | §5, omsources |
| F7 | SEC amendments to Rule 605 (Release 34-99679, adopted March 6, 2024; 89 FR 26428, April 15, 2024): realized spread at five horizons, 50 milliseconds, 1 second, 15 seconds, 1 minute and 5 minutes; time to execution in milliseconds or finer, share-weighted | Federal Register | https://www.federalregister.gov/documents/full_text/text/2024/04/15/2024-05556.txt | 2026-09-25 | "In total, there will be five realized spread time horizons: 50 milliseconds, 1 second, 15 seconds, 1 minute, and 5 minutes." | dat:mx:decomposing-the-spread:rule605 |
| F8 | Compliance date first set to December 14, 2025, extended on September 30, 2025 to August 1, 2026 (Release 34-104147, 90 FR 47552) | SEC exemptive order, Release 34-105136, April 1, 2026, footnote 5 | https://www.sec.gov/files/rules/exorders/2026/34-105136.pdf | 2026-09-25 | "Thus the compliance date was initially set as December 14, 2025. On September 30, 2025, the Commission extended the compliance date to August 1, 2026." | dat:mx:decomposing-the-spread:rule605 |

## EXCLUDED

- The hook (a buy of 1,000 shares two cents over the mid) is an illustration, not a fact about a market.
- Published estimates of the adverse-selection share for NYSE stocks (in the Glosten-Harris, Huang-Stoll and MRR papers): not quoted; the chapter scores the methods on the simulator, where the truth is known.
- All spreads, impacts, estimator outputs and standard errors are computed on firm.tape and tested.
