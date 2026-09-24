# Book 2 figure log (each figure checked on its own rendered band)

| ch | figure | checked | verdict / fix |
|---|---|---|---|
| 1 | 1.1 Fed balance sheet (stacked bars) | 2026-09-23 | sides sum to 6 747; legend ragged -> `legend cell align=left`; clean |
| 1 | 1.2 reserve demand in a corridor | 2026-09-23 | deposit label crossed by the curve -> moved under the line; lines drawn with \draw; 300 dpi check: both facility lines red dashed; clean |
| 1 | 1.3 fixings and running compounded rate | 2026-09-23 | step plot correct (hike day 17, quarter-end 30); caption said "days remaining" (wrong) -> rewritten |
| 1 | 1.4 lookback schematic | 2026-09-23 | brace moved over the last p days; start/end labels moved off the axis; clean |
| 2 | 2.1 bill curve, three conventions | 2026-09-23 | ordering d < m < i at every maturity; 52w money-market yield above 26w as the caption says; clean |
| 2 | 2.2 money-fund plumbing schematic | 2026-09-23 | "cash for shares" raised to 17pt; caption's "middle arrow" (four arrows) -> named arrows; clean |
| 2 | 2.3 ON RRP take-up 2022-23 (FRED) | 2026-09-23 | labels hit the frame / clipped at right -> anchor east, ymax 2700; spikes at 30 Sep, 30 Dec, 31 Mar match the CSV; clean |
| 2 | 2.4 one-week rate by start date | 2026-09-23 | step up for starts 24-30 Sep (spanning 30 Sep); ticks 30/1 crowded -> 30 dropped; clean |
| 3 | 3.1 settlement timeline | 2026-09-23 | settlement label collided with both brace labels -> moved up with a dotted leader; clean |
| 3 | 3.2 price-yield with tangent and 2nd order | 2026-09-23 | at +-1% the convexity gap was invisible -> range +-2.5%, gaps 2.2/2.6 asserted in a test; tangent below curve both sides; clean |
| 3 | 3.3 par and bootstrapped zero curve | 2026-09-23 | zero above par where par rises, below at 1-2y (asserted); clean |
| 3 | 3.4 clean and dirty over a year | 2026-09-23 | dirty clipped at top -> ymax 102.8; weekly sampling slanted the coupon drop -> daily; clean |
| 4 | 4.1 auction demand curve | 2026-09-23 | when-issued label clipped; offered-amount label crossed the curve then the WI line -> both moved; crossing at 4.198 matches the stop-out (asserted); clean |
| 4 | 4.2 market-structure schematic | 2026-09-23 | arrows and labels clear; clean |
| 4 | 4.3 15 Oct 2014 event window | 2026-09-23 | ERROR found: tick "2.13" and the close line drawn at 2.13 not 2.14 -> scale recomputed (y = 0.5 + 12.5(yield - 1.85)); times now to scale (6m20s, 4m56s); 1.86 label moved below with the axis lowered; clean |
| 4 | 4.4 Fed Treasury holdings 2020 (FRED) | 2026-09-23 | dashed lines at 15 and 23 March placed by day index 102/110; clean |
| 5 | 5.1 bilateral / tri-party / sponsored schematic | 2026-09-23 | added to reach 4 figures; "cash" labels crowded boxes then the panel title -> narrower boxes, labels moved, titles raised; clean |
| 5 | 5.2 FICC sponsored volumes (OFR) | 2026-09-23 | reverse repo above repo throughout, year-end peaks (Dec 2025 max, asserted); clean |
| 5 | 5.3 specialness path | 2026-09-23 | both labels clipped at the frame -> anchored inside; clean |
| 5 | 5.4 SOFR, EFFR, range Sept 2019 (FRED) | 2026-09-23 | range steps down on 19 Sep (joined by date after a paste misalignment was caught); 5.25 label off the frame; clean |
| 6 | 6.1 cash-and-carry schematic | 2026-09-23 | sloped labels clear of boxes; clean |
| 6 | 6.2 delivery-month timeline | 2026-09-23 | first draft had five overlapping labels -> redesigned with short labels, rules moved to the caption; clean |
| 6 | 6.3 price/factor minus cheapest vs parallel shift | 2026-09-23 | raw price/factor lines were indistinguishable -> plotted relative to the envelope; switch at +147 matches switch_shift() (asserted); clean |
| 6 | 6.4 implied repo by note | 2026-09-23 | tick labels ran together -> maturities only; CTD bar just under the repo line; clean |
| 7 | 7.1 euro spreads to Germany (OECD) | 2026-09-23 | peak label sat on the peaks -> moved right; Spain's higher 2012 peak (555) added to the caption and asserted; clean |
| 7 | 7.2 JGB 10y with YCC shading | 2026-09-23 | shading Sep 2016 - Mar 2024 matches the BoJ statements; clean |
| 7 | 7.3 collateral-spiral schematic | 2026-09-23 | bottom arrow label touched the boxes -> lowered; clean |
| 7 | 7.4 LDI cushion vs yield rise | 2026-09-23 | +160 label crossed the 250 line, then the curve -> two lines at bottom left; 43% at 160 and zero at 351 asserted; clean |
| 8 | 8.1 contract reference periods and FOMC dates | 2026-09-23 | coordinates first eyeballed -> computed from day fractions; decision dashes crossed the SR1 labels -> stopped below the bars; clean |
| 8 | 8.2 implied policy path | 2026-09-23 | \foreach inside axis was fatal -> explicit \draw; labels crowded / clipped -> moved; clean |
| 8 | 8.3 hike probability vs turn | 2026-09-23 | monotone, 35.2 at 0 and 33.4 at 10 (asserted); clean |
| 8 | 8.4 convexity adjustment by horizon | 2026-09-23 | quadratic growth; 13.1 and 51.25 at 5 and 10 years (asserted); clean |
| 9 | 9.1 swap cash flows schematic | 2026-09-23 | added (chapter had 2 figures); two labels collided -> moved; clean |
| 9 | 9.2 par inputs, zero and forward curves | 2026-09-23 | forwards piecewise flat as the caption says (log-linear DF interpolation); inputs on the curve; clean |
| 9 | 9.3 bucketed DV01 | 2026-09-23 | par 10y only on 10y; 5y5y -45/+83 (asserted); minus-zero label in CSV removed; clean |
| 9 | 9.4 compression cycle | 2026-09-23 | added; clean |
| 10 | 10.1 bilateral web vs cleared star | 2026-09-23 | added (chapter had 3); caption first set beside the picture (no blank line before `\omcaption`) -> blank line; clean |
| 10 | 10.2 how the basis arises (flows) | 2026-09-23 | "pays fixed at CCP B" label ran under the other-dealers box -> two lines below the arrow; clean |
| 10 | 10.3 IM profiles 10y / 30y | 2026-09-23 | 10y line ran along the axis from 10 to 30 -> `restrict x to domain`; sawtooth between payment dates is real (DV01 accretes); clean |
| 10 | 10.4 basis by maturity and funding | 2026-09-23 | caption said "grows faster than maturity" but curve is concave (0.94 at 10y, 2.30 at 30y) -> caption corrected; clean |
| 11 | 11.1 indexation lag timeline | 2026-09-23 | 13 July arrow first drawn in mid-June (x=1.45) -> placed at 1 Jul + 12/31; unlabelled trailing ticks removed; clean |
| 11 | 11.2 10y nominal, real, breakeven 2018-2026 | 2026-09-23 | breakeven = nominal - real within 0.03 (asserted); 2022 real-yield rise visible; clean |
| 11 | 11.3 monthly accrual of the reference index | 2026-09-23 | annotation clipped right, then left -> two lines anchored east; Aug 2022 bar 1.37 (asserted); clean |
| 11 | 11.4 CPI seasonal factors | 2026-09-23 | factors sum to zero (asserted); Mar max, Nov min; range stated 2010-2024 because 2025 lacks October (shutdown); clean |
| 12 | 12.1 pass-through flows schematic | 2026-09-23 | arrow labels overlapped the boxes -> boxes narrowed, spaced, labels raised; clean |
| 12 | 12.2 PSA ramp 50/100/200 | 2026-09-23 | 6% at 30 months for 100% (asserted in build tests); clean |
| 12 | 12.3 price-yield, responsive vs frozen speeds | 2026-09-23 | both at par at 6% (asserted); pass-through below frozen off the money on both sides; "at the money" label sat on the line -> anchor west; clean |
| 12 | 12.4 Fed MBS holdings 2007-2026 | 2026-09-23 | first holdings Jan 2009, resumptions 2012/2020, peak 2022 match the ledger; clean |
| 13 | 13.1 payer/receiver payoffs and time value | 2026-09-23 | annuity 7.80 slope (asserted); clean |
| 13 | 13.2 callable option flow schematic | 2026-09-23 | added (chapter short); arrow labels overlapped boxes -> three-line labels; clean |
| 13 | 13.3 Black vol equivalent of 90 bp normal (log scale) | 2026-09-23 | label sat on the axis frame, then on the curve -> bottom-left with arrow to the 0.36% line; text said 216% where the data give 215.2 -> 215 (caught at the render check, not by the numbers gate: add every quoted value to the test) ; clean |
| 13 | 13.4 German and Japanese 10y yields 2012-2022 | 2026-09-23 | was not referenced in the text -> cross-reference added; 38 and 24 negative months asserted; clean |
| 13 | 13.5 cube slice and smile (illustrative) | 2026-09-23 | two panels, shared legend below; clean |
| 14 | 14.1 spot value dates around holidays | 2026-09-23 | four cases match the build tests and the published example; clean |
| 14 | 14.2 spot market structure schematic | 2026-09-23 | client box overlapped the lower arrows and hid the dashed PB arrow -> boxes moved; clean |
| 14 | 14.3 turnover by instrument 2022/2025 | 2026-09-23 | tick labels collided -> two-line labels; legend then sat on them -> lowered; shares from the BIS release (data file); clean |
| 14 | 14.4 currency shares 2025 | 2026-09-23 | 89.2 label hit the frame -> ymax 110; clean |
| 15 | 15.1 request timeline under last look | 2026-09-23 | added; "quote sent" and "request arrives" labels touched -> spaced; clean |
| 15 | 15.2 move distribution, rejected tails | 2026-09-23 | added; 30.9/61.7% match the closed form (asserted); symmetric label sat on the curve -> moved to the tail; clean |
| 15 | 15.3 reject rates and mark-outs by hold (simulated) | 2026-09-23 | hold 0 dropped by the log axis (intended); "no last look" label on the symmetric line -> below; clean |
| 15 | 15.4 quote skewing schematic | 2026-09-23 | added; mid label collided with the short-inventory bid -> moved left; clean |
| 16 | 16.1 FX swap legs schematic | 2026-09-23 | near-leg label ran over both boxes -> boxes spread, leg headers added; clean |
| 16 | 16.2 forward points by tenor | 2026-09-23 | -106.7/-116.4 at 91 days (asserted); clean |
| 16 | 16.3 hedged Treasury vs JGB 2018-2026 | 2026-09-23 | hedged line clipped at -1 in 2023 -> ymin -2; 57 months below (asserted); clean |
| 16 | 16.4 Fed swap lines 2007-2026 | 2026-09-23 | month-end peak 554 vs weekly 583 quoted -> caption says "weekly high"; clean |
| 17 | 17.1 the day's fixes and cuts (London time) | 2026-09-23 | added; "WM/Reuters" inside a \foreach list was parsed as a key path (fatal) -> braces, then explicit nodes; labels crossed other lines -> NY cut below the axis, ECB label to the left; clean |
| 17 | 17.2 price path of a fixing order | 2026-09-23 | fixes 1.5/2.25/3 match the proposition (asserted); clean |
| 17 | 17.3 month-end hedge flows by return and ratio | 2026-09-23 | added; linear through zero as the formula says; clean |
| 17 | 17.4 dealer profit vs pre-hedged share | 2026-09-23 | band from the seeded simulation; clean |
| 18 | 18.1 onshore, offshore, NDF schematic | 2026-09-23 | added; clean |
| 18 | 18.2 NDF life cycle | 2026-09-23 | clean |
| 18 | 18.3 EURCHF 2010-2016 with the floor | 2026-09-23 | floor label crossed the 2011 dip and the 2015 jump -> two lines under the floor; never below 1.20 in the floor period (asserted); clean |
| 18 | 18.4 leverage multiples for the 15 Jan 2015 move | 2026-09-23 | "deposit lost" label on a bar, 7.2 on the frame -> moved, ymax 9; clean |
| 19 | 19.1 the three quotes as smile points | 2026-09-23 | added; RR label clipped and overlapping the BF label -> moved; clean |
| 19 | 19.2 USDJPY smile, regular vs premium-adjusted | 2026-09-23 | strikes match the example (asserted); clean |
| 19 | 19.3 regular vs premium-adjusted call delta | 2026-09-23 | added; label clipped twice -> three lines inside; the render showed the maximum is deep IN the money, and the text said "out of the money" -> corrected; clean |
| 19 | 19.4 down-and-out call value and delta | 2026-09-23 | delta 0.63 at the barrier (asserted); clean |
| 20 | 20.1 payment hours by currency and the yen-dollar window | 2026-09-23 | clean |
| 20 | 20.2 the Herstatt day | 2026-09-23 | added, after the ECB 2007 account; clean |
| 20 | 20.3 exposure profile gross / netted / PvP | 2026-09-23 | peaks 1,330 / 430 / 30 (asserted); gross and netted steps overlap at 330 between 04:00 and 06:00 (data checked); clean |
| 20 | 20.4 settlement by method, April 2025 | 2026-09-23 | added; values from the BIS article (data file); clean |
| 21 | 21.1 fallen-angel spread path | 2026-09-23 | added; "fair for BB+" label on the recovery segment -> moved left; clean |
| 21 | 21.2 bond vs Treasury and swap curves, G and I spreads | 2026-09-23 | 117.5 / 142.5 (asserted); clean |
| 21 | 21.3 HQM 10y minus Treasury 10y, 1984-2026 | 2026-09-23 | peak Oct 2008 5.04 (asserted); public Treasury data used instead of licensed index spreads; clean |
| 21 | 21.4 seniority and recovery schematic | 2026-09-23 | added; 100/80/0% asserted; clean |
| 22 | 22.1 expected RFQ cost by dealers asked | 2026-09-23 | minima 6/3/2 (asserted); clean |
| 22 | 22.2 simulated winning-bid discount | 2026-09-23 | densities integrate to one (asserted); clean |
| 22 | 22.3 portfolio trade schematic | 2026-09-23 | arrow label ran over both boxes -> two lines; clean |
| 22 | 22.4 bond ETF liquidity layer | 2026-09-23 | added; clean |
| 23 | 23.1 CDS cash flows schematic | 2026-09-23 | arrow labels ran into the boxes and the dashed-line labels -> wider spacing, side labels; clean |
| 23 | 23.2 upfront vs quoted spread, 100/500 coupons | 2026-09-23 | zero at each coupon (asserted); dots = example; clean |
| 23 | 23.3 survival curves at 100/300/800 bp | 2026-09-23 | monotone and ordered (asserted); clean |
| 23 | 23.4 Lehman first stage bids/offers | 2026-09-23 | pairs as published, offer - bid <= 2 (asserted); midpoint and final lines; clean |
| 23 | 23.5 second-stage order book | 2026-09-23 | reversed x, fills cross OI at 8.625 (asserted); label moved off the 8.5 step; clean |
| 24 | 24.1 constituents sorted, average/intrinsic/index lines | 2026-09-24 | caption first said three names off the chart; counted: two (asserted); clean |
| 24 | 24.2 skew trade P&L vs exit skew | 2026-09-24 | zero at entry, increasing (asserted); dots = problem; clean |
| 24 | 24.3 tranche stack schematic | 2026-09-24 | label touched the box edges -> wider box; clean |
| 24 | 24.4 tranche expected loss vs correlation (log) | 2026-09-24 | caption first said "senior tranches rise": the 7-15% peaks at 0.65 (asserted) -> caption fixed; clean |
| 24 | 24.5 finite-pool loss distribution, rho 0.1/0.4 | 2026-09-24 | first binned by 0.5% of loss, aliasing against 0.48% per default -> one point per default count; sums to one (asserted); clean |
| 25 | 25.1 CLO structure schematic | 2026-09-24 | arrow labels ran into the boxes -> wider spacing; clean |
| 25 | 25.2 interest waterfall schematic | 2026-09-24 | TikZ style named "step" clashed with the built-in key (fatal) -> "wstep"; "yes" moved off the arrow; clean |
| 25 | 25.3 BB OC ratio and equity cash paths | 2026-09-24 | last quarter's sale drew a spike at the edge -> domain 1:19; cut-off quarters asserted; clean |
| 25 | 25.4 equity IRR vs default rate | 2026-09-24 | monotone (asserted); caption said off-chart from 8.5%, it is 9% -> fixed; clean |
| 26 | 26.1 exchange offer value vs exit yield | 2026-09-24 | decreasing, cash gap constant (asserted); dots = example; clean |
| 26 | 26.2 holdout probability tree | 2026-09-24 | branch values asserted in the numbers gate; clean |
| 26 | 26.3 holdout vs participation, with/without CAC | 2026-09-24 | jump at 75% below tender (asserted); curves coincide below p* by construction; clean |
| 26 | 26.4 loss-absorbing stack, two orders | 2026-09-24 | clean |
| 27 | 27.1 give-up line schematic | 2026-09-24 | clean |
| 27 | 27.2 prime-of-prime chain | 2026-09-24 | clean |
| 27 | 27.3 NOP utilisation along a routed day | 2026-09-24 | never above 100% (asserted); first full at order 107 (asserted); clean |
| 27 | 27.4 daily cost of four allocation plans | 2026-09-24 | tick labels ran together -> two lines, legend lowered; totals asserted; clean |
| 28 | 28.1 documentation stack | 2026-09-24 | clean |
| 28 | 28.2 repo access routes | 2026-09-24 | arc label sat on the arc -> moved above its apex; clean |
| 28 | 28.3 annual cost of three routes | 2026-09-24 | a comma inside a legend entry split it, shifting every label by one -> braced; break-even asserted; clean |
| 28 | 28.4 break-even vs sponsor spread | 2026-09-24 | decreasing (asserted); dots asserted; clean |
| 29 | 29.1 growth rate vs fraction staked | 2026-09-24 | labels clipped by the frame and on the curve -> ymax raised, label moved; peak at 0.2 asserted; clean |
| 29 | 29.2 wealth percentiles after 300 flips | 2026-09-24 | 2-Kelly 10th percentile sat on the frame -> ymin 1e-4; clean |
| 29 | 29.3 P(ever halving) theory vs simulation | 2026-09-24 | first simulated the drawdown from the peak (always ~1 over 4,000 bets): the formula is for falls from the start -> fixed the build and the definition; clean |
| 29 | 29.4 growth vs multiple of estimated Kelly | 2026-09-24 | peak 0.7 vs theory 0.669 (asserted); clean |
| 30 | 30.1 distribution of the five-card sum | 2026-09-24 | "/pgf/number format/.cd" in yticklabel style swallowed the tick-scale label's "at" key (fatal) -> keys spelled in full, scaled ticks off; symmetric about 35 (asserted); clean |
| 30 | 30.2 maker's mid over one game | 2026-09-24 | path asserted (value 31, start 35, max 39); clean |
| 30 | 30.3 P&L by width, three tables and no updating | 2026-09-24 | the first version (independent draws per width) had noisy argmax -> common deals for every width; clean |
| 31 | 31.1 September 2026 calendar with blackout | 2026-09-24 | day numbers sat under the event arrows -> moved above the axis; "{1,...,21}" would trip the drafty gate -> explicit list; clean |
| 31 | 31.2 mean absolute moves, payroll vs other days | 2026-09-24 | bar label "4" -> fixed zerofill "4.0"; values asserted; clean |
| 31 | 31.3 payroll-day 2y vs 10y changes, classified | 2026-09-24 | caption first said "same direction" but some bull steepening days had the 10-year up -> caption states the classification rule; counts asserted; clean |
| 31 | 31.4 Treasury curve on three dates | 2026-09-24 | slopes and fly asserted; clean |
