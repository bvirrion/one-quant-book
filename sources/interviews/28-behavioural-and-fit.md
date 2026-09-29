# 28. Behavioural and Fit — brief and source ledger

## Brief

- **Hook.** 'Tell me about the worst loss you have been responsible for.' The candidate who answers with a loss that was someone else's fault, or a loss that was not a loss, has answered a different question. The one who names the number, what she believed at the time, what she did in the first hour and what she changed afterwards has answered the one being scored.
- **Sections.** What behavioural questions measure, and the evidence that they do; Structuring an answer: situation, task, action, result; Why trading, why this firm, why this role; The loss question and integrity scenarios.
- **Defines.** behavioural question, STAR structure, integrity scenario.
- **Uses (defined earlier).** structured interview (B16.10), outcome bias (B16.26), pre-mortem (B16.26), decision journal (B16.26), personal account dealing (B16.16), inside information (B16.16), information barrier (B16.16), market abuse (B16.16), stop-loss rule (B16.8), interview rubric (ch1), final round (ch6).
- **Question bank.** 10 questions, 3/4/3. Families: why trading or research, why this firm type (with what a scoring answer contains); a teamwork or conflict question; the loss question (outcome against decision quality); a mistake-in-production question for developers; integrity scenarios (a friend's tip that may be inside information; a colleague's backtest you believe is wrong before a deadline; a personal trade in a name on the watch list; a fat-finger you alone noticed) -- each answer tied to the rule it engages, no legal advice; the questions to ask the interviewer. Roles: trader 3, researcher 2, developer 2, risk 1, bank 1, mle 1. Firms: any 6, market maker 1, multi-manager fund 1, bank 1, asset manager 1.
- **Facts to verify.** Janz 1982 (J. Applied Psychology), patterned behaviour description interviews; Latham, Saari, Pursell and Campion 1980 (J. Applied Psychology), the situational interview; the documented origin of the STAR acronym (a training organisation's publication, if one is citable; otherwise stated as common practice); Taylor and Small 2002 or a later meta-analysis comparing past-behaviour and situational questions; FCA Code of Conduct sourcebook (COCON) individual conduct rules, as the rule an integrity scenario engages (dated; pointer to Book 16 ch. 16); EU Market Abuse Regulation articles 7, 8 and 14 (pointer to Book 16 ch. 16 ledger).
- **Data.** Figures: none planned. Code: tests/test_solutions.py holds the chapter's few numbers (the loss question's arithmetic, if any); most answers are qualitative and carry no test.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Janz, Initial comparisons of patterned behavior description interviews versus unstructured interviews, J. Applied Psychology 67(5), 577-580, 1982 | Crossref | https://api.crossref.org/works/10.1037/0021-9010.67.5.577 | 2026-09-29 | title, journal, volume, issue, pages | section 1; omsources |
| F2 | Latham, Saari, Pursell and Campion, The situational interview, J. Applied Psychology 65(4), 422-427, 1980 | Crossref | https://api.crossref.org/works/10.1037/0021-9010.65.4.422 | 2026-09-29 | title, journal, volume, issue, pages | section 1; omsources |
| F3 | Taylor and Small, Asking applicants what they would do versus what they did do: a meta-analytic comparison of situational and past behaviour employment interview questions, JOOP 75(3), 277-294, 2002: both formats valid; past-behaviour questions with descriptively anchored scales mean validity .63 against .47 for situational | Crossref (citation); OpenAlex (abstract) | https://api.crossref.org/works/10.1348/096317902320369712 | 2026-09-29 | "yielded a substantially higher mean validity estimate than studies using the situational question format with descriptively-anchored answer rating scales (.63 versus .47)" | section 1; omsources |
| F4 | MAR (Regulation (EU) No 596/2014) art. 10: unlawful disclosure of inside information; art. 14: a person shall not engage in insider dealing, recommend or induce it, or unlawfully disclose inside information; art. 8 insider dealing (pointer: ledger desk/16 F3) | EU Publications Office, CELEX 32014R0596 | http://publications.europa.eu/resource/celex/32014R0596 | 2026-09-29 | "Article 14 ... A person shall not: (a) engage or attempt to engage in insider dealing; (b) recommend ...; or (c) unlawfully disclose inside information." | section 4; solution iq 8 |

## EXCLUDED

- The documented origin of the STAR acronym: no citable primary source found without a search; the text calls it a structure and makes no claim about its origin.
- FCA COCON individual conduct rules: not needed; the integrity answers rest on MAR.

