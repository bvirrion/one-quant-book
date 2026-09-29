# 1. What Each Interview Tests, by Role — brief and source ledger

## Brief

- **Hook.** Two candidates leave the same building on the same afternoon with opposite verdicts on the same probability question. The trader candidate reached the right answer in four minutes and was marked down; the developer candidate gave a wrong first answer, tested it against a small case, found the error and fixed it, and was marked up. Nobody was being inconsistent: the two interviewers were measuring different jobs.
- **Sections.** What an interview measures: skills, signal and the rubric; The roles and the skills each is probed on (trader, researcher, developer, machine-learning engineer, bank quant, risk); Formats: the loop, the question types and the time each gets; How to prepare by role: a map of this book.
- **Defines.** interview loop, technical interview, interview rubric.
- **Uses (defined earlier).** risk trader (B17.16), execution trader (B17.16), algorithm supervisor (B17.16), quantitative researcher (B17.17), desk strategist (B17.18), model validator (B17.18), risk quant (B17.18), quant developer (B16.21), research engineer (B17.19), low-latency engineer (B17.20), machine-learning engineer (B12.28), portfolio manager (B17.22), pod analyst (B17.22), compliance officer (B17.24), control function (B17.24), sales-trader (B1.2), chief risk officer (B16.12), market maker (B1.1), proprietary trading firm (B1.1), hedge fund (B1.1), multi-manager platform (B1.1), asset manager (B1.1), structured interview (B16.10), pod (B8.28), sales-trader (B1.2).
- **Question bank.** 8 questions, 3/3/2. Families: 'what would this interviewer be scoring?' on a given question (the same question read for four roles); sizing up a role's day from its skills; choosing the preparation order for a stated background; reading a rubric and placing an answer on it; the expected number of interviews before an offer given stage pass rates (numeric). Roles: trader 3, researcher 2, developer 2, mle 1, bank 1, risk 1. Firms: any 6, market maker 2, bank 1, systematic fund 1.
- **Facts to verify.** Schmidt and Hunter 1998, and Sackett, Zhang, Berry and Lievens 2022, on the validity of structured interviews and work samples (pointer to Book 16 ch. 10 ledger); Campion, Palmer and Campion 1997 (Personnel Psychology), components of interview structure; firms' own published descriptions of what their interviews assess, one per firm type, from their careers pages (dated; named only with the page in the ledger, never with a question).
- **Data.** Figures: one schematic (roles against question families, a matrix). Code: iv_loop.py, the pass-rate arithmetic (expected interviews, offer probability through a loop); exact Fraction tests.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Sackett, Zhang, Berry and Lievens, Revisiting meta-analytic estimates of validity in personnel selection, Journal of Applied Psychology 107(11), 2040-2068, 2022: structured interviews emerge as the top-ranked selection procedure once range-restriction overcorrection is removed | Crossref (citation); Book 16 ch. 10 ledger F7 (content) | https://api.crossref.org/works/10.1037/apl0000994 | 2026-09-29 | title, journal, volume, issue, pages; finding as recorded in desk/10 F7 | section 1; omsources |
| F2 | Schmidt and Hunter, The validity and utility of selection methods in personnel psychology, Psychological Bulletin 124(2), 262-274, 1998 | Crossref | https://api.crossref.org/works/10.1037/0033-2909.124.2.262 | 2026-09-29 | title, journal, volume, pages | omsources |
| F3 | Campion, Palmer and Campion, A review of structure in the selection interview, Personnel Psychology 50(3), 655-702, 1997 | Crossref | https://api.crossref.org/works/10.1111/j.1744-6570.1997.tb00709.x | 2026-09-29 | title, journal, volume, issue, pages | section 1; omsources |

## EXCLUDED

- Firms' own published descriptions of what their interviews assess (planned in the brief): not used; the chapter states the mechanism by role, and Part I names firms only in ch. 2.

