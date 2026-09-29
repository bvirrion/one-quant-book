# 8. Mental Arithmetic — brief and source ledger

## Brief

- **Hook.** Across the desk: 'Seven per cent of 340 million, spread over 250 trading days, per day?' The answer, about 95 thousand, comes back in five seconds from the candidate who turned seven per cent over 250 days into 2.8 basis points a day, and 2.8 basis points of 340 million into 340 times 280; the one who started long multiplication in her head is still carrying digits.
- **Sections.** Products and squares: decomposition around round numbers; Fractions, percentages and reciprocals: the table worth knowing; Roots, logarithms and compounding: the rule of 72 and its error; Checking an answer: magnitude, last digit and casting out nines.
- **Defines.** casting out nines, rule of 72.
- **Uses (defined earlier).** sanity check (ch5), numerical reasoning test (ch4), notional (B1.7), carry (B1.7).
- **Question bank.** 14 questions, 5/5/4. Families: two-digit and three-digit products (difference of squares, near-100 products); percentages of large numbers and per-day conversions; fractions to decimals via a reciprocal table (1/7, 1/13, 1/17); square roots by linearisation (the error bound); doubling times and compounding (rule of 72 against the exact ln 2 answer, with the error at 1 to 20 per cent); a chained desk calculation in basis points; verifying a product by casting out nines and its blind spot (transposed digits). Roles: trader 9, researcher 3, bank 2, risk 1. Firms: market maker 6, proprietary firm 3, bank 2, any 4.
- **Facts to verify.** none external: all answers are computed; the history of casting out nines and the rule of 72 (Pacioli 1494) cited in omsources from a scholarly source.
- **Data.** Figures: one chart (the rule of 72, 69.3 and 70 against the exact doubling time, 1 to 25 per cent; fig_iv_rule72.py). Code: iv_arith.py (every printed answer, the approximations and their error bounds); exact tests (Fraction, math.isclose to the printed precision).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|

## EXCLUDED

- History of casting out nines and of the rule of 72 (Pacioli 1494 in the brief): not stated; the chapter needs only the mathematics.

No external facts: every number is computed (tests/test_solutions.py).

