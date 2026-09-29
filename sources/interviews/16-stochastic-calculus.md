# 16. Stochastic Calculus — brief and source ledger

## Brief

- **Hook.** 'What is d(W squared)?' The candidate writes 2W dW and stops. The interviewer asks for the expectation of W squared at time t, and the missing dt appears on its own: a zero expectation for a quantity that cannot be negative.
- **Sections.** Itô's formula as a calculation rule; Martingales, hitting times and the reflection principle; Changes of measure in one line; From an SDE to a PDE and back.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** Brownian motion (B4.2), hitting time (B4.2), first-passage time (B4.2), quadratic variation (B4.2), Brownian bridge (B4.2), Itô integral (B4.3), Itô process (B4.3), martingale (B4.1), stopping time (B4.1), equivalent martingale measure (B4.5), risk-neutral measure (B4.5), numeraire (B4.5), infinitesimal generator (B4.4), Black--Scholes equation (B5.3), sanity check (ch5).
- **Question bank.** 13 questions, 4/5/4. Families: Itô on polynomials and exponentials of W (which are martingales); the expected hitting time of a two-sided barrier and its probability (with and without drift, numeric); the distribution of the running maximum by reflection; E[W_tau] and optional stopping pitfalls; a Girsanov question (the drift that makes a process a martingale; pricing a digital by a change of measure); the Feynman-Kac link for a simple payoff; the integral of W over [0, T] (its law, numeric variance). Roles: researcher 5, bank 5, trader 2, risk 1. Firms: bank 5, systematic fund 3, market maker 2, any 3.
- **Facts to verify.** none external: all answers derived (pointers to Book 4 ch. 2-5).
- **Data.** Figures: one chart (simulated paths with the running maximum and the reflected path, and the empirical against the exact law of the maximum; fig_iv_reflect.py). Code: iv_stoch.py (sympy for Itô calculations; Monte Carlo over many seeds for every probability and expectation, with discretisation bias controlled by the time-step-divided-by-four check).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Karatzas and Shreve, Brownian Motion and Stochastic Calculus, Springer (first edition 1988; second edition 1991) | Open Library catalogue | https://openlibrary.org/works/OL1858792W | 2026-09-29 | title, authors, first publication 1988 | omsources |

## EXCLUDED

- Karatzas and Shreve: cited by the first edition (1988), the date the catalogue confirms.

