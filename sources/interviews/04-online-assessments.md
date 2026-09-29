# 4. Online Assessments — brief and source ledger

## Brief

- **Hook.** A timer in the corner of the screen counts down from eight minutes; the counter reads question 1 of 80; a wrong answer costs more than a blank. The candidate who answers everything finishes with a lower score than the one who skipped a fifth of the questions, and the assessment was designed so that she would.
- **Sections.** Timed arithmetic and the scoring rule: when to skip; Sequences, patterns and logic items; Automated coding assessments: hidden tests, edge cases and time limits; Probability quizzes and game-based assessments; accommodations and integrity rules.
- **Defines.** online assessment, numerical reasoning test, automated coding assessment.
- **Uses (defined earlier).** proper scoring rule (B12.11), Brier score (B16.26), recruiting cycle (ch2), CV screen (ch3), interview rubric (ch1).
- **Question bank.** 10 questions, 3/4/3. Families: timed arithmetic items done in the book's own way (three, with the time a fast method takes); the skip-or-guess rule under a negative marking scheme (numeric: the break-even confidence); number and letter sequences (finite differences, interleaved sequences, ratio sequences); a logic item (constraint elimination); an automated coding task with the edge cases its hidden tests would probe (Python, tested against an oracle); a timed probability item; reading a game-based assessment's hidden score. Roles: trader 5, researcher 3, developer 3, mle 1. Firms: market maker 5, proprietary firm 2, any 5.
- **Facts to verify.** published descriptions of online assessment formats by firms that describe them publicly (numerical test length and time, coding platform use, game-based assessments) (dated; named only with the page, never with a question); UK Equality Act 2010 s.20 and EHRC guidance: reasonable adjustments in recruitment tests (dated); US ADA Title I and EEOC guidance on employment tests and accommodations (dated); Hausknecht, Halpert, Di Paolo and Moriarty Gerrard 2007 (J. Applied Psychology), retesting and practice effects; NYC Local Law 144 and EU AI Act Annex III (pointer to ch3 ledger).
- **Data.** Figures: one chart (expected score against the share of questions attempted under the negative-marking rule, for three accuracy levels; figdata from fig_iv_skip.py). Code: iv_oa.py (scoring rule, break-even confidence, sequence solver by finite differences), iv_oa_code.py (the coding task and its oracle); Fraction tests, property tests over seeds.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F4 | Cormen, Leiserson, Rivest and Stein, Introduction to Algorithms, Fourth Edition, MIT Press, 2022 | Open Library edition record (ISBN 9780262046305) | https://openlibrary.org/isbn/9780262046305.json | 2026-09-29 | title ``Introduction to Algorithms, Fourth Edition'', publisher MIT Press, 2022 | omsources |
| F1 | Hausknecht, Halpert, Di Paolo and Moriarty Gerrard, Retesting in selection: a meta-analysis of coaching and practice effects for tests of cognitive ability, J. Applied Psychology 92(2), 373-385, 2007: 50 studies, 107 samples, 134,436 participants, adjusted overall effect size .26 | OpenAlex (abstract and bibliographic data) | https://api.openalex.org/works/doi:10.1037/0021-9010.92.2.373 | 2026-09-29 | "Results from 107 samples and 134,436 participants revealed an adjusted overall effect size of .26" | met:iv:online-assessments:timed; omsources |
| F2 | Equality Act 2010 s.20: duty to make reasonable adjustments where a provision, criterion or practice puts a disabled person at a substantial disadvantage; Schedule 8 applies it to employers | legislation.gov.uk | https://www.legislation.gov.uk/ukpga/2010/15/section/20 | 2026-09-29 | "where a provision, criterion or practice of A's puts a disabled person at a substantial disadvantage ... to take such steps as it is reasonable to have to take to avoid the disadvantage" | dat:iv:online-assessments:adjust |
| F3 | 29 CFR 1630.11 Administration of tests: tests must be administered so that results reflect the skills the test purports to measure rather than impaired sensory, manual or speaking skills | eCFR (versioner API, 2026-09-01) | https://www.ecfr.gov/current/title-29/section-1630.11 | 2026-09-29 | "the test results accurately reflect the skills, aptitude, or whatever other factor ... that the test purports to measure, rather than reflecting the impaired sensory, manual, or speaking skills" | dat:iv:online-assessments:adjust |

## EXCLUDED

- Firms' published numerical-test formats (item counts and times): only prep sites and forums state them; not used. The hook's eight minutes and eighty items are a constructed scene, not a firm's test. Retake limits: pointer to ch. 2 F4.

