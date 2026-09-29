# 19. Machine Learning — brief and source ledger

## Brief

- **Hook.** A candidate's model scored 71 per cent accuracy in cross-validation on daily direction and 50 in its first month live. Asked why, he says 'overfitting'. The interviewer asks him to name the three lines of his pipeline most likely to have leaked the future, and the interview starts there.
- **Sections.** Bias, variance and regularisation: the questions and the answers that score; Trees, ensembles and networks: what interviewers probe; Validation with time: leakage, purging and the honest test; Design questions: from a vague goal to a model, a target and a metric.
- **Defines.** machine-learning design question.
- **Uses (defined earlier).** bias--variance decomposition (B12.1), overfitting (B12.1), out-of-sample R-squared (B12.1), target leakage (B12.3), logistic regression (B12.4), decision tree (B12.5), random forest (B12.5), gradient boosting (B12.5), neural network (B12.7), proper scoring rule (B12.11), regularisation (B4.16), ridge regression (B4.16), lasso (B4.16), cross-validation (B4.16), walk-forward analysis (B7.20), purging (B7.20), embargo (B7.20), look-ahead bias (B7.3), point-in-time data (B7.3), backtest overfitting (B7.20).
- **Question bank.** 13 questions, 4/5/4. Families: bias and variance in a concrete setting (what happens to each with more data, more features, more regularisation); ridge against lasso geometry and correlated features; trees (why boosting overfits noisy returns, feature importance traps); networks (why a deep net on daily returns disappoints; initialisation and scaling questions); validation with time (find the leak in a described pipeline; why k-fold on overlapping labels lies, numeric inflation on a generated example); metrics (accuracy against a proper scoring rule for a trading decision); two design questions (predict fill probability for a passive order; flag toxic flow for a market maker). Roles: mle 6, researcher 6, developer 1, trader 1. Firms: systematic fund 5, market maker 3, proprietary firm 2, multi-manager fund 1, any 3.
- **Facts to verify.** none external: every numeric claim comes from generated data in the tests; method pointers to Book 12 ch. 1-7, 11 and Book 7 ch. 3, 20.
- **Data.** Figures: one chart (cross-validated against honest walk-forward score on a generated panel with overlapping labels, over twenty seeds; fig_iv_leak.py). Code: iv_ml.py (scikit-learn on generated data: the leak demonstrations, ridge and lasso paths with correlated features, the boosting-on-noise demonstration), asserted over many seeds; full-size runs reference-marked.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Lopez de Prado, Advances in Financial Machine Learning, 2018 (purging and embargoes) | Open Library catalogue | https://openlibrary.org/works/OL20583340W | 2026-09-29 | title, author, first publication 2018 | omsources |

## EXCLUDED

- Publisher (Wiley) of Lopez de Prado 2018: not in the catalogue record; kept as common bibliographic knowledge of a book already cited in Books 7 and 12.

