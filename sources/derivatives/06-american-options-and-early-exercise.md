# 6. American Options and Early Exercise — brief and source ledger

## Brief

- **Hook.** The share pays a dividend of 1.00 tomorrow and trades at 100.30; the 80 call is bid 20.40. Holders who exercise tonight keep the dividend; holders who forget leave it to the writers.
- **Sections.** Why and when to exercise early; The exercise boundary; Dividends and rates as triggers; Approximations and bounds; The practical exercise decision.
- **Defines.** early-exercise premium, exercise boundary, Bermudan exercise, quadratic approximation.
- **Uses (defined earlier).** American exercise, European exercise, assignment (Book 1 ch. 23), dividend, ex-dividend date (Book 1 ch. 8), optimal stopping, free boundary, smooth pasting, variational inequality (Book 4 ch. 10), binomial model (ch. 2), escrowed dividend model (ch. 5).
- **Tutorial.** Compute the exercise boundary of an American put on a 2,000-step tree and compare it with the quadratic approximation; then find, for a call before an ex-dividend date, the dividend above which exercise is optimal.
- **Build.** `firm.american`: American pricer (tree with discrete dividends, Barone-Adesi-Whaley approximation) and an exercise-decision helper (exercise now or hold, with the threshold dividend).
- **Weekend problem.** The night before the ex-date — named result: the smallest dividend at which exercising the 80 call the night before is optimal, and the value transferred to writers when a given share of holders fails to exercise.
- **Facts to verify.** Merton 1973: no early exercise of a call without dividends; Barone-Adesi & Whaley 1987 JF; Bjerksund-Stensland 1993/2002; Pool, Stoll, Whaley 2008 'Failure to exercise call options' (J. Financial Markets); OCC exercise-by-exception threshold (reuse Book 1 ledger).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Pool, Stoll, Whaley, "Failure to exercise call options: an anomaly and a trading game", Journal of Financial Markets, February 2008: calls on stocks with quarterly dividends, January 1996 - April 2006; more than half of long positions that should be exercised the day before the ex-date are not; holders lost over $491 million over ten years; market makers capture most through a dividend spread strategy | Vanderbilt University news release, 26 Feb 2008, and SSRN record | https://news.vanderbilt.edu/2008/02/26/retail-investors-losing-big-bucks-by-failing-to-exercise-call-options-vanderbilt-research-shows-58253/ | 2026-09-24 | "more than half of outstanding long positions go unexercised"; "lose over $491 million over a ten-year period" (search summary of the release and abstract) | dat:dv:american-options-and-early-exercise:pool; omsources |
| F2 | Exercise by exception at expiry: equity and index options $.01 in the money | Book 1 ledger, ch. 23 F1 (OIC Options Exercise FAQ) | https://www.optionseducation.org/referencelibrary/faq/options-exercise | 2026-09-18 | reused row | §5; dat box |
| F3 | Barone-Adesi and Whaley, "Efficient analytic approximation of American option values", JF 42(2) (1987) 301-320 | IDEAS/RePEc | https://ideas.repec.org/a/bla/jfinan/v42y1987i2p301-20.html | 2026-09-24 | bibliographic record | def quadratic approximation; omsources |
| F4 | Bjerksund and Stensland, "Closed-form approximation of American options", Scandinavian Journal of Management 9 (1993) 87-99: a lower bound from a flat exercise trigger | ScienceDirect record | https://www.sciencedirect.com/science/article/abs/pii/095652219390009H | 2026-09-24 | "a closed form lower bound to the value of the American option based on imposing a feasible but non-optimal exercise strategy" (abstract via search) | §4; omsources |
| F5 | Merton (1973), Bell Journal 4(1) 141-183: no early exercise of calls without dividends | ch. 3 ledger F4 | https://www.hbs.edu/faculty/Pages/item.aspx?num=8804 | 2026-09-24 | reused row | prop when; omsources |

## EXCLUDED

- The Book 1 ledger URL for the OIC exercise FAQ is reused as recorded there; not re-fetched.
