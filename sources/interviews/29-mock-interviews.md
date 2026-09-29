# 29. Mock Interviews — brief and source ledger

## Brief

- **Hook.** Two transcripts of the same forty-minute interview for the same trading role, same questions, same interviewer. Both candidates reached most of the right answers. One was hired. The assessor's margin notes on the other say 'did not update', 'did not check', and, twice, 'no number'.
- **Sections.** How to read a transcript; Trader; Researcher; Developer; Machine-learning engineer; Bank quant; Portfolio-manager hire.
- **Defines.** mock interview.
- **Uses (defined earlier).** risk trader (B17.16), execution trader (B17.16), algorithm supervisor (B17.16), quantitative researcher (B17.17), desk strategist (B17.18), model validator (B17.18), risk quant (B17.18), quant developer (B16.21), research engineer (B17.19), low-latency engineer (B17.20), machine-learning engineer (B12.28), portfolio manager (B17.22), pod analyst (B17.22), compliance officer (B17.24), control function (B17.24), sales-trader (B1.2), chief risk officer (B16.12), interview rubric (ch1), interview loop (ch1), think-aloud protocol (ch5), sanity check (ch5), trading game (ch6), Fermi estimate (ch9), calibrated interval (ch9), system-design interview (ch26), machine-learning design question (ch19), STAR structure (ch28), track record portability (B16.25), drawdown limit (B8.28), pod (B8.28), sub-portfolio manager (B17.22).
- **Question bank.** 18 questions, 6/6/6: six transcribed interviews (trader at a market maker; researcher at a systematic fund; developer at a proprietary firm; machine-learning engineer at a systematic fund; bank quant at a bank; portfolio-manager hire at a multi-manager fund), each about 3 pp with three `interviewq` inside the transcript (one of each star), the candidate's answers in the transcript and the assessor's commentary in the margin; the solutions give the model answer and what the assessor scored. All questions new and different from ch. 1-28's. Roles: one interview per role (trader, researcher, developer, mle, bank; the PM hire tagged trader, researcher). Firms: market maker, systematic fund 2, proprietary firm, bank, multi-manager fund.
- **Facts to verify.** none external beyond pointers: the PM-hire interview's track-record questions use Book 16 ch. 3 and 25 and Book 17 ch. 22 (by outline).
- **Data.** Figures: none planned (the transcript layout is a two-column environment or margin notes built from existing boxes; no new macro unless unavoidable). Code: iv_mock.py (every number spoken in a transcript or its solution, asserted: game values, estimates, the researcher's test statistic, the developer's complexity counts, the bank quant's prices, the PM's track-record statistics).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|

No external fact: the chapter prints composite transcripts; every number is in `code/interviews/29-mock-interviews` (six tests), and the pointers are to Books 5, 12, 16 and 17 and to chapters of this book.

## EXCLUDED

