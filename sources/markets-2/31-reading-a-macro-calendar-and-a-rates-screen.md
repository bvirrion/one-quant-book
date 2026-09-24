# 31. Reading a Macro Calendar and a Rates Screen — brief and source ledger

## Brief

- **Hook.** On payroll Fridays at 08:30 Eastern the employment report comes out; from 2023 to 2026 the 2-year Treasury yield moved on those days by more than twice as much as on other days.
- **Sections.** The calendar; Consensus and surprise; Positioning into events; Reading curve shapes; A rates screen at a glance.
- **Defines.** economic release, consensus forecast, data surprise, blackout period, steepener, flattener, curve fly, bull steepening, bear flattening.
- **Uses (defined earlier).** policy rate, DV01, par swap rate, swap spread, cross-currency basis, implied policy path.
- **Tutorial.** Build a release calendar, measure surprise-to-yield-move sensitivities on synthetic data, and summarise a curve screen.
- **Build.** `firm.macrocal`: event calendar and curve-shape summary.
- **Weekend problem.** Payrolls Friday — named result: the DV01-neutral 2s10s position size and its P&L under the surprise.
- **Facts to verify.** BLS employment situation timing (08:30 ET, first Friday); FOMC blackout rules; US CPI release time; ECB meeting schedule.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Employment Situation 2026 schedule: releases at 08:30 AM ET; e.g. 4 Sep 2026 (August), 2 Oct 2026, 6 Nov 2026, 4 Dec 2026 | BLS, Employment Situation release schedule | https://www.bls.gov/schedule/news_release/empsit.htm | 2026-09-24 | "Sep. 04, 2026 08:30 AM" (schedule row) | §1; fig; dat:m2:reading-a-macro-calendar-and-a-rates-screen:calendar |
| F2 | Employment Situation release dates 2023-2026 from the BLS archive (file names); the October 2025 release was "Not published because of 2025 lapse in federal government appropriations"; September 2025 data released 20 Nov 2025 | BLS, archive of Employment Situation news releases | https://www.bls.gov/bls/news-release/empsit.htm | 2026-09-24 | "October 2025 Employment Situation – Not published because of 2025 lapse in federal government appropriations" | §2; fig; data/markets-2/bls_empsit_release_dates.csv |
| F3 | CPI 2026 schedule: releases at 08:30 AM ET; August 2026 CPI on 11 Sep 2026, September on 14 Oct 2026 | BLS, CPI release schedule | https://www.bls.gov/schedule/news_release/cpi.htm | 2026-09-24 | "Sep. 11, 2026 08:30 AM" (schedule row) | §1; fig |
| F4 | FOMC blackout: begins 12:00 a.m. ET the second Saturday before a meeting, ends 11:59 p.m. ET the day after; e.g. a Tuesday meeting: from the Saturday ten days earlier to the Thursday after a Wednesday end; if the second Friday before is a federal holiday, begins that Friday; participants refrain from expressing views on macroeconomic developments or monetary policy to the public; policy adopted 22 Jun 2011, reaffirmed 27 Jan 2026 | FOMC, "Policy on External Communications of Committee Participants" | https://www.federalreserve.gov/monetarypolicy/files/FOMC_ExtCommunicationParticipants.pdf | 2026-09-24 | "The blackout period will begin at 12:00 a.m. Eastern Time the second Saturday before a meeting and end at 11:59 p.m. Eastern Time the day after a meeting." | §3; build; dat:m2:reading-a-macro-calendar-and-a-rates-screen:calendar |
| F5 | FOMC 2026 meetings: Jan 27-28, Mar 17-18*, Apr 28-29, Jun 16-17*, Jul 28-29, Sep 15-16*, Oct 27-28, Dec 8-9* (* with Summary of Economic Projections) | Federal Reserve, FOMC calendars | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | 2026-09-24 | "September 15-16*" | §1; §3; fig |
| F6 | Daily Treasury yields (H.15): 2y/10y 1 Dec 2022 to 22 Sep 2026; 2y/5y/10y/30y 2 Sep 2025 to 22 Sep 2026 (e.g. 22 Sep 2026: 4.71/4.83/4.96/5.29; 22 Sep 2025: 3.61/3.71/4.15/4.77); payroll days: 2 Aug 2024 2y -28 bp, 10y -19 bp; 4 Oct 2024 2y +23 bp, 10y +13 bp; mean absolute 2y change 10.2 bp on 44 payroll days vs 4.6 bp on other days (2023-2026) | FRED DGS2, DGS5, DGS10, DGS30 (data/markets-2/ust_2y10y_daily.csv, ust_curve_daily.csv) | https://fred.stlouisfed.org/series/DGS2 | 2026-09-24 | computed from the downloaded series (tests assert every figure) | hook; §2; §4; §5; problem; dat:m2:reading-a-macro-calendar-and-a-rates-screen:screen |

## EXCLUDED

- Consensus forecasts of payrolls (Bloomberg, Reuters surveys): licensed; the surprise regression uses synthetic data and says so.
- Intraday trading volume at 08:30 (the brief's hook): no public source fetched; replaced by daily yield changes from H.15.
- FOMC statement release time and ECB meeting schedule: not needed; not stated.

